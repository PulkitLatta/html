import 'package:flutter/material.dart';

class CameraOverlay extends StatelessWidget {
  final bool isRecording;
  final VoidCallback onRecordingToggle;

  const CameraOverlay({
    Key? key,
    required this.isRecording,
    required this.onRecordingToggle,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        children: [
          // Top bar
          Container(
            padding: EdgeInsets.all(16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                IconButton(
                  onPressed: () => Navigator.of(context).pop(),
                  icon: Icon(
                    Icons.arrow_back,
                    color: Colors.white,
                    size: 28,
                  ),
                ),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: isRecording ? Colors.red : Colors.grey,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Text(
                    isRecording ? 'RECORDING' : 'READY',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                    ),
                  ),
                ),
                IconButton(
                  onPressed: () {
                    // TODO: Implement camera flip
                  },
                  icon: Icon(
                    Icons.flip_camera_ios,
                    color: Colors.white,
                    size: 28,
                  ),
                ),
              ],
            ),
          ),

          Spacer(),

          // Pose guide overlay (placeholder)
          if (!isRecording)
            Container(
              margin: EdgeInsets.symmetric(horizontal: 32),
              child: CustomPaint(
                size: Size(double.infinity, 300),
                painter: PoseGuidePainter(),
              ),
            ),

          Spacer(),

          // Bottom controls
          Container(
            padding: EdgeInsets.all(32),
            child: Column(
              children: [
                // Instructions
                Container(
                  padding: EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.6),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    isRecording
                        ? 'Performing exercise... Stay in frame!'
                        : 'Position yourself in the frame and tap to start recording',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 14,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
                
                SizedBox(height: 24),
                
                // Record button
                GestureDetector(
                  onTap: onRecordingToggle,
                  child: Container(
                    width: 80,
                    height: 80,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: isRecording ? Colors.red : Colors.white,
                      border: Border.all(
                        color: isRecording ? Colors.white : Colors.red,
                        width: 4,
                      ),
                    ),
                    child: Icon(
                      isRecording ? Icons.stop : Icons.circle,
                      color: isRecording ? Colors.white : Colors.red,
                      size: isRecording ? 32 : 40,
                    ),
                  ),
                ),
                
                SizedBox(height: 16),
                
                // Timer display
                if (isRecording)
                  Container(
                    padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.red.withOpacity(0.8),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Text(
                      '00:00', // TODO: Implement real timer
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class PoseGuidePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.6)
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;

    final dotPaint = Paint()
      ..color = Colors.blue.withOpacity(0.8)
      ..style = PaintingStyle.fill;

    // Draw simple stick figure as pose guide
    final centerX = size.width / 2;
    final centerY = size.height / 2;
    
    // Head
    canvas.drawCircle(Offset(centerX, centerY - 80), 20, paint);
    
    // Body
    canvas.drawLine(
      Offset(centerX, centerY - 60),
      Offset(centerX, centerY + 40),
      paint,
    );
    
    // Arms
    canvas.drawLine(
      Offset(centerX, centerY - 20),
      Offset(centerX - 40, centerY + 10),
      paint,
    );
    canvas.drawLine(
      Offset(centerX, centerY - 20),
      Offset(centerX + 40, centerY + 10),
      paint,
    );
    
    // Legs
    canvas.drawLine(
      Offset(centerX, centerY + 40),
      Offset(centerX - 30, centerY + 100),
      paint,
    );
    canvas.drawLine(
      Offset(centerX, centerY + 40),
      Offset(centerX + 30, centerY + 100),
      paint,
    );
    
    // Key points
    final keyPoints = [
      Offset(centerX, centerY - 100), // head
      Offset(centerX - 25, centerY - 30), // left shoulder
      Offset(centerX + 25, centerY - 30), // right shoulder
      Offset(centerX - 40, centerY + 10), // left hand
      Offset(centerX + 40, centerY + 10), // right hand
      Offset(centerX - 15, centerY + 40), // left hip
      Offset(centerX + 15, centerY + 40), // right hip
      Offset(centerX - 30, centerY + 100), // left foot
      Offset(centerX + 30, centerY + 100), // right foot
    ];
    
    for (final point in keyPoints) {
      canvas.drawCircle(point, 4, dotPaint);
    }
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => false;
}