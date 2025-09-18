import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:camera/camera.dart';
import 'routes.dart';
import 'services/ml_service.dart';
import 'services/submission_service.dart';

List<CameraDescription> cameras = [];

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  try {
    cameras = await availableCameras();
  } catch (e) {
    print('Error initializing cameras: $e');
  }
  
  runApp(
    MultiProvider(
      providers: [
        Provider<MLService>(create: (_) => MLService()),
        Provider<SubmissionService>(create: (_) => SubmissionService()),
      ],
      child: const CampusPulseApp(),
    ),
  );
}

class CampusPulseApp extends StatelessWidget {
  const CampusPulseApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CampusPulse',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      initialRoute: '/',
      onGenerateRoute: AppRoutes.generateRoute,
    );
  }
}