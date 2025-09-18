#!/bin/bash

# Download MoveNet Thunder model for pose detection
MODEL_DIR="$(dirname "$0")/.."
MODEL_FILE="$MODEL_DIR/movenet_thunder.tflite"

# Create models directory if it doesn't exist
mkdir -p "$MODEL_DIR"

echo "Downloading MoveNet Thunder model..."

# TensorFlow Hub model URL
MODEL_URL="https://storage.googleapis.com/tfhub-lite-models/google/movenet/singlepose/thunder/tflite_int8/4.tflite"

# Download the model
if command -v curl > /dev/null; then
    curl -L -o "$MODEL_FILE" "$MODEL_URL"
elif command -v wget > /dev/null; then
    wget -O "$MODEL_FILE" "$MODEL_URL"
else
    echo "Error: Neither curl nor wget is available. Please install one of them."
    exit 1
fi

if [ -f "$MODEL_FILE" ]; then
    echo "✅ Model downloaded successfully to: $MODEL_FILE"
    echo "📏 File size: $(du -h "$MODEL_FILE" | cut -f1)"
else
    echo "❌ Failed to download model"
    exit 1
fi

echo "🚀 Model is ready for use in the CampusPulse mobile app!"