# Keep TensorFlow Lite classes
-keep class org.tensorflow.lite.** { *; }
-keep class org.tensorflow.lite.support.** { *; }

# Keep Flutter and Dart classes
-keep class io.flutter.** { *; }
-keep class dart.** { *; }

# Keep camera plugin classes
-keep class io.flutter.plugins.camera.** { *; }

# Keep SQLite classes
-keep class io.flutter.plugins.sqflite.** { *; }

# Preserve line numbers for debugging
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile