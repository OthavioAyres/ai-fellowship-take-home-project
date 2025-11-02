"""
In-memory caching service for extraction results
Uses PDF content hash + extraction_schema hash as composite key
"""
import hashlib
import json
from typing import Optional, Dict, Any


class CacheService:
    """In-memory cache for extraction results"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def _generate_key(self, pdf_content: bytes, extraction_schema: dict) -> str:
        """
        Generate cache key from PDF content and extraction schema
        
        Args:
            pdf_content: PDF file content as bytes
            extraction_schema: Dictionary of field names and descriptions
            
        Returns:
            Cache key as string (hash of PDF + schema)
        """
        # Hash PDF content
        pdf_hash = hashlib.sha256(pdf_content).hexdigest()
        
        # Hash extraction schema (normalize by sorting keys)
        schema_str = json.dumps(extraction_schema, sort_keys=True)
        schema_hash = hashlib.sha256(schema_str.encode()).hexdigest()
        
        # Composite key
        return f"{pdf_hash}:{schema_hash}"
    
    def get(self, pdf_content: bytes, extraction_schema: dict) -> Optional[Dict[str, Any]]:
        """
        Get cached extraction result
        
        Args:
            pdf_content: PDF file content as bytes
            extraction_schema: Dictionary of field names and descriptions
            
        Returns:
            Cached result dictionary or None if not found
        """
        key = self._generate_key(pdf_content, extraction_schema)
        return self._cache.get(key)
    
    def set(self, pdf_content: bytes, extraction_schema: dict, result: Dict[str, Any]) -> None:
        """
        Cache extraction result
        
        Args:
            pdf_content: PDF file content as bytes
            extraction_schema: Dictionary of field names and descriptions
            result: Extraction result to cache
        """
        key = self._generate_key(pdf_content, extraction_schema)
        self._cache[key] = result
    
    def clear(self) -> None:
        """Clear all cached results"""
        self._cache.clear()
    
    def size(self) -> int:
        """Get number of cached entries"""
        return len(self._cache)


# Global cache instance
cache_service = CacheService()

