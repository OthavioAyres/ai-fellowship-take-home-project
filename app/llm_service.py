"""
OpenAI LLM service with optimized prompts for data extraction
Uses GPT-5-mini for extraction
"""
import json
import os
from typing import Dict, Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    """OpenAI LLM service for structured data extraction"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Initialize OpenAI client with explicit api_key parameter only
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-5-mini"  # Cost-effective model as specified
    
    def extract_data(
        self, 
        text: str, 
        extraction_schema: Dict[str, str],
        label: Optional[str] = None
    ) -> Tuple[Dict[str, Optional[str]], float]:
        """
        Extract structured data from text using LLM
        
        Args:
            text: Extracted PDF text
            extraction_schema: Dictionary mapping field names to descriptions
            
        Returns:
            Tuple of (extracted_data dictionary, cost in USD)
        """
        # Build optimized prompt
        prompt = self._build_prompt(text, extraction_schema, label)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data extraction assistant. Extract information from the given text and return ONLY valid JSON. If a field cannot be found, return null for that field."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
            )
            
            # Calculate cost for gpt-5-mini
            # Pricing: Input: $0.075 per 1M tokens, Output: $0.30 per 1M tokens
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = (input_tokens * 0.075 / 1_000_000) + (output_tokens * 0.30 / 1_000_000)
            
            # Parse response
            result_json = json.loads(response.choices[0].message.content)
            
            # Ensure all schema fields are present
            extracted_data = {}
            for field in extraction_schema.keys():
                extracted_data[field] = result_json.get(field)
            
            return extracted_data, cost
            
        except Exception as e:
            print(f"Error in LLM extraction: {e}")
            # Return null values for all fields on error
            return {field: None for field in extraction_schema.keys()}, 0.0
    
    def _build_prompt(self, text: str, extraction_schema: Dict[str, str], label: Optional[str] = None) -> str:
        """
        Build optimized prompt with minimal tokens
        
        Args:
            text: PDF text content
            extraction_schema: Field descriptions
            label: Document type identifier (optional)
            
        Returns:
            Optimized prompt string
        """
        # Build field descriptions (minimal format)
        schema_parts = []
        for field, description in extraction_schema.items():
            schema_parts.append(f'"{field}": {description}')
        
        schema_text = "\n".join(schema_parts)
        
        # Add label information to prompt if available
        label_context = ""
        if label:
            label_context = f"\nDocument type (label): {label}\n"
        
        prompt = f"""Extract the following fields from this text. Return JSON only.{label_context}

Fields to extract:
{schema_text}

Text:
{text}"""
        
        return prompt


# Global LLM service instance (lazy initialization)
_llm_service = None

def get_llm_service() -> LLMService:
    """Get or create LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

