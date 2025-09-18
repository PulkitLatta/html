import 'dart:async';
import 'dart:math' as math;

class AnalysisService {
  static const int debounceDelayMs = 300;
  static Timer? _debounceTimer;

  /// Analyze a sequence of pose detections with debouncing
  static Future<Map<String, dynamic>> analyzePoseSequenceDebounced(
    List<Map<String, dynamic>> poseSequence,
  ) async {
    final completer = Completer<Map<String, dynamic>>();

    // Cancel existing timer if any
    _debounceTimer?.cancel();

    // Set up new debounced analysis
    _debounceTimer = Timer(Duration(milliseconds: debounceDelayMs), () {
      final result = analyzePoseSequence(poseSequence);
      completer.complete(result);
    });

    return completer.future;
  }

  /// Main analysis function - processes pose sequence and calculates metrics
  static Map<String, dynamic> analyzePoseSequence(List<Map<String, dynamic>> poseSequence) {
    if (poseSequence.isEmpty) {
      return _getEmptyAnalysisResult();
    }

    final startTime = poseSequence.first['timestamp'] ?? 0;
    final endTime = poseSequence.last['timestamp'] ?? 0;
    final duration = (endTime - startTime) / 1000.0; // Convert to seconds

    // Calculate individual metrics
    final formConsistency = _calculateFormConsistency(poseSequence);
    final movementEfficiency = _calculateMovementEfficiency(poseSequence);
    final techniqueScore = _calculateTechniqueScore(poseSequence);
    final balance = _calculateBalance(poseSequence);
    
    // Calculate overall score with weighted average
    final overallScore = _calculateOverallScore(
      formConsistency,
      movementEfficiency,
      techniqueScore,
      balance,
    );

    // Calculate average confidence
    final avgConfidence = _calculateAverageConfidence(poseSequence);

    return {
      'overallScore': overallScore,
      'formConsistency': formConsistency,
      'movementEfficiency': movementEfficiency,
      'techniqueScore': techniqueScore,
      'balance': balance,
      'duration': duration,
      'totalFrames': poseSequence.length,
      'avgConfidence': avgConfidence,
      'timestamp': DateTime.now().millisecondsSinceEpoch,
      'analysisVersion': '1.0.0',
    };
  }

  /// Calculate form consistency based on pose similarity over time
  static double _calculateFormConsistency(List<Map<String, dynamic>> poseSequence) {
    if (poseSequence.length < 2) return 0.0;

    final consistencyScores = <double>[];
    
    // Calculate pose similarity between consecutive frames
    for (int i = 1; i < poseSequence.length; i++) {
      final pose1 = poseSequence[i - 1];
      final pose2 = poseSequence[i];
      
      final similarity = _calculatePoseSimilarity(pose1, pose2);
      consistencyScores.add(similarity);
    }

    if (consistencyScores.isEmpty) return 0.0;

    // Calculate average similarity and convert to percentage
    final averageSimilarity = consistencyScores.reduce((a, b) => a + b) / consistencyScores.length;
    
    // Apply smoothing and scaling
    return (averageSimilarity * 100).clamp(0.0, 100.0);
  }

  /// Calculate movement efficiency based on smoothness and energy optimization
  static double _calculateMovementEfficiency(List<Map<String, dynamic>> poseSequence) {
    if (poseSequence.length < 3) return 0.0;

    double totalJerk = 0.0;
    int validMeasurements = 0;

    // Calculate jerk (third derivative of position) for key joints
    final keyJoints = ['left_wrist', 'right_wrist', 'left_ankle', 'right_ankle'];
    
    for (final jointName in keyJoints) {
      final jerkValues = _calculateJointJerk(poseSequence, jointName);
      if (jerkValues.isNotEmpty) {
        totalJerk += jerkValues.reduce((a, b) => a + b) / jerkValues.length;
        validMeasurements++;
      }
    }

    if (validMeasurements == 0) return 0.0;

    final averageJerk = totalJerk / validMeasurements;
    
    // Convert jerk to efficiency score (lower jerk = higher efficiency)
    final efficiency = math.exp(-averageJerk / 1000) * 100;
    
    return efficiency.clamp(0.0, 100.0);
  }

  /// Calculate technique score based on biomechanical principles
  static double _calculateTechniqueScore(List<Map<String, dynamic>> poseSequence) {
    if (poseSequence.isEmpty) return 0.0;

    double totalTechniqueScore = 0.0;
    int validFrames = 0;

    for (final pose in poseSequence) {
      final keypoints = pose['keypoints'] as List<Map<String, dynamic>>?;
      if (keypoints == null || keypoints.length < 17) continue;

      // Check body alignment, joint angles, and posture
      final alignmentScore = _checkBodyAlignment(keypoints);
      final jointAngleScore = _checkJointAngles(keypoints);
      final postureScore = _checkPosture(keypoints);

      final frameScore = (alignmentScore + jointAngleScore + postureScore) / 3.0;
      totalTechniqueScore += frameScore;
      validFrames++;
    }

    if (validFrames == 0) return 0.0;

    return (totalTechniqueScore / validFrames).clamp(0.0, 100.0);
  }

  /// Calculate balance and stability metrics
  static double _calculateBalance(List<Map<String, dynamic>> poseSequence) {
    if (poseSequence.isEmpty) return 0.0;

    double totalBalanceScore = 0.0;
    int validFrames = 0;

    for (final pose in poseSequence) {
      final keypoints = pose['keypoints'] as List<Map<String, dynamic>>?;
      if (keypoints == null || keypoints.length < 17) continue;

      // Calculate center of mass stability
      final comStability = _calculateCenterOfMassStability(keypoints);
      
      // Check base of support
      final supportScore = _checkBaseOfSupport(keypoints);

      final frameBalance = (comStability + supportScore) / 2.0;
      totalBalanceScore += frameBalance;
      validFrames++;
    }

    if (validFrames == 0) return 0.0;

    return (totalBalanceScore / validFrames).clamp(0.0, 100.0);
  }

  /// Helper: Calculate pose similarity between two poses
  static double _calculatePoseSimilarity(Map<String, dynamic> pose1, Map<String, dynamic> pose2) {
    final keypoints1 = pose1['keypoints'] as List<Map<String, dynamic>>?;
    final keypoints2 = pose2['keypoints'] as List<Map<String, dynamic>>?;

    if (keypoints1 == null || keypoints2 == null) return 0.0;
    if (keypoints1.length != keypoints2.length) return 0.0;

    double totalDistance = 0.0;
    int validComparisons = 0;

    for (int i = 0; i < keypoints1.length; i++) {
      final kp1 = keypoints1[i];
      final kp2 = keypoints2[i];

      if (kp1['visible'] == true && kp2['visible'] == true) {
        final dx = (kp1['x'] as double) - (kp2['x'] as double);
        final dy = (kp1['y'] as double) - (kp2['y'] as double);
        final distance = math.sqrt(dx * dx + dy * dy);

        totalDistance += distance;
        validComparisons++;
      }
    }

    if (validComparisons == 0) return 0.0;

    final averageDistance = totalDistance / validComparisons;
    return math.exp(-averageDistance / 50.0); // Normalize to 0-1
  }

  /// Helper: Calculate jerk for a specific joint
  static List<double> _calculateJointJerk(List<Map<String, dynamic>> poseSequence, String jointName) {
    final positions = <Map<String, double>>[];
    
    // Extract joint positions over time
    for (final pose in poseSequence) {
      final keypoints = pose['keypoints'] as List<Map<String, dynamic>>?;
      if (keypoints == null) continue;

      final joint = keypoints.firstWhere(
        (kp) => kp['name'] == jointName,
        orElse: () => <String, dynamic>{},
      );

      if (joint['visible'] == true) {
        positions.add({
          'x': joint['x'] as double,
          'y': joint['y'] as double,
        });
      }
    }

    if (positions.length < 3) return [];

    // Calculate jerk (third derivative)
    final jerkValues = <double>[];
    for (int i = 2; i < positions.length; i++) {
      final p0 = positions[i - 2];
      final p1 = positions[i - 1];
      final p2 = positions[i];

      // Simple numerical differentiation for jerk
      final jerkX = (p2['x']! - 2 * p1['x']! + p0['x']!).abs();
      final jerkY = (p2['y']! - 2 * p1['y']! + p0['y']!).abs();
      
      jerkValues.add(math.sqrt(jerkX * jerkX + jerkY * jerkY));
    }

    return jerkValues;
  }

  /// Helper: Check body alignment
  static double _checkBodyAlignment(List<Map<String, dynamic>> keypoints) {
    // Check shoulder alignment, hip alignment, spine straightness
    final leftShoulder = _getKeypointByName(keypoints, 'left_shoulder');
    final rightShoulder = _getKeypointByName(keypoints, 'right_shoulder');
    final leftHip = _getKeypointByName(keypoints, 'left_hip');
    final rightHip = _getKeypointByName(keypoints, 'right_hip');

    if (leftShoulder == null || rightShoulder == null || leftHip == null || rightHip == null) {
      return 50.0; // Default middle score
    }

    // Calculate shoulder and hip level differences
    final shoulderDiff = (leftShoulder['y']! - rightShoulder['y']!).abs();
    final hipDiff = (leftHip['y']! - rightHip['y']!).abs();

    // Lower differences indicate better alignment
    final alignmentScore = 100 - ((shoulderDiff + hipDiff) * 2).clamp(0.0, 100.0);
    return alignmentScore;
  }

  /// Helper: Check joint angles
  static double _checkJointAngles(List<Map<String, dynamic>> keypoints) {
    // Check elbow and knee angles for proper form
    double totalAngleScore = 0.0;
    int validAngles = 0;

    final angleChecks = [
      ['left_shoulder', 'left_elbow', 'left_wrist'],
      ['right_shoulder', 'right_elbow', 'right_wrist'],
      ['left_hip', 'left_knee', 'left_ankle'],
      ['right_hip', 'right_knee', 'right_ankle'],
    ];

    for (final angleCheck in angleChecks) {
      final angle = _calculateAngle(keypoints, angleCheck[0], angleCheck[1], angleCheck[2]);
      if (angle != null) {
        // Score based on angle reasonableness (avoiding hyperextension, etc.)
        final angleScore = _scoreJointAngle(angle);
        totalAngleScore += angleScore;
        validAngles++;
      }
    }

    return validAngles > 0 ? totalAngleScore / validAngles : 50.0;
  }

  /// Helper: Check posture
  static double _checkPosture(List<Map<String, dynamic>> keypoints) {
    final nose = _getKeypointByName(keypoints, 'nose');
    final leftHip = _getKeypointByName(keypoints, 'left_hip');
    final rightHip = _getKeypointByName(keypoints, 'right_hip');

    if (nose == null || leftHip == null || rightHip == null) return 50.0;

    // Calculate head position relative to hips
    final hipCenterX = (leftHip['x']! + rightHip['x']!) / 2;
    final hipCenterY = (leftHip['y']! + rightHip['y']!) / 2;

    final headOffset = (nose['x']! - hipCenterX).abs();
    
    // Good posture has minimal head offset
    final postureScore = math.max(0, 100 - headOffset * 2);
    return postureScore.clamp(0.0, 100.0);
  }

  /// Helper: Calculate center of mass stability
  static double _calculateCenterOfMassStability(List<Map<String, dynamic>> keypoints) {
    // Simplified COM calculation using major body points
    final majorPoints = ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip'];
    final visiblePoints = <Map<String, double>>[];

    for (final pointName in majorPoints) {
      final point = _getKeypointByName(keypoints, pointName);
      if (point != null && point['visible'] == true) {
        visiblePoints.add({'x': point['x']!, 'y': point['y']!});
      }
    }

    if (visiblePoints.length < 2) return 50.0;

    // Calculate center of mass
    final comX = visiblePoints.map((p) => p['x']!).reduce((a, b) => a + b) / visiblePoints.length;
    final comY = visiblePoints.map((p) => p['y']!).reduce((a, b) => a + b) / visiblePoints.length;

    // Stability score based on COM position (higher is more stable)
    return 75.0; // Simplified - in real app would analyze movement patterns
  }

  /// Helper: Check base of support
  static double _checkBaseOfSupport(List<Map<String, dynamic>> keypoints) {
    final leftAnkle = _getKeypointByName(keypoints, 'left_ankle');
    final rightAnkle = _getKeypointByName(keypoints, 'right_ankle');

    if (leftAnkle == null || rightAnkle == null) return 50.0;

    final footDistance = math.sqrt(
      math.pow(leftAnkle['x']! - rightAnkle['x']!, 2) +
      math.pow(leftAnkle['y']! - rightAnkle['y']!, 2),
    );

    // Appropriate foot spacing indicates good base of support
    final optimalDistance = 50.0; // Arbitrary units
    final distanceScore = 100 - (footDistance - optimalDistance).abs() * 2;
    
    return distanceScore.clamp(0.0, 100.0);
  }

  /// Helper: Get keypoint by name
  static Map<String, double>? _getKeypointByName(List<Map<String, dynamic>> keypoints, String name) {
    try {
      final keypoint = keypoints.firstWhere((kp) => kp['name'] == name);
      if (keypoint['visible'] == true) {
        return {
          'x': keypoint['x'] as double,
          'y': keypoint['y'] as double,
        };
      }
    } catch (e) {
      // Keypoint not found
    }
    return null;
  }

  /// Helper: Calculate angle between three points
  static double? _calculateAngle(List<Map<String, dynamic>> keypoints, String p1Name, String p2Name, String p3Name) {
    final p1 = _getKeypointByName(keypoints, p1Name);
    final p2 = _getKeypointByName(keypoints, p2Name);
    final p3 = _getKeypointByName(keypoints, p3Name);

    if (p1 == null || p2 == null || p3 == null) return null;

    final v1x = p1['x']! - p2['x']!;
    final v1y = p1['y']! - p2['y']!;
    final v2x = p3['x']! - p2['x']!;
    final v2y = p3['y']! - p2['y']!;

    final dot = v1x * v2x + v1y * v2y;
    final mag1 = math.sqrt(v1x * v1x + v1y * v1y);
    final mag2 = math.sqrt(v2x * v2x + v2y * v2y);

    if (mag1 == 0 || mag2 == 0) return null;

    final cosAngle = dot / (mag1 * mag2);
    final angle = math.acos(cosAngle.clamp(-1.0, 1.0)) * 180 / math.pi;

    return angle;
  }

  /// Helper: Score joint angle
  static double _scoreJointAngle(double angle) {
    // Score based on biomechanically sound angles
    if (angle >= 90 && angle <= 150) return 100.0; // Good range
    if (angle >= 60 && angle <= 180) return 80.0;  // Acceptable range
    return 50.0; // Outside ideal ranges
  }

  /// Helper: Calculate overall score with weighted average
  static double _calculateOverallScore(double form, double efficiency, double technique, double balance) {
    // Weighted average of all metrics
    const formWeight = 0.3;
    const efficiencyWeight = 0.25;
    const techniqueWeight = 0.3;
    const balanceWeight = 0.15;

    final weightedScore = 
      form * formWeight +
      efficiency * efficiencyWeight +
      technique * techniqueWeight +
      balance * balanceWeight;

    return weightedScore.clamp(0.0, 100.0);
  }

  /// Helper: Calculate average confidence across pose sequence
  static double _calculateAverageConfidence(List<Map<String, dynamic>> poseSequence) {
    if (poseSequence.isEmpty) return 0.0;

    double totalConfidence = 0.0;
    int validFrames = 0;

    for (final pose in poseSequence) {
      final avgConfidence = pose['averageConfidence'] as double?;
      if (avgConfidence != null) {
        totalConfidence += avgConfidence;
        validFrames++;
      }
    }

    return validFrames > 0 ? totalConfidence / validFrames : 0.0;
  }

  /// Helper: Return empty analysis result
  static Map<String, dynamic> _getEmptyAnalysisResult() {
    return {
      'overallScore': 0.0,
      'formConsistency': 0.0,
      'movementEfficiency': 0.0,
      'techniqueScore': 0.0,
      'balance': 0.0,
      'duration': 0.0,
      'totalFrames': 0,
      'avgConfidence': 0.0,
      'timestamp': DateTime.now().millisecondsSinceEpoch,
      'analysisVersion': '1.0.0',
    };
  }

  /// Cancel any pending debounced analysis
  static void cancelPendingAnalysis() {
    _debounceTimer?.cancel();
    _debounceTimer = null;
  }
}