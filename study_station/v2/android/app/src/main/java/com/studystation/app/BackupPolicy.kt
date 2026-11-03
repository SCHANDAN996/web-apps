package com.studystation.app

/** Shared protocol limits; no platform dependencies, so origin and size checks are unit-testable. */
object BackupPolicy {
    const val MAX_BYTES = 4 * 1024 * 1024
    const val FILE_NAME = "study-station-backup-v1.json"
    val OPERATIONS = setOf("backup", "restore", "local-backup", "local-restore")
    fun allowed(origin: String, page: String?, base: String, topFrame: Boolean): Boolean =
        topFrame && page != null && Links.isInApp(origin, base) && Links.isInApp(page, base)
    fun allowedSize(bytes: Int) = bytes in 1..MAX_BYTES
}
