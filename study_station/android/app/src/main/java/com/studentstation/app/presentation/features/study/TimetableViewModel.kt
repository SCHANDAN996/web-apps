package com.studentstation.app.presentation.features.study

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.studentstation.app.data.local.entity.SubjectEntity
import com.studentstation.app.data.local.entity.TimetableEntryEntity
import com.studentstation.app.domain.repository.SubjectRepository
import com.studentstation.app.domain.repository.TimetableRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class TimetableViewState(
    val subjects: List<SubjectEntity> = emptyList(),
    val entries: List<TimetableEntryEntity> = emptyList()
)

@HiltViewModel
class TimetableViewModel @Inject constructor(
    private val subjectRepository: SubjectRepository,
    private val timetableRepository: TimetableRepository
) : ViewModel() {

    private val _selectedDay = MutableStateFlow(1) // 1 = Monday
    val selectedDay: StateFlow<Int> = _selectedDay.asStateFlow()

    val uiState: StateFlow<TimetableViewState> = combine(
        subjectRepository.getAllSubjects(),
        _selectedDay.flatMapLatest { day -> timetableRepository.getEntriesForDay(day) }
    ) { subjects, entries ->
        TimetableViewState(subjects, entries)
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = TimetableViewState()
    )

    fun selectDay(dayOfWeek: Int) {
        _selectedDay.value = dayOfWeek
    }

    fun addEntry(subjectId: Long, dayOfWeek: Int, startHour: Int, startMinute: Int, durationMinutes: Int) {
        val startTimeMinutes = (startHour * 60) + startMinute
        viewModelScope.launch {
            timetableRepository.addEntry(
                TimetableEntryEntity(
                    subjectId = subjectId,
                    dayOfWeek = dayOfWeek,
                    startTimeMinutes = startTimeMinutes,
                    durationMinutes = durationMinutes
                )
            )
        }
    }

    fun deleteEntry(entry: TimetableEntryEntity) {
        viewModelScope.launch {
            timetableRepository.deleteEntry(entry)
        }
    }

    fun autoGenerateTimetable() {
        viewModelScope.launch {
            val subjects = subjectRepository.getAllSubjects().first()
            if (subjects.isEmpty()) return@launch

            timetableRepository.clearTimetable()

            val newEntries = mutableListOf<TimetableEntryEntity>()
            val sessionDuration = 45
            val breakDuration = 15
            
            // Simple logic: 3 sessions a day, Monday to Friday
            for (day in 1..5) {
                var currentStartTime = 17 * 60 // Starts at 5:00 PM
                for (i in 0 until 3) {
                    val randomSubject = subjects.random()
                    newEntries.add(
                        TimetableEntryEntity(
                            subjectId = randomSubject.id,
                            dayOfWeek = day,
                            startTimeMinutes = currentStartTime,
                            durationMinutes = sessionDuration
                        )
                    )
                    currentStartTime += sessionDuration + breakDuration
                }
            }
            timetableRepository.addEntries(newEntries)
        }
    }
}
