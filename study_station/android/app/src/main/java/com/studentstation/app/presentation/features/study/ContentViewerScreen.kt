package com.studentstation.app.presentation.features.study

import android.content.Intent
import android.net.Uri
import android.speech.tts.TextToSpeech
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.BookmarkBorder
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import com.studentstation.app.data.local.entity.StudyContentEntity
import com.studentstation.app.data.remote.api.StudentStationApi
import com.studentstation.app.data.remote.dto.ChatRequestDto
import com.studentstation.app.domain.repository.StudyContentRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.Locale
import javax.inject.Inject

data class ChatMessage(val text: String, val isUser: Boolean, val isError: Boolean = false)

@HiltViewModel
class ContentViewerViewModel @Inject constructor(
    private val repository: StudyContentRepository,
    private val api: StudentStationApi
) : ViewModel() {

    private val _content = MutableStateFlow<StudyContentEntity?>(null)
    val content: StateFlow<StudyContentEntity?> = _content.asStateFlow()

    private val _chatMessages = MutableStateFlow<List<ChatMessage>>(
        listOf(ChatMessage("Hello! I am your AI Tutor. 🎓\nAsk me any question or doubt about this chapter!", false))
    )
    val chatMessages: StateFlow<List<ChatMessage>> = _chatMessages.asStateFlow()

    private val _isChatLoading = MutableStateFlow(false)
    val isChatLoading: StateFlow<Boolean> = _isChatLoading.asStateFlow()

    fun loadContent(id: Long) {
        viewModelScope.launch {
            _content.value = repository.getContentById(id)
            repository.updateProgress(id, 0)
        }
    }

    fun toggleBookmark() {
        viewModelScope.launch {
            _content.value?.let { current ->
                val newStatus = !current.isBookmarked
                repository.toggleBookmark(current.id, newStatus)
                _content.value = current.copy(isBookmarked = newStatus)
            }
        }
    }

    fun sendChatMessage(message: String) {
        val chapter = _content.value ?: return
        if (message.isBlank()) return

        _chatMessages.value = _chatMessages.value + ChatMessage(message, true)
        _isChatLoading.value = true

        viewModelScope.launch {
            try {
                val response = api.sendChatMessage(ChatRequestDto(chapterId = chapter.id, message = message))
                if (response.success && response.reply != null) {
                    _chatMessages.value = _chatMessages.value + ChatMessage(response.reply, false)
                } else {
                    _chatMessages.value = _chatMessages.value + ChatMessage("Oops! ${response.error ?: "Network error"}", false, true)
                }
            } catch (e: Exception) {
                _chatMessages.value = _chatMessages.value + ChatMessage("Connection failed. Please check internet.", false, true)
            } finally {
                _isChatLoading.value = false
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ContentViewerScreen(
    contentId: Long,
    viewModel: ContentViewerViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit
) {
    val content by viewModel.content.collectAsStateWithLifecycle()
    val chatMessages by viewModel.chatMessages.collectAsStateWithLifecycle()
    val isChatLoading by viewModel.isChatLoading.collectAsStateWithLifecycle()
    
    var selectedTabIndex by remember { mutableIntStateOf(1) } // Default to AI Notes
    val tabs = listOf("Original Book", "AI Notes", "AI Tutor")

    val context = LocalContext.current
    var textToSpeech by remember { mutableStateOf<TextToSpeech?>(null) }
    var isSpeaking by remember { mutableStateOf(false) }

    DisposableEffect(Unit) {
        textToSpeech = TextToSpeech(context) { status ->
            if (status == TextToSpeech.SUCCESS) {
                textToSpeech?.language = Locale("en", "IN")
            }
        }
        onDispose {
            textToSpeech?.stop()
            textToSpeech?.shutdown()
        }
    }

    LaunchedEffect(contentId) {
        viewModel.loadContent(contentId)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Text(content?.chapterName ?: "Loading...", style = MaterialTheme.typography.titleMedium, maxLines = 1) 
                },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) { Icon(Icons.Default.ArrowBack, contentDescription = "Back") }
                },
                actions = {
                    if (selectedTabIndex == 1 && content != null) {
                        IconButton(onClick = {
                            if (isSpeaking) {
                                textToSpeech?.stop()
                                isSpeaking = false
                            } else {
                                textToSpeech?.speak(content!!.contentText, TextToSpeech.QUEUE_FLUSH, null, null)
                                isSpeaking = true
                            }
                        }) {
                            Icon(if (isSpeaking) Icons.Default.VolumeOff else Icons.Default.VolumeUp, "Listen")
                        }
                    }
                    content?.let { c ->
                        IconButton(onClick = { viewModel.toggleBookmark() }) {
                            Icon(
                                imageVector = if (c.isBookmarked) Icons.Filled.Bookmark else Icons.Outlined.BookmarkBorder,
                                contentDescription = "Bookmark",
                                tint = if (c.isBookmarked) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
                            )
                        }
                    }
                }
            )
        }
    ) { paddingValues ->
        if (content == null) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
        } else {
            Column(modifier = Modifier.fillMaxSize().padding(paddingValues)) {
                TabRow(selectedTabIndex = selectedTabIndex) {
                    tabs.forEachIndexed { index, title ->
                        Tab(
                            selected = selectedTabIndex == index,
                            onClick = { selectedTabIndex = index },
                            text = { Text(title) }
                        )
                    }
                }
                
                when (selectedTabIndex) {
                    0 -> PdfTabContent(content!!.contentUrl)
                    1 -> NotesTabContent(content!!)
                    2 -> ChatTabContent(chatMessages, isChatLoading) { viewModel.sendChatMessage(it) }
                }
            }
        }
    }
}

@Composable
fun PdfTabContent(pdfUrl: String) {
    val context = LocalContext.current
    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        if (pdfUrl.isNotEmpty()) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Icon(Icons.Default.MenuBook, contentDescription = null, modifier = Modifier.size(64.dp), tint = MaterialTheme.colorScheme.primary)
                Spacer(modifier = Modifier.height(16.dp))
                Button(onClick = {
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(pdfUrl))
                    context.startActivity(intent)
                }) {
                    Text("Open Original PDF Book")
                }
            }
        } else {
            Text("No PDF available for this chapter.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
fun NotesTabContent(content: StudyContentEntity) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        Text(text = content.title, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
        Spacer(modifier = Modifier.height(8.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Badge(containerColor = MaterialTheme.colorScheme.secondaryContainer) {
                Text(content.subject, color = MaterialTheme.colorScheme.onSecondaryContainer)
            }
            Spacer(modifier = Modifier.width(8.dp))
            Text("Class ${content.classLevel} • ${content.board}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Spacer(modifier = Modifier.height(24.dp))
        HorizontalDivider()
        Spacer(modifier = Modifier.height(24.dp))
        Text(text = content.contentText, style = MaterialTheme.typography.bodyLarge, lineHeight = MaterialTheme.typography.bodyLarge.lineHeight * 1.5f)
        Spacer(modifier = Modifier.height(40.dp))
    }
}

@Composable
fun ChatTabContent(messages: List<ChatMessage>, isLoading: Boolean, onSend: (String) -> Unit) {
    var text by remember { mutableStateOf("") }
    Column(modifier = Modifier.fillMaxSize()) {
        LazyColumn(
            modifier = Modifier.weight(1f).padding(16.dp),
            reverseLayout = false
        ) {
            items(messages) { msg ->
                ChatBubble(msg)
                Spacer(modifier = Modifier.height(8.dp))
            }
            if (isLoading) {
                item {
                    CircularProgressIndicator(modifier = Modifier.size(24.dp).padding(8.dp))
                }
            }
        }
        Row(modifier = Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            OutlinedTextField(
                value = text,
                onValueChange = { text = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text("Ask a question...") },
                shape = RoundedCornerShape(24.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            IconButton(
                onClick = { 
                    if (text.isNotBlank()) {
                        onSend(text)
                        text = ""
                    }
                },
                modifier = Modifier.background(MaterialTheme.colorScheme.primary, CircleShape)
            ) {
                Icon(Icons.Default.Send, contentDescription = "Send", tint = MaterialTheme.colorScheme.onPrimary)
            }
        }
    }
}

@Composable
fun ChatBubble(message: ChatMessage) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (message.isUser) Arrangement.End else Arrangement.Start
    ) {
        if (!message.isUser) {
            Box(modifier = Modifier.size(32.dp).background(MaterialTheme.colorScheme.secondary, CircleShape), contentAlignment = Alignment.Center) {
                Text("🤖", style = MaterialTheme.typography.bodySmall)
            }
            Spacer(modifier = Modifier.width(8.dp))
        }
        Surface(
            shape = RoundedCornerShape(16.dp).copy(
                bottomEnd = if (message.isUser) RoundedCornerShape(0.dp) else RoundedCornerShape(16.dp),
                bottomStart = if (!message.isUser) RoundedCornerShape(0.dp) else RoundedCornerShape(16.dp)
            ),
            color = if (message.isError) MaterialTheme.colorScheme.errorContainer 
                    else if (message.isUser) MaterialTheme.colorScheme.primary 
                    else MaterialTheme.colorScheme.surfaceVariant
        ) {
            Text(
                text = message.text,
                modifier = Modifier.padding(12.dp),
                color = if (message.isError) MaterialTheme.colorScheme.onErrorContainer 
                        else if (message.isUser) MaterialTheme.colorScheme.onPrimary 
                        else MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
