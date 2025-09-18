import 'package:flutter/material.dart';

class LeaderboardScreen extends StatefulWidget {
  const LeaderboardScreen({Key? key}) : super(key: key);

  @override
  State<LeaderboardScreen> createState() => _LeaderboardScreenState();
}

class _LeaderboardScreenState extends State<LeaderboardScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  
  // Mock data - in real app this would come from API
  final List<Map<String, dynamic>> _weeklyLeaders = [
    {'rank': 1, 'name': 'Alex Chen', 'score': 94.2, 'sessions': 15},
    {'rank': 2, 'name': 'Sarah Johnson', 'score': 91.8, 'sessions': 12},
    {'rank': 3, 'name': 'Mike Rodriguez', 'score': 89.5, 'sessions': 18},
    {'rank': 4, 'name': 'Emma Davis', 'score': 87.3, 'sessions': 10},
    {'rank': 5, 'name': 'James Wilson', 'score': 85.9, 'sessions': 14},
    {'rank': 6, 'name': 'Lisa Anderson', 'score': 84.7, 'sessions': 11},
    {'rank': 7, 'name': 'David Brown', 'score': 83.2, 'sessions': 16},
    {'rank': 8, 'name': 'You', 'score': 82.1, 'sessions': 9, 'isCurrentUser': true},
  ];

  final List<Map<String, dynamic>> _monthlyLeaders = [
    {'rank': 1, 'name': 'Sarah Johnson', 'score': 92.4, 'sessions': 48},
    {'rank': 2, 'name': 'Alex Chen', 'score': 91.2, 'sessions': 52},
    {'rank': 3, 'name': 'Mike Rodriguez', 'score': 88.9, 'sessions': 61},
    {'rank': 4, 'name': 'You', 'score': 87.5, 'sessions': 34, 'isCurrentUser': true},
    {'rank': 5, 'name': 'Emma Davis', 'score': 86.1, 'sessions': 41},
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Leaderboard'),
        backgroundColor: Colors.blue[900],
        foregroundColor: Colors.white,
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: const [
            Tab(text: 'This Week'),
            Tab(text: 'This Month'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildLeaderboardList(_weeklyLeaders),
          _buildLeaderboardList(_monthlyLeaders),
        ],
      ),
    );
  }

  Widget _buildLeaderboardList(List<Map<String, dynamic>> leaders) {
    return Column(
      children: [
        // Top 3 Podium
        Container(
          padding: const EdgeInsets.all(16.0),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [Colors.blue[50]!, Colors.white],
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              if (leaders.length > 1) _buildPodiumItem(leaders[1], 2, 120),
              if (leaders.isNotEmpty) _buildPodiumItem(leaders[0], 1, 140),
              if (leaders.length > 2) _buildPodiumItem(leaders[2], 3, 100),
            ],
          ),
        ),
        // Remaining Rankings
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            itemCount: leaders.length - 3,
            itemBuilder: (context, index) {
              final leader = leaders[index + 3];
              return _buildLeaderboardItem(leader);
            },
          ),
        ),
      ],
    );
  }

  Widget _buildPodiumItem(Map<String, dynamic> leader, int position, double height) {
    final isCurrentUser = leader['isCurrentUser'] == true;
    Color podiumColor;
    IconData medal;
    
    switch (position) {
      case 1:
        podiumColor = Colors.amber;
        medal = Icons.emoji_events;
        break;
      case 2:
        podiumColor = Colors.grey[400]!;
        medal = Icons.emoji_events;
        break;
      case 3:
        podiumColor = Colors.brown[400]!;
        medal = Icons.emoji_events;
        break;
      default:
        podiumColor = Colors.grey;
        medal = Icons.emoji_events;
    }

    return Column(
      children: [
        CircleAvatar(
          radius: 30,
          backgroundColor: isCurrentUser ? Colors.blue[700] : Colors.grey[300],
          child: Text(
            leader['name'][0].toUpperCase(),
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: isCurrentUser ? Colors.white : Colors.grey[700],
            ),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          leader['name'],
          style: TextStyle(
            fontSize: 14,
            fontWeight: isCurrentUser ? FontWeight.bold : FontWeight.normal,
            color: isCurrentUser ? Colors.blue[700] : Colors.black87,
          ),
          overflow: TextOverflow.ellipsis,
        ),
        const SizedBox(height: 4),
        Text(
          '${leader['score']}%',
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          width: 60,
          height: height,
          decoration: BoxDecoration(
            color: podiumColor,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(8)),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(medal, color: Colors.white, size: 30),
              const SizedBox(height: 4),
              Text(
                '#$position',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildLeaderboardItem(Map<String, dynamic> leader) {
    final isCurrentUser = leader['isCurrentUser'] == true;
    
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4.0),
      color: isCurrentUser ? Colors.blue[50] : null,
      child: ListTile(
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: _getRankColor(leader['rank']),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Center(
            child: Text(
              '#${leader['rank']}',
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          ),
        ),
        title: Text(
          leader['name'],
          style: TextStyle(
            fontWeight: isCurrentUser ? FontWeight.bold : FontWeight.normal,
            color: isCurrentUser ? Colors.blue[700] : null,
          ),
        ),
        subtitle: Text('${leader['sessions']} sessions'),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: Colors.green[100],
            borderRadius: BorderRadius.circular(16),
          ),
          child: Text(
            '${leader['score']}%',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              color: Colors.green[700],
            ),
          ),
        ),
      ),
    );
  }

  Color _getRankColor(int rank) {
    if (rank <= 3) return Colors.orange;
    if (rank <= 10) return Colors.blue;
    return Colors.grey;
  }
}