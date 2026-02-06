import { useState, useEffect } from 'react';
import { convertCSV, downloadConvertedCSV, getTableList, healthCheck } from '../services/api';
import './CSVUploader.css';

/**
 * CSV Upload and Conversion Component
 * 
 * Features:
 * - File upload with drag & drop
 * - Target table selection
 * - Conversion with metadata display
 * - Automatic download of cleaned CSV
 * - Backend health check
 */
export default function CSVUploader() {
  const [file, setFile] = useState(null);
  const [targetTable, setTargetTable] = useState('');
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [backendStatus, setBackendStatus] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  // Check backend health on mount
  useEffect(() => {
    async function checkBackend() {
      try {
        const health = await healthCheck();
        setBackendStatus(health);
        
        // Load available tables
        const tableList = await getTableList();
        setTables(tableList);
      } catch (err) {
        setError('Backend is not available. Please start the backend service.');
      }
    }
    
    checkBackend();
  }, []);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files[0]);
    }
  };

  const handleFiles = (selectedFile) => {
    if (selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile);
      setError(null);
      setResult(null);
    } else {
      setError('Please select a CSV file');
      setFile(null);
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
      // Get metadata to show mapping
      const metadata = await convertCSV(file, targetTable || null, true);
      setResult(metadata);
      
      // Download the cleaned CSV
      await downloadConvertedCSV(file, targetTable || null);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="csv-uploader">
      {/* Backend Status */}
      {backendStatus && (
        <div className="backend-status">
          <span className="status-indicator status-healthy"></span>
          Backend Connected: {backendStatus.service} v{backendStatus.version}
        </div>
      )}

      <h2>📊 CSV Data Ingestion</h2>
      <p className="subtitle">Upload messy clinic data, get clean structured CSV</p>
      
      <form onSubmit={handleSubmit}>
        {/* File Drop Zone */}
        <div 
          className={`drop-zone ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="file-input"
            accept=".csv"
            onChange={handleFileChange}
            disabled={loading}
            style={{ display: 'none' }}
          />
          
          {!file ? (
            <label htmlFor="file-input" className="drop-zone-label">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              <p>Drag & drop CSV file here or click to browse</p>
            </label>
          ) : (
            <div className="file-info">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              <div>
                <p className="file-name">{file.name}</p>
                <p className="file-size">{(file.size / 1024).toFixed(2)} KB</p>
              </div>
              <button 
                type="button" 
                onClick={() => setFile(null)}
                className="remove-file"
                disabled={loading}
              >
                ✕
              </button>
            </div>
          )}
        </div>

        {/* Target Table Selection */}
        <div className="form-group">
          <label htmlFor="targetTable">
            Target Table (Optional)
            <span className="label-hint">AI will auto-detect if not specified</span>
          </label>
          <select
            id="targetTable"
            value={targetTable}
            onChange={(e) => setTargetTable(e.target.value)}
            disabled={loading}
          >
            <option value="">Auto-detect</option>
            {tables.map(table => (
              <option key={table} value={table}>
                {table}
              </option>
            ))}
          </select>
        </div>

        {/* Submit Button */}
        <button 
          type="submit" 
          disabled={!file || loading}
          className="submit-button"
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              Converting...
            </>
          ) : (
            '🚀 Convert CSV'
          )}
        </button>
      </form>

      {/* Error Display */}
      {error && (
        <div className="alert alert-error">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" stroke="white" strokeWidth="2" />
            <line x1="12" y1="16" x2="12.01" y2="16" stroke="white" strokeWidth="2" />
          </svg>
          <div>
            <h4>Error</h4>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Success Result */}
      {result && (
        <div className="alert alert-success">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" stroke="white" strokeWidth="2" />
          </svg>
          <div>
            <h4>✅ Conversion Successful!</h4>
            <p>File downloaded: cleaned_{file.name}</p>
            <p className="stats">
              Mapped {result.mapped_count} columns
              {result.unmapped_count > 0 && `, ${result.unmapped_count} unmapped`}
            </p>
          </div>
        </div>
      )}

      {/* Mapping Details */}
      {result && (
        <div className="results-panel">
          <h3>Column Mapping</h3>
          <div className="mapping-table">
            <div className="mapping-header">
              <div>Original Column</div>
              <div>→</div>
              <div>Target Column</div>
            </div>
            {Object.entries(result.column_mapping).map(([orig, target]) => (
              <div key={orig} className="mapping-row">
                <div className="original-col">{orig}</div>
                <div className="arrow">→</div>
                <div className="target-col"><code>{target}</code></div>
              </div>
            ))}
          </div>

          {result.unmapped_columns.length > 0 && (
            <div className="unmapped-section">
              <h4>⚠️ Unmapped Columns</h4>
              <p>These columns were not matched to the schema:</p>
              <div className="unmapped-list">
                {result.unmapped_columns.map(col => (
                  <span key={col} className="unmapped-tag">{col}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
