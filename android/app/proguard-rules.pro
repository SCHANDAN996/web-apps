# Student Station ProGuard Rules

# Hilt
-keepclasseswithmembernames class * {
    @dagger.hilt.* <fields>;
}

# Room
-keep class * extends androidx.room.RoomDatabase
-dontwarn androidx.room.paging.**

# Compose
-dontwarn androidx.compose.**

# Keep data classes
-keep class com.studentstation.app.data.local.entity.** { *; }
-keep class com.studentstation.app.domain.model.** { *; }
