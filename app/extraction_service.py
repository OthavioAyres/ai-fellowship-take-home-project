"""
Core extraction service orchestrating PDF → Cache → LLM → Response
"""
import time
from typing import Dict, Optional
from app.pdf_extractor import extract_text_from_pdf
from app.llm_service import get_llm_service
from app.cache_service import cache_service


class ExtractionService:
    """Main extraction service coordinating all components"""
    
    def extract(
        self,
        pdf_content: bytes,
        extraction_schema: Dict[str, str],
        label: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Extract data from PDF with caching
        
        Args:
            pdf_content: PDF file content as bytes
            extraction_schema: Dictionary of field names and descriptions
            
        Returns:
            Dictionary with extracted_data, cost, processing_time, cache_hit
        """
        start_time = time.time()
        cache_hit = False
        
        # Check cache first
        cached_result = cache_service.get(pdf_content, extraction_schema)
        if cached_result:
            cache_hit = True
            processing_time = time.time() - start_time
            return {
                "extracted_data": cached_result["extracted_data"],
                "cost": cached_result.get("cost", 0.0),
                "processing_time": processing_time,
                "cache_hit": True
            }
        
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_content)
        if not text:
            processing_time = time.time() - start_time
            return {
                "extracted_data": {field: None for field in extraction_schema.keys()},
                "cost": 0.0,
                "processing_time": processing_time,
                "cache_hit": False
            }
        
        # Extract data using LLM
        llm_service = get_llm_service()
        extracted_data, cost = llm_service.extract_data(text, extraction_schema, label)
        
        # Cache the result
        result = {
            "extracted_data": extracted_data,
            "cost": cost,
            "processing_time": time.time() - start_time,
            "cache_hit": False
        }
        cache_service.set(pdf_content, extraction_schema, result)
        
        return result


# Global extraction service instance
extraction_service = ExtractionService()

