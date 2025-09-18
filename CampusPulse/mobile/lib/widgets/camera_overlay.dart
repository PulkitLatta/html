import 'package:flutter/material.dart';
import 'dart:math' as math;

class CameraOverlay extends StatelessWidget {
  final bool isRecording;
  final bool isAnalyzing;
  final Map<String, dynamic>? poseData;

  const CameraOverlay({
    Key? key,
    required this.isRecording,
    required this.isAnalyzing,
    this.poseData,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Recording indicator
        if (isRecording)
          Positioned(
            top: 50,
            left: 20,
            child: _buildRecordingIndicator(),
          ),
        // Analysis status
        if (isAnalyzing)
          Positioned(
            top: 50,
            right: 20,
            child: _buildAnalysisIndicator(),
          ),
        // Pose visualization overlay
        if (poseData != null)
          Positioned.fill(
            child: CustomPaint(
              painter: PoseOverlayPainter(poseData!),
            ),
          ),
        // Guidance overlay
        Positioned.fill(
          child: _buildGuidanceOverlay(),
        ),
      ],
    );
  }

  Widget _buildRecordingIndicator() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.red.withOpacity(0.8),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: const BoxDecoration(
              color: Colors.white,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 8),
          const Text(
            'RECORDING',
            style: TextStyle(
              color: Colors.white,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAnalysisIndicator() {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.blue.withOpacity(0.8),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 16,
            height: 16,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: const AlwaysStoppedAnimation<Color>(Colors.white),
            ),
          ),
          const SizedBox(width: 8),
          const Text(
            'ANALYZING',
            style: TextStyle(
              color: Colors.white,
              fontSize: 10,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGuidanceOverlay() {
    return Container(
      child: CustomPaint(
        painter: GuidanceOverlayPainter(),
      ),
    );
  }
}

class PoseOverlayPainter extends CustomPainter {
  final Map<String, dynamic> poseData;

  PoseOverlayPainter(this.poseData);

  @override
  void paint(Canvas canvas, Size size) {
    final keypoints = poseData['keypoints'] as List<Map<String, dynamic>>?;
    if (keypoints == null) return;

    // Paint for keypoints
    final keypointPaint = Paint()
      ..color = Colors.green
      ..strokeWidth = 4
      ..style = PaintingStyle.fill;

    // Paint for skeleton connections
    final skeletonPaint = Paint()
      ..color = Colors.green.withOpacity(0.7)
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    // Draw skeleton connections first
    _drawSkeleton(canvas, size, keypoints, skeletonPaint);

    // Draw keypoints
    _drawKeypoints(canvas, size, keypoints, keypointPaint);

    // Draw confidence overlay
    _drawConfidenceOverlay(canvas, size);
  }

  void _drawKeypoints(Canvas canvas, Size size, List<Map<String, dynamic>> keypoints, Paint paint) {
    for (final keypoint in keypoints) {
      final visible = keypoint['visible'] as bool? ?? false;
      final confidence = keypoint['confidence'] as double? ?? 0.0;
      
      if (visible && confidence > 0.3) {
        final x = (keypoint['x'] as double) * size.width;
        final y = (keypoint['y'] as double) * size.height;

        // Adjust color based on confidence
        paint.color = confidence > 0.7 
            ? Colors.green 
            : confidence > 0.5 
                ? Colors.orange 
                : Colors.red;

        canvas.drawCircle(Offset(x, y), 6, paint);
        
        // Draw confidence text for debugging (optional)
        if (confidence > 0.5) {
          final textPainter = TextPainter(
            text: TextSpan(
              text: '${(confidence * 100).toInt()}%',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 10,
                fontWeight: FontWeight.bold,
              ),
            ),
            textDirection: TextDirection.ltr,
          );
          textPainter.layout();
          textPainter.paint(canvas, Offset(x + 8, y - 5));
        }
      }
    }
  }

  void _drawSkeleton(Canvas canvas, Size size, List<Map<String, dynamic>> keypoints, Paint paint) {
    // Define skeleton connections for MoveNet
    final connections = [
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

    for (final connection in connections) {
      final fromKeypoint = _findKeypoint(keypoints, connection[0]);
      final toKeypoint = _findKeypoint(keypoints, connection[1]);

      if (fromKeypoint != null && 
          toKeypoint != null && 
          fromKeypoint['visible'] == true && 
          toKeypoint['visible'] == true &&
          (fromKeypoint['confidence'] as double) > 0.3 &&
          (toKeypoint['confidence'] as double) > 0.3) {
        
        final fromX = (fromKeypoint['x'] as double) * size.width;
        final fromY = (fromKeypoint['y'] as double) * size.height;
        final toX = (toKeypoint['x'] as double) * size.width;
        final toY = (toKeypoint['y'] as double) * size.height;

        canvas.drawLine(
          Offset(fromX, fromY),
          Offset(toX, toY),
          paint,
        );
      }
    }
  }

  void _drawConfidenceOverlay(Canvas canvas, Size size) {
    final confidence = poseData['averageConfidence'] as double? ?? 0.0;
    
    // Draw confidence bar
    final barWidth = 100.0;
    final barHeight = 8.0;
    final barX = size.width - barWidth - 20;
    final barY = 20.0;

    // Background
    final backgroundPaint = Paint()
      ..color = Colors.black.withOpacity(0.3)
      ..style = PaintingStyle.fill;
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(barX, barY, barWidth, barHeight),
        const Radius.circular(4),
      ),
      backgroundPaint,
    );

    // Confidence fill
    final confidencePaint = Paint()
      ..color = confidence > 0.7 
          ? Colors.green 
          : confidence > 0.5 
              ? Colors.orange 
              : Colors.red
      ..style = PaintingStyle.fill;
    canvas.drawRRect(
      RRect.fromRectAndRadius(
        Rect.fromLTWH(barX, barY, barWidth * confidence, barHeight),
        const Radius.circular(4),
      ),
      confidencePaint,
    );

    // Confidence text
    final textPainter = TextPainter(
      text: TextSpan(
        text: 'Confidence: ${(confidence * 100).toInt()}%',
        style: const TextStyle(
          color: Colors.white,
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(canvas, Offset(barX, barY + barHeight + 5));
  }

  Map<String, dynamic>? _findKeypoint(List<Map<String, dynamic>> keypoints, String name) {
    try {
      return keypoints.firstWhere((kp) => kp['name'] == name);
    } catch (e) {
      return null;
    }
  }

  @override
  bool shouldRepaint(covariant PoseOverlayPainter oldDelegate) {
    return oldDelegate.poseData != poseData;
  }
}

class GuidanceOverlayPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    // Draw guidance frame
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.3)
      ..strokeWidth = 2
      ..style = PaintingStyle.stroke;

    // Draw a frame indicating ideal positioning
    final frameWidth = size.width * 0.6;
    final frameHeight = size.height * 0.8;
    final frameLeft = (size.width - frameWidth) / 2;
    final frameTop = (size.height - frameHeight) / 2;

    final rect = Rect.fromLTWH(frameLeft, frameTop, frameWidth, frameHeight);
    canvas.drawRect(rect, paint);

    // Draw corner indicators
    final cornerLength = 20.0;
    final cornerPaint = Paint()
      ..color = Colors.white
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;

    // Top-left corner
    canvas.drawLine(
      Offset(frameLeft, frameTop),
      Offset(frameLeft + cornerLength, frameTop),
      cornerPaint,
    );
    canvas.drawLine(
      Offset(frameLeft, frameTop),
      Offset(frameLeft, frameTop + cornerLength),
      cornerPaint,
    );

    // Top-right corner
    canvas.drawLine(
      Offset(frameLeft + frameWidth, frameTop),
      Offset(frameLeft + frameWidth - cornerLength, frameTop),
      cornerPaint,
    );
    canvas.drawLine(
      Offset(frameLeft + frameWidth, frameTop),
      Offset(frameLeft + frameWidth, frameTop + cornerLength),
      cornerPaint,
    );

    // Bottom-left corner
    canvas.drawLine(
      Offset(frameLeft, frameTop + frameHeight),
      Offset(frameLeft + cornerLength, frameTop + frameHeight),
      cornerPaint,
    );
    canvas.drawLine(
      Offset(frameLeft, frameTop + frameHeight),
      Offset(frameLeft, frameTop + frameHeight - cornerLength),
      cornerPaint,
    );

    // Bottom-right corner
    canvas.drawLine(
      Offset(frameLeft + frameWidth, frameTop + frameHeight),
      Offset(frameLeft + frameWidth - cornerLength, frameTop + frameHeight),
      cornerPaint,
    );
    canvas.drawLine(
      Offset(frameLeft + frameWidth, frameTop + frameHeight),
      Offset(frameLeft + frameWidth, frameTop + frameHeight - cornerLength),
      cornerPaint,
    );

    // Draw center crosshair
    final centerX = size.width / 2;
    final centerY = size.height / 2;
    final crosshairSize = 10.0;

    final crosshairPaint = Paint()
      ..color = Colors.white.withOpacity(0.5)
      ..strokeWidth = 1;

    canvas.drawLine(
      Offset(centerX - crosshairSize, centerY),
      Offset(centerX + crosshairSize, centerY),
      crosshairPaint,
    );
    canvas.drawLine(
      Offset(centerX, centerY - crosshairSize),
      Offset(centerX, centerY + crosshairSize),
      crosshairPaint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return false; // Static overlay
  }
}