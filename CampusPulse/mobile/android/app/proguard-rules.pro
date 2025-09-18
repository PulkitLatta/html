# Add project specific ProGuard rules here.
-keep class org.tensorflow.** { *; }
-keep class org.tensorflow.lite.** { *; }
-keep class tflite_flutter.** { *; }

# Keep native methods
-keepclasseswithmembers class * {
    native <methods>;
}

# Keep model loading classes
-keep class * implements org.tensorflow.lite.Interpreter$Options { *; }

# Camera related
-keep class androidx.camera.** { *; }

# SQLite
-keep class io.flutter.plugins.sqflite.** { *; }

# Dio HTTP client
-keep class dio.** { *; }
-keep class retrofit2.** { *; }

# Shared Preferences
-keep class io.flutter.plugins.sharedpreferences.** { *; }

# Path provider
-keep class io.flutter.plugins.pathprovider.** { *; }

# Permission handler
-keep class com.baseflow.permissionhandler.** { *; }

# Image processing
-keep class io.flutter.plugins.imagepicker.** { *; }

# Flutter engine
-keep class io.flutter.embedding.** { *; }
-keep class io.flutter.plugin.** { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }
-keep class io.flutter.** { *; }

# Don't warn about missing classes
-dontwarn org.tensorflow.**
-dontwarn tflite_flutter.**