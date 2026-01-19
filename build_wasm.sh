#!/bin/bash
set -e

# Build voca_core to WebAssembly using Emscripten
# Requires: Emscripten SDK (emsdk) to be installed and activated
# Install: https://emscripten.org/docs/getting_started/downloads.html

BUILD_DIR="build_wasm"
OUTPUT_DIR="web/wasm"

echo "=== Building voca_core for WebAssembly ==="

# Check if emcmake is available
if ! command -v emcmake &> /dev/null; then
    echo "Error: emcmake not found. Please install and activate Emscripten SDK."
    echo "  git clone https://github.com/emscripten-core/emsdk.git"
    echo "  cd emsdk && ./emsdk install latest && ./emsdk activate latest"
    echo "  source ./emsdk_env.sh"
    exit 1
fi

# Create build directory
mkdir -p "$BUILD_DIR"
mkdir -p "$OUTPUT_DIR"

# Configure with Emscripten
echo "Configuring CMake with Emscripten..."
emcmake cmake -S . -B "$BUILD_DIR" \
    -DCMAKE_BUILD_TYPE=Release

# Build
echo "Building..."
cmake --build "$BUILD_DIR" --target voca_wasm

# Copy outputs to web directory
echo "Copying outputs to $OUTPUT_DIR..."
cp "$BUILD_DIR/voca_core.js" "$OUTPUT_DIR/"
cp "$BUILD_DIR/voca_core.wasm" "$OUTPUT_DIR/"

echo "=== Build complete ==="
echo "Output files:"
ls -la "$OUTPUT_DIR"
