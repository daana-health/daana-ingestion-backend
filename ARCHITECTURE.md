# 🏗️ Architecture Documentation

## System Overview

The Daana Ingestion Service is a microservice that intelligently transforms messy medical clinic CSV files into clean, schema-compliant data using AI-powered column mapping.

## 📐 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  (Frontend App, cURL, Python Scripts, Postman, etc.)           │
└────────────┬────────────────────────────────────────────────────┘
             │ HTTP/REST API
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   main.py (Entry Point)                   │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │  │
│  │  │  CORS       │  │  Logging    │  │  Error          │  │  │
│  │  │  Middleware │  │  Config     │  │  Handling       │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │  │
│  │                                                           │  │
│  │  ┌───────────────────────────────────────────────────┐   │  │
│  │  │              API ENDPOINTS                        │   │  │
│  │  │  • GET  /           - Health check                │   │  │
│  │  │  • GET  /health     - Detailed status             │   │  │
│  │  │  • POST /convert    - CSV conversion              │   │  │
│  │  │  • GET  /schema     - Schema info                 │   │  │
│  │  │  • GET  /docs       - API documentation           │   │  │
│  │  └───────────────────────────────────────────────────┘   │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           services/converter.py (Core Logic)              │  │
│  │                                                           │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  CSVConverter Class                                │  │  │
│  │  │                                                    │  │  │
│  │  │  1. smart_convert_csv()                           │  │  │
│  │  │     ├─ Read CSV with Pandas                       │  │  │
│  │  │     ├─ Extract headers                            │  │  │
│  │  │     ├─ Call _get_column_mapping()                 │  │  │
│  │  │     ├─ Rename columns                             │  │  │
│  │  │     ├─ Call _enforce_data_types()                 │  │  │
│  │  │     └─ Return cleaned CSV                         │  │  │
│  │  │                                                    │  │  │
│  │  │  2. _get_column_mapping()                         │  │  │
│  │  │     ├─ Build AI prompt                            │  │  │
│  │  │     ├─ Call OpenAI API                            │  │  │
│  │  │     └─ Parse JSON response                        │  │  │
│  │  │                                                    │  │  │
│  │  │  3. _enforce_data_types()                         │  │  │
│  │  │     ├─ Convert dates to ISO-8601                  │  │  │
│  │  │     ├─ Convert integers                           │  │  │
│  │  │     ├─ Convert decimals                           │  │  │
│  │  │     └─ Clean strings                              │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────┬────────────────────────┬───────────────────────────┘
             │                        │
             ▼                        ▼
┌─────────────────────┐    ┌─────────────────────────────────────┐
│   EXTERNAL API      │    │     CONFIGURATION & DATA            │
│                     │    │                                     │
│  OpenAI GPT-4 API   │    │  • config.py - Settings/env vars   │
│  ├─ Column mapping  │    │  • schema.py - DB schema def       │
│  ├─ AI intelligence │    │  • .env - API keys & config        │
│  └─ JSON responses  │    │                                     │
└─────────────────────┘    └─────────────────────────────────────┘
```

## 🔄 Request Flow

### 1. CSV Upload Flow

```
User
 │
 │ 1. POST /convert
 │    • file: messy.csv
 │    • target_table: "units"
 ▼
FastAPI Endpoint (main.py)
 │
 │ 2. Validate file
 │    • Check .csv extension
 │    • Check not empty
 ▼
CSVConverter.smart_convert_csv()
 │
 │ 3. Read CSV
 │    • pandas.read_csv()
 │    • Extract headers: ["Med Name", "NDC", "Exp Date", ...]
 ▼
CSVConverter._get_column_mapping()
 │
 │ 4. Build AI Prompt
 │    • System: "You are a Data Engineer..."
 │    • User: "Map these headers..."
 │    • Schema: Full Daana-Rx schema
 ▼
OpenAI GPT-4 API
 │
 │ 5. AI Processing
 │    • Analyze headers
 │    • Match to schema
 │    • Return JSON mapping
 ▼
CSVConverter (continued)
 │
 │ 6. Transform Data
 │    • Rename columns using mapping
 │    • _enforce_data_types()
 │      ├─ Dates → ISO-8601
 │      ├─ Numbers → int/decimal
 │      └─ Strings → cleaned
 ▼
FastAPI Response
 │
 │ 7. Return to User
 │    • Cleaned CSV file (download)
 │    • OR JSON metadata (if requested)
 ▼
User receives clean data
```

## 📦 Component Breakdown

### 1. **main.py** - FastAPI Application
- **Purpose**: HTTP API layer, routing, middleware
- **Responsibilities**:
  - Request handling and validation
  - CORS configuration
  - Error handling and logging
  - Response formatting
  - API documentation (OpenAPI/Swagger)

### 2. **services/converter.py** - Core Business Logic
- **Purpose**: CSV conversion and AI integration
- **Key Methods**:
  - `smart_convert_csv()`: Main conversion orchestrator
  - `_get_column_mapping()`: AI-powered header mapping
  - `_enforce_data_types()`: Data type standardization

### 3. **schema.py** - Database Schema Definition
- **Purpose**: Source of truth for target schema
- **Contains**:
  - Complete Daana-Rx schema (7 tables)
  - Column metadata (name, type, description)
  - Helper functions for schema queries

### 4. **config.py** - Configuration Management
- **Purpose**: Environment-based settings
- **Features**:
  - Pydantic settings validation
  - Environment variable loading
  - Centralized configuration

## 🔐 Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Security Layers                          │
├─────────────────────────────────────────────────────────────┤
│  1. API Key Protection                                      │
│     • OpenAI key stored in .env (not in code)              │
│     • .env file is gitignored                              │
│     • Environment-based secrets                            │
├─────────────────────────────────────────────────────────────┤
│  2. Input Validation                                        │
│     • File type checking (.csv only)                       │
│     • File size validation                                 │
│     • Content validation with Pandas                       │
├─────────────────────────────────────────────────────────────┤
│  3. CORS Configuration                                      │
│     • Currently: Allow all (development)                   │
│     • Production: Restrict to specific origins             │
├─────────────────────────────────────────────────────────────┤
│  4. Error Handling                                          │
│     • No sensitive data in error messages                  │
│     • Structured exception handling                        │
│     • Detailed server-side logging                         │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Data Flow

### Input Data (Messy CSV)
```csv
Med Name,NDC,Exp Date,Qty,Available
Lisinopril 10mg Tablet,0781-1506-01,12/31/2025,100,100
```

### AI Mapping Process
```json
{
  "Med Name": "medication_name",
  "NDC": "ndc_id",
  "Exp Date": "expiry_date",
  "Qty": "total_quantity",
  "Available": "available_quantity"
}
```

### Output Data (Clean CSV)
```csv
medication_name,ndc_id,expiry_date,total_quantity,available_quantity
Lisinopril 10mg Tablet,0781-1506-01,2025-12-31,100,100
```

## 🎯 Design Patterns

### 1. **Dependency Injection**
- Settings injected via `config.py`
- OpenAI client initialized in converter
- Singleton converter instance

### 2. **Separation of Concerns**
- API layer (main.py)
- Business logic (converter.py)
- Configuration (config.py, schema.py)
- Clear boundaries between layers

### 3. **Error Handling Strategy**
```python
Try/Except at multiple levels:
├─ API Layer: HTTPException with status codes
├─ Service Layer: ValueError for validation
└─ Helper Methods: Specific exceptions with context
```

### 4. **Async/Await Pattern**
- Async endpoints for scalability
- Non-blocking I/O operations
- Efficient request handling

## 🚀 Scalability Considerations

### Horizontal Scaling
```
Load Balancer
     │
     ├─► Service Instance 1
     ├─► Service Instance 2
     ├─► Service Instance 3
     └─► Service Instance N
```

### Performance Optimization
1. **Pandas**: Fast CSV processing
2. **Async FastAPI**: Concurrent requests
3. **Streaming Responses**: Large files
4. **OpenAI**: Batching possible for multiple files

### Deployment Options
- **Docker**: Containerized, portable
- **Kubernetes**: Auto-scaling, load balancing
- **Serverless**: AWS Lambda, Cloud Run
- **Traditional**: VM/VPS with Nginx

## 🔄 Extension Points

### 1. Add New Data Sources
```python
# In converter.py, add methods:
def convert_excel(): ...
def convert_json(): ...
def convert_xml(): ...
```

### 2. Add New Schema Tables
```python
# In schema.py:
TARGET_SCHEMA["new_table"] = {
    "columns": [...]
}
```

### 3. Customize AI Behavior
```python
# In converter.py, modify:
system_prompt = """..."""  # Adjust instructions
model = "gpt-4-turbo"     # Change model
temperature = 0.1         # Adjust creativity
```

### 4. Add Preprocessing
```python
# In converter.py:
def _preprocess_csv(df):
    # Custom cleaning
    return df
```

## 📈 Monitoring & Observability

### Logging Strategy
```python
logger.info()   # Normal operations
logger.warning() # Potential issues
logger.error()   # Failures
```

### Metrics to Track
- Request count per endpoint
- Conversion success/failure rate
- OpenAI API latency
- CSV processing time
- File size distribution

### Health Checks
- `/health` endpoint
- OpenAI connectivity check
- Service readiness probe

## 🔧 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | FastAPI | Modern async Python web framework |
| Server | Uvicorn | ASGI server |
| AI | OpenAI GPT-4 | Intelligent column mapping |
| Data Processing | Pandas | CSV manipulation |
| Configuration | Pydantic | Settings validation |
| Container | Docker | Deployment |
| Language | Python 3.11+ | Runtime |

## 📝 API Specification

### OpenAPI/Swagger
- Auto-generated from FastAPI decorators
- Available at `/docs` endpoint
- Interactive testing interface
- Complete request/response schemas

### Response Formats

**Success (CSV Download)**
```
Status: 200 OK
Content-Type: text/csv
Content-Disposition: attachment; filename=cleaned_file.csv
X-Mapped-Columns: 5
X-Unmapped-Columns: 2
```

**Success (Metadata)**
```json
{
  "success": true,
  "original_filename": "messy.csv",
  "column_mapping": {...},
  "unmapped_columns": [...],
  "cleaned_csv": "..."
}
```

**Error**
```json
{
  "detail": "Error message"
}
```

## 🎓 Best Practices Implemented

✅ **Type Hints**: Complete type annotations
✅ **Docstrings**: Comprehensive documentation
✅ **Error Handling**: Structured exceptions
✅ **Async/Await**: Non-blocking operations
✅ **Environment Config**: 12-factor app
✅ **Logging**: Structured logging
✅ **API Documentation**: Auto-generated
✅ **Containerization**: Docker support
✅ **Testing**: Test suite included
✅ **Clean Code**: Separation of concerns

---

**Last Updated**: February 5, 2026
**Version**: 1.0.0
