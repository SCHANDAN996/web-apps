package com.studentstation.app.presentation.features.settings

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.studentstation.app.data.local.dao.StreakDao
import com.studentstation.app.data.local.entity.StreakEntity
import com.studentstation.app.domain.model.BlockedApp
import com.studentstation.app.domain.model.TimerStrategy
import com.studentstation.app.domain.repository.AppConfigRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

private val Context.dataStore by preferencesDataStore(name = "settings")
private val PARENT_PIN_KEY = stringPreferencesKey("parent_pin")

data class SettingsUiState(
    val blockedApps: List<BlockedApp> = emptyList(),
    val parentPinEnabled: Boolean = false,
    val parentPin: String = "",
    val showPinDialog: Boolean = false,
    val showPinVerifyDialog: Boolean = false,
    val isServiceActive: Boolean = false
)

@HiltViewModel
class SettingsViewModel @Inject constructor(
    @ApplicationContext private val context: Context,
    private val appConfigRepo: AppConfigRepository,
    private val streakDao: StreakDao
) : ViewModel() {
    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            appConfigRepo.getAllConfigs().collect { apps ->
                _uiState.update { it.copy(blockedApps = apps) }
            }
        }
        // Load saved PIN
        viewModelScope.launch {
            context.dataStore.data.collect { prefs ->
                val pin = prefs[PARENT_PIN_KEY] ?: ""
                _uiState.update { it.copy(parentPin = pin, parentPinEnabled = pin.isNotEmpty()) }
            }
        }
        // Initialize streak row if not exists
        viewModelScope.launch {
            if (streakDao.getStreakSync() == null) {
                streakDao.upsertStreak(StreakEntity())
            }
        }
    }

    fun initializeDefaultApps() {
        viewModelScope.launch {
            val defaults = listOf(
                BlockedApp(packageName = "com.google.android.youtube", displayName = "YouTube Shorts",
                    blockShorts = true, blockReels = false, waitTimeSeconds = 30),
                BlockedApp(packageName = "com.instagram.android", displayName = "Instagram",
                    blockShorts = false, blockReels = true, waitTimeSeconds = 30),
                BlockedApp(packageName = "com.facebook.katana", displayName = "Facebook",
                    blockShorts = false, blockReels = true, waitTimeSeconds = 30),
                BlockedApp(packageName = "com.facebook.lite", displayName = "Facebook Lite",
                    blockShorts = false, blockReels = true, waitTimeSeconds = 30),
                BlockedApp(packageName = "com.snapchat.android", displayName = "Snapchat",
                    blockShorts = true, blockReels = false, waitTimeSeconds = 30,
                    isBlocked = false),
                BlockedApp(packageName = "com.twitter.android", displayName = "Twitter / X",
                    blockShorts = true, blockReels = false, waitTimeSeconds = 30,
                    isBlocked = false),
                BlockedApp(packageName = "com.instagram.barcelona", displayName = "Threads",
                    blockShorts = true, blockReels = false, waitTimeSeconds = 30,
                    isBlocked = false)
            )
            defaults.forEach { app ->
                if (appConfigRepo.getConfigByPackage(app.packageName) == null) {
                    appConfigRepo.saveConfig(app)
                }
            }
        }
    }

    fun toggleAppBlocking(app: BlockedApp) {
        viewModelScope.launch {
            appConfigRepo.updateConfig(app.copy(isBlocked = !app.isBlocked))
        }
    }

    fun updateWaitTime(app: BlockedApp, seconds: Int) {
        viewModelScope.launch {
            appConfigRepo.updateConfig(app.copy(waitTimeSeconds = seconds))
        }
    }

    fun updateTimerStrategy(app: BlockedApp, strategy: TimerStrategy) {
        viewModelScope.launch {
            appConfigRepo.updateConfig(app.copy(timerStrategy = strategy))
        }
    }

    fun toggleBlockShorts(app: BlockedApp) {
        viewModelScope.launch {
            appConfigRepo.updateConfig(app.copy(blockShorts = !app.blockShorts))
        }
    }

    fun toggleBlockReels(app: BlockedApp) {
        viewModelScope.launch {
            appConfigRepo.updateConfig(app.copy(blockReels = !app.blockReels))
        }
    }

    fun saveParentPin(pin: String) {
        viewModelScope.launch {
            context.dataStore.edit { prefs ->
                prefs[PARENT_PIN_KEY] = pin
            }
            _uiState.update { it.copy(parentPin = pin, parentPinEnabled = pin.isNotEmpty(), showPinDialog = false) }
        }
    }

    fun verifyPin(inputPin: String): Boolean {
        return inputPin == _uiState.value.parentPin
    }

    fun togglePinDialog() {
        _uiState.update { it.copy(showPinDialog = !it.showPinDialog) }
    }

    fun togglePinVerifyDialog() {
        _uiState.update { it.copy(showPinVerifyDialog = !it.showPinVerifyDialog) }
    }
}
