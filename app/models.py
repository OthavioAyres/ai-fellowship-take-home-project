"""
Pydantic models for request and response validation
"""
from typing import Dict, Optional, List
from pydantic import BaseModel


class ExtractionRequest(BaseModel):
    """Request model for single extraction"""
    label: str
    extraction_schema: Dict[str, str]


class ExtractionResponse(BaseModel):
    """Response model for extraction results"""
    extracted_data: Dict[str, Optional[str]]
    cost: float = 0.0
    processing_time: float = 0.0
    cache_hit: bool = False


class BatchItem(BaseModel):
    """Single item in batch request"""
    label: str
    extraction_schema: Dict[str, str]
    pdf_path: str


class BatchExtractionRequest(BaseModel):
    """Request model for batch extraction"""
    requests: List[BatchItem]


class BatchExtractionResponse(BaseModel):
    """Response model for batch extraction"""
    results: List[ExtractionResponse]
    total_cost: float = 0.0
    total_processing_time: float = 0.0

