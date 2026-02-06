# 🎨 Frontend Integration Examples

Ready-to-use code to connect your frontend to the Daana Ingestion Backend.

## 📁 What's Included

```
frontend-examples/
├── README.md                    # This file
├── api-service.js              # Universal API client (copy to any project)
├── react/
│   ├── CSVUploader.jsx         # Complete React component
│   └── CSVUploader.css         # Styled component
├── vue/                        # (Vue examples - coming soon)
├── nextjs/                     # (Next.js examples - coming soon)
└── vanilla/                    # (Vanilla JS examples - coming soon)
```

## 🚀 Quick Start

### Step 1: Copy the API Service

Copy `api-service.js` to your frontend project:

```bash
# From your frontend repo
cp path/to/daana-ingestion-backend/frontend-examples/api-service.js src/services/api.js
```

### Step 2: Configure Environment

Create `.env` in your frontend root:

**For Vite (React/Vue):**
```env
VITE_API_BASE_URL=http://localhost:8000
```

**For Create React App:**
```env
REACT_APP_API_BASE_URL=http://localhost:8000
```

**For Next.js:**
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Step 3: Use in Your Components

```javascript
import { convertCSV, downloadConvertedCSV, getSchema } from './services/api';

// Convert and download CSV
const handleUpload = async (file) => {
  const metadata = await convertCSV(file, 'units', true);
  await downloadConvertedCSV(file, 'units');
};
```

## 📦 React Component Usage

### Full Component (Recommended)

Copy the complete uploader with styling:

```bash
# Copy component
cp frontend-examples/react/CSVUploader.jsx src/components/
cp frontend-examples/react/CSVUploader.css src/components/
```

Use in your app:

```jsx
import CSVUploader from './components/CSVUploader';

function App() {
  return (
    <div>
      <h1>Data Ingestion Portal</h1>
      <CSVUploader />
    </div>
  );
}
```

### Simple Integration

Or build your own component using the API:

```jsx
import { useState } from 'react';
import { convertCSV } from './services/api';

function SimpleUploader() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);

  const handleSubmit = async () => {
    const metadata = await convertCSV(file, null, true);
    setResult(metadata);
  };

  return (
    <div>
      <input 
        type="file" 
        accept=".csv"
        onChange={(e) => setFile(e.target.files[0])}
      />
      <button onClick={handleSubmit}>Convert</button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
```

## 🎯 API Functions Reference

### `convertCSV(file, targetTable, returnMetadata)`
Convert a CSV file using AI mapping.

**Parameters:**
- `file` (File) - The CSV file to upload
- `targetTable` (string, optional) - Target table name ('units', 'drugs', etc.)
- `returnMetadata` (boolean) - If true, returns JSON with mapping info

**Returns:** Promise<Object|Blob>

**Example:**
```javascript
// Get metadata
const metadata = await convertCSV(file, 'units', true);
console.log(metadata.column_mapping);

// Get CSV blob
const csvBlob = await convertCSV(file, 'units', false);
```

### `downloadConvertedCSV(file, targetTable, filename)`
Convert and automatically download the cleaned CSV.

**Example:**
```javascript
await downloadConvertedCSV(file, 'units', 'cleaned_data.csv');
```

### `getSchema()`
Get the complete database schema for all tables.

**Example:**
```javascript
const schema = await getSchema();
console.log(schema.tables); // ['clinics', 'users', 'units', ...]
```

### `getTableSchema(tableName)`
Get schema for a specific table.

**Example:**
```javascript
const tableSchema = await getTableSchema('units');
console.log(tableSchema.schema.columns);
```

### `healthCheck()`
Check if the backend is available.

**Example:**
```javascript
const health = await healthCheck();
console.log(health.status); // 'healthy'
```

## 🎨 Component Features

The provided React component includes:

- ✅ Drag & drop file upload
- ✅ File validation (.csv only)
- ✅ Target table selection
- ✅ Backend health check
- ✅ Loading states
- ✅ Error handling
- ✅ Automatic CSV download
- ✅ Column mapping display
- ✅ Unmapped columns warning
- ✅ Beautiful, responsive UI

## 🔧 Running Both Services

### Terminal 1 - Backend:
```bash
cd daana-ingestion-backend
source venv/bin/activate
python main.py
# Running on http://localhost:8000
```

### Terminal 2 - Frontend:
```bash
cd your-frontend-repo
npm install
npm run dev
# Running on http://localhost:5173
```

## 🎯 Integration Checklist

- [ ] Copy `api-service.js` to `src/services/api.js`
- [ ] Create `.env` with `VITE_API_BASE_URL=http://localhost:8000`
- [ ] Install dependencies: `npm install` (no extra packages needed!)
- [ ] Start backend: `python main.py`
- [ ] Start frontend: `npm run dev`
- [ ] Test file upload at http://localhost:5173

## 📝 Example Response

When you upload a CSV, the metadata response looks like:

```json
{
  "success": true,
  "original_filename": "clinic_data.csv",
  "target_table": "units",
  "column_mapping": {
    "Med Name": "medication_name",
    "NDC": "ndc_id",
    "Exp Date": "expiry_date",
    "Qty": "total_quantity",
    "Available": "available_quantity"
  },
  "unmapped_columns": ["Internal Code", "Notes"],
  "mapped_count": 5,
  "unmapped_count": 2
}
```

## 🐛 Troubleshooting

### "Backend is not available"
- Ensure backend is running: `python main.py`
- Check backend URL in `.env` matches where backend is running
- Verify CORS is enabled in backend (it is by default)

### "Failed to fetch"
- Check console for CORS errors
- Ensure backend URL is correct (include http://)
- Try accessing http://localhost:8000/health directly in browser

### File upload fails
- Ensure file is .csv format
- Check file size (backend should handle reasonable sizes)
- Check browser console for specific error messages

## 🎓 Framework-Specific Notes

### Vite + React
```bash
npm create vite@latest my-app -- --template react
cd my-app
npm install
# Copy api-service.js
# Add VITE_API_BASE_URL to .env
npm run dev
```

### Create React App
```bash
npx create-react-app my-app
cd my-app
# Copy api-service.js
# Add REACT_APP_API_BASE_URL to .env
npm start
```

### Next.js
```bash
npx create-next-app@latest my-app
cd my-app
# Copy api-service.js
# Add NEXT_PUBLIC_API_BASE_URL to .env.local
npm run dev
```

### Vue 3
```bash
npm create vue@latest my-app
cd my-app
npm install
# Copy api-service.js
# Add VITE_API_BASE_URL to .env
npm run dev
```

## 📚 Additional Resources

- **Backend API Docs**: http://localhost:8000/docs (when backend is running)
- **Full Integration Guide**: See `../FRONTEND_INTEGRATION.md`
- **Backend README**: See `../README.md`

## 💡 Tips

1. **Test with sample data**: Use the `test_sample.csv` from the backend repo
2. **Check backend health**: Visit http://localhost:8000/health
3. **View available tables**: Call `getSchema()` to see all supported tables
4. **Handle errors gracefully**: The API throws descriptive errors
5. **Show progress**: Use loading states for better UX

---

**Need help?** Check the comprehensive integration guide: `FRONTEND_INTEGRATION.md`
