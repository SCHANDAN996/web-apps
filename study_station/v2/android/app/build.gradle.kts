import java.security.MessageDigest
import java.net.URI
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
val googleWebClientId = setting("ss.googleWebClientId", "")
require(googleWebClientId.isEmpty() || Regex("[A-Za-z0-9_-]+\\.apps\\.googleusercontent\\.com").matches(googleWebClientId)) { "Invalid ss.googleWebClientId" }
// Signing material lives outside the checkout; only its path is configured locally.
val signingFile = setting("ss.signingProperties", "")
val uploadSigning = Properties().apply {
    if (signingFile.isNotEmpty()) file(signingFile).inputStream().use { load(it) }
}
val releaseVersionCode = setting("ss.versionCode", "3").toInt()
val releaseVersionName = setting("ss.versionName", "1.2.0")
require(releaseVersionCode > 2 && Regex("[0-9]+\\.[0-9]+\\.[0-9]+").matches(releaseVersionName)) { "Use an increasing release version" }

android {
    namespace = "com.studystation.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.studystation.app"
        minSdk = 26
        targetSdk = 36
        versionCode = releaseVersionCode
        versionName = releaseVersionName
        buildConfigField("String", "ASSET_V", "\"${assetVersion()}\"")
        buildConfigField("String", "GOOGLE_WEB_CLIENT_ID", "\"$googleWebClientId\"")
        buildConfigField("boolean", "GOOGLE_DRIVE_ENABLED", setting("ss.googleDriveEnabled", "false").toBooleanStrict().toString())
    }

    signingConfigs {
        if (signingFile.isNotEmpty()) create("upload") {
            storeFile = file(requireNotNull(uploadSigning.getProperty("storeFile")))
            storeType = uploadSigning.getProperty("storeType", "PKCS12")
            storePassword = requireNotNull(uploadSigning.getProperty("storePassword"))
            keyAlias = requireNotNull(uploadSigning.getProperty("keyAlias"))
            keyPassword = requireNotNull(uploadSigning.getProperty("keyPassword"))
        }
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            buildConfigField("String", "BASE_URL", "\"$debugUrl\"")
            manifestPlaceholders["cleartext"] = "true"       // local test server is plain http
        }
        release {
            if (signingFile.isNotEmpty()) signingConfig = signingConfigs.getByName("upload")
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
    implementation("androidx.credentials:credentials:1.6.0")
    implementation("androidx.credentials:credentials-play-services-auth:1.6.0")
    implementation("com.google.android.libraries.identity.googleid:googleid:1.1.1")
    testImplementation("junit:junit:4.13.2")
}

tasks.matching { it.name == "preReleaseBuild" }.configureEach {
    doFirst {
        check(signingFile.isNotEmpty() && uploadSigning.getProperty("storeFile")?.let { file(it).isFile } == true) {
            "Configure ss.signingProperties with an external upload keystore before a release build."
        }
        check(runCatching { URI(releaseUrl).let { it.scheme == "https" && it.host != null && it.userInfo == null && it.query == null && it.fragment == null && (it.path.isNullOrEmpty() || it.path == "/") } }.getOrDefault(false)) {
            "Set ss.releaseUrl=https://<your server> in local.properties (release builds are HTTPS only)."
        }
    }
}

tasks.matching { it.name == "preBuild" }.configureEach {
    doFirst {
        if (setting("ss.requireStudyPack", "true").toBooleanStrict()) {
            check(file("src/main/assets/study/manifest.json").isFile &&
                file("src/main/assets/offline/hi.html").isFile &&
                file("src/main/assets/offline/en.html").isFile) {
                "Generate the public study pack and run python -m app.shell before building. Use -Pss.requireStudyPack=false only for the legacy online wrapper."
            }
        }
    }
}
