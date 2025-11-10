#!/bin/bash
# Pre-commit CI checks - run locally before pushing

set -e

echo "🔍 Running local CI checks..."

# Check Python version
echo "✓ Checking Python version..."
python --version

# Install dependencies
echo "✓ Installing dependencies..."
pip install -q -r requirements.txt pytest pytest-cov 2>/dev/null || true

# Run tests
echo "✓ Running tests..."
pytest -q --tb=line

# Check linting (optional)
if command -v flake8 &> /dev/null; then
    echo "✓ Running flake8..."
    flake8 app --max-line-length=120 --statistics || true
fi

echo ""
echo "✅ All checks passed!"
echo ""
echo "You can now push your changes."
