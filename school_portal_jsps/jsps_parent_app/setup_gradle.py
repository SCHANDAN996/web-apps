import os
import shutil
import subprocess

source_dir = r"C:\Users\Admin\Desktop\my project\student_station"
target_dir = r"C:\Users\Admin\Desktop\my project\js public\flask_jspschandauli\jsps_parent_app"

def copy_if_exists(src, dst):
    if os.path.exists(src):
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

# 1. Copy Gradle Root Files
print("Copying Gradle Wrapper and Root Files...")
files_to_copy = [
    "gradle",
    "gradlew",
    "gradlew.bat",
    "gradle.properties",
    "local.properties",
    "build.gradle.kts"
]
for item in files_to_copy:
    copy_if_exists(os.path.join(source_dir, item), os.path.join(target_dir, item))

# 2. Setup settings.gradle.kts
print("Setting up settings.gradle.kts...")
settings_content = """
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "JspsParentApp"
include(":app")
"""
with open(os.path.join(target_dir, "settings.gradle.kts"), "w") as f:
    f.write(settings_content)

# 3. Setup app/build.gradle.kts
print("Setting up app/build.gradle.kts...")
app_build_content = """
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.jsps.parentapp"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.jsps.parentapp"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables {
            useSupportLibrary = true
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        compose = true
    }
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.1"
    }
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.activity:activity-compose:1.8.2")
    implementation(platform("androidx.compose:compose-bom:2023.08.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.navigation:navigation-compose:2.7.6")
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation(platform("androidx.compose:compose-bom:2023.08.00"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
"""
os.makedirs(os.path.join(target_dir, "app"), exist_ok=True)
with open(os.path.join(target_dir, "app", "build.gradle.kts"), "w") as f:
    f.write(app_build_content)

# 4. Setup AndroidManifest.xml
print("Setting up AndroidManifest.xml...")
manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.jsps.parentapp">

    <uses-permission android:name="android.permission.INTERNET" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="JSPS Parent"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.JspsParentApp"
        android:usesCleartextTraffic="true">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:theme="@style/Theme.JspsParentApp">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>

</manifest>
"""
os.makedirs(os.path.join(target_dir, "app", "src", "main"), exist_ok=True)
with open(os.path.join(target_dir, "app", "src", "main", "AndroidManifest.xml"), "w") as f:
    f.write(manifest_content)

# 5. Copy Resources from student_station (for icons/themes)
print("Copying res folder...")
res_src = os.path.join(source_dir, "app", "src", "main", "res")
res_dst = os.path.join(target_dir, "app", "src", "main", "res")
if not os.path.exists(res_dst):
    copy_if_exists(res_src, res_dst)

# Fix Theme name in res/values/themes.xml
themes_xml_path = os.path.join(res_dst, "values", "themes.xml")
if os.path.exists(themes_xml_path):
    with open(themes_xml_path, "r") as f:
        content = f.read()
    content = content.replace("Theme.StudentStation", "Theme.JspsParentApp")
    with open(themes_xml_path, "w") as f:
        f.write(content)

# 6. Create MainActivity.kt
print("Creating MainActivity.kt...")
main_activity_content = """package com.jsps.parentapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.jsps.parentapp.data.remote.JspsApi
import com.jsps.parentapp.ui.navigation.AppNavigation
import com.jsps.parentapp.ui.viewmodels.ParentViewModel
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Setup Retrofit (Using 10.0.2.2 for Android Emulator to access localhost)
        val retrofit = Retrofit.Builder()
            .baseUrl("http://10.0.2.2:5000/") 
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            
        val api = retrofit.create(JspsApi::class.java)
        val viewModel = ParentViewModel(api)

        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    AppNavigation(viewModel)
                }
            }
        }
    }
}
"""
os.makedirs(os.path.join(target_dir, "app", "src", "main", "java", "com", "jsps", "parentapp"), exist_ok=True)
with open(os.path.join(target_dir, "app", "src", "main", "java", "com", "jsps", "parentapp", "MainActivity.kt"), "w") as f:
    f.write(main_activity_content)

print("Setup Complete! Ready to build APK.")
