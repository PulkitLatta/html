# CampusPulse ML Components

This directory contains machine learning components for the CampusPulse platform, including model training scripts, inference pipelines, and evaluation tools.

## Directory Structure

```
ml/
├── train/                  # Training scripts
│   └── train_technique_detector.py
├── models/                 # Saved model weights (not included in git)
├── inference/              # Inference scripts and utilities
├── evaluation/             # Model evaluation and benchmarking
└── notebooks/              # Jupyter notebooks for experimentation
```

## Components

### 1. Technique Detection Model

The technique detection model is a PyTorch-based LSTM with attention mechanism that classifies exercise techniques from pose keypoint sequences.

**Features:**
- Bidirectional LSTM with multi-head attention
- Handles variable-length sequences
- Supports multiple exercise types (squat, deadlift, pushup, pullup, plank)
- Dropout for regularization
- Learning rate scheduling

**Training:**
```bash
cd train/
python train_technique_detector.py --epochs 100 --batch-size 64 --lr 0.001
```

**Model Architecture:**
- Input: Pose keypoint sequences (30 frames × 51 features)
- LSTM: 2-layer bidirectional with 128 hidden units
- Attention: 8-head multi-head attention
- Output: 5 exercise technique classes

### 2. Data Requirements

The training script expects pose sequence data in JSON format:

```json
[
  {
    "pose_sequence": [
      [
        [x1, y1, conf1], [x2, y2, conf2], ..., [x17, y17, conf17]
      ],
      ...
    ],
    "technique_label": "squat",
    "athlete_id": "uuid",
    "video_id": "uuid",
    "metadata": {
      "duration": 5.2,
      "fps": 30,
      "exercise_count": 12
    }
  }
]
```

### 3. Model Performance

The model achieves the following performance on synthetic data:
- Training Accuracy: ~95%
- Validation Accuracy: ~88%
- Test Accuracy: ~85%

**Note:** Performance on real data will vary depending on data quality and diversity.

### 4. Pose Keypoint Format

We use the MoveNet model's 17-keypoint format:
1. Nose
2. Left Eye
3. Right Eye
4. Left Ear
5. Right Ear
6. Left Shoulder
7. Right Shoulder
8. Left Elbow
9. Right Elbow
10. Left Wrist
11. Right Wrist
12. Left Hip
13. Right Hip
14. Left Knee
15. Right Knee
16. Left Ankle
17. Right Ankle

Each keypoint has (x, y, confidence) values normalized to [0, 1].

## Future Improvements

1. **Data Augmentation**
   - Temporal augmentation (speed changes)
   - Spatial augmentation (rotation, scaling)
   - Noise injection

2. **Model Architecture**
   - Transformer-based models
   - Graph neural networks for skeleton data
   - Multi-scale temporal modeling

3. **Advanced Features**
   - Real-time inference optimization
   - Form quality scoring (not just classification)
   - Multi-person pose analysis
   - 3D pose estimation integration

4. **Deployment**
   - ONNX model conversion
   - TensorRT optimization
   - Mobile deployment (Core ML, TensorFlow Lite)

## Dependencies

```
torch>=1.9.0
torchvision>=0.10.0
numpy>=1.21.0
scikit-learn>=1.0.0
matplotlib>=3.5.0
seaborn>=0.11.0
tqdm>=4.62.0
```

## Installation

```bash
pip install torch torchvision numpy scikit-learn matplotlib seaborn tqdm
```

## Usage Example

```python
from train.train_technique_detector import TechniqueClassifier
import torch

# Load trained model
model = TechniqueClassifier(input_size=51, num_classes=5)
checkpoint = torch.load('models/best_model.pth')
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# Inference on new data
with torch.no_grad():
    pose_sequence = torch.randn(1, 30, 51)  # (batch, seq_len, features)
    predictions = model(pose_sequence)
    technique_class = torch.argmax(predictions, dim=1)
```

## Contributing

1. Follow PEP 8 coding standards
2. Add unit tests for new components
3. Update documentation for API changes
4. Use type hints for function signatures
5. Add logging for debugging

## License

This ML component is part of the CampusPulse project and follows the same MIT license.