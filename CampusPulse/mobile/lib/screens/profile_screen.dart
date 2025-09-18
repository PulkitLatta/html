import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ProfileScreen extends StatefulWidget {
  @override
  _ProfileScreenState createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  String _userName = 'John Athlete';
  String _userSport = 'Track & Field';
  String _userYear = 'Junior';
  
  @override
  void initState() {
    super.initState();
    _loadUserData();
  }

  Future<void> _loadUserData() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _userName = prefs.getString('user_name') ?? 'John Athlete';
      _userSport = prefs.getString('user_sport') ?? 'Track & Field';
      _userYear = prefs.getString('user_year') ?? 'Junior';
    });
  }

  Future<void> _saveUserData() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('user_name', _userName);
    await prefs.setString('user_sport', _userSport);
    await prefs.setString('user_year', _userYear);
  }

  void _showEditDialog() {
    showDialog(
      context: context,
      builder: (context) => _EditProfileDialog(
        name: _userName,
        sport: _userSport,
        year: _userYear,
        onSave: (name, sport, year) {
          setState(() {
            _userName = name;
            _userSport = sport;
            _userYear = year;
          });
          _saveUserData();
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Profile'),
        backgroundColor: Colors.blue[600],
        actions: [
          IconButton(
            icon: Icon(Icons.edit),
            onPressed: _showEditDialog,
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            // Header Section
            Container(
              width: double.infinity,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Colors.blue[600]!, Colors.blue[800]!],
                ),
              ),
              child: Padding(
                padding: EdgeInsets.all(32),
                child: Column(
                  children: [
                    CircleAvatar(
                      radius: 60,
                      backgroundColor: Colors.white,
                      child: Icon(
                        Icons.person,
                        size: 80,
                        color: Colors.blue[600],
                      ),
                    ),
                    SizedBox(height: 16),
                    Text(
                      _userName,
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    SizedBox(height: 8),
                    Text(
                      '$_userSport • $_userYear',
                      style: TextStyle(
                        fontSize: 16,
                        color: Colors.white.withOpacity(0.9),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            // Stats Section
            Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                children: [
                  Row(
                    children: [
                      Expanded(child: _buildStatCard('Total Sessions', '42', Icons.fitness_center)),
                      SizedBox(width: 16),
                      Expanded(child: _buildStatCard('Avg Score', '88.5', Icons.trending_up)),
                    ],
                  ),
                  SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(child: _buildStatCard('Best Score', '96.2', Icons.star)),
                      SizedBox(width: 16),
                      Expanded(child: _buildStatCard('Rank', '#7', Icons.leaderboard)),
                    ],
                  ),
                  
                  SizedBox(height: 32),
                  
                  // Recent Activity
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      'Recent Activity',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  SizedBox(height: 16),
                  
                  ..._mockRecentActivities.map((activity) => Card(
                    margin: EdgeInsets.only(bottom: 8),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor: activity['color'],
                        child: Icon(
                          activity['icon'],
                          color: Colors.white,
                          size: 20,
                        ),
                      ),
                      title: Text(activity['title']),
                      subtitle: Text(activity['date']),
                      trailing: Text(
                        'Score: ${activity['score']}',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Colors.blue[600],
                        ),
                      ),
                    ),
                  )),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatCard(String label, String value, IconData icon) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            Icon(icon, color: Colors.blue[600], size: 32),
            SizedBox(height: 8),
            Text(
              value,
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.blue[600],
              ),
            ),
            SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  final List<Map<String, dynamic>> _mockRecentActivities = [
    {
      'title': 'Squat Analysis',
      'date': '2 hours ago',
      'score': '94.2',
      'icon': Icons.fitness_center,
      'color': Colors.green,
    },
    {
      'title': 'Deadlift Form Check',
      'date': '1 day ago',
      'score': '91.8',
      'icon': Icons.fitness_center,
      'color': Colors.orange,
    },
    {
      'title': 'Push-up Challenge',
      'date': '3 days ago',
      'score': '87.5',
      'icon': Icons.fitness_center,
      'color': Colors.blue,
    },
  ];
}

class _EditProfileDialog extends StatefulWidget {
  final String name;
  final String sport;
  final String year;
  final Function(String, String, String) onSave;

  const _EditProfileDialog({
    required this.name,
    required this.sport,
    required this.year,
    required this.onSave,
  });

  @override
  _EditProfileDialogState createState() => _EditProfileDialogState();
}

class _EditProfileDialogState extends State<_EditProfileDialog> {
  late TextEditingController _nameController;
  late TextEditingController _sportController;
  String _selectedYear = '';

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.name);
    _sportController = TextEditingController(text: widget.sport);
    _selectedYear = widget.year;
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Edit Profile'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: _nameController,
            decoration: InputDecoration(
              labelText: 'Name',
              border: OutlineInputBorder(),
            ),
          ),
          SizedBox(height: 16),
          TextField(
            controller: _sportController,
            decoration: InputDecoration(
              labelText: 'Sport',
              border: OutlineInputBorder(),
            ),
          ),
          SizedBox(height: 16),
          DropdownButtonFormField<String>(
            value: _selectedYear,
            decoration: InputDecoration(
              labelText: 'Year',
              border: OutlineInputBorder(),
            ),
            items: ['Freshman', 'Sophomore', 'Junior', 'Senior']
                .map((year) => DropdownMenuItem(
                      value: year,
                      child: Text(year),
                    ))
                .toList(),
            onChanged: (value) {
              setState(() {
                _selectedYear = value!;
              });
            },
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: () {
            widget.onSave(
              _nameController.text,
              _sportController.text,
              _selectedYear,
            );
            Navigator.of(context).pop();
          },
          child: Text('Save'),
        ),
      ],
    );
  }
}