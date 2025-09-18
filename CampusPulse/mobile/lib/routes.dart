import 'package:flutter/material.dart';
import 'screens/splash_screen.dart';
import 'screens/home_screen.dart';
import 'screens/camera_screen.dart';
import 'screens/results_screen.dart';
import 'screens/leaderboard_screen.dart';
import 'screens/profile_screen.dart';

class AppRoutes {
  static const String splash = '/';
  static const String home = '/home';
  static const String camera = '/camera';
  static const String results = '/results';
  static const String leaderboard = '/leaderboard';
  static const String profile = '/profile';

  static Route<dynamic> generateRoute(RouteSettings settings) {
    switch (settings.name) {
      case splash:
        return MaterialPageRoute(builder: (_) => SplashScreen());
      case home:
        return MaterialPageRoute(builder: (_) => HomeScreen());
      case camera:
        return MaterialPageRoute(builder: (_) => CameraScreen());
      case results:
        final args = settings.arguments as Map<String, dynamic>?;
        return MaterialPageRoute(
          builder: (_) => ResultsScreen(
            analysisData: args?['analysisData'],
          ),
        );
      case leaderboard:
        return MaterialPageRoute(builder: (_) => LeaderboardScreen());
      case profile:
        return MaterialPageRoute(builder: (_) => ProfileScreen());
      default:
        return MaterialPageRoute(
          builder: (_) => Scaffold(
            body: Center(
              child: Text('No route defined for ${settings.name}'),
            ),
          ),
        );
    }
  }
}