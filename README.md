# Daana Ingestion Service

A specialized data ingestion microservice built with FastAPI and Python that intelligently converts messy CSV files from medical clinics into clean, structured data matching the Daana-Rx database schema.

## 🎯 Overview

Medical clinics often provide data exports with inconsistent column names, formatting, and structure. This service uses OpenAI's GPT-4 to intelligently map arbitrary CSV headers to your standardized database schema, making data ingestion seamless and automated.

## ✨ Features

- **Intelligent Column Mapping**: Uses OpenAI GPT-4 to understand and map messy column names to your database schema
- **Flexible Matching**: Handles abbreviations, synonyms, and common variations (e.g., "Med Name", "Medicine" → "medication_name")
- **Data Type Enforcement**: Automatically converts dates to ISO-8601, integers, decimals, and cleans string data
- **Multi-Table Support**: Supports all Daana-Rx tables (clinics, users, locations, lots, drugs, units, transactions)
- **RESTful API**: Easy-to-use HTTP endpoints with comprehensive error handling
- **CORS Enabled**: Ready for frontend integration
- **Metadata Export**: Optional JSON response with mapping details and unmapped columns

## 🏗️ Architecture

```
daana-ingestion-backend/
├── main.py                 # FastAPI application with endpoints
├── config.py              # Configuration management
├── schema.py              # Daana-Rx database schema definition
├── services/
│   ├── __init__.py
│   └── converter.py       # Core CSV conversion logic
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### 2. Installation

```bash
# Clone or navigate to the project directory
cd daana-ingestion-backend

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# You can use nano, vim, or any text editor
nano .env
```

Update the `.env` file:
```env
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

### 4. Run the Service

```bash
# Start the FastAPI server
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The service will be available at: **http://localhost:8000**

## 📚 API Documentation

### Interactive API Docs

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

#### `GET /`
Health check endpoint

**Response:**
```json
{
  "service": "Daana Ingestion Service",
  "version": "1.0.0",
  "status": "healthy"
}
```

#### `POST /convert`
Convert a messy CSV file to match the Daana-Rx schema

**Parameters:**
- `file` (required): CSV file upload
- `target_table` (optional): Specific table to target (e.g., "units", "drugs")
- `return_metadata` (optional): Return JSON with metadata instead of CSV

**Example (Download Cleaned CSV):**
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@messy_clinic_data.csv" \
  -F "target_table=units" \
  -o cleaned_output.csv
```

**Example (Get Metadata):**
```bash
curl -X POST "http://localhost:8000/convert?return_metadata=true" \
  -F "file=@messy_clinic_data.csv" \
  -F "target_table=units"
```

**Response (with metadata):**
```json
{
  "success": true,
  "original_filename": "messy_clinic_data.csv",
  "target_table": "units",
  "column_mapping": {
    "Med Name": "medication_name",
    "NDC": "ndc_id",
    "Exp Date": "expiry_date",
    "Qty": "total_quantity"
  },
  "unmapped_columns": ["Internal Code", "Notes"],
  "mapped_count": 4,
  "unmapped_count": 2,
  "cleaned_csv": "medication_name,ndc_id,expiry_date,total_quantity\n..."
}
```

#### `GET /schema`
Get the complete target database schema

#### `GET /schema/{table_name}`
Get schema for a specific table (e.g., `/schema/units`)

## 🗄️ Supported Tables

The service supports all Daana-Rx database tables:

1. **clinics** - Clinic information
2. **users** - User accounts
3. **locations** - Storage locations
4. **lots** - Medication lots
5. **drugs** - Universal drug database
6. **units** - Inventory units
7. **transactions** - Inventory transactions

## 🧪 Example Usage

### Python Example

```python
import requests

# Upload and convert CSV
with open('messy_data.csv', 'rb') as f:
    files = {'file': f}
    data = {'target_table': 'units'}
    
    response = requests.post(
        'http://localhost:8000/convert',
        files=files,
        data=data
    )
    
    # Save cleaned CSV
    with open('cleaned_data.csv', 'wb') as out:
        out.write(response.content)
```

### JavaScript/Frontend Example

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('target_table', 'units');

const response = await fetch('http://localhost:8000/convert?return_metadata=true', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Mapping:', result.column_mapping);
console.log('Unmapped:', result.unmapped_columns);
```

## 🔧 Configuration Options

Edit `.env` to customize:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here

# Application Configuration
APP_NAME=Daana Ingestion Service
APP_VERSION=1.0.0
DEBUG=True

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

## 🎓 How It Works

1. **Upload**: Client uploads a messy CSV file
2. **Header Analysis**: Service extracts column headers
3. **AI Mapping**: OpenAI GPT-4 intelligently maps headers to schema fields
4. **Transformation**: Data is cleaned and transformed:
   - Dates → ISO-8601 format
   - Numbers → Proper types (int, decimal)
   - Strings → Cleaned and trimmed
5. **Output**: Returns cleaned CSV matching the exact schema

## 🛡️ Error Handling

The service provides clear error messages:

- `400 Bad Request`: Invalid file, empty CSV, validation errors
- `500 Internal Server Error`: Processing errors with detailed messages

## 📊 Schema Information

The target schema is based on the Daana-Rx PostgreSQL database with:
- UUID primary keys
- Foreign key relationships
- Timestamptz for dates
- Row-level security support
- Full CRUD operations

## 🚀 Deployment

### Docker (Optional)

```dockerfile
# Create a Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t daana-ingestion .
docker run -p 8000:8000 --env-file .env daana-ingestion
```

### Cloud Deployment

Deploy to:
- **AWS Lambda** (with Mangum adapter)
- **Google Cloud Run**
- **Heroku**
- **DigitalOcean App Platform**

## 🤝 Contributing

This is a specialized internal service. For modifications:

1. Update `schema.py` if database schema changes
2. Adjust AI prompts in `services/converter.py` for better mapping
3. Add new endpoints in `main.py` as needed

## 📝 License

Internal use only - Daana-Rx Platform

## 🆘 Support

For issues or questions:
1. Check service logs (printed to console)
2. Verify OpenAI API key is valid
3. Ensure CSV files are properly formatted
4. Review API documentation at `/docs`

## 🔄 Version History

- **1.0.0** (Current)
  - Initial release
  - GPT-4 powered column mapping
  - Support for all Daana-Rx tables
  - RESTful API with CORS
  - Metadata export option
