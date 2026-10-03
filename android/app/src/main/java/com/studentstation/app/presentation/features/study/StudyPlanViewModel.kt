package com.studentstation.app.presentation.features.study

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.studentstation.app.data.local.entity.SubjectEntity
import com.studentstation.app.domain.repository.SubjectRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class StudyPlanViewModel @Inject constructor(
    private val subjectRepository: SubjectRepository
) : ViewModel() {

    val subjects: StateFlow<List<SubjectEntity>> = subjectRepository.getAllSubjects()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )

    fun addSubject(name: String, totalChapters: Int, colorHex: String? = null) {
        viewModelScope.launch {
            subjectRepository.addSubject(
                SubjectEntity(
                    name = name,
                    totalChapters = totalChapters,
                    completedChapters = 0,
                    colorHex = colorHex
                )
            )
        }
    }

    fun updateProgress(subject: SubjectEntity, chaptersCompleted: Int) {
        viewModelScope.launch {
            subjectRepository.updateSubject(
                subject.copy(completedChapters = chaptersCompleted)
            )
        }
    }

    fun deleteSubject(subject: SubjectEntity) {
        viewModelScope.launch {
            subjectRepository.deleteSubject(subject)
        }
    }
}
