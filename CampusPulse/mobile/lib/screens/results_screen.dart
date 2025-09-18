import 'package:flutter/material.dart';
import '../widgets/result_card.dart';

class ResultsScreen extends StatelessWidget {
  final Map<String, dynamic>? analysisData;

  const ResultsScreen({Key? key, this.analysisData}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Analysis Results'),
        backgroundColor: Colors.blue[600],
      ),
      body: analysisData == null
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.analytics_outlined,
                    size: 64,
                    color: Colors.grey[400],
                  ),
                  SizedBox(height: 16),
                  Text(
                    'No analysis data available',
                    style: TextStyle(
                      fontSize: 18,
                      color: Colors.grey[600],
                    ),
                  ),
                  SizedBox(height: 32),
                  ElevatedButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: Text('Go Back'),
                  ),
                ],
              ),
            )
          : SingleChildScrollView(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Overall Score
                  Card(
                    elevation: 4,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Container(
                      padding: EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(12),
                        gradient: LinearGradient(
                          colors: [Colors.blue[400]!, Colors.blue[600]!],
                        ),
                      ),
                      child: Column(
                        children: [
                          Text(
                            'Overall Score',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                          SizedBox(height: 8),
                          Text(
                            '${analysisData!['overallScore']?.toStringAsFixed(1) ?? '0.0'}',
                            style: TextStyle(
                              fontSize: 48,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                          Text(
                            'out of 100',
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.white.withOpacity(0.8),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  SizedBox(height: 16),
                  
                  // Detailed Metrics
                  ResultCard(
                    title: 'Form Consistency',
                    value: '${analysisData!['formConsistency']?.toStringAsFixed(1) ?? '0.0'}%',
                    icon: Icons.trending_up,
                    color: Colors.green,
                  ),
                  SizedBox(height: 12),
                  
                  ResultCard(
                    title: 'Stability',
                    value: '${analysisData!['stability']?.toStringAsFixed(1) ?? '0.0'}%',
                    icon: Icons.balance,
                    color: Colors.orange,
                  ),
                  SizedBox(height: 12),
                  
                  ResultCard(
                    title: 'Range of Motion',
                    value: '${analysisData!['rangeOfMotion']?.toStringAsFixed(1) ?? '0.0'}°',
                    icon: Icons.rotate_right,
                    color: Colors.purple,
                  ),
                  SizedBox(height: 12),
                  
                  ResultCard(
                    title: 'Timing',
                    value: '${analysisData!['timing']?.toStringAsFixed(2) ?? '0.00'}s',
                    icon: Icons.timer,
                    color: Colors.red,
                  ),
                  SizedBox(height: 24),
                  
                  // Action Buttons
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () {
                            // TODO: Implement share functionality
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Share functionality coming soon!')),
                            );
                          },
                          icon: Icon(Icons.share),
                          label: Text('Share'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.blue[600],
                            foregroundColor: Colors.white,
                            padding: EdgeInsets.symmetric(vertical: 12),
                          ),
                        ),
                      ),
                      SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {
                            Navigator.of(context).pop();
                          },
                          icon: Icon(Icons.camera_alt),
                          label: Text('Record Again'),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: Colors.blue[600],
                            padding: EdgeInsets.symmetric(vertical: 12),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
    );
  }
}