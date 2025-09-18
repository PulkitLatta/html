import 'package:tflite_flutter/tflite_flutter.dart';
import 'package:image/image.dart' as img;

class MLService {
  Interpreter? _interpreter;
  bool _isModelLoaded = false;

  // MoveNet Lightning model configuration
  static const int inputSize = 192;
  static const int numKeypoints = 17;
  static const double confidenceThreshold = 0.3;

  // Keypoint names for MoveNet model
  static const List<String> keypointNames = [
    'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
    'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
    'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
    'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
  ];

  /// Initialize the MoveNet Lightning model
  Future<bool> initializeModel() async {
    if (_isModelLoaded) return true;

    try {
      // Load the TFLite model
      _interpreter = await Interpreter.fromAsset('assets/models/movenet_lightning.tflite');
      _isModelLoaded = true;
      print('MoveNet Lightning model loaded successfully');
      return true;
    } catch (e) {
      print('Failed to load MoveNet model: $e');
      return false;
    }
  }

  /// Detect poses in an image
  Future<Map<String, dynamic>?> detectPose(img.Image image) async {
    if (!_isModelLoaded || _interpreter == null) {
      print('Model not loaded. Call initializeModel() first.');
      return null;
    }

    try {
      // Preprocess image
      final preprocessedImage = _preprocessImage(image);
      
      // Prepare input and output tensors
      final input = [preprocessedImage];
      final output = [List.filled(1 * numKeypoints * 3, 0.0)];

      // Run inference
      _interpreter!.run(input, output);

      // Post-process results
      return _postprocessOutput(output[0], image.width, image.height);
    } catch (e) {
      print('Pose detection error: $e');
      return null;
    }
  }

  /// Preprocess image for MoveNet input
  List<List<List<List<double>>>> _preprocessImage(img.Image image) {
    // Resize image to 192x192
    final resized = img.copyResize(image, width: inputSize, height: inputSize);
    
    // Convert to normalized float values [0, 1]
    final input = List.generate(
      1,
      (b) => List.generate(
        inputSize,
        (y) => List.generate(
          inputSize,
          (x) => List.generate(3, (c) {
            final pixel = resized.getPixel(x, y);
            switch (c) {
              case 0: return pixel.r / 255.0; // Red
              case 1: return pixel.g / 255.0; // Green  
              case 2: return pixel.b / 255.0; // Blue
              default: return 0.0;
            }
          }),
        ),
      ),
    );

    return input;
  }

  /// Post-process model output to extract keypoints
  Map<String, dynamic> _postprocessOutput(List<double> output, int imageWidth, int imageHeight) {
    final keypoints = <Map<String, dynamic>>[];
    double totalConfidence = 0.0;
    int validKeypoints = 0;

    // Extract keypoints (y, x, confidence) for each of 17 keypoints
    for (int i = 0; i < numKeypoints; i++) {
      final y = output[i * 3];     // Y coordinate (normalized)
      final x = output[i * 3 + 1]; // X coordinate (normalized)
      final confidence = output[i * 3 + 2]; // Confidence score

      // Convert normalized coordinates to image coordinates
      final keypoint = {
        'name': keypointNames[i],
        'x': x * imageWidth,
        'y': y * imageHeight,
        'confidence': confidence,
        'visible': confidence > confidenceThreshold,
      };

      keypoints.add(keypoint);

      if (confidence > confidenceThreshold) {
        totalConfidence += confidence;
        validKeypoints++;
      }
    }

    final averageConfidence = validKeypoints > 0 ? totalConfidence / validKeypoints : 0.0;

    return {
      'keypoints': keypoints,
      'averageConfidence': averageConfidence,
      'validKeypointsCount': validKeypoints,
      'timestamp': DateTime.now().millisecondsSinceEpoch,
    };
  }

  /// Calculate skeleton connections for visualization
  List<Map<String, dynamic>> getSkeletonConnections() {
    // MoveNet skeleton connections (parent-child keypoint pairs)
    const connections = [
      ['nose', 'left_eye'],
      ['nose', 'right_eye'],
      ['left_eye', 'left_ear'],
      ['right_eye', 'right_ear'],
      ['left_shoulder', 'right_shoulder'],
      ['left_shoulder', 'left_elbow'],
      ['right_shoulder', 'right_elbow'],
      ['left_elbow', 'left_wrist'],
      ['right_elbow', 'right_wrist'],
      ['left_shoulder', 'left_hip'],
      ['right_shoulder', 'right_hip'],
      ['left_hip', 'right_hip'],
      ['left_hip', 'left_knee'],
      ['right_hip', 'right_knee'],
      ['left_knee', 'left_ankle'],
      ['right_knee', 'right_ankle'],
    ];

    return connections.map((connection) => {
      'from': connection[0],
      'to': connection[1],
    }).toList();
  }

  /// Check if pose detection is available
  bool get isModelLoaded => _isModelLoaded;

  /// Dispose of resources
  void dispose() {
    _interpreter?.close();
    _interpreter = null;
    _isModelLoaded = false;
  }

  /// Get model input shape information
  Map<String, dynamic> getModelInfo() {
    if (_interpreter == null) return {};

    return {
      'inputShape': _interpreter!.getInputTensor(0).shape,
      'outputShape': _interpreter!.getOutputTensor(0).shape,
      'inputType': _interpreter!.getInputTensor(0).type.toString(),
      'outputType': _interpreter!.getOutputTensor(0).type.toString(),
    };
  }

  /// Batch process multiple images for video analysis
  Future<List<Map<String, dynamic>>> batchDetectPoses(List<img.Image> images) async {
    final results = <Map<String, dynamic>>[];
    
    for (final image in images) {
      final result = await detectPose(image);
      if (result != null) {
        results.add(result);
      }
    }
    
    return results;
  }

  /// Calculate pose similarity between two pose detections
  static double calculatePoseSimilarity(
    Map<String, dynamic> pose1,
    Map<String, dynamic> pose2,
  ) {
    final keypoints1 = pose1['keypoints'] as List<Map<String, dynamic>>;
    final keypoints2 = pose2['keypoints'] as List<Map<String, dynamic>>;

    if (keypoints1.length != keypoints2.length) return 0.0;

    double totalDistance = 0.0;
    int validComparisons = 0;

    for (int i = 0; i < keypoints1.length; i++) {
      final kp1 = keypoints1[i];
      final kp2 = keypoints2[i];

      // Only compare visible keypoints
      if (kp1['visible'] == true && kp2['visible'] == true) {
        final dx = (kp1['x'] as double) - (kp2['x'] as double);
        final dy = (kp1['y'] as double) - (kp2['y'] as double);
        final distance = (dx * dx + dy * dy).abs();

        totalDistance += distance;
        validComparisons++;
      }
    }

    if (validComparisons == 0) return 0.0;

    // Convert distance to similarity score (0-1)
    final averageDistance = totalDistance / validComparisons;
    return (1.0 / (1.0 + averageDistance / 10000)).clamp(0.0, 1.0);
  }
}