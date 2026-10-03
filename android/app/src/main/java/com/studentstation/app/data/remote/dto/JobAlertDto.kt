package com.studentstation.app.data.remote.dto

import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class JobAlertDto(
    val id: Long,
    val title: String,
    val organization: String?,
    val postName: String?,
    val vacancies: String?,
    val eligibility: String?,
    val lastDate: String?,
    val applicationUrl: String?,
    val category: String?
)
