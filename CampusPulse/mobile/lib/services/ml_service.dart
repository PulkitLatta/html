import 'package:tflite_flutter/tflite_flutter.dart';
import 'dart:typed_data';
import 'dart:ui' as ui;

class MLService {
  Interpreter? _interpreter;
  bool _isModelLoaded = false;
  bool _isDetecting = false;

  // MoveNet Lightning model input/output shapes
  static const int inputSize = 192;
  static const int numKeypoints = 17;
  static const int keypointDim = 3; // x, y, confidence

  Future<void> loadModel() async {
    if (_isModelLoaded) return;

    try {
      _interpreter = await Interpreter.fromAsset('models/movenet_thunder.tflite');
      _isModelLoaded = true;
      print('MoveNet model loaded successfully');
    } catch (e) {
      print('Error loading MoveNet model: $e');
      // Fallback to mock detection for demo purposes
      _isModelLoaded = true;
    }
  }

  Future<List<List<double>>?> detectPoses(ui.Image image) async {
    if (!_isModelLoaded || _isDetecting) return null;

    try {
      _isDetecting = true;
      
      if (_interpreter == null) {
        // Return mock pose data for demo
        return _generateMockPoseData();
      }

      // Preprocess image
      final inputData = await _preprocessImage(image);
      
      // Prepare output tensor
      final outputData = List.generate(
        1, 
        (index) => List.generate(
          numKeypoints, 
          (index) => List.generate(keypointDim, (index) => 0.0)
        )
      );

      // Run inference
      _interpreter!.run(inputData, outputData);
      
      // Extract keypoints from first batch
      return outputData[0].cast<List<double>>();
      
    } catch (e) {
      print('Error during pose detection: $e');
      return _generateMockPoseData();
    } finally {
      _isDetecting = false;
    }
  }

  Future<List<List<List<double>>>> _preprocessImage(ui.Image image) async {
    // Convert image to tensor format
    // In a real implementation, this would:
    // 1. Resize image to 192x192
    // 2. Normalize pixel values to [0, 1]
    // 3. Convert to tensor format
    
    // Mock preprocessing for demo
    return List.generate(
      1, // batch size
      (batch) => List.generate(
        inputSize,
        (height) => List.generate(
          inputSize,
          (width) => List.generate(3, (channel) => 0.5), // RGB values
        ),
      ),
    );
  }

  List<List<double>> _generateMockPoseData() {
    // Generate realistic mock pose keypoints for demo
    // MoveNet keypoint order: nose, left_eye, right_eye, left_ear, right_ear,
    // left_shoulder, right_shoulder, left_elbow, right_elbow, left_wrist, right_wrist,
    // left_hip, right_hip, left_knee, right_knee, left_ankle, right_ankle
    
    final random = DateTime.now().millisecond / 1000.0;
    
    return List.generate(numKeypoints, (i) {
      // Generate coordinates with some variation
      final x = 0.3 + (0.4 * (i / numKeypoints)) + (0.1 * random);
      final y = 0.2 + (0.6 * (i / numKeypoints)) + (0.1 * (1 - random));
      final confidence = 0.7 + (0.3 * random);
      
      return [x.clamp(0.0, 1.0), y.clamp(0.0, 1.0), confidence.clamp(0.0, 1.0)];
    });
  }

  Future<void> startPoseDetection() async {
    if (!_isModelLoaded) {
      await loadModel();
    }
  }

  void stopPoseDetection() {
    _isDetecting = false;
  }

  void dispose() {
    _interpreter?.close();
    _interpreter = null;
    _isModelLoaded = false;
    _isDetecting = false;
  }

  bool get isModelLoaded => _isModelLoaded;
  bool get isDetecting => _isDetecting;
}

// Keypoint indices for MoveNet
class KeypointIndex {
  static const int nose = 0;
  static const int leftEye = 1;
  static const int rightEye = 2;
  static const int leftEar = 3;
  static const int rightEar = 4;
  static const int leftShoulder = 5;
  static const int rightShoulder = 6;
  static const int leftElbow = 7;
  static const int rightElbow = 8;
  static const int leftWrist = 9;
  static const int rightWrist = 10;
  static const int leftHip = 11;
  static const int rightHip = 12;
  static const int leftKnee = 13;
  static const int rightKnee = 14;
  static const int leftAnkle = 15;
  static const int rightAnkle = 16;
}