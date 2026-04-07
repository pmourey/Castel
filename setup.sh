#!/bin/bash
# Castel Game - Installation and Setup Script

echo "==========================================="
echo "Castel - Board Game Setup"
echo "==========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Install dependencies
echo ""
echo "Installing dependencies..."
python3 -m pip install -q pygame
echo "✓ Dependencies installed"

# Run tests
echo ""
echo "Running tests..."
python3 test_suite.py

# Check setup
echo ""
echo "==========================================="
echo "Setup Complete! 🎲"
echo "==========================================="
echo ""
echo "To start the game, run:"
echo "  python3 main.py"
echo ""
echo "Documentation:"
echo "  - README.md          : Quick start"
echo "  - DOCUMENTATION.md   : Full guide"
echo "  - SUMMARY.md         : Project overview"
echo ""
echo "Good game!"
