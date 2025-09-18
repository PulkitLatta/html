import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:dio/dio.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:crypto/crypto.dart';

class SubmissionService {
  static final SubmissionService _instance = SubmissionService._internal();
  factory SubmissionService() => _instance;
  SubmissionService._internal();

  Database? _database;
  final Dio _dio = Dio();
  Timer? _uploadTimer;
  bool _isUploading = false;

  // API configuration
  static const String _baseUrl = 'https://api.campuspulse.example.com';
  static const Duration _retryInterval = Duration(minutes: 5);
  static const int _maxRetries = 3;

  Future<void> initialize() async {
    await _initializeDatabase();
    _configureHttpClient();
    _startPeriodicUpload();
  }

  Future<void> _initializeDatabase() async {
    if (_database != null) return;

    final databasesPath = await getDatabasesPath();
    final path = join(databasesPath, 'campuspulse_submissions.db');

    _database = await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_path TEXT NOT NULL,
            analysis_data TEXT NOT NULL,
            athlete_id TEXT,
            submission_time INTEGER NOT NULL,
            upload_status INTEGER DEFAULT 0,
            retry_count INTEGER DEFAULT 0,
            error_message TEXT,
            file_hash TEXT,
            created_at INTEGER NOT NULL
          )
        ''');

        await db.execute('''
          CREATE INDEX idx_upload_status ON submissions(upload_status);
        ''');

        await db.execute('''
          CREATE INDEX idx_submission_time ON submissions(submission_time);
        ''');
      },
    );
  }

  void _configureHttpClient() {
    _dio.options.baseUrl = _baseUrl;
    _dio.options.connectTimeout = Duration(seconds: 30);
    _dio.options.receiveTimeout = Duration(seconds: 60);

    // Add authentication interceptor
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _getAuthToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        // Implement exponential backoff for server errors
        if (error.response?.statusCode != null && 
            error.response!.statusCode! >= 500) {
          await Future.delayed(Duration(seconds: 2));
        }
        handler.next(error);
      },
    ));
  }

  Future<String?> _getAuthToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('auth_token');
  }

  Future<int> queueSubmission({
    required String videoPath,
    required Map<String, dynamic> analysisData,
    String? athleteId,
  }) async {
    if (_database == null) await initialize();

    // Generate file hash for deduplication
    final file = File(videoPath);
    final bytes = await file.readAsBytes();
    final hash = sha256.convert(bytes).toString();

    // Check if already submitted
    final existing = await _database!.query(
      'submissions',
      where: 'file_hash = ?',
      whereArgs: [hash],
      limit: 1,
    );

    if (existing.isNotEmpty) {
      throw Exception('This video has already been submitted');
    }

    final submissionTime = DateTime.now().millisecondsSinceEpoch;
    
    final id = await _database!.insert('submissions', {
      'video_path': videoPath,
      'analysis_data': jsonEncode(analysisData),
      'athlete_id': athleteId,
      'submission_time': submissionTime,
      'upload_status': 0, // 0 = queued, 1 = uploading, 2 = completed, -1 = failed
      'retry_count': 0,
      'file_hash': hash,
      'created_at': submissionTime,
    });

    // Attempt immediate upload if connected
    final connectivity = await Connectivity().checkConnectivity();
    if (connectivity != ConnectivityResult.none) {
      _uploadQueuedSubmissions();
    }

    return id;
  }

  void _startPeriodicUpload() {
    _uploadTimer = Timer.periodic(_retryInterval, (timer) {
      _uploadQueuedSubmissions();
    });
  }

  Future<void> _uploadQueuedSubmissions() async {
    if (_isUploading || _database == null) return;

    _isUploading = true;

    try {
      // Check connectivity
      final connectivity = await Connectivity().checkConnectivity();
      if (connectivity == ConnectivityResult.none) return;

      // Get queued and failed submissions (with retry limit)
      final submissions = await _database!.query(
        'submissions',
        where: '(upload_status = 0 OR upload_status = -1) AND retry_count < ?',
        whereArgs: [_maxRetries],
        orderBy: 'submission_time ASC',
        limit: 5, // Process in batches
      );

      for (final submission in submissions) {
        await _uploadSingleSubmission(submission);
      }
    } catch (e) {
      print('Error during batch upload: $e');
    } finally {
      _isUploading = false;
    }
  }

  Future<void> _uploadSingleSubmission(Map<String, dynamic> submission) async {
    final id = submission['id'];
    
    try {
      // Mark as uploading
      await _database!.update(
        'submissions',
        {'upload_status': 1},
        where: 'id = ?',
        whereArgs: [id],
      );

      // Prepare form data
      final videoPath = submission['video_path'];
      final analysisData = jsonDecode(submission['analysis_data']);
      
      final formData = FormData.fromMap({
        'video': await MultipartFile.fromFile(videoPath),
        'analysis_data': jsonEncode(analysisData),
        'athlete_id': submission['athlete_id'],
        'submission_time': submission['submission_time'],
        'client_id': submission['id'].toString(),
      });

      // Upload with exponential backoff
      final retryCount = submission['retry_count'];
      final backoffDelay = Duration(seconds: math.pow(2, retryCount).toInt());
      
      if (retryCount > 0) {
        await Future.delayed(backoffDelay);
      }

      final response = await _dio.post('/api/submissions', data: formData);

      if (response.statusCode == 200 || response.statusCode == 201) {
        // Mark as completed
        await _database!.update(
          'submissions',
          {
            'upload_status': 2,
            'error_message': null,
          },
          where: 'id = ?',
          whereArgs: [id],
        );
        
        // Optionally delete local video file after successful upload
        // await File(videoPath).delete();
      } else {
        throw Exception('Upload failed with status: ${response.statusCode}');
      }

    } catch (e) {
      // Increment retry count and mark as failed
      final newRetryCount = (submission['retry_count'] ?? 0) + 1;
      
      await _database!.update(
        'submissions',
        {
          'upload_status': -1,
          'retry_count': newRetryCount,
          'error_message': e.toString(),
        },
        where: 'id = ?',
        whereArgs: [id],
      );

      print('Upload failed for submission $id (attempt $newRetryCount): $e');
    }
  }

  Future<List<Map<String, dynamic>>> getSubmissionHistory({
    int limit = 50,
    int offset = 0,
  }) async {
    if (_database == null) await initialize();

    return await _database!.query(
      'submissions',
      orderBy: 'created_at DESC',
      limit: limit,
      offset: offset,
    );
  }

  Future<Map<String, int>> getSubmissionStats() async {
    if (_database == null) await initialize();

    final results = await _database!.rawQuery('''
      SELECT 
        upload_status,
        COUNT(*) as count
      FROM submissions 
      GROUP BY upload_status
    ''');

    final stats = <String, int>{
      'queued': 0,
      'uploading': 0,
      'completed': 0,
      'failed': 0,
    };

    for (final row in results) {
      final status = row['upload_status'] as int;
      final count = row['count'] as int;
      
      switch (status) {
        case 0:
          stats['queued'] = count;
          break;
        case 1:
          stats['uploading'] = count;
          break;
        case 2:
          stats['completed'] = count;
          break;
        case -1:
          stats['failed'] = count;
          break;
      }
    }

    return stats;
  }

  Future<void> retryFailedSubmissions() async {
    if (_database == null) await initialize();

    // Reset failed submissions that haven't exceeded retry limit
    await _database!.update(
      'submissions',
      {
        'upload_status': 0,
        'error_message': null,
      },
      where: 'upload_status = -1 AND retry_count < ?',
      whereArgs: [_maxRetries],
    );

    // Trigger upload attempt
    _uploadQueuedSubmissions();
  }

  Future<void> clearCompletedSubmissions() async {
    if (_database == null) await initialize();

    // Delete submissions older than 30 days that are completed
    final cutoffTime = DateTime.now()
        .subtract(Duration(days: 30))
        .millisecondsSinceEpoch;

    await _database!.delete(
      'submissions',
      where: 'upload_status = 2 AND created_at < ?',
      whereArgs: [cutoffTime],
    );
  }

  void dispose() {
    _uploadTimer?.cancel();
    _database?.close();
    _database = null;
    _isUploading = false;
  }
}

// Import math for exponential backoff
import 'dart:math' as math;