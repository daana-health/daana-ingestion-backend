# ⚡ Quick Start Guide

Get the Daana Ingestion Service running in under 5 minutes!

## 🎯 Prerequisites

- Python 3.9+ installed
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## 🚀 3-Step Setup

### Step 1: Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# Replace 'your_openai_api_key_here' with your actual key
nano .env
```

### Step 2: Install Dependencies

**Option A - Using the run script (macOS/Linux):**
```bash
chmod +x run.sh
./run.sh
```

**Option B - Manual setup:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Start the Service

```bash
# If you used the run script, it's already running!

# Otherwise, start manually:
python main.py
```

## ✅ Verify It's Working

Open a new terminal and run:

```bash
# Activate venv if needed
source venv/bin/activate

# Run tests
python test_service.py
```

Or visit in your browser:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🎉 Try It Out!

### Using curl:

```bash
# Convert the sample CSV
curl -X POST "http://localhost:8000/convert?return_metadata=true" \
  -F "file=@test_sample.csv" \
  -F "target_table=units"
```

### Using Python:

```python
import requests

with open('test_sample.csv', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/convert?return_metadata=true',
        files=files,
        data={'target_table': 'units'}
    )
    print(response.json())
```

### Using the Interactive Docs:

1. Go to http://localhost:8000/docs
2. Click on `POST /convert`
3. Click "Try it out"
4. Upload your CSV file
5. Click "Execute"

## 🐳 Docker Alternative

If you prefer Docker:

```bash
# Build and run with docker-compose
docker-compose up --build

# Or with Docker directly
docker build -t daana-ingestion .
docker run -p 8000:8000 --env-file .env daana-ingestion
```

## 🆘 Troubleshooting

### "Could not connect to service"
- Make sure the service is running: `python main.py`
- Check if port 8000 is available

### "OpenAI API Error"
- Verify your API key in `.env` is correct
- Ensure you have OpenAI API credits

### "Module not found"
- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out the API docs at http://localhost:8000/docs
- Try converting your own CSV files
- Explore the `/schema` endpoint to see all supported tables

## 🎓 Example Workflow

1. **Get a messy CSV** from a medical clinic
2. **Upload it** to `POST /convert` with `target_table=units`
3. **Receive a cleaned CSV** matching your database schema
4. **Import directly** into your Daana-Rx database

No manual column mapping needed! 🎯
