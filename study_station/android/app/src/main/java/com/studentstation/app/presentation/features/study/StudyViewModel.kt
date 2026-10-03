package com.studentstation.app.presentation.features.study

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.studentstation.app.data.local.dao.SubjectInfo
import com.studentstation.app.data.local.entity.StudyContentEntity
import com.studentstation.app.domain.repository.StudyContentRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class StudyUiState(
    val classLevel: Int = 10, // Default class 10 for now
    val subjects: List<SubjectInfo> = emptyList(),
    val selectedSubject: String? = null,
    val contentList: List<StudyContentEntity> = emptyList(),
    val isLoading: Boolean = false
)

@HiltViewModel
class StudyViewModel @Inject constructor(
    private val studyContentRepository: StudyContentRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(StudyUiState())
    val uiState: StateFlow<StudyUiState> = _uiState.asStateFlow()

    init {
        loadSubjects(10)
    }

    fun loadSubjects(classLevel: Int) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, classLevel = classLevel)
            
            // Preload data if none exists
            studyContentRepository.preloadDefaultContent(classLevel)
            
            val subjects = studyContentRepository.getSubjectsForClass(classLevel)
            _uiState.value = _uiState.value.copy(
                subjects = subjects,
                selectedSubject = subjects.firstOrNull()?.subject,
                isLoading = false
            )
            
            // Load content for first subject
            subjects.firstOrNull()?.let {
                loadContentForSubject(classLevel, it.subject)
            }
        }
    }

    fun selectSubject(subject: String) {
        _uiState.value = _uiState.value.copy(selectedSubject = subject)
        loadContentForSubject(_uiState.value.classLevel, subject)
    }

    private fun loadContentForSubject(classLevel: Int, subject: String) {
        viewModelScope.launch {
            studyContentRepository.getContentBySubject(classLevel, subject).collect { content ->
                _uiState.value = _uiState.value.copy(contentList = content)
            }
        }
    }
}
