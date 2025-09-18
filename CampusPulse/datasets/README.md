# CampusPulse Datasets

This directory contains datasets and sample data for training, validation, and testing the CampusPulse athletic performance analysis system.

## Overview

The CampusPulse datasets include:
- **Pose sequence data**: Extracted keypoints from athletic movements
- **Video recordings**: Raw footage for pose extraction and validation
- **Performance annotations**: Expert-labeled technique assessments
- **Synthetic data**: Generated examples for testing and development

## Dataset Structure

```
datasets/
├── sample/                     # Sample data for testing
│   ├── dummy_poses.json       # Example pose sequence data
│   ├── test_video.mp4         # Sample video file (placeholder)
│   └── README.md              # This file
├── training/                  # Training datasets (not in repo)
│   ├── basketball/
│   ├── soccer/
│   └── general/
├── validation/                # Validation datasets (not in repo)
│   ├── technique_validation/
│   └── performance_metrics/
└── annotations/               # Expert annotations (not in repo)
    ├── technique_labels.csv
    ├── quality_scores.csv
    └── expert_feedback.json
```

## Sample Data

### Pose Sequence Format

The `dummy_poses.json` file demonstrates the expected format for pose sequence data:

```json
{
  "sequence_id": "demo_seq_001",
  "sport": "basketball",
  "athlete_id": "demo_athlete_123",
  "frames": [
    {
      "frame_id": 0,
      "timestamp": 1640995200000,
      "keypoints": [
        {"name": "nose", "x": 0.502, "y": 0.298, "confidence": 0.92},
        // ... 17 total keypoints
      ]
    }
  ],
  "ground_truth": {
    "technique_class": 0,
    "overall_score": 94.2,
    "annotations": ["proper_stance", "good_balance"]
  }
}
```

### Keypoint Schema

Each frame contains 17 keypoints following the COCO pose format:
1. **Nose** - Face center reference
2. **Eyes** - Left/right eye positions
3. **Ears** - Left/right ear positions  
4. **Shoulders** - Left/right shoulder joints
5. **Elbows** - Left/right elbow joints
6. **Wrists** - Left/right wrist positions
7. **Hips** - Left/right hip joints
8. **Knees** - Left/right knee joints
9. **Ankles** - Left/right ankle positions

### Coordinate System

- **X coordinates**: 0.0 (left) to 1.0 (right) of frame
- **Y coordinates**: 0.0 (top) to 1.0 (bottom) of frame
- **Confidence**: 0.0 to 1.0 (pose estimation confidence)

## Data Collection Guidelines

### Video Requirements

For optimal pose detection and analysis:
- **Resolution**: Minimum 720p, recommended 1080p
- **Frame rate**: 30 FPS or higher
- **Duration**: 3-10 seconds per technique sample
- **Format**: MP4 with H.264 encoding
- **Aspect ratio**: 16:9 preferred

### Recording Setup

- **Camera position**: Front-facing view of athlete
- **Distance**: Full body visible with some margin
- **Lighting**: Even, bright lighting without harsh shadows
- **Background**: Minimal distractions, contrasting with athlete
- **Stability**: Tripod or stable mounting recommended

### Athlete Positioning

- **Centering**: Athlete centered in frame
- **Visibility**: All keypoints clearly visible throughout motion
- **Clothing**: Contrasting colors to background
- **Multiple angles**: Optional but recommended for validation

## Ground Truth Annotations

### Technique Classification

The system classifies techniques into 5 categories:
- **Class 0**: Excellent form (90-100 points)
- **Class 1**: Poor balance (balance issues detected)
- **Class 2**: Inconsistent timing (temporal irregularities)
- **Class 3**: Overextension (joint angle violations)
- **Class 4**: Normal variation (70-89 points)

### Performance Metrics

Each sample includes quantitative scores:
- **Overall Score**: 0-100 composite performance rating
- **Form Consistency**: Smoothness and repeatability
- **Movement Efficiency**: Economy of motion
- **Technique Score**: Sport-specific technique quality
- **Balance Score**: Stability throughout movement

### Expert Annotations

Professional annotations include:
- **Qualitative feedback**: Written assessment
- **Improvement suggestions**: Specific recommendations
- **Risk factors**: Injury prevention notes
- **Comparison benchmarks**: Relative to skill level

## Data Privacy and Ethics

### Privacy Protection
- All athlete data is anonymized
- No personally identifiable information stored
- Consent obtained for all recordings
- Data retention policies followed

### Ethical Considerations
- Fair representation across demographics
- Bias testing and mitigation
- Inclusive dataset compilation
- Regular ethical review processes

## Usage Examples

### Loading Pose Data

```python
import json
import numpy as np

# Load sample pose sequence
with open('sample/dummy_poses.json', 'r') as f:
    pose_data = json.load(f)

# Extract keypoints for ML processing
frames = pose_data['frames']
keypoints = []
for frame in frames:
    frame_keypoints = []
    for kp in frame['keypoints']:
        frame_keypoints.extend([kp['x'], kp['y']])
    keypoints.append(frame_keypoints)

# Convert to numpy array (frames, features)
pose_sequence = np.array(keypoints)
```

### Data Validation

```python
def validate_pose_sequence(sequence_data):
    """Validate pose sequence format and content."""
    required_fields = ['sequence_id', 'sport', 'frames']
    for field in required_fields:
        if field not in sequence_data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate keypoints
    for frame in sequence_data['frames']:
        if len(frame['keypoints']) != 17:
            raise ValueError("Each frame must have 17 keypoints")
        
        for kp in frame['keypoints']:
            if not (0 <= kp['x'] <= 1 and 0 <= kp['y'] <= 1):
                raise ValueError("Keypoint coordinates must be normalized (0-1)")
    
    return True
```

## Dataset Statistics

### Current Sample Data
- **Sequences**: 1 sample sequence
- **Frames**: 2 frames per sequence
- **Sports covered**: Basketball
- **Quality annotations**: Complete ground truth

### Target Production Dataset
- **Sequences**: 10,000+ technique samples
- **Athletes**: 500+ unique participants
- **Sports**: Basketball, Soccer, Tennis, Swimming
- **Universities**: 20+ participating institutions
- **Expert annotations**: 3+ reviewers per sample

## Contributing Data

### Data Submission Process
1. Contact CampusPulse team for guidelines
2. Complete data sharing agreement
3. Follow technical specifications
4. Submit for quality review
5. Integration into training pipeline

### Quality Standards
- Technical requirements compliance
- Expert annotation quality
- Privacy protection verification
- Ethical review completion
- Data integrity validation

## Future Datasets

### Planned Additions
- Multi-sport expansion
- Longitudinal athlete tracking
- Injury prevention data
- Performance prediction samples
- Real-time streaming data

### Research Collaborations
- University partnerships
- Professional sports organizations
- Olympic training centers
- Sports medicine clinics
- Biomechanics laboratories

## References

1. Microsoft COCO Keypoint Detection: https://cocodataset.org/
2. OpenPose Human Pose Estimation: https://github.com/CMU-Perceptual-Computing-Lab/openpose
3. MediaPipe Pose: https://google.github.io/mediapipe/solutions/pose.html
4. Sports Analytics Research Database: http://www.sloansportsconference.com/

## License

This dataset and documentation is part of CampusPulse and is licensed under the MIT License. Please see the main repository LICENSE file for details.

Individual video and pose data may have additional attribution requirements - please check metadata for specific files.