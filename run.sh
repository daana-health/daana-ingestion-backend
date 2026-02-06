#!/bin/bash

# Daana Ingestion Service - Quick Start Script

echo "🚀 Starting Daana Ingestion Service..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating from template..."
    cp .env.example .env
    echo "✅ Please edit .env and add your OPENAI_API_KEY"
    echo "   Then run this script again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Start the service
echo "✨ Starting FastAPI server..."
echo "🌐 Service will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
python main.py
