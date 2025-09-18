#!/bin/bash
# Download MoveNet Lightning model from TensorFlow Hub

MODEL_DIR="$(dirname "$0")/.."
MODEL_URL="https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
MODEL_FILE="$MODEL_DIR/movenet_lightning.tflite"

echo "Downloading MoveNet Lightning model..."
echo "URL: $MODEL_URL"
echo "Destination: $MODEL_FILE"

# Create models directory if it doesn't exist
mkdir -p "$MODEL_DIR"

# Download the model
if command -v curl >/dev/null 2>&1; then
    curl -L "$MODEL_URL" -o "$MODEL_FILE"
elif command -v wget >/dev/null 2>&1; then
    wget "$MODEL_URL" -O "$MODEL_FILE"
else
    echo "Error: Neither curl nor wget is available. Please install one of them."
    exit 1
fi

# Check if download was successful
if [ -f "$MODEL_FILE" ]; then
    echo "Model downloaded successfully to $MODEL_FILE"
    echo "Model size: $(du -h "$MODEL_FILE" | cut -f1)"
else
    echo "Error: Model download failed"
    exit 1
fi

echo "Note: This is a placeholder script. In production, use the actual MoveNet Lightning model."
echo "TensorFlow Hub URL: https://tfhub.dev/google/lite-model/movenet/singlepose/lightning/4"