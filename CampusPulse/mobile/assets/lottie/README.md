# Lottie Animations for CampusPulse

This directory contains Lottie animation files used throughout the CampusPulse mobile application.

## Files

- `loading.json` - Loading animation for splash screen and data processing
- `success.json` - Success animation for completed exercises and achievements
- `error.json` - Error animation for failed uploads or connectivity issues

## Usage

These animations are loaded using the `lottie` Flutter package:

```dart
import 'package:lottie/lottie.dart';

Lottie.asset('assets/lottie/loading.json')
```

## Sources

All animations are sourced from LottieFiles community or created specifically for CampusPulse. Ensure proper licensing for any third-party animations.

## Notes

- Keep file sizes small for better app performance
- Use appropriate compression for mobile delivery
- Test animations on different screen sizes and densities