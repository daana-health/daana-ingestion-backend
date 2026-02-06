/**
 * Daana Ingestion API Client
 * 
 * Copy this file to your frontend project: src/services/api.js
 * 
 * Usage:
 *   import { convertCSV, getSchema } from './services/api';
 */

// Configure your backend URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
                     process.env.REACT_APP_API_BASE_URL || 
                     process.env.NEXT_PUBLIC_API_BASE_URL ||
                     'http://localhost:8000';

/**
 * Upload and convert CSV file
 * @param {File} file - The CSV file to upload
 * @param {string} targetTable - Optional target table (e.g., 'units', 'drugs')
 * @param {boolean} returnMetadata - If true, return JSON metadata instead of CSV
 * @returns {Promise<Object|Blob>} - Response data or CSV blob
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
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to convert CSV');
  }

  if (returnMetadata) {
    return await response.json();
  } else {
    return await response.blob();
  }
}

/**
 * Download converted CSV file
 * @param {File} file - The CSV file to convert
 * @param {string} targetTable - Optional target table
 * @param {string} downloadFilename - Optional custom filename
 */
export async function downloadConvertedCSV(file, targetTable = null, downloadFilename = null) {
  const blob = await convertCSV(file, targetTable, false);
  
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = downloadFilename || `cleaned_${file.name}`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

/**
 * Get database schema for all tables
 * @returns {Promise<Object>} - Complete schema information
 */
export async function getSchema() {
  const response = await fetch(`${API_BASE_URL}/schema`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch schema');
  }
  
  return await response.json();
}

/**
 * Get schema for a specific table
 * @param {string} tableName - Name of the table
 * @returns {Promise<Object>} - Table schema information
 */
export async function getTableSchema(tableName) {
  const response = await fetch(`${API_BASE_URL}/schema/${tableName}`);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Table not found' }));
    throw new Error(error.detail || 'Failed to fetch table schema');
  }
  
  return await response.json();
}

/**
 * Check backend health status
 * @returns {Promise<Object>} - Health status information
 */
export async function healthCheck() {
  const response = await fetch(`${API_BASE_URL}/health`);
  
  if (!response.ok) {
    throw new Error('Backend is not available');
  }
  
  return await response.json();
}

/**
 * Get list of available tables
 * @returns {Promise<string[]>} - Array of table names
 */
export async function getTableList() {
  const schema = await getSchema();
  return schema.tables || [];
}

// Export API base URL for reference
export { API_BASE_URL };
