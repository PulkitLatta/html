import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;

import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SubmissionService {
  static const String _dbName = 'campuspulse_submissions.db';
  static const int _dbVersion = 1;
  static const String _tableName = 'submission_queue';
  static const String _baseUrl = 'https://api.campuspulse.com'; // Replace with actual API
  
  Database? _database;
  Dio? _dio;
  Timer? _uploadTimer;
  bool _isUploading = false;

  /// Initialize the submission service
  Future<void> initialize() async {
    await _initializeDatabase();
    await _initializeDio();
    _startPeriodicUpload();
  }

  /// Initialize SQLite database
  Future<void> _initializeDatabase() async {
    final databasesPath = await getDatabasesPath();
    final path = join(databasesPath, _dbName);

    _database = await openDatabase(
      path,
      version: _dbVersion,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE $_tableName (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_data TEXT NOT NULL,
            user_id TEXT,
            submission_type TEXT DEFAULT 'analysis',
            created_at INTEGER NOT NULL,
            retry_count INTEGER DEFAULT 0,
            last_retry_at INTEGER,
            status TEXT DEFAULT 'pending',
            error_message TEXT
          )
        ''');
      },
    );
  }

  /// Initialize Dio HTTP client
  Future<void> _initializeDio() async {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'CampusPulse-Mobile/1.0.0',
      },
    ));

    // Add auth interceptor
    _dio!.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _getAuthToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) {
        print('Upload error: ${error.message}');
        handler.next(error);
      },
    ));
  }

  /// Submit analysis data to queue
  Future<bool> submitAnalysis(Map<String, dynamic> analysisData) async {
    if (_database == null) {
      print('Database not initialized');
      return false;
    }

    try {
      final userId = await _getCurrentUserId();
      final timestamp = DateTime.now().millisecondsSinceEpoch;

      await _database!.insert(_tableName, {
        'analysis_data': jsonEncode(analysisData),
        'user_id': userId,
        'submission_type': 'analysis',
        'created_at': timestamp,
        'status': 'pending',
      });

      print('Analysis queued for submission');
      
      // Trigger immediate upload attempt
      _attemptUpload();
      
      return true;
    } catch (e) {
      print('Failed to queue analysis: $e');
      return false;
    }
  }

  /// Start periodic upload attempts
  void _startPeriodicUpload() {
    // Upload every 30 seconds
    _uploadTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      _attemptUpload();
    });
  }

  /// Attempt to upload pending submissions
  Future<void> _attemptUpload() async {
    if (_isUploading || _database == null || _dio == null) return;

    _isUploading = true;

    try {
      final pendingSubmissions = await _database!.query(
        _tableName,
        where: 'status = ? OR status = ?',
        whereArgs: ['pending', 'retry'],
        orderBy: 'created_at ASC',
        limit: 10, // Process max 10 at a time
      );

      for (final submission in pendingSubmissions) {
        await _uploadSubmission(submission);
      }
    } catch (e) {
      print('Upload batch error: $e');
    } finally {
      _isUploading = false;
    }
  }

  /// Upload a single submission with exponential backoff
  Future<void> _uploadSubmission(Map<String, dynamic> submission) async {
    final id = submission['id'] as int;
    final retryCount = submission['retry_count'] as int;
    final analysisDataJson = submission['analysis_data'] as String;

    // Check if we should retry (exponential backoff)
    if (retryCount > 0) {
      final lastRetry = submission['last_retry_at'] as int?;
      if (lastRetry != null) {
        final backoffDelay = math.pow(2, retryCount - 1) * 1000; // Exponential backoff in ms
        final timeSinceLastRetry = DateTime.now().millisecondsSinceEpoch - lastRetry;
        
        if (timeSinceLastRetry < backoffDelay) {
          return; // Too soon to retry
        }
      }
    }

    // Give up after 5 retries
    if (retryCount >= 5) {
      await _updateSubmissionStatus(id, 'failed', 'Max retries exceeded');
      return;
    }

    try {
      final analysisData = jsonDecode(analysisDataJson) as Map<String, dynamic>;
      
      // Add submission metadata
      final payload = {
        'analysis_data': analysisData,
        'user_id': submission['user_id'],
        'submission_type': submission['submission_type'],
        'client_timestamp': submission['created_at'],
        'retry_count': retryCount,
      };

      // Attempt upload
      final response = await _dio!.post('/api/submissions', data: payload);

      if (response.statusCode == 200 || response.statusCode == 201) {
        // Success - mark as completed
        await _updateSubmissionStatus(id, 'completed', null);
        print('Successfully uploaded submission $id');
      } else {
        throw DioException(
          requestOptions: RequestOptions(path: '/api/submissions'),
          message: 'Unexpected status code: ${response.statusCode}',
        );
      }
    } catch (e) {
      // Handle different error types
      String errorMessage = e.toString();
      String newStatus = 'retry';

      if (e is DioException) {
        if (e.response?.statusCode == 401) {
          errorMessage = 'Authentication failed';
          newStatus = 'auth_failed';
        } else if (e.response?.statusCode == 400) {
          errorMessage = 'Invalid data format';
          newStatus = 'failed'; // Don't retry client errors
        } else if (e.response?.statusCode != null && e.response!.statusCode! >= 500) {
          errorMessage = 'Server error: ${e.response!.statusCode}';
        } else {
          errorMessage = 'Network error: ${e.message}';
        }
      }

      // Update retry count and status
      await _database!.update(
        _tableName,
        {
          'status': newStatus,
          'retry_count': retryCount + 1,
          'last_retry_at': DateTime.now().millisecondsSinceEpoch,
          'error_message': errorMessage,
        },
        where: 'id = ?',
        whereArgs: [id],
      );

      print('Failed to upload submission $id: $errorMessage (retry $retryCount)');
    }
  }

  /// Update submission status
  Future<void> _updateSubmissionStatus(int id, String status, String? errorMessage) async {
    await _database!.update(
      _tableName,
      {
        'status': status,
        'error_message': errorMessage,
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  /// Get queue statistics
  Future<Map<String, int>> getQueueStats() async {
    if (_database == null) return {};

    final results = await _database!.rawQuery('''
      SELECT status, COUNT(*) as count 
      FROM $_tableName 
      GROUP BY status
    ''');

    final stats = <String, int>{};
    for (final row in results) {
      stats[row['status'] as String] = row['count'] as int;
    }

    return stats;
  }

  /// Get pending submissions count
  Future<int> getPendingCount() async {
    if (_database == null) return 0;

    final result = await _database!.rawQuery('''
      SELECT COUNT(*) as count 
      FROM $_tableName 
      WHERE status IN ('pending', 'retry')
    ''');

    return result.first['count'] as int;
  }

  /// Clear completed submissions older than specified days
  Future<void> cleanupOldSubmissions({int daysOld = 7}) async {
    if (_database == null) return;

    final cutoffTime = DateTime.now()
        .subtract(Duration(days: daysOld))
        .millisecondsSinceEpoch;

    await _database!.delete(
      _tableName,
      where: 'status = ? AND created_at < ?',
      whereArgs: ['completed', cutoffTime],
    );
  }

  /// Retry failed submissions
  Future<void> retryFailedSubmissions() async {
    if (_database == null) return;

    await _database!.update(
      _tableName,
      {
        'status': 'retry',
        'retry_count': 0,
        'last_retry_at': null,
        'error_message': null,
      },
      where: 'status IN (?, ?)',
      whereArgs: ['failed', 'auth_failed'],
    );

    // Trigger immediate upload attempt
    _attemptUpload();
  }

  /// Get current user ID (placeholder - would integrate with auth service)
  Future<String?> _getCurrentUserId() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString('user_id') ?? 'anonymous';
    } catch (e) {
      return 'anonymous';
    }
  }

  /// Get auth token (placeholder - would integrate with auth service)
  Future<String?> _getAuthToken() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString('auth_token');
    } catch (e) {
      return null;
    }
  }

  /// Set auth token
  Future<void> setAuthToken(String token) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('auth_token', token);
    } catch (e) {
      print('Failed to save auth token: $e');
    }
  }

  /// Set user ID
  Future<void> setUserId(String userId) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('user_id', userId);
    } catch (e) {
      print('Failed to save user ID: $e');
    }
  }

  /// Get submission history for debugging
  Future<List<Map<String, dynamic>>> getSubmissionHistory({int limit = 50}) async {
    if (_database == null) return [];

    return await _database!.query(
      _tableName,
      orderBy: 'created_at DESC',
      limit: limit,
    );
  }

  /// Force sync - upload all pending immediately
  Future<bool> forcSync() async {
    if (_isUploading) return false;

    await _attemptUpload();
    
    // Wait a moment and check if anything is still pending
    await Future.delayed(const Duration(seconds: 2));
    final pendingCount = await getPendingCount();
    
    return pendingCount == 0;
  }

  /// Dispose resources
  void dispose() {
    _uploadTimer?.cancel();
    _uploadTimer = null;
    _database?.close();
    _database = null;
    _dio?.close();
    _dio = null;
  }

  /// Check network connectivity status
  Future<bool> isNetworkAvailable() async {
    if (_dio == null) return false;

    try {
      final response = await _dio!.get('/api/health', 
        options: Options(receiveTimeout: const Duration(seconds: 5)),
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  /// Get upload progress info
  Map<String, dynamic> getUploadInfo() {
    return {
      'isUploading': _isUploading,
      'hasNetworkConnection': _dio != null,
      'uploadTimerActive': _uploadTimer?.isActive ?? false,
    };
  }
}