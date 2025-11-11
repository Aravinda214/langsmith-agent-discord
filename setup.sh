#!/bin/bash
# Setup script for Discord Channel Selector (Mac/Linux)
# This script automates the initial setup process

echo "========================================"
echo "Discord Channel Selector - Setup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "[1/5] Python found"
python3 --version

# Create virtual environment
echo ""
echo "[2/5] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created successfully"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo ""
echo "[3/5] Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Setup .env file
echo ""
echo "[4/5] Setting up environment file..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ".env file created from template"
    echo ""
    echo "IMPORTANT: Edit .env file and add your OpenAI API key"
    echo "You can get an API key from: https://platform.openai.com/api-keys"
else
    echo ".env file already exists"
fi

# Verify configuration
echo ""
echo "[5/5] Verifying configuration..."
if [ -f "config.yaml" ]; then
    echo "config.yaml found"
else
    echo "WARNING: config.yaml not found"
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OPENAI_API_KEY"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python src/main.py"
echo ""
echo "For quick start guide, see QUICKSTART.md"
echo "For full documentation, see README.md"
echo ""
