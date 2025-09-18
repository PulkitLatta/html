import 'package:flutter_test/flutter_test.dart';
import 'package:campuspulse/services/analysis.dart';

void main() {
  group('AnalysisService', () {
    late AnalysisService service;

    setUp(() {
      service = AnalysisService();
    });

    tearDown(() {
      service.dispose();
    });

    test('should start and stop analysis', () async {
      bool updateReceived = false;
      
      service.startAnalysis(onUpdate: (data) {
        updateReceived = true;
        expect(data.containsKey('formConsistency'), isTrue);
        expect(data.containsKey('stability'), isTrue);
        expect(data.containsKey('rangeOfMotion'), isTrue);
      });

      // Add some mock pose data
      service.addPoseData([
        [0.5, 0.5, 0.9], // nose
        [0.4, 0.4, 0.8], // left eye
        [0.6, 0.4, 0.8], // right eye
      ]);

      // Wait for debounced analysis
      await Future.delayed(Duration(milliseconds: 400));
      
      final result = await service.stopAnalysis();
      
      expect(result, isA<Map<String, dynamic>>());
      expect(result.containsKey('overallScore'), isTrue);
      expect(result['overallScore'], isA<double>());
    });

    test('should handle empty pose data gracefully', () async {
      service.startAnalysis();
      final result = await service.stopAnalysis();
      
      expect(result['formConsistency'], equals(0.0));
      expect(result['stability'], equals(0.0));
      expect(result['overallScore'], equals(0.0));
    });

    test('should calculate form consistency', () async {
      service.startAnalysis();
      
      // Add consistent pose data
      for (int i = 0; i < 10; i++) {
        service.addPoseData([
          [0.5, 0.5, 0.9],
          [0.4, 0.4, 0.8],
          [0.6, 0.4, 0.8],
        ]);
      }
      
      final result = await service.stopAnalysis();
      expect(result['formConsistency'], greaterThan(80.0));
    });
  });
}