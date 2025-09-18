import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/submission_service.dart';
import '../widgets/result_card.dart';

class ResultsScreen extends StatefulWidget {
  final Map<String, dynamic> analysisData;

  const ResultsScreen({Key? key, required this.analysisData}) : super(key: key);

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> {
  bool _isSubmitting = false;

  @override
  Widget build(BuildContext context) {
    final data = widget.analysisData;
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('Analysis Results'),
        backgroundColor: Colors.blue[900],
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            onPressed: _isSubmitting ? null : _submitResults,
            icon: _isSubmitting
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  )
                : const Icon(Icons.cloud_upload),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Overall Score
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  children: [
                    const Text(
                      'Overall Performance',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    CircularProgressIndicator(
                      value: (data['overallScore'] ?? 0.0) / 100.0,
                      strokeWidth: 8,
                      backgroundColor: Colors.grey[300],
                      valueColor: AlwaysStoppedAnimation<Color>(
                        _getScoreColor(data['overallScore'] ?? 0.0),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      '${(data['overallScore'] ?? 0.0).toStringAsFixed(1)}%',
                      style: const TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            // Detailed Metrics
            Expanded(
              child: ListView(
                children: [
                  ResultCard(
                    title: 'Form Consistency',
                    value: '${(data['formConsistency'] ?? 0.0).toStringAsFixed(1)}%',
                    icon: Icons.timeline,
                    color: Colors.blue,
                    description: 'Stability and repeatability of movement patterns',
                  ),
                  const SizedBox(height: 12),
                  ResultCard(
                    title: 'Movement Efficiency',
                    value: '${(data['movementEfficiency'] ?? 0.0).toStringAsFixed(1)}%',
                    icon: Icons.speed,
                    color: Colors.green,
                    description: 'Optimization of energy expenditure and technique',
                  ),
                  const SizedBox(height: 12),
                  ResultCard(
                    title: 'Technique Score',
                    value: '${(data['techniqueScore'] ?? 0.0).toStringAsFixed(1)}%',
                    icon: Icons.emoji_events,
                    color: Colors.orange,
                    description: 'Adherence to proper athletic form and technique',
                  ),
                  const SizedBox(height: 12),
                  ResultCard(
                    title: 'Balance & Stability',
                    value: '${(data['balance'] ?? 0.0).toStringAsFixed(1)}%',
                    icon: Icons.balance,
                    color: Colors.purple,
                    description: 'Postural control and center of mass management',
                  ),
                  const SizedBox(height: 12),
                  // Additional metrics
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Session Details',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 12),
                          _buildDetailRow('Duration', '${(data['duration'] ?? 0).toStringAsFixed(1)}s'),
                          _buildDetailRow('Frames Analyzed', '${data['totalFrames'] ?? 0}'),
                          _buildDetailRow('Average Confidence', '${((data['avgConfidence'] ?? 0.0) * 100).toStringAsFixed(1)}%'),
                          _buildDetailRow('Timestamp', _formatTimestamp(data['timestamp'])),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: () => Navigator.pushNamedAndRemoveUntil(
                  context,
                  '/home',
                  (route) => false,
                ),
                icon: const Icon(Icons.home),
                label: const Text('Home'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: ElevatedButton.icon(
                onPressed: () => Navigator.pushNamed(context, '/camera'),
                icon: const Icon(Icons.camera_alt),
                label: const Text('Record Again'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue[900],
                  foregroundColor: Colors.white,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(color: Colors.grey[600]),
          ),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }

  Color _getScoreColor(double score) {
    if (score >= 80) return Colors.green;
    if (score >= 60) return Colors.orange;
    return Colors.red;
  }

  String _formatTimestamp(dynamic timestamp) {
    if (timestamp == null) return 'Unknown';
    try {
      final dt = DateTime.fromMillisecondsSinceEpoch(timestamp);
      return '${dt.hour}:${dt.minute.toString().padLeft(2, '0')}:${dt.second.toString().padLeft(2, '0')}';
    } catch (e) {
      return 'Invalid';
    }
  }

  Future<void> _submitResults() async {
    setState(() => _isSubmitting = true);

    try {
      final submissionService = Provider.of<SubmissionService>(context, listen: false);
      await submissionService.submitAnalysis(widget.analysisData);
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Results submitted successfully!'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to submit: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }
}