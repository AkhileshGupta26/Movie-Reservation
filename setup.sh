#!/bin/bash
# Movie Reservation System - Setup Script

echo "🎬 Movie Reservation System Setup"
echo "=================================="

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.11+"
    exit 1
fi

echo "✅ Python found: $(python --version)"

# Backend setup
echo ""
echo "📦 Setting up backend..."

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate
echo "✅ Virtual environment activated"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Run tests
echo ""
echo "🧪 Running tests..."
pytest tests/test_auth.py -v
echo "✅ Tests passed"

# Frontend setup
echo ""
echo "📦 Setting up frontend..."

cd frontend

# Check if Node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 16+"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"

# Install dependencies
echo "Installing npm dependencies..."
npm install
echo "✅ Frontend dependencies installed"

cd ..

echo ""
echo "=================================="
echo "✅ Setup complete!"
echo ""
echo "To start development:"
echo ""
echo "Backend:"
echo "  cd ."
echo "  source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "Frontend (in another terminal):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "Frontend: http://localhost:3000"
echo ""
echo "🎬 Happy booking!"
