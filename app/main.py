"""
FastAPI application with extraction endpoints
"""
import time
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict
import json

from app.models import ExtractionRequest, ExtractionResponse, BatchExtractionRequest, BatchExtractionResponse
from app.extraction_service import extraction_service

app = FastAPI(
    title="PDF Data Extraction API",
    description="Extract structured data from PDFs using LLM",
    version="1.0.0"
)

# Mount static files for frontend (only if directory exists)
import os
if os.path.exists("frontend/static"):
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve frontend HTML"""
    try:
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<html><body><h1>PDF Extraction API</h1><p>Frontend not found. Use /docs for API documentation.</p></body></html>"


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/extract", response_model=ExtractionResponse)
async def extract(
    label: str = Form(...),
    extraction_schema: str = Form(...),
    pdf: UploadFile = File(...)
):
    """
    Extract structured data from a single PDF
    
    Args:
        label: Document type identifier
        extraction_schema: JSON string with field names and descriptions
        pdf: PDF file to process
        
    Returns:
        ExtractionResponse with extracted data, cost, and timing
    """
    try:
        # Parse extraction schema
        try:
            schema_dict = json.loads(extraction_schema)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in extraction_schema")
        
        # Read PDF content
        pdf_content = await pdf.read()
        
        # Extract data
        result = extraction_service.extract(pdf_content, schema_dict, label)
        
        return ExtractionResponse(
            extracted_data=result["extracted_data"],
            cost=result["cost"],
            processing_time=result["processing_time"],
            cache_hit=result["cache_hit"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/extract-batch", response_model=BatchExtractionResponse)
async def extract_batch(batch_request: BatchExtractionRequest):
    """
    Process multiple extraction requests in batch.
    IMPORTANT: Processing is done SERIALLY (sequentially), one item at a time.
    Each item is processed completely and independently before moving to the next.
    The first item should be returned in less than 10 seconds.
    
    Args:
        batch_request: BatchExtractionRequest with list of extraction requests
        
    Returns:
        BatchExtractionResponse with all results and totals
    """
    import os
    
    start_time = time.time()
    results = []
    total_cost = 0.0
    
    # Process each request SERIALLY (one at a time, in sequence)
    # Each item is processed completely before moving to the next
    for item in batch_request.requests:
        try:
            # Read PDF from path
            pdf_path = item.pdf_path
            if not os.path.exists(pdf_path):
                # Try relative to files directory
                pdf_path = os.path.join("files", item.pdf_path)
                if not os.path.exists(pdf_path):
                    raise FileNotFoundError(f"PDF not found: {item.pdf_path}")
            
            with open(pdf_path, "rb") as f:
                pdf_content = f.read()
            
            # Extract data - processing happens sequentially (serially)
            # This ensures each request is processed independently and completely
            # before moving to the next one
            result = extraction_service.extract(pdf_content, item.extraction_schema, item.label)
            total_cost += result["cost"]
            
            # Append result immediately after processing (serial execution)
            results.append(ExtractionResponse(
                extracted_data=result["extracted_data"],
                cost=result["cost"],
                processing_time=result["processing_time"],
                cache_hit=result["cache_hit"]
            ))
        except Exception as e:
            # Continue processing other requests even if one fails
            results.append(ExtractionResponse(
                extracted_data={field: None for field in item.extraction_schema.keys()},
                cost=0.0,
                processing_time=0.0,
                cache_hit=False
            ))
    
    total_processing_time = time.time() - start_time
    
    return BatchExtractionResponse(
        results=results,
        total_cost=total_cost,
        total_processing_time=total_processing_time
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

