"""
Daana Ingestion Service - Main FastAPI Application
Converts messy CSV files to match the Daana-Rx database schema
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
from typing import Optional
import logging

from config import settings
from services.converter import converter

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Intelligent CSV conversion service for medical clinic data ingestion",
    debug=settings.debug
)

# Configure CORS - Allow all origins for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "healthy",
        "message": "Daana Ingestion Service is running"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "openai_configured": bool(settings.openai_api_key)
    }


@app.post("/convert")
async def convert_csv(
    file: UploadFile = File(..., description="CSV file to convert"),
    target_table: Optional[str] = Query(
        None, 
        description="Optional target table name (e.g., 'units', 'drugs', 'transactions')"
    ),
    return_metadata: bool = Query(
        False, 
        description="If true, return JSON with metadata instead of CSV file"
    )
):
    """
    Convert a messy CSV file to match the Daana-Rx database schema
    
    Args:
        file: The CSV file to convert (multipart/form-data)
        target_table: Optional specific table to target for mapping
        return_metadata: If true, returns JSON with mapping info instead of CSV
    
    Returns:
        - If return_metadata=false: Cleaned CSV file as download
        - If return_metadata=true: JSON with cleaned CSV, mapping, and unmapped columns
    
    Example usage:
        curl -X POST "http://localhost:8000/convert" \\
             -F "file=@messy_data.csv" \\
             -F "target_table=units"
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Only CSV files are accepted."
            )
        
        logger.info(f"Processing file: {file.filename}, target_table: {target_table}")
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        
        # Convert the CSV
        cleaned_csv, column_mapping, unmapped_columns = await converter.smart_convert_csv(
            file_content=file_content,
            target_table=target_table
        )
        
        logger.info(f"Conversion successful. Mapped {len(column_mapping)} columns, "
                   f"{len(unmapped_columns)} unmapped")
        
        # Return metadata if requested
        if return_metadata:
            return JSONResponse(content={
                "success": True,
                "original_filename": file.filename,
                "target_table": target_table,
                "column_mapping": column_mapping,
                "unmapped_columns": unmapped_columns,
                "mapped_count": len(column_mapping),
                "unmapped_count": len(unmapped_columns),
                "cleaned_csv": cleaned_csv
            })
        
        # Otherwise return CSV file for download
        output_filename = f"cleaned_{file.filename}"
        
        return StreamingResponse(
            BytesIO(cleaned_csv.encode('utf-8')),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={output_filename}",
                "X-Mapped-Columns": str(len(column_mapping)),
                "X-Unmapped-Columns": str(len(unmapped_columns))
            }
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to convert CSV: {str(e)}"
        )


@app.get("/schema")
async def get_schema():
    """
    Get the target database schema information
    
    Returns:
        JSON representation of the target schema
    """
    from schema import TARGET_SCHEMA
    
    return {
        "schema": TARGET_SCHEMA,
        "tables": list(TARGET_SCHEMA.keys())
    }


@app.get("/schema/{table_name}")
async def get_table_schema(table_name: str):
    """
    Get schema information for a specific table
    
    Args:
        table_name: Name of the table (e.g., 'units', 'drugs')
    
    Returns:
        Schema information for the specified table
    """
    from schema import TARGET_SCHEMA
    
    if table_name not in TARGET_SCHEMA:
        raise HTTPException(
            status_code=404, 
            detail=f"Table '{table_name}' not found in schema. "
                   f"Available tables: {', '.join(TARGET_SCHEMA.keys())}"
        )
    
    return {
        "table": table_name,
        "schema": TARGET_SCHEMA[table_name]
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
