"""
CampusPulse Technique Detector Training Script

This script trains a PyTorch LSTM model to classify exercise techniques
based on pose keypoint sequences extracted from video data.

Author: CampusPulse Team
Date: 2024-01-15
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import json
import os
from pathlib import Path
import argparse
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

# Constants
SEQUENCE_LENGTH = 30  # Number of frames per sequence
NUM_KEYPOINTS = 17    # MoveNet keypoints
KEYPOINT_DIM = 3      # x, y, confidence

class TechniqueDataset(Dataset):
    """Dataset class for exercise technique classification"""
    
    def __init__(self, sequences, labels, transform=None):
        self.sequences = sequences
        self.labels = labels
        self.transform = transform
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        sequence = self.sequences[idx]
        label = self.labels[idx]
        
        # Convert to tensor
        sequence = torch.FloatTensor(sequence)
        
        # Apply transforms if any
        if self.transform:
            sequence = self.transform(sequence)
        
        return sequence, torch.LongTensor([label])[0]

class TechniqueClassifier(nn.Module):
    """LSTM-based technique classification model"""
    
    def __init__(self, input_size, hidden_size=128, num_layers=2, num_classes=5, dropout=0.3):
        super(TechniqueClassifier, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size * 2,  # bidirectional
            num_heads=8,
            dropout=dropout
        )
        
        # Classification layers
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, num_classes)
        )
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x):
        # x shape: (batch_size, sequence_length, input_size)
        batch_size = x.size(0)
        
        # LSTM
        lstm_out, (hidden, cell) = self.lstm(x)
        # lstm_out shape: (batch_size, sequence_length, hidden_size * 2)
        
        # Apply attention
        attn_out, _ = self.attention(
            lstm_out.transpose(0, 1),  # (seq_len, batch_size, hidden_size * 2)
            lstm_out.transpose(0, 1),
            lstm_out.transpose(0, 1)
        )
        attn_out = attn_out.transpose(0, 1)  # Back to (batch_size, seq_len, hidden_size * 2)
        
        # Global average pooling
        pooled = torch.mean(attn_out, dim=1)  # (batch_size, hidden_size * 2)
        
        # Classification
        output = self.classifier(pooled)
        
        return output

def load_dataset(data_path):
    """Load and preprocess pose sequence data"""
    print("Loading dataset...")
    
    sequences = []
    labels = []
    
    # Load data from JSON files (placeholder implementation)
    if os.path.exists(data_path):
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        for item in data:
            sequence = np.array(item['pose_sequence'])
            technique = item['technique_label']
            
            # Ensure sequence has correct shape
            if len(sequence) >= SEQUENCE_LENGTH:
                # Take first SEQUENCE_LENGTH frames
                sequence = sequence[:SEQUENCE_LENGTH]
            else:
                # Pad with zeros if too short
                padding = np.zeros((SEQUENCE_LENGTH - len(sequence), NUM_KEYPOINTS, KEYPOINT_DIM))
                sequence = np.concatenate([sequence, padding], axis=0)
            
            # Flatten keypoints for each frame
            sequence_flat = sequence.reshape(SEQUENCE_LENGTH, -1)
            
            sequences.append(sequence_flat)
            labels.append(technique)
    else:
        print(f"Data file not found: {data_path}")
        print("Generating synthetic data for demonstration...")
        
        # Generate synthetic training data
        techniques = ['squat', 'deadlift', 'pushup', 'pullup', 'plank']
        
        for technique_idx, technique in enumerate(techniques):
            for _ in range(200):  # 200 samples per technique
                # Generate random pose sequence with some technique-specific patterns
                sequence = np.random.randn(SEQUENCE_LENGTH, NUM_KEYPOINTS * KEYPOINT_DIM)
                
                # Add technique-specific bias
                if technique == 'squat':
                    # Lower body movement bias
                    sequence[:, 33:45] += 0.5  # Hip and knee keypoints
                elif technique == 'deadlift':
                    # Back and hip movement bias
                    sequence[:, 30:42] += 0.3
                elif technique == 'pushup':
                    # Upper body movement bias
                    sequence[:, 15:30] += 0.4  # Shoulder and elbow keypoints
                
                sequences.append(sequence)
                labels.append(technique)
    
    return np.array(sequences), np.array(labels)

def train_epoch(model, dataloader, criterion, optimizer, device):
    """Train for one epoch"""
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    
    progress_bar = tqdm(dataloader, desc='Training')
    
    for batch_idx, (sequences, labels) in enumerate(progress_bar):
        sequences, labels = sequences.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(sequences)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        
        # Update progress bar
        progress_bar.set_postfix({
            'Loss': f'{loss.item():.4f}',
            'Acc': f'{100.*correct/total:.2f}%'
        })
    
    return total_loss / len(dataloader), 100. * correct / total

def validate_epoch(model, dataloader, criterion, device):
    """Validate for one epoch"""
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    all_predicted = []
    all_labels = []
    
    with torch.no_grad():
        for sequences, labels in tqdm(dataloader, desc='Validation'):
            sequences, labels = sequences.to(device), labels.to(device)
            
            outputs = model(sequences)
            loss = criterion(outputs, labels)
            
            total_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
            
            all_predicted.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    
    return total_loss / len(dataloader), 100. * correct / total, all_predicted, all_labels

def plot_training_history(train_losses, train_accs, val_losses, val_accs, save_path):
    """Plot training history"""
    plt.figure(figsize=(12, 4))
    
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Val Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.title('Training and Validation Loss')
    
    plt.subplot(1, 2, 2)
    plt.plot(train_accs, label='Train Acc')
    plt.plot(val_accs, label='Val Acc')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.legend()
    plt.title('Training and Validation Accuracy')
    
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Train CampusPulse Technique Classifier')
    parser.add_argument('--data-path', default='../datasets/sample/dummy_poses.json',
                       help='Path to training data')
    parser.add_argument('--batch-size', type=int, default=32,
                       help='Training batch size')
    parser.add_argument('--epochs', type=int, default=50,
                       help='Number of training epochs')
    parser.add_argument('--lr', type=float, default=0.001,
                       help='Learning rate')
    parser.add_argument('--hidden-size', type=int, default=128,
                       help='LSTM hidden size')
    parser.add_argument('--num-layers', type=int, default=2,
                       help='Number of LSTM layers')
    parser.add_argument('--dropout', type=float, default=0.3,
                       help='Dropout rate')
    parser.add_argument('--save-dir', default='./models',
                       help='Directory to save trained models')
    
    args = parser.parse_args()
    
    # Create save directory
    os.makedirs(args.save_dir, exist_ok=True)
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    # Load dataset
    sequences, labels = load_dataset(args.data_path)
    print(f"Loaded {len(sequences)} sequences")
    
    # Encode labels
    label_encoder = LabelEncoder()
    encoded_labels = label_encoder.fit_transform(labels)
    num_classes = len(label_encoder.classes_)
    print(f"Number of classes: {num_classes}")
    print(f"Classes: {label_encoder.classes_}")
    
    # Split dataset
    X_train, X_test, y_train, y_test = train_test_split(
        sequences, encoded_labels, test_size=0.2, random_state=42, stratify=encoded_labels
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
    )
    
    print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    # Create datasets and dataloaders
    train_dataset = TechniqueDataset(X_train, y_train)
    val_dataset = TechniqueDataset(X_val, y_val)
    test_dataset = TechniqueDataset(X_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)
    
    # Initialize model
    input_size = NUM_KEYPOINTS * KEYPOINT_DIM
    model = TechniqueClassifier(
        input_size=input_size,
        hidden_size=args.hidden_size,
        num_layers=args.num_layers,
        num_classes=num_classes,
        dropout=args.dropout
    ).to(device)
    
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5)
    
    # Training loop
    train_losses, train_accs = [], []
    val_losses, val_accs = [], []
    best_val_acc = 0.0
    
    print("Starting training...")
    for epoch in range(args.epochs):
        print(f"\nEpoch {epoch+1}/{args.epochs}")
        
        # Train
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        
        # Validate
        val_loss, val_acc, _, _ = validate_epoch(model, val_loader, criterion, device)
        
        # Update learning rate
        scheduler.step(val_loss)
        
        # Save metrics
        train_losses.append(train_loss)
        train_accs.append(train_acc)
        val_losses.append(val_loss)
        val_accs.append(val_acc)
        
        print(f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
        print(f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
                'label_encoder': label_encoder
            }, os.path.join(args.save_dir, 'best_model.pth'))
            print(f"New best model saved! Val Acc: {val_acc:.2f}%")
    
    # Plot training history
    plot_training_history(train_losses, train_accs, val_losses, val_accs, 
                         os.path.join(args.save_dir, 'training_history.png'))
    
    # Final evaluation on test set
    print("\nEvaluating on test set...")
    test_loss, test_acc, test_preds, test_labels = validate_epoch(model, test_loader, criterion, device)
    print(f"Test Accuracy: {test_acc:.2f}%")
    
    # Classification report
    print("\nClassification Report:")
    print(classification_report(test_labels, test_preds, target_names=label_encoder.classes_))
    
    # Confusion matrix
    cm = confusion_matrix(test_labels, test_preds)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=label_encoder.classes_,
                yticklabels=label_encoder.classes_)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(os.path.join(args.save_dir, 'confusion_matrix.png'))
    plt.close()
    
    print(f"\nTraining completed! Best validation accuracy: {best_val_acc:.2f}%")
    print(f"Models and plots saved to: {args.save_dir}")

if __name__ == '__main__':
    main()