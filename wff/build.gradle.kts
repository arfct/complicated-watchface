plugins {
    id("com.android.application")
}

android {
    namespace = "com.artifact.complicated.wff"
    compileSdk = 37

    defaultConfig {
        applicationId = "com.artifact.complicated.wff"
        // Tied to the Watch Face Format version in the manifest: format 5
        // needs Wear OS 7.
        minSdk = 37
        targetSdk = 37
        versionCode = 1
        versionName = "0.1.0"
    }

    buildTypes {
        release {
            // R8 strips the empty generated classes: a WFF package with
            // minSdk >= 33 must contain no dex files (bundletool enforces it)
            isMinifyEnabled = true
            isShrinkResources = false
        }
    }
}
