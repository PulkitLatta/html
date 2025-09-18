import 'package:flutter_test/flutter_test.dart';
import 'package:campuspulse_mobile/services/analysis.dart';

void main() {
  group('AnalysisService Tests', () {
    test('analyzePoseSequence returns empty result for empty sequence', () {
      final result = AnalysisService.analyzePoseSequence([]);
      
      expect(result['overallScore'], 0.0);
      expect(result['formConsistency'], 0.0);
      expect(result['movementEfficiency'], 0.0);
      expect(result['techniqueScore'], 0.0);
      expect(result['balance'], 0.0);
      expect(result['totalFrames'], 0);
    });

    test('analyzePoseSequence calculates metrics for valid sequence', () {
      final mockPoseSequence = [
        {
          'timestamp': 1000,
          'keypoints': _generateMockKeypoints(),
          'averageConfidence': 0.8,
        },
        {
          'timestamp': 1100,
          'keypoints': _generateMockKeypoints(),
          'averageConfidence': 0.82,
        },
        {
          'timestamp': 1200,
          'keypoints': _generateMockKeypoints(),
          'averageConfidence': 0.78,
        },
      ];

      final result = AnalysisService.analyzePoseSequence(mockPoseSequence);
      
      expect(result['overallScore'], greaterThan(0.0));
      expect(result['formConsistency'], greaterThan(0.0));
      expect(result['movementEfficiency'], greaterThan(0.0));
      expect(result['techniqueScore'], greaterThan(0.0));
      expect(result['balance'], greaterThan(0.0));
      expect(result['totalFrames'], 3);
      expect(result['duration'], closeTo(0.2, 0.01));
    });

    test('debounced analysis waits for debounce period', () async {
      final mockPoseSequence = [
        {
          'timestamp': 1000,
          'keypoints': _generateMockKeypoints(),
          'averageConfidence': 0.8,
        },
      ];

      final stopwatch = Stopwatch()..start();
      final result = await AnalysisService.analyzePoseSequenceDebounced(mockPoseSequence);
      stopwatch.stop();

      expect(stopwatch.elapsedMilliseconds, greaterThanOrEqualTo(300));
      expect(result['totalFrames'], 1);
    });

    test('canceling pending analysis works', () {
      AnalysisService.cancelPendingAnalysis();
      // Should not throw any exceptions
      expect(true, true);
    });
  });
}

List<Map<String, dynamic>> _generateMockKeypoints() {
  return List.generate(17, (i) => {
    'name': 'keypoint_$i',
    'x': 100.0 + i * 10,
    'y': 200.0 + i * 15,
    'confidence': 0.8 + (i % 3) * 0.05,
    'visible': true,
  });
}