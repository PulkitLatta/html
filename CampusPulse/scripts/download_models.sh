#!/bin/bash

# CampusPulse Model Download Script
# Downloads ML models for local development and testing

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MODELS_DIR="CampusPulse/mobile/assets/models"
TF_HUB_BASE_URL="https://tfhub.dev/google/lite-model"

# Models to download
declare -A MODELS=(
    ["movenet_lightning"]="movenet/singlepose/lightning/tflite_int8/4?lite-format=tflite"
    ["movenet_thunder"]="movenet/singlepose/thunder/tflite_int8/4?lite-format=tflite"
)

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

# Function to check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    local missing_deps=()
    
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    if ! command -v wget &> /dev/null; then
        missing_deps+=("wget")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        print_status "Please install missing dependencies and try again."
        exit 1
    fi
    
    print_success "All dependencies found"
}

# Function to create directory structure
setup_directories() {
    print_status "Setting up directory structure..."
    
    if [ ! -d "$MODELS_DIR" ]; then
        mkdir -p "$MODELS_DIR"
        print_status "Created models directory: $MODELS_DIR"
    fi
    
    print_success "Directory structure ready"
}

# Function to download a model
download_model() {
    local model_name=$1
    local model_url_path=$2
    local full_url="${TF_HUB_BASE_URL}/${model_url_path}"
    local output_file="${MODELS_DIR}/${model_name}.tflite"
    
    print_status "Downloading ${model_name}..."
    print_status "URL: ${full_url}"
    
    # Check if model already exists
    if [ -f "$output_file" ]; then
        print_warning "Model ${model_name} already exists at ${output_file}"
        read -p "Do you want to re-download it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Skipping ${model_name}"
            return 0
        fi
    fi
    
    # Download with progress bar
    if curl -L --progress-bar --fail "$full_url" -o "$output_file"; then
        print_success "Downloaded ${model_name} to ${output_file}"
        
        # Check file size
        local file_size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null)
        print_status "File size: $(numfmt --to=iec $file_size)B"
        
        return 0
    else
        print_error "Failed to download ${model_name}"
        rm -f "$output_file"  # Clean up partial download
        return 1
    fi
}

# Function to verify downloaded models
verify_models() {
    print_status "Verifying downloaded models..."
    
    local verified=0
    local total=0
    
    for model_name in "${!MODELS[@]}"; do
        local model_file="${MODELS_DIR}/${model_name}.tflite"
        total=$((total + 1))
        
        if [ -f "$model_file" ]; then
            local file_size=$(stat -f%z "$model_file" 2>/dev/null || stat -c%s "$model_file" 2>/dev/null)
            
            # Basic verification - check if file size is reasonable (> 1MB)
            if [ "$file_size" -gt 1048576 ]; then
                print_success "✓ ${model_name}: $(numfmt --to=iec $file_size)B"
                verified=$((verified + 1))
            else
                print_warning "✗ ${model_name}: File too small ($(numfmt --to=iec $file_size)B)"
            fi
        else
            print_warning "✗ ${model_name}: File not found"
        fi
    done
    
    print_status "Verification complete: ${verified}/${total} models verified"
    
    if [ $verified -eq $total ]; then
        print_success "All models verified successfully!"
        return 0
    else
        print_warning "Some models may not have downloaded correctly"
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "CampusPulse Model Download Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verify   Only verify existing models (skip download)"
    echo "  -f, --force    Force re-download all models"
    echo ""
    echo "Models that will be downloaded:"
    for model_name in "${!MODELS[@]}"; do
        echo "  - ${model_name}"
    done
    echo ""
    echo "Models will be saved to: ${MODELS_DIR}"
}

# Main execution
main() {
    local verify_only=false
    local force_download=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -v|--verify)
                verify_only=true
                shift
                ;;
            -f|--force)
                force_download=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_status "CampusPulse Model Download Script"
    print_status "=================================="
    
    # Check dependencies
    check_dependencies
    
    # Setup directories
    setup_directories
    
    if [ "$verify_only" = true ]; then
        verify_models
        exit $?
    fi
    
    # Download models
    local download_failed=()
    
    for model_name in "${!MODELS[@]}"; do
        if ! download_model "$model_name" "${MODELS[$model_name]}"; then
            download_failed+=("$model_name")
        fi
    done
    
    # Report results
    if [ ${#download_failed[@]} -eq 0 ]; then
        print_success "All models downloaded successfully!"
    else
        print_error "Failed to download: ${download_failed[*]}"
    fi
    
    # Verify downloads
    verify_models
    
    print_status "Model download complete!"
    print_status "You can now use these models in the CampusPulse mobile app."
}

# Execute main function
main "$@"