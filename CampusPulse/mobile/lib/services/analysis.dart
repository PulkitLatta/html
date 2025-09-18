import 'dart:async';
import 'dart:math' as math;

class AnalysisService {
  Timer? _analysisTimer;
  List<List<List<double>>> _poseHistory = [];
  DateTime? _analysisStartTime;
  
  // 300ms debounce for real-time analysis updates
  static const Duration _debounceDuration = Duration(milliseconds: 300);
  Timer? _debounceTimer;
  Function(Map<String, dynamic>)? _onAnalysisUpdate;

  void startAnalysis({Function(Map<String, dynamic>)? onUpdate}) {
    _analysisStartTime = DateTime.now();
    _poseHistory.clear();
    _onAnalysisUpdate = onUpdate;
    
    // Start periodic analysis (every 100ms for smooth updates)
    _analysisTimer = Timer.periodic(Duration(milliseconds: 100), (timer) {
      _triggerDebouncedAnalysis();
    });
  }

  void _triggerDebouncedAnalysis() {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(_debounceDuration, () {
      if (_poseHistory.isNotEmpty && _onAnalysisUpdate != null) {
        final analysis = _performRealTimeAnalysis();
        _onAnalysisUpdate!(analysis);
      }
    });
  }

  void addPoseData(List<List<double>> poseData) {
    _poseHistory.add(poseData);
    
    // Keep only the last 5 seconds of data (assuming ~30 FPS)
    if (_poseHistory.length > 150) {
      _poseHistory.removeAt(0);
    }
  }

  Map<String, dynamic> _performRealTimeAnalysis() {
    if (_poseHistory.isEmpty) {
      return _getEmptyAnalysis();
    }

    return {
      'formConsistency': _calculateFormConsistency(),
      'stability': _calculateStability(),
      'rangeOfMotion': _calculateRangeOfMotion(),
      'timing': _calculateTiming(),
      'overallScore': 0.0, // Will be calculated from other metrics
    };
  }

  Future<Map<String, dynamic>> stopAnalysis() async {
    _analysisTimer?.cancel();
    _debounceTimer?.cancel();
    
    if (_poseHistory.isEmpty) {
      return _getEmptyAnalysis();
    }

    final finalAnalysis = _performFinalAnalysis();
    
    // Calculate overall score
    finalAnalysis['overallScore'] = _calculateOverallScore(finalAnalysis);
    
    return finalAnalysis;
  }

  Map<String, dynamic> _performFinalAnalysis() {
    return {
      'formConsistency': _calculateFormConsistency(),
      'stability': _calculateStability(),
      'rangeOfMotion': _calculateRangeOfMotion(),
      'timing': _calculateTiming(),
      'duration': _getAnalysisDuration(),
      'totalFrames': _poseHistory.length,
    };
  }

  double _calculateFormConsistency() {
    if (_poseHistory.length < 2) return 0.0;

    double totalVariation = 0.0;
    int comparisonCount = 0;

    // Compare consecutive frames to measure consistency
    for (int i = 1; i < _poseHistory.length; i++) {
      final pose1 = _poseHistory[i - 1];
      final pose2 = _poseHistory[i];
      
      double frameVariation = 0.0;
      for (int j = 0; j < pose1.length; j++) {
        if (pose1[j].length >= 2 && pose2[j].length >= 2) {
          // Calculate Euclidean distance between keypoints
          final dx = pose1[j][0] - pose2[j][0];
          final dy = pose1[j][1] - pose2[j][1];
          frameVariation += math.sqrt(dx * dx + dy * dy);
        }
      }
      
      totalVariation += frameVariation;
      comparisonCount++;
    }

    if (comparisonCount == 0) return 0.0;

    final avgVariation = totalVariation / comparisonCount;
    // Convert to percentage (lower variation = higher consistency)
    return math.max(0.0, 100.0 - (avgVariation * 1000));
  }

  double _calculateStability() {
    if (_poseHistory.length < 10) return 0.0;

    // Focus on core stability keypoints (shoulders, hips)
    const stabilityKeypoints = [5, 6, 11, 12]; // shoulders and hips
    
    double totalStability = 0.0;
    int keypointCount = 0;

    for (int keypoint in stabilityKeypoints) {
      final positions = <List<double>>[];
      
      for (final pose in _poseHistory) {
        if (keypoint < pose.length && pose[keypoint].length >= 2) {
          positions.add([pose[keypoint][0], pose[keypoint][1]]);
        }
      }
      
      if (positions.length < 2) continue;

      // Calculate standard deviation of positions
      double meanX = positions.map((p) => p[0]).reduce((a, b) => a + b) / positions.length;
      double meanY = positions.map((p) => p[1]).reduce((a, b) => a + b) / positions.length;
      
      double varianceX = positions.map((p) => math.pow(p[0] - meanX, 2)).reduce((a, b) => a + b) / positions.length;
      double varianceY = positions.map((p) => math.pow(p[1] - meanY, 2)).reduce((a, b) => a + b) / positions.length;
      
      double stdDev = math.sqrt((varianceX + varianceY) / 2);
      
      // Convert to stability score (lower std dev = higher stability)
      totalStability += math.max(0.0, 100.0 - (stdDev * 5000));
      keypointCount++;
    }

    return keypointCount > 0 ? totalStability / keypointCount : 0.0;
  }

  double _calculateRangeOfMotion() {
    if (_poseHistory.isEmpty) return 0.0;

    // Calculate range of motion for major joints
    const motionKeypoints = [7, 8, 13, 14]; // elbows and knees
    
    double totalRange = 0.0;
    int keypointCount = 0;

    for (int keypoint in motionKeypoints) {
      double minX = double.infinity, maxX = double.negativeInfinity;
      double minY = double.infinity, maxY = double.negativeInfinity;
      
      for (final pose in _poseHistory) {
        if (keypoint < pose.length && pose[keypoint].length >= 2) {
          minX = math.min(minX, pose[keypoint][0]);
          maxX = math.max(maxX, pose[keypoint][0]);
          minY = math.min(minY, pose[keypoint][1]);
          maxY = math.max(maxY, pose[keypoint][1]);
        }
      }
      
      if (minX != double.infinity) {
        final rangeX = maxX - minX;
        final rangeY = maxY - minY;
        final totalRangeForKeypoint = math.sqrt(rangeX * rangeX + rangeY * rangeY);
        
        // Convert to degrees (approximate)
        totalRange += totalRangeForKeypoint * 180;
        keypointCount++;
      }
    }

    return keypointCount > 0 ? totalRange / keypointCount : 0.0;
  }

  double _calculateTiming() {
    if (_analysisStartTime == null) return 0.0;
    
    final duration = DateTime.now().difference(_analysisStartTime!);
    return duration.inMilliseconds / 1000.0; // Return duration in seconds
  }

  double _getAnalysisDuration() {
    if (_analysisStartTime == null) return 0.0;
    
    final duration = DateTime.now().difference(_analysisStartTime!);
    return duration.inMilliseconds / 1000.0;
  }

  double _calculateOverallScore(Map<String, dynamic> analysis) {
    final consistency = analysis['formConsistency'] ?? 0.0;
    final stability = analysis['stability'] ?? 0.0;
    final rangeOfMotion = math.min(100.0, (analysis['rangeOfMotion'] ?? 0.0) / 2.0);
    
    // Weighted average of different metrics
    return (consistency * 0.4 + stability * 0.3 + rangeOfMotion * 0.3).clamp(0.0, 100.0);
  }

  Map<String, dynamic> _getEmptyAnalysis() {
    return {
      'formConsistency': 0.0,
      'stability': 0.0,
      'rangeOfMotion': 0.0,
      'timing': 0.0,
      'overallScore': 0.0,
      'duration': 0.0,
      'totalFrames': 0,
    };
  }

  void dispose() {
    _analysisTimer?.cancel();
    _debounceTimer?.cancel();
    _poseHistory.clear();
    _onAnalysisUpdate = null;
  }
}