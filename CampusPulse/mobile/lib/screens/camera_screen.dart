import 'package:flutter/material.dart';
import 'package:camera/camera.dart';
import 'package:provider/provider.dart';
import '../main.dart';
import '../services/ml_service.dart';
import '../services/analysis.dart';
import '../widgets/camera_overlay.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({Key? key}) : super(key: key);

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  CameraController? _controller;
  bool _isRecording = false;
  bool _isAnalyzing = false;
  List<Map<String, dynamic>> _poseData = [];

  @override
  void initState() {
    super.initState();
    _initializeCamera();
  }

  Future<void> _initializeCamera() async {
    if (cameras.isEmpty) return;

    _controller = CameraController(
      cameras.first,
      ResolutionPreset.high,
      enableAudio: false,
    );

    try {
      await _controller!.initialize();
      if (mounted) setState(() {});
    } catch (e) {
      print('Camera initialization error: $e');
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  Future<void> _startRecording() async {
    if (_controller == null || !_controller!.value.isInitialized) return;

    setState(() {
      _isRecording = true;
      _isAnalyzing = true;
    });

    // Start ML pose detection
    final mlService = Provider.of<MLService>(context, listen: false);
    await mlService.initializeModel();

    // Simulate pose detection data collection
    _startPoseDetection();
  }

  void _startPoseDetection() {
    // Simulate pose detection every 100ms
    Stream.periodic(const Duration(milliseconds: 100), (i) => i)
        .take(50) // 5 seconds of recording
        .listen(
      (frame) async {
        if (!_isRecording) return;

        // Simulate pose detection results
        final poseResult = {
          'timestamp': DateTime.now().millisecondsSinceEpoch,
          'keypoints': _generateMockKeypoints(),
          'confidence': 0.8 + (frame % 10) * 0.02,
        };

        setState(() {
          _poseData.add(poseResult);
        });
      },
      onDone: () => _stopRecording(),
    );
  }

  List<Map<String, double>> _generateMockKeypoints() {
    // Generate mock MoveNet keypoints (17 keypoints)
    return List.generate(17, (i) => {
          'x': 0.3 + (i % 3) * 0.2,
          'y': 0.2 + (i ~/ 3) * 0.15,
          'confidence': 0.7 + (i % 5) * 0.05,
        });
  }

  Future<void> _stopRecording() async {
    setState(() {
      _isRecording = false;
      _isAnalyzing = false;
    });

    // Analyze the collected pose data
    final analysisData = AnalysisService.analyzePoseSequence(_poseData);

    // Navigate to results screen
    Navigator.pushNamed(
      context,
      '/results',
      arguments: analysisData,
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_controller == null || !_controller!.value.isInitialized) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Camera Preview
          Center(
            child: AspectRatio(
              aspectRatio: _controller!.value.aspectRatio,
              child: CameraPreview(_controller!),
            ),
          ),
          // Camera Overlay with pose visualization
          CameraOverlay(
            isRecording: _isRecording,
            isAnalyzing: _isAnalyzing,
            poseData: _poseData.isNotEmpty ? _poseData.last : null,
          ),
          // Control Panel
          Positioned(
            bottom: 50,
            left: 0,
            right: 0,
            child: Column(
              children: [
                if (_isRecording)
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 8,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.red.withOpacity(0.8),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      'Recording... ${_poseData.length} frames',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                const SizedBox(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    // Back Button
                    IconButton(
                      onPressed: _isRecording ? null : () => Navigator.pop(context),
                      icon: const Icon(Icons.arrow_back, color: Colors.white),
                      iconSize: 40,
                    ),
                    // Record Button
                    GestureDetector(
                      onTap: _isRecording ? _stopRecording : _startRecording,
                      child: Container(
                        width: 80,
                        height: 80,
                        decoration: BoxDecoration(
                          color: _isRecording ? Colors.red : Colors.white,
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: Colors.white,
                            width: 4,
                          ),
                        ),
                        child: Icon(
                          _isRecording ? Icons.stop : Icons.fiber_manual_record,
                          size: 40,
                          color: _isRecording ? Colors.white : Colors.red,
                        ),
                      ),
                    ),
                    // Settings Button
                    IconButton(
                      onPressed: _isRecording ? null : () {},
                      icon: const Icon(Icons.settings, color: Colors.white),
                      iconSize: 40,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}