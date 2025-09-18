# Lottie Animation Assets

This directory contains Lottie animation files used in the CampusPulse mobile app.

## Animation Files

### Splash Screen
- `splash_animation.json` - Loading animation for the splash screen
- Duration: 3 seconds loop
- Theme: Athletic performance and AI technology

### Recording Animations  
- `recording_pulse.json` - Pulsing animation during video recording
- `analysis_spinner.json` - Processing animation during pose analysis
- `success_checkmark.json` - Success animation for completed analysis

### Onboarding Animations
- `welcome_hero.json` - Welcome screen hero animation
- `pose_detection_demo.json` - Demonstration of pose detection features
- `leaderboard_celebration.json` - Achievement celebration animation

## Usage

Import animations in Flutter using the `lottie` package:

```dart
import 'package:lottie/lottie.dart';

Lottie.asset(
  'assets/lottie/splash_animation.json',
  width: 200,
  height: 200,
  fit: BoxFit.fill,
)
```

## Animation Requirements

All animations should:
- Be optimized for mobile performance (< 500KB)
- Support loop and reverse playback
- Use the app's color scheme
- Work well on both light and dark backgrounds
- Be 60fps for smooth playback

## Sources

Animations are custom-created for CampusPulse or licensed from:
- LottieFiles.com (with appropriate license)
- Custom designs by the CampusPulse team

Note: Actual animation files are not included in this repository to keep size manageable. Download them from the assets server or design team.