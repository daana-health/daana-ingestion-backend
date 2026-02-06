.PHONY: help install run test clean docker-build docker-run setup

help:
	@echo "Daana Ingestion Service - Available Commands:"
	@echo ""
	@echo "  make setup        - Initial setup (create venv, install deps, create .env)"
	@echo "  make install      - Install dependencies"
	@echo "  make run          - Start the service"
	@echo "  make test         - Run test suite"
	@echo "  make clean        - Clean up temporary files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run with Docker Compose"
	@echo "  make docker-stop  - Stop Docker containers"
	@echo ""

setup:
	@echo "🔧 Setting up Daana Ingestion Service..."
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file..."; \
		cp .env.example .env; \
		echo "⚠️  Please edit .env and add your OPENAI_API_KEY"; \
	fi
	@if [ ! -d venv ]; then \
		echo "📦 Creating virtual environment..."; \
		python3 -m venv venv; \
	fi
	@echo "📥 Installing dependencies..."
	@. venv/bin/activate && pip install -q -r requirements.txt
	@echo "✅ Setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env and add your OpenAI API key"
	@echo "  2. Run: make run"

install:
	@echo "📥 Installing dependencies..."
	@pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

run:
	@echo "🚀 Starting Daana Ingestion Service..."
	@python main.py

test:
	@echo "🧪 Running tests..."
	@python test_service.py

clean:
	@echo "🧹 Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache 2>/dev/null || true
	@echo "✅ Cleanup complete!"

docker-build:
	@echo "🐳 Building Docker image..."
	@docker build -t daana-ingestion:latest .
	@echo "✅ Docker image built!"

docker-run:
	@echo "🐳 Starting with Docker Compose..."
	@docker-compose up --build

docker-stop:
	@echo "🛑 Stopping Docker containers..."
	@docker-compose down
	@echo "✅ Containers stopped!"

dev:
	@echo "🔧 Starting in development mode..."
	@uvicorn main:app --reload --host 0.0.0.0 --port 8000
