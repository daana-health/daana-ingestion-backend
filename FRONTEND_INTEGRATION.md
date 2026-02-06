# 🔗 Frontend Integration Guide

This guide shows you how to integrate your frontend application with the Daana Ingestion Backend API.

## 📡 Backend API Information

**Base URL** (when running locally): `http://localhost:8000`

**API Endpoints**:
- `POST /convert` - Convert CSV files
- `GET /schema` - Get database schema
- `GET /schema/{table}` - Get specific table schema
- `GET /health` - Health check

## 🎯 Quick Setup

### 1. Environment Configuration

Create a `.env` file in your frontend repo:

```env
VITE_API_BASE_URL=http://localhost:8000
# OR for React (CRA)
REACT_APP_API_BASE_URL=http://localhost:8000
# OR for Next.js
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 2. API Service Setup

Create an API service file in your frontend:

**`src/services/api.js`**
```javascript
// API Base URL from environment
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Upload and convert CSV file
 * @param {File} file - The CSV file to upload
 * @param {string} targetTable - Optional target table (e.g., 'units', 'drugs')
 * @param {boolean} returnMetadata - If true, return JSON metadata instead of CSV
 * @returns {Promise} - Response data
 */
export async function convertCSV(file, targetTable = null, returnMetadata = false) {
  const formData = new FormData();
  formData.append('file', file);
  
  if (targetTable) {
    formData.append('target_table', targetTable);
  }

  const url = new URL(`${API_BASE_URL}/convert`);
  if (returnMetadata) {
    url.searchParams.append('return_metadata', 'true');
  }

  const response = await fetch(url.toString(), {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to convert CSV');
  }

  if (returnMetadata) {
    return await response.json();
  } else {
    // Return blob for CSV download
    return await response.blob();
  }
}

/**
 * Get database schema
 * @returns {Promise} - Schema information
 */
export async function getSchema() {
  const response = await fetch(`${API_BASE_URL}/schema`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch schema');
  }
  
  return await response.json();
}

/**
 * Get specific table schema
 * @param {string} tableName - Name of the table
 * @returns {Promise} - Table schema information
 */
export async function getTableSchema(tableName) {
  const response = await fetch(`${API_BASE_URL}/schema/${tableName}`);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch table schema');
  }
  
  return await response.json();
}

/**
 * Health check
 * @returns {Promise} - Health status
 */
export async function healthCheck() {
  const response = await fetch(`${API_BASE_URL}/health`);
  
  if (!response.ok) {
    throw new Error('Backend is not available');
  }
  
  return await response.json();
}
```

## 🎨 React Component Examples

### Example 1: File Upload Component

**`src/components/CSVUploader.jsx`**
```jsx
import { useState } from 'react';
import { convertCSV } from '../services/api';

export default function CSVUploader() {
  const [file, setFile] = useState(null);
  const [targetTable, setTargetTable] = useState('units');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const tables = [
    'clinics', 'users', 'locations', 'lots', 
    'drugs', 'units', 'transactions'
  ];

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a CSV file');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // Get metadata first to show mapping
      const metadata = await convertCSV(file, targetTable, true);
      setResult(metadata);
      
      // Optionally download the cleaned CSV
      const csvBlob = await convertCSV(file, targetTable, false);
      const url = window.URL.createObjectURL(csvBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cleaned_${file.name}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="csv-uploader">
      <h2>Upload CSV for Conversion</h2>
      
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="file">Select CSV File:</label>
          <input
            type="file"
            id="file"
            accept=".csv"
            onChange={handleFileChange}
            disabled={loading}
          />
        </div>

        <div>
          <label htmlFor="targetTable">Target Table:</label>
          <select
            id="targetTable"
            value={targetTable}
            onChange={(e) => setTargetTable(e.target.value)}
            disabled={loading}
          >
            <option value="">Auto-detect</option>
            {tables.map(table => (
              <option key={table} value={table}>{table}</option>
            ))}
          </select>
        </div>

        <button type="submit" disabled={!file || loading}>
          {loading ? 'Converting...' : 'Convert CSV'}
        </button>
      </form>

      {error && (
        <div className="error">
          <h3>Error:</h3>
          <p>{error}</p>
        </div>
      )}

      {result && (
        <div className="result">
          <h3>Conversion Successful!</h3>
          <p>Mapped {result.mapped_count} columns</p>
          
          <h4>Column Mapping:</h4>
          <table>
            <thead>
              <tr>
                <th>Original Column</th>
                <th>Target Column</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(result.column_mapping).map(([orig, target]) => (
                <tr key={orig}>
                  <td>{orig}</td>
                  <td>{target}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {result.unmapped_columns.length > 0 && (
            <>
              <h4>Unmapped Columns:</h4>
              <ul>
                {result.unmapped_columns.map(col => (
                  <li key={col}>{col}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
```

### Example 2: Schema Viewer Component

**`src/components/SchemaViewer.jsx`**
```jsx
import { useState, useEffect } from 'react';
import { getSchema } from '../services/api';

export default function SchemaViewer() {
  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchSchema() {
      try {
        const data = await getSchema();
        setSchema(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchSchema();
  }, []);

  if (loading) return <div>Loading schema...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="schema-viewer">
      <h2>Database Schema</h2>
      
      {schema && Object.entries(schema.schema).map(([tableName, tableInfo]) => (
        <div key={tableName} className="table-schema">
          <h3>{tableName}</h3>
          <table>
            <thead>
              <tr>
                <th>Column</th>
                <th>Type</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {tableInfo.columns.map(col => (
                <tr key={col.name}>
                  <td><code>{col.name}</code></td>
                  <td>{col.type}</td>
                  <td>{col.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
```

## 🎨 Vue.js Example

**`src/composables/useAPI.js`**
```javascript
import { ref } from 'vue';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function useCSVConverter() {
  const loading = ref(false);
  const error = ref(null);
  const result = ref(null);

  const convertCSV = async (file, targetTable = null) => {
    loading.value = true;
    error.value = null;
    result.value = null;

    try {
      const formData = new FormData();
      formData.append('file', file);
      if (targetTable) {
        formData.append('target_table', targetTable);
      }

      const response = await fetch(
        `${API_BASE_URL}/convert?return_metadata=true`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail);
      }

      result.value = await response.json();
    } catch (err) {
      error.value = err.message;
    } finally {
      loading.value = false;
    }
  };

  return {
    loading,
    error,
    result,
    convertCSV,
  };
}
```

## 🔧 TypeScript Types

**`src/types/api.ts`**
```typescript
export interface ColumnMapping {
  [originalColumn: string]: string;
}

export interface ConversionResult {
  success: boolean;
  original_filename: string;
  target_table: string | null;
  column_mapping: ColumnMapping;
  unmapped_columns: string[];
  mapped_count: number;
  unmapped_count: number;
  cleaned_csv: string;
}

export interface TableColumn {
  name: string;
  type: string;
  description: string;
}

export interface TableSchema {
  columns: TableColumn[];
}

export interface SchemaResponse {
  schema: {
    [tableName: string]: TableSchema;
  };
  tables: string[];
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  openai_configured: boolean;
}
```

## 🚀 Running Both Services

### Terminal 1 - Backend:
```bash
cd daana-ingestion-backend
source venv/bin/activate
python main.py
# Backend runs on http://localhost:8000
```

### Terminal 2 - Frontend:
```bash
cd your-frontend-repo
npm install
npm run dev
# Frontend runs on http://localhost:5173 (or 3000 for CRA)
```

## 🔐 CORS Note

The backend is already configured to allow all origins:
```python
# In main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For production, update to specific origins:
```python
allow_origins=["https://your-frontend-domain.com"]
```

## 📦 Required Frontend Dependencies

```bash
# No additional dependencies needed for fetch API
# Optional: for better error handling and dev experience
npm install axios  # If you prefer axios over fetch
```

## 🎯 Next.js App Router Example

**`app/api/convert/route.js`** (API Route - optional proxy)
```javascript
import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.BACKEND_API_URL || 'http://localhost:8000';

export async function POST(request) {
  try {
    const formData = await request.formData();
    
    const response = await fetch(`${API_BASE_URL}/convert`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(error, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { detail: error.message },
      { status: 500 }
    );
  }
}
```

## 🧪 Testing the Connection

Create a simple test in your frontend:

```javascript
// Test backend connection
async function testBackendConnection() {
  try {
    const response = await fetch('http://localhost:8000/health');
    const data = await response.json();
    console.log('✅ Backend connected:', data);
    return true;
  } catch (error) {
    console.error('❌ Backend connection failed:', error);
    return false;
  }
}

// Run on app startup
testBackendConnection();
```

## 📝 Summary

1. **Backend runs on**: `http://localhost:8000`
2. **Frontend connects via**: Fetch API or Axios
3. **CORS is enabled**: Frontend can make requests directly
4. **Use the API service**: Import functions from `services/api.js`
5. **Environment variable**: Set `VITE_API_BASE_URL` in frontend `.env`

## 🎨 Complete Example App Structure

```
your-frontend-repo/
├── src/
│   ├── services/
│   │   └── api.js                 # API integration
│   ├── components/
│   │   ├── CSVUploader.jsx       # Upload component
│   │   ├── SchemaViewer.jsx      # Schema display
│   │   └── ResultsDisplay.jsx    # Results component
│   ├── types/
│   │   └── api.ts                # TypeScript types
│   ├── App.jsx                   # Main app
│   └── main.jsx                  # Entry point
├── .env                          # Environment variables
└── package.json
```

Your frontend and backend are now properly separated and can communicate via API calls! 🚀
