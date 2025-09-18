# CampusPulse Datasets

This directory contains training and testing datasets for the CampusPulse athletic performance analysis system.

## Directory Structure

```
datasets/
├── sample/                 # Sample data for testing and development
│   ├── dummy_poses.json   # Sample pose keypoint sequences
│   ├── test_video.mp4     # Sample exercise video (placeholder)
│   └── README.md          # This file
├── training/               # Full training datasets (not included in repo)
├── validation/             # Validation datasets
└── testing/                # Testing datasets for evaluation
```

## Dataset Description

### Sample Data

The sample directory contains minimal data for development and testing:

1. **dummy_poses.json**: Contains 5 example pose sequences representing different exercises:
   - Squats: Hip and knee flexion patterns
   - Deadlifts: Hip hinge movement patterns  
   - Push-ups: Upper body pressing patterns
   - Pull-ups: Upper body pulling patterns
   - Planks: Isometric core stability patterns

2. **test_video.mp4**: Placeholder for video data (see file contents for specifications)

### Data Format

#### Pose Sequence Data
Each pose sequence follows this JSON structure:

```json
{
  "pose_sequence": [
    [
      [x1, y1, confidence1],  // Nose
      [x2, y2, confidence2],  // Left Eye
      // ... (17 keypoints total)
      [x17, y17, confidence17] // Right Ankle
    ],
    // ... (multiple frames)
  ],
  "technique_label": "exercise_name",
  "athlete_id": "uuid",
  "video_id": "uuid",
  "metadata": {
    "duration": 5.2,
    "fps": 30,
    "exercise_count": 12,
    "form_score": 92.5
  }
}
```

#### Keypoint Format
We use MoveNet's 17-keypoint format with normalized coordinates:
- **Coordinates**: (x, y) normalized to [0, 1] relative to image dimensions
- **Confidence**: Keypoint detection confidence [0, 1]
- **Order**: See ML/README.md for complete keypoint list

### Data Collection Guidelines

For production datasets:

1. **Video Quality**
   - Minimum 720p resolution
   - 30 FPS frame rate
   - Good lighting conditions
   - Stable camera positioning
   - Full body visibility

2. **Exercise Diversity**
   - Multiple exercise types
   - Various skill levels (beginner to advanced)
   - Different body types and demographics
   - Various camera angles and distances

3. **Annotation Quality**
   - Expert-validated technique labels
   - Form quality scores (0-100)
   - Exercise count verification
   - Movement phase annotations

4. **Data Volume**
   - Target: 10,000+ sequences per exercise type
   - Minimum: 1,000+ sequences per type for initial training
   - Balanced distribution across difficulty levels

### Privacy and Ethics

All video data collection follows these guidelines:

1. **Informed Consent**: Athletes provide explicit consent for data use
2. **Anonymization**: Personal identifiers removed from public datasets
3. **Data Security**: Encrypted storage and secure transmission
4. **Access Control**: Limited access to authorized researchers
5. **Retention Policy**: Data deleted according to consent agreements

### Data Augmentation

The training pipeline applies these augmentation techniques:

1. **Temporal Augmentation**
   - Speed variations (0.8x to 1.2x)
   - Frame sampling variations
   - Sequence length variations

2. **Spatial Augmentation**
   - Small rotations (±5 degrees)
   - Scale variations (0.9x to 1.1x)
   - Horizontal flipping (where appropriate)

3. **Noise Injection**
   - Gaussian noise on keypoint coordinates
   - Confidence score variations
   - Missing keypoint simulation

### Quality Metrics

We track these quality metrics for our datasets:

- **Coverage**: Percentage of body keypoints visible
- **Consistency**: Frame-to-frame keypoint stability
- **Accuracy**: Expert annotation agreement
- **Diversity**: Distribution across demographic groups
- **Balance**: Equal representation across exercise types

### Usage Examples

#### Loading Sample Data
```python
import json

with open('sample/dummy_poses.json', 'r') as f:
    poses = json.load(f)

for sample in poses:
    sequence = sample['pose_sequence']
    label = sample['technique_label']
    print(f"Exercise: {label}, Frames: {len(sequence)}")
```

#### Converting Video to Poses
```python
# Pseudo-code for video processing
import cv2
from pose_detector import PoseDetector

detector = PoseDetector()
cap = cv2.VideoCapture('sample/test_video.mp4')

poses = []
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    keypoints = detector.detect(frame)
    poses.append(keypoints)

cap.release()
```

## Contributing

When adding new datasets:

1. Follow the established JSON format
2. Validate keypoint coordinates are normalized
3. Include proper metadata
4. Test with the training pipeline
5. Update documentation

## License

Dataset usage is governed by the CampusPulse data usage agreement. All data is collected and used in compliance with applicable privacy laws and institutional policies.

For questions about data access or contribution, contact the CampusPulse development team.