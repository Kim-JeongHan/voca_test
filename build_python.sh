#!/usr/bin/env bash
set -euo pipefail

# Build Python bindings for voca_test C++ engine
# Output: backend/app/core/voca_cpp.cpython-*.so

echo "Building Python bindings..."

# Create build directory
mkdir -p build_python
cd build_python

# Configure with Python bindings enabled
cmake .. -DBUILD_PYTHON=ON -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build . --target voca_cpp

# Install to backend/app/core/
cmake --install . --component voca_cpp 2>/dev/null || \
    cp voca_cpp*.so ../backend/app/core/

echo ""
echo "Done! Python module installed to backend/app/core/"
echo "Test with: cd backend && uv run python -c 'from app.core import voca_cpp; print(dir(voca_cpp))'"
