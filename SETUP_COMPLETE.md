# ✅ Setup Complete: Frontend ↔️ Backend Integration

Your Daana Ingestion system is ready! Here's everything you need to connect your frontend to the backend.

## 📦 What You Have

### Backend (This Repository)
✅ FastAPI application with AI-powered CSV conversion  
✅ OpenAI GPT-4 integration for smart column mapping  
✅ Complete Daana-Rx schema (7 tables)  
✅ CORS enabled for frontend communication  
✅ RESTful API endpoints  
✅ Docker support  
✅ Comprehensive documentation  

### Frontend Integration Resources
✅ Ready-to-use API client (`frontend-examples/api-service.js`)  
✅ Complete React component with styling  
✅ Detailed integration guide  
✅ Example code for all frameworks  

## 🚀 Quick Integration (3 Steps)

### Step 1: Start the Backend

```bash
cd daana-ingestion-backend
source venv/bin/activate
python main.py
```

Backend will run at: **http://localhost:8000**

### Step 2: Setup Your Frontend

In your **separate frontend repository**:

```bash
# 1. Copy the API client
cp path/to/daana-ingestion-backend/frontend-examples/api-service.js src/services/api.js

# 2. Create .env file
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
# OR for CRA: REACT_APP_API_BASE_URL=http://localhost:8000
# OR for Next.js: NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# 3. Start your frontend
npm run dev
```

### Step 3: Use the API in Your Components

```javascript
import { convertCSV, downloadConvertedCSV } from './services/api';

// Upload and convert CSV
const handleUpload = async (file) => {
  // Get metadata
  const result = await convertCSV(file, 'units', true);
  console.log('Mapping:', result.column_mapping);
  
  // Download cleaned CSV
  await downloadConvertedCSV(file, 'units');
};
```

## 📂 File Locations

### Copy to Your Frontend:

| Source File | Destination in Frontend |
|------------|------------------------|
| `frontend-examples/api-service.js` | `src/services/api.js` |
| `frontend-examples/react/CSVUploader.jsx` | `src/components/CSVUploader.jsx` |
| `frontend-examples/react/CSVUploader.css` | `src/components/CSVUploader.css` |

### Reference Documentation:

| File | Purpose |
|------|---------|
| `FRONTEND_INTEGRATION.md` | Complete integration guide |
| `frontend-examples/README.md` | Quick start for examples |
| `README.md` | Backend documentation |

## 🎯 API Endpoints

Your frontend can call these endpoints:

```
POST   http://localhost:8000/convert
       Upload CSV file, get cleaned version

GET    http://localhost:8000/schema
       Get all table schemas

GET    http://localhost:8000/schema/{table}
       Get specific table schema

GET    http://localhost:8000/health
       Check backend status
```

## 💡 Example: Complete React Component

Copy the full component with styling:

```bash
# From your frontend repo
cp path/to/daana-ingestion-backend/frontend-examples/react/CSVUploader.jsx src/components/
cp path/to/daana-ingestion-backend/frontend-examples/react/CSVUploader.css src/components/
```

Then use it:

```jsx
import CSVUploader from './components/CSVUploader';

function App() {
  return (
    <div className="App">
      <h1>Daana Data Ingestion</h1>
      <CSVUploader />
    </div>
  );
}
```

The component includes:
- 📤 Drag & drop file upload
- 🎯 Target table selection
- 🔄 Real-time conversion
- 📊 Mapping visualization
- ⚠️ Error handling
- 💾 Automatic download

## 🔧 Environment Configuration

### Backend (.env - already configured):
```env
OPENAI_API_KEY=your_key_here
APP_NAME=Daana Ingestion Service
PORT=8000
```

### Frontend (.env - add to your frontend repo):
```env
# For Vite
VITE_API_BASE_URL=http://localhost:8000

# For Create React App
REACT_APP_API_BASE_URL=http://localhost:8000

# For Next.js
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## 🎨 Sample Usage in Frontend

### Basic Upload
```javascript
import { convertCSV } from './services/api';

const file = document.getElementById('file').files[0];
const result = await convertCSV(file, 'units', true);

console.log('Converted!', result.column_mapping);
```

### With React Hook
```javascript
import { useState } from 'react';
import { convertCSV } from './services/api';

function MyComponent() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);

  const handleSubmit = async () => {
    const data = await convertCSV(file, 'units', true);
    setResult(data);
  };

  return (
    <>
      <input 
        type="file" 
        onChange={(e) => setFile(e.target.files[0])} 
      />
      <button onClick={handleSubmit}>Convert</button>
      {result && <div>Success! Mapped {result.mapped_count} columns</div>}
    </>
  );
}
```

### View Schema
```javascript
import { getSchema, getTableSchema } from './services/api';

// Get all tables
const schema = await getSchema();
console.log('Tables:', schema.tables);

// Get specific table
const unitsSchema = await getTableSchema('units');
console.log('Columns:', unitsSchema.schema.columns);
```

## ✅ Testing the Connection

### 1. Test Backend Health
```bash
curl http://localhost:8000/health
```

Or in your frontend:
```javascript
import { healthCheck } from './services/api';

const health = await healthCheck();
console.log(health); // { status: 'healthy', service: 'Daana Ingestion Service' }
```

### 2. Test File Upload
```bash
curl -X POST "http://localhost:8000/convert?return_metadata=true" \
  -F "file=@test_sample.csv" \
  -F "target_table=units"
```

### 3. Test from Frontend
Use the sample CSV file included in the backend repo.

## 🎓 Supported Tables

Your backend supports all Daana-Rx tables:
- **clinics** - Clinic information
- **users** - User accounts
- **locations** - Storage locations
- **lots** - Medication lots
- **drugs** - Drug database (NDC)
- **units** - Inventory units
- **transactions** - Inventory transactions

## 📊 Example API Response

When you upload a CSV, the API returns:

```json
{
  "success": true,
  "original_filename": "clinic_data.csv",
  "target_table": "units",
  "column_mapping": {
    "Med Name": "medication_name",
    "NDC": "ndc_id",
    "Exp Date": "expiry_date",
    "Qty": "total_quantity"
  },
  "unmapped_columns": ["Internal Notes"],
  "mapped_count": 4,
  "unmapped_count": 1,
  "cleaned_csv": "medication_name,ndc_id,expiry_date,total_quantity\n..."
}
```

## 🐛 Troubleshooting

### Backend not accessible from frontend?
1. Ensure backend is running: `python main.py`
2. Check it responds: `curl http://localhost:8000/health`
3. Verify CORS is enabled (it is by default)

### CORS errors in browser?
- Backend has CORS enabled for all origins by default
- Check browser console for specific error
- Ensure you're using the correct URL in `.env`

### API calls failing?
```javascript
// Add error handling
try {
  const result = await convertCSV(file, 'units', true);
  console.log('Success:', result);
} catch (error) {
  console.error('Failed:', error.message);
}
```

## 📚 Documentation Reference

| Document | Purpose |
|----------|---------|
| `FRONTEND_INTEGRATION.md` | Comprehensive frontend integration guide |
| `frontend-examples/README.md` | Quick start with example code |
| `README.md` | Backend API documentation |
| `QUICKSTART.md` | Backend setup guide |
| `ARCHITECTURE.md` | System architecture |
| `PROJECT_SUMMARY.md` | Project overview |

## 🎯 Deployment Checklist

### Development (Both Local)
- [x] Backend: `python main.py` (port 8000)
- [x] Frontend: `npm run dev` (port 5173)
- [x] `.env` configured in both repos

### Production
- [ ] Backend: Deploy to cloud (AWS, GCP, etc.)
- [ ] Frontend: Deploy to hosting (Vercel, Netlify, etc.)
- [ ] Update `VITE_API_BASE_URL` to production backend URL
- [ ] Update CORS to specific frontend origin
- [ ] Add authentication if needed

## 🔐 Security Notes

### Current (Development)
- CORS allows all origins (`*`)
- No authentication required
- API key secured in backend `.env`

### Production Recommendations
- Restrict CORS to your frontend domain
- Add API authentication (JWT, API keys)
- Use HTTPS for all communication
- Implement rate limiting
- Add request validation

## 🚀 Next Steps

1. **Copy Files**: Copy `api-service.js` to your frontend
2. **Configure**: Add `.env` with backend URL
3. **Test**: Upload a CSV and verify it works
4. **Customize**: Adjust UI to match your design
5. **Deploy**: Push to production when ready

## 💪 You're All Set!

Everything is ready for frontend-backend integration:

```
Frontend Repo                    Backend Repo (This)
     │                                  │
     │  HTTP Requests                   │
     ├─────────────────────────────────▶│
     │  POST /convert                   │ FastAPI
     │  (CSV file)                      │ + OpenAI
     │                                  │ + Schema
     │  JSON Response                   │
     │◀─────────────────────────────────┤
     │  (Clean CSV + mapping)           │
     │                                  │
```

**Questions?** Check:
- `FRONTEND_INTEGRATION.md` - Complete guide
- `frontend-examples/README.md` - Quick examples
- API docs: http://localhost:8000/docs

---

**Backend**: http://localhost:8000  
**Frontend**: Your separate repository  
**Communication**: RESTful API with JSON  
**Status**: ✅ Ready to integrate!
