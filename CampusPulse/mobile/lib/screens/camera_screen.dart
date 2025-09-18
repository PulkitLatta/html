import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../routes.dart';
import '../services/ml_service.dart';
import '../services/analysis.dart';
import '../widgets/camera_overlay.dart';

class CameraScreen extends StatefulWidget {
  @override
  _CameraScreenState createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  CameraController? _cameraController;
  bool _isRecording = false;
  bool _isInitialized = false;
  final AnalysisService _analysisService = AnalysisService();

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    if (cameras.isEmpty) {
      debugPrint('No cameras available');
      return;
    }

    _cameraController = CameraController(
      cameras[0],
      ResolutionPreset.high,
      enableAudio: false,
    );

    try {
      await _cameraController!.initialize();
      setState(() {
        _isInitialized = true;
      });
    } catch (e) {
      debugPrint('Error initializing camera: $e');
    }
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    _analysisService.dispose();
    super.dispose();
  }

  Future<void> _startRecording() async {
    if (!_isInitialized || _cameraController == null) return;

    try {
      await _cameraController!.startVideoRecording();
      setState(() {
        _isRecording = true;
      });
      
      // Start pose detection
      final mlService = Provider.of<MLService>(context, listen: false);
      await mlService.startPoseDetection();
      _analysisService.startAnalysis();
      
    } catch (e) {
      debugPrint('Error starting recording: $e');
    }
  }

  Future<void> _stopRecording() async {
    if (!_isRecording || _cameraController == null) return;

    try {
      final videoFile = await _cameraController!.stopVideoRecording();
      setState(() {
        _isRecording = false;
      });
      
      // Stop pose detection and get analysis
      final mlService = Provider.of<MLService>(context, listen: false);
      mlService.stopPoseDetection();
      final analysisData = await _analysisService.stopAnalysis();
      
      // Navigate to results
      Navigator.of(context).pushNamed(
        AppRoutes.results,
        arguments: {
          'analysisData': analysisData,
          'videoPath': videoFile.path,
        },
      );
      
    } catch (e) {
      debugPrint('Error stopping recording: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: _isInitialized
          ? Stack(
              children: [
                // Camera preview
                Positioned.fill(
                  child: CameraPreview(_cameraController!),
                ),
                // Camera overlay with pose visualization
                CameraOverlay(
                  isRecording: _isRecording,
                  onRecordingToggle: _isRecording ? _stopRecording : _startRecording,
                ),
              ],
            )
          : Center(
              child: CircularProgressIndicator(color: Colors.blue),
            ),
    );
  }
}