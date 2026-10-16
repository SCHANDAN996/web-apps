import java.security.MessageDigest
import java.util.Properties

plugins {
    id("com.android.application")
}

// The web UI's own files (CSS, JS, icon) ship inside the APK; pages, questions, books and progress
// come from the server.
val staticDir = rootProject.file("../app/static")

/** Same value as _asset_version() in app/main.py: the app serves its own copy of a file only when the
 *  page asks for exactly this version, so an APK older than the server can never show stale CSS/JS. */
fun assetVersion(): String {
    val md = MessageDigest.getInstance("SHA-1")
    staticDir.walkTopDown()
        .filter { it.isFile && it.name != "sw.js" }
        .sortedBy { it.relativeTo(staticDir).invariantSeparatorsPath.replace('/', '\u0000') }   // path-part order, like Python
        .forEach { md.update(it.name.toByteArray()); md.update(it.readBytes()) }
    return md.digest().joinToString("") { "%02x".format(it) }.take(10)
}

// Server address: -Pss.debugUrl=… / -Pss.releaseUrl=… or the same keys in local.properties (never committed).
val local = Properties().apply {
    rootProject.file("local.properties").takeIf { it.isFile }?.inputStream()?.use { load(it) }
}
fun setting(name: String, default: String) =
    ((findProperty(name) as String?) ?: local.getProperty(name) ?: default).trim().trimEnd('/')

val debugUrl = setting("ss.debugUrl", "http://10.0.2.2:8000")      // emulator's name for this PC
val releaseUrl = setting("ss.releaseUrl", "")

android {
    namespace = "com.studystation.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.studystation.app"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "1.0.0"
        buildConfigField("String", "ASSET_V", "\"${assetVersion()}\"")
        buildConfigField("boolean", "GOOGLE_DRIVE_ENABLED", setting("ss.googleDriveEnabled", "false").toBooleanStrict().toString())
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            buildConfigField("String", "BASE_URL", "\"$debugUrl\"")
            manifestPlaceholders["cleartext"] = "true"       // local test server is plain http
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
            buildConfigField("String", "BASE_URL", "\"$releaseUrl\"")
            manifestPlaceholders["cleartext"] = "false"      // HTTPS only
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        buildConfig = true
    }

    sourceSets.getByName("main").assets.directories.add(staticDir.path)
}

dependencies {
    implementation("androidx.webkit:webkit:1.14.0")
    implementation("com.google.android.gms:play-services-auth:22.0.0")
    testImplementation("junit:junit:4.13.2")
}

tasks.matching { it.name == "preReleaseBuild" }.configureEach {
    doFirst {
        check(releaseUrl.startsWith("https://")) {
            "Set ss.releaseUrl=https://<your server> in local.properties (release builds are HTTPS only)."
        }
    }
}
