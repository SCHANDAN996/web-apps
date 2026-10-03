package com.studentstation.app.data.repository

import com.studentstation.app.data.local.dao.SubjectDao
import com.studentstation.app.data.local.entity.SubjectEntity
import com.studentstation.app.domain.repository.SubjectRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SubjectRepositoryImpl @Inject constructor(
    private val subjectDao: SubjectDao
) : SubjectRepository {

    override fun getAllSubjects(): Flow<List<SubjectEntity>> {
        return subjectDao.getAllSubjects()
    }

    override suspend fun getSubjectById(id: Long): SubjectEntity? {
        return subjectDao.getSubjectById(id)
    }

    override suspend fun addSubject(subject: SubjectEntity): Long {
        return subjectDao.insertSubject(subject)
    }

    override suspend fun updateSubject(subject: SubjectEntity) {
        subjectDao.updateSubject(subject)
    }

    override suspend fun deleteSubject(subject: SubjectEntity) {
        subjectDao.deleteSubject(subject)
    }
}
