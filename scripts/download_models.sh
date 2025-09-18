#!/bin/bash

# CampusPulse Model Download Script
# This script downloads the required ML models for the CampusPulse platform

set -e

echo "🤖 CampusPulse Model Download Script"
echo "===================================="

# Configuration
MODELS_DIR="./CampusPulse/mobile/assets/models"
MOBILE_SCRIPT="./CampusPulse/mobile/assets/models/scripts/download_models.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required commands are available
check_dependencies() {
    print_status "Checking dependencies..."
    
    local deps=("curl" "wget")
    local missing_deps=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            missing_deps+=("$dep")
        fi
    done
    
    if [[ ${#missing_deps[@]} -eq 2 ]]; then
        print_error "Neither curl nor wget is available. Please install one of them."
        exit 1
    fi
    
    print_success "Dependencies check passed"
}

# Create models directory if it doesn't exist
create_directories() {
    print_status "Creating directories..."
    mkdir -p "$MODELS_DIR"
    print_success "Directories created"
}

# Download models for mobile app
download_mobile_models() {
    print_status "Downloading mobile app models..."
    
    if [[ -x "$MOBILE_SCRIPT" ]]; then
        print_status "Running mobile model download script..."
        cd "$(dirname "$MOBILE_SCRIPT")" || exit 1
        ./download_models.sh
        cd - > /dev/null || exit 1
        print_success "Mobile models downloaded"
    else
        print_warning "Mobile model download script not found or not executable"
        print_status "Attempting direct download..."
        
        # Download MoveNet Thunder model directly
        local model_url="https://storage.googleapis.com/tfhub-lite-models/google/movenet/singlepose/thunder/tflite_int8/4.tflite"
        local model_file="$MODELS_DIR/movenet_thunder.tflite"
        
        if command -v curl >/dev/null 2>&1; then
            curl -L -o "$model_file" "$model_url"
        elif command -v wget >/dev/null 2>&1; then
            wget -O "$model_file" "$model_url"
        fi
        
        if [[ -f "$model_file" ]]; then
            print_success "MoveNet model downloaded to $model_file"
            print_status "File size: $(du -h "$model_file" | cut -f1)"
        else
            print_error "Failed to download MoveNet model"
            exit 1
        fi
    fi
}

# Verify downloaded models
verify_models() {
    print_status "Verifying downloaded models..."
    
    local model_file="$MODELS_DIR/movenet_thunder.tflite"
    
    if [[ -f "$model_file" ]]; then
        local file_size
        file_size=$(stat -c%s "$model_file" 2>/dev/null || stat -f%z "$model_file" 2>/dev/null)
        
        # Expected file size is approximately 6-8 MB
        if [[ $file_size -gt 5000000 ]] && [[ $file_size -lt 10000000 ]]; then
            print_success "Model verification passed"
            print_status "Model size: $(echo "scale=1; $file_size/1024/1024" | bc)MB"
        else
            print_warning "Model file size seems incorrect (${file_size} bytes)"
            print_warning "Expected size: 6-8 MB"
        fi
    else
        print_error "Model file not found: $model_file"
        exit 1
    fi
}

# Create model info file
create_model_info() {
    print_status "Creating model information file..."
    
    local info_file="$MODELS_DIR/model_info.json"
    
    cat > "$info_file" << EOF
{
  "models": [
    {
      "name": "MoveNet Thunder",
      "filename": "movenet_thunder.tflite",
      "version": "4",
      "description": "Single-pose pose detection model optimized for accuracy",
      "input_size": [256, 256],
      "keypoints": 17,
      "format": "TensorFlow Lite",
      "downloaded_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    }
  ],
  "usage_notes": [
    "Models are used for real-time pose detection in the mobile app",
    "TensorFlow Lite format is optimized for mobile devices",
    "Models should be updated periodically for best performance"
  ]
}
EOF
    
    print_success "Model info file created: $info_file"
}

# Main execution
main() {
    echo
    print_status "Starting model download process..."
    
    check_dependencies
    create_directories
    download_mobile_models
    verify_models
    create_model_info
    
    echo
    print_success "✅ All models downloaded successfully!"
    print_status "Models are ready for use in the CampusPulse mobile app"
    print_status "Location: $MODELS_DIR"
    
    # Display summary
    echo
    echo "📊 Summary:"
    echo "  - Models directory: $MODELS_DIR"
    echo "  - Files downloaded: $(find "$MODELS_DIR" -name "*.tflite" | wc -l) model(s)"
    echo "  - Total size: $(du -sh "$MODELS_DIR" 2>/dev/null | cut -f1 || echo "unknown")"
    echo
    echo "🚀 You can now run the CampusPulse mobile app with ML support!"
    echo
}

# Handle script interruption
trap 'print_error "Script interrupted"; exit 1' INT TERM

# Run main function
main "$@"