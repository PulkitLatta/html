#!/usr/bin/env python3
"""
CampusPulse Technique Detector Training Script

This script trains an LSTM-based neural network to detect and classify
athletic techniques from pose sequence data.

Author: CampusPulse Team
License: MIT
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Dict, Any
import logging

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PoseSequenceDataset(Dataset):
    """Dataset class for pose sequences and technique labels."""
    
    def __init__(self, sequences: np.ndarray, labels: np.ndarray, sequence_length: int = 30):
        self.sequences = torch.FloatTensor(sequences)
        self.labels = torch.LongTensor(labels)
        self.sequence_length = sequence_length
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]

class TechniqueDetectorLSTM(nn.Module):
    """LSTM-based model for athletic technique detection."""
    
    def __init__(self, input_size: int, hidden_size: int, num_layers: int, 
                 num_classes: int, dropout: float = 0.2):
        super(TechniqueDetectorLSTM, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size,
            num_heads=8,
            dropout=dropout,
            batch_first=True
        )
        
        # Classification head
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, num_classes)
        )
        
    def forward(self, x):
        # LSTM forward pass
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # Apply attention
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # Use the last time step output
        final_out = attn_out[:, -1, :]
        
        # Classification
        output = self.classifier(final_out)
        
        return output

class TechniqueDetectorTrainer:
    """Main trainer class for the technique detector."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {self.device}")
        
        # Model parameters
        self.input_size = config.get('input_size', 34)  # 17 keypoints * 2 (x,y)
        self.hidden_size = config.get('hidden_size', 128)
        self.num_layers = config.get('num_layers', 2)
        self.num_classes = config.get('num_classes', 5)  # Different technique classes
        self.sequence_length = config.get('sequence_length', 30)
        
        # Training parameters
        self.batch_size = config.get('batch_size', 32)
        self.learning_rate = config.get('learning_rate', 0.001)
        self.num_epochs = config.get('num_epochs', 100)
        self.patience = config.get('patience', 10)
        
        # Initialize model
        self.model = TechniqueDetectorLSTM(
            input_size=self.input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            num_classes=self.num_classes
        ).to(self.device)
        
        # Loss and optimizer
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', patience=5, factor=0.5
        )
        
        # Training history
        self.train_losses = []
        self.val_losses = []
        self.train_accuracies = []
        self.val_accuracies = []
    
    def load_data(self, data_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """Load and preprocess pose sequence data."""
        logger.info(f"Loading data from {data_path}")
        
        # For this placeholder implementation, we'll generate synthetic data
        # In a real implementation, you would load actual pose sequence data
        
        num_samples = 1000
        sequences = []
        labels = []
        
        for i in range(num_samples):
            # Generate synthetic pose sequence (sequence_length, input_size)
            sequence = np.random.randn(self.sequence_length, self.input_size)
            
            # Add some pattern based on technique class
            technique_class = i % self.num_classes
            
            if technique_class == 0:  # Good form
                sequence += np.sin(np.linspace(0, 2*np.pi, self.sequence_length))[:, np.newaxis] * 0.1
            elif technique_class == 1:  # Poor balance
                sequence[:, 0::2] += np.random.randn(self.sequence_length, self.input_size//2) * 0.2
            elif technique_class == 2:  # Inconsistent timing
                sequence[::3] += 0.3
            elif technique_class == 3:  # Overextension
                sequence[:, 1::2] += np.abs(np.random.randn(self.sequence_length, self.input_size//2)) * 0.15
            else:  # Normal variation
                pass
            
            sequences.append(sequence)
            labels.append(technique_class)
        
        return np.array(sequences), np.array(labels)
    
    def create_data_loaders(self, X: np.ndarray, y: np.ndarray) -> Tuple[DataLoader, DataLoader]:
        """Create training and validation data loaders."""
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"Training samples: {len(X_train)}, Validation samples: {len(X_val)}")
        
        # Create datasets
        train_dataset = PoseSequenceDataset(X_train, y_train, self.sequence_length)
        val_dataset = PoseSequenceDataset(X_val, y_val, self.sequence_length)
        
        # Create data loaders
        train_loader = DataLoader(
            train_dataset, batch_size=self.batch_size, shuffle=True, num_workers=2
        )
        val_loader = DataLoader(
            val_dataset, batch_size=self.batch_size, shuffle=False, num_workers=2
        )
        
        return train_loader, val_loader
    
    def train_epoch(self, data_loader: DataLoader) -> Tuple[float, float]:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for batch_idx, (data, target) in enumerate(data_loader):
            data, target = data.to(self.device), target.to(self.device)
            
            self.optimizer.zero_grad()
            output = self.model(data)
            loss = self.criterion(output, target)
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            pred = output.argmax(dim=1, keepdim=True)
            correct += pred.eq(target.view_as(pred)).sum().item()
            total += target.size(0)
        
        avg_loss = total_loss / len(data_loader)
        accuracy = 100. * correct / total
        
        return avg_loss, accuracy
    
    def validate(self, data_loader: DataLoader) -> Tuple[float, float]:
        """Validate the model."""
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for data, target in data_loader:
                data, target = data.to(self.device), target.to(self.device)
                output = self.model(data)
                loss = self.criterion(output, target)
                
                total_loss += loss.item()
                pred = output.argmax(dim=1, keepdim=True)
                correct += pred.eq(target.view_as(pred)).sum().item()
                total += target.size(0)
        
        avg_loss = total_loss / len(data_loader)
        accuracy = 100. * correct / total
        
        return avg_loss, accuracy
    
    def train(self, data_path: str, model_save_path: str = "technique_detector.pth"):
        """Main training loop."""
        logger.info("Starting training...")
        
        # Load data
        X, y = self.load_data(data_path)
        train_loader, val_loader = self.create_data_loaders(X, y)
        
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(self.num_epochs):
            # Training
            train_loss, train_acc = self.train_epoch(train_loader)
            
            # Validation
            val_loss, val_acc = self.validate(val_loader)
            
            # Learning rate scheduling
            self.scheduler.step(val_loss)
            
            # Record history
            self.train_losses.append(train_loss)
            self.val_losses.append(val_loss)
            self.train_accuracies.append(train_acc)
            self.val_accuracies.append(val_acc)
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                
                # Save best model
                torch.save({
                    'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'epoch': epoch,
                    'val_loss': val_loss,
                    'val_accuracy': val_acc,
                    'config': self.config
                }, model_save_path)
                
            else:
                patience_counter += 1
            
            logger.info(f"Epoch {epoch+1}/{self.num_epochs} - "
                       f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}% - "
                       f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
            
            # Early stopping check
            if patience_counter >= self.patience:
                logger.info(f"Early stopping triggered after {epoch+1} epochs")
                break
        
        logger.info("Training completed!")
        return model_save_path
    
    def plot_training_history(self, save_path: str = "training_history.png"):
        """Plot training history."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Plot losses
        ax1.plot(self.train_losses, label='Training Loss')
        ax1.plot(self.val_losses, label='Validation Loss')
        ax1.set_title('Training and Validation Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        ax1.grid(True)
        
        # Plot accuracies
        ax2.plot(self.train_accuracies, label='Training Accuracy')
        ax2.plot(self.val_accuracies, label='Validation Accuracy')
        ax2.set_title('Training and Validation Accuracy')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy (%)')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        logger.info(f"Training history saved to {save_path}")

def main():
    """Main training function."""
    # Configuration
    config = {
        'input_size': 34,  # 17 keypoints * 2 coordinates
        'hidden_size': 128,
        'num_layers': 2,
        'num_classes': 5,
        'sequence_length': 30,
        'batch_size': 32,
        'learning_rate': 0.001,
        'num_epochs': 100,
        'patience': 10
    }
    
    # Create trainer
    trainer = TechniqueDetectorTrainer(config)
    
    # Train model
    data_path = "../datasets/sample"  # Placeholder path
    model_path = trainer.train(data_path)
    
    # Plot training history
    trainer.plot_training_history()
    
    logger.info(f"Training completed! Model saved to: {model_path}")

if __name__ == "__main__":
    main()