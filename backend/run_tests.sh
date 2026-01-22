#!/bin/bash

# Test runner script for voca_test backend
# Run with: ./run_tests.sh

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           Voca Test - Backend Test Suite                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if in backend directory
if [ ! -f "pytest.ini" ]; then
    echo "Error: Please run from backend directory"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check dependencies
echo "Checking dependencies..."
python -c "import pytest" 2>/dev/null || {
    echo "Installing test dependencies..."
    pip install -r requirements.txt
}

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo " Running Tests"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Parse command line arguments
if [ "$1" = "unit" ]; then
    echo "Running unit tests only..."
    pytest -m unit -v
elif [ "$1" = "integration" ]; then
    echo "Running integration tests..."
    pytest -m integration -v
elif [ "$1" = "api" ]; then
    echo "Running API tests..."
    pytest -m api -v
elif [ "$1" = "coverage" ]; then
    echo "Running tests with coverage report..."
    pytest --cov=app --cov-report=term-missing --cov-report=html -v
    echo ""
    echo "Coverage report generated in htmlcov/index.html"
elif [ "$1" = "quick" ]; then
    echo "Running quick tests (unit only)..."
    pytest -m "unit" -v --tb=short
elif [ "$1" = "ci" ]; then
    echo "Running CI tests (skip external APIs)..."
    pytest -m "not external" --cov=app --cov-report=term -v
else
    echo "Running all tests..."
    pytest -v
fi

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                   ✅ All Tests Passed!                         ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
else
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                   ❌ Tests Failed                              ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    exit 1
fi
