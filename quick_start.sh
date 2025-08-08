#!/bin/bash

# Quick Start Script for AI File Manager
echo "🚀 AI File Manager - Quick Start"
echo "================================="
echo ""
echo "Setting up the AI File Manager..."
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    echo "✅ Python3 found"
else
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check Node
if command -v node &> /dev/null; then
    echo "✅ Node.js found"
else
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

echo ""
echo "Installing backend dependencies..."
cd backend
pip3 install -r requirements.txt
cd ..

echo ""
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "✨ Setup complete!"
echo ""
echo "To start the application, run:"
echo "  ./run_dev.sh"
echo ""
echo "Then open:"
echo "  Frontend: http://localhost:3000"
echo "  API Docs: http://localhost:8000/docs"
echo ""