import 'package:flutter_test/flutter_test.dart';
import 'package:campuspulse_mobile/services/ml_service.dart';

void main() {
  group('MLService Tests', () {
    late MLService mlService;

    setUp(() {
      mlService = MLService();
    });

    tearDown(() {
      mlService.dispose();
    });

    test('initial state is not loaded', () {
      expect(mlService.isModelLoaded, false);
    });

    test('model info returns empty map when not initialized', () {
      final info = mlService.getModelInfo();
      expect(info, isEmpty);
    });

    test('pose similarity calculation works', () {
      final pose1 = {
        'keypoints': [
          {'x': 100.0, 'y': 200.0, 'visible': true},
          {'x': 150.0, 'y': 250.0, 'visible': true},
        ]
      };

      final pose2 = {
        'keypoints': [
          {'x': 105.0, 'y': 205.0, 'visible': true},
          {'x': 155.0, 'y': 255.0, 'visible': true},
        ]
      };

      final similarity = MLService.calculatePoseSimilarity(pose1, pose2);
      expect(similarity, greaterThan(0.0));
      expect(similarity, lessThanOrEqualTo(1.0));
    });

    test('skeleton connections are properly defined', () {
      final connections = mlService.getSkeletonConnections();
      expect(connections, isNotEmpty);
      expect(connections.length, greaterThan(10));
      
      for (final connection in connections) {
        expect(connection, containsPair('from', isA<String>()));
        expect(connection, containsPair('to', isA<String>()));
      }
    });

    test('pose similarity with mismatched keypoints returns 0', () {
      final pose1 = {
        'keypoints': [
          {'x': 100.0, 'y': 200.0, 'visible': true},
        ]
      };

      final pose2 = {
        'keypoints': [
          {'x': 100.0, 'y': 200.0, 'visible': true},
          {'x': 150.0, 'y': 250.0, 'visible': true},
        ]
      };

      final similarity = MLService.calculatePoseSimilarity(pose1, pose2);
      expect(similarity, 0.0);
    });

    test('batch processing handles empty list', () async {
      final results = await mlService.batchDetectPoses([]);
      expect(results, isEmpty);
    });
  });
}