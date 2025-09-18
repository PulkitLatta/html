import 'package:flutter/material.dart';

class LeaderboardScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Leaderboard'),
        backgroundColor: Colors.blue[600],
      ),
      body: Column(
        children: [
          // Top 3 Podium
          Container(
            height: 200,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [Colors.blue[600]!, Colors.blue[800]!],
              ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                _buildPodiumPlace(2, 'Sarah J.', 94.2, 80),
                _buildPodiumPlace(1, 'Alex M.', 96.8, 100),
                _buildPodiumPlace(3, 'Mike R.', 91.5, 60),
              ],
            ),
          ),
          
          // Rankings List
          Expanded(
            child: ListView.builder(
              padding: EdgeInsets.all(16),
              itemCount: _mockLeaderboardData.length,
              itemBuilder: (context, index) {
                final athlete = _mockLeaderboardData[index];
                return Card(
                  margin: EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: _getRankColor(index + 4),
                      child: Text(
                        '${index + 4}',
                        style: TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    title: Text(
                      athlete['name'],
                      style: TextStyle(fontWeight: FontWeight.w600),
                    ),
                    subtitle: Text('${athlete['sport']} • ${athlete['year']}'),
                    trailing: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          '${athlete['score']}',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Colors.blue[600],
                          ),
                        ),
                        Text(
                          '${athlete['exercises']} exercises',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Refresh functionality coming soon!')),
          );
        },
        backgroundColor: Colors.blue[600],
        child: Icon(Icons.refresh),
      ),
    );
  }

  Widget _buildPodiumPlace(int place, String name, double score, double height) {
    Color color;
    switch (place) {
      case 1:
        color = Colors.amber;
        break;
      case 2:
        color = Colors.grey[400]!;
        break;
      case 3:
        color = Colors.brown[400]!;
        break;
      default:
        color = Colors.grey;
    }

    return Column(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        Container(
          padding: EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.white,
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 4,
                offset: Offset(0, 2),
              ),
            ],
          ),
          child: Text(
            name.split(' ')[0],
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 12,
            ),
          ),
        ),
        SizedBox(height: 8),
        Text(
          score.toString(),
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
        SizedBox(height: 4),
        Container(
          width: 60,
          height: height,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.vertical(top: Radius.circular(8)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.2),
                blurRadius: 4,
                offset: Offset(0, -2),
              ),
            ],
          ),
          child: Center(
            child: Text(
              '$place',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 24,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Color _getRankColor(int rank) {
    if (rank <= 5) return Colors.green;
    if (rank <= 10) return Colors.orange;
    return Colors.grey;
  }

  final List<Map<String, dynamic>> _mockLeaderboardData = [
    {'name': 'Emma Davis', 'score': 89.3, 'sport': 'Track & Field', 'year': 'Junior', 'exercises': 24},
    {'name': 'Jake Wilson', 'score': 87.9, 'sport': 'Basketball', 'year': 'Senior', 'exercises': 18},
    {'name': 'Sophie Chen', 'score': 85.7, 'sport': 'Swimming', 'year': 'Sophomore', 'exercises': 31},
    {'name': 'Ryan Adams', 'score': 84.2, 'sport': 'Football', 'year': 'Junior', 'exercises': 22},
    {'name': 'Maya Patel', 'score': 82.8, 'sport': 'Tennis', 'year': 'Senior', 'exercises': 19},
    {'name': 'Chris Lee', 'score': 81.5, 'sport': 'Soccer', 'year': 'Sophomore', 'exercises': 27},
    {'name': 'Zoe Martinez', 'score': 80.1, 'sport': 'Volleyball', 'year': 'Freshman', 'exercises': 15},
  ];
}