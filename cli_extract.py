#!/usr/bin/env python3
"""
CLI script for batch PDF extraction
Supports JSON file input and folder-based processing
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

from app.extraction_service import extraction_service
from app.models import BatchItem, ExtractionResponse


def load_batch_json(json_path: str) -> list:
    """Load batch requests from JSON file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError("JSON file must contain an array of requests")
    
    return data


def process_batch(batch_data: list, base_dir: str = "files") -> list:
    """
    Process batch of extraction requests SERIALLY (sequentially).
    Each item is processed completely and independently before moving to the next.
    
    Args:
        batch_data: List of dictionaries with label, extraction_schema, pdf_path
        base_dir: Base directory for PDF files
        
    Returns:
        List of extraction results
    """
    results = []
    total_cost = 0.0
    start_time = time.time()
    
    print(f"Processing {len(batch_data)} documents SERIALLY (one at a time)...")
    print("-" * 60)
    
    # Process each item SERIALLY - one at a time, in sequence
    # Each item is processed completely before moving to the next
    for i, item in enumerate(batch_data, 1):
        try:
            # Construct PDF path
            pdf_path = item.get('pdf_path', '')
            if not os.path.isabs(pdf_path):
                pdf_path = os.path.join(base_dir, pdf_path)
            
            if not os.path.exists(pdf_path):
                print(f"[{i}/{len(batch_data)}] ERROR: PDF not found: {pdf_path}")
                results.append({
                    "label": item.get('label', 'unknown'),
                    "pdf_path": item.get('pdf_path', ''),
                    "error": f"PDF not found: {pdf_path}",
                    "extracted_data": None
                })
                continue
            
            # Read PDF
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Extract data - processing happens SERIALLY (sequentially)
            # Each request is processed independently and completely before the next
            extraction_schema = item.get('extraction_schema', {})
            label = item.get('label', None)
            result = extraction_service.extract(pdf_content, extraction_schema, label)
            
            total_cost += result['cost']
            
            print(f"[{i}/{len(batch_data)}] {item.get('label', 'unknown')} - "
                  f"{result['processing_time']:.3f}s - "
                  f"${result['cost']:.6f} - "
                  f"{'CACHE' if result['cache_hit'] else 'LLM'}")
            
            results.append({
                "label": item.get('label', 'unknown'),
                "pdf_path": item.get('pdf_path', ''),
                "extracted_data": result['extracted_data'],
                "cost": result['cost'],
                "processing_time": result['processing_time'],
                "cache_hit": result['cache_hit']
            })
            
        except Exception as e:
            print(f"[{i}/{len(batch_data)}] ERROR: {str(e)}")
            results.append({
                "label": item.get('label', 'unknown'),
                "pdf_path": item.get('pdf_path', ''),
                "error": str(e),
                "extracted_data": None
            })
    
    total_time = time.time() - start_time
    print("-" * 60)
    print(f"Total: {len(batch_data)} documents")
    print(f"Total time: {total_time:.3f}s")
    print(f"Total cost: ${total_cost:.6f}")
    print(f"Average time per document: {total_time/len(batch_data):.3f}s")
    print(f"Average cost per document: ${total_cost/len(batch_data):.6f}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Batch PDF data extraction CLI tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli_extract.py --json dataset.json
  python cli_extract.py --json dataset.json --output results.json
  python cli_extract.py --json dataset.json --base-dir /path/to/pdfs
        """
    )
    
    parser.add_argument(
        '--json',
        type=str,
        required=True,
        help='Path to JSON file with batch extraction requests'
    )
    
    parser.add_argument(
        '--base-dir',
        type=str,
        default='files',
        help='Base directory for PDF files (default: files)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output JSON file path (default: print to stdout)'
    )
    
    args = parser.parse_args()
    
    # Validate JSON file exists
    if not os.path.exists(args.json):
        print(f"Error: JSON file not found: {args.json}")
        sys.exit(1)
    
    # Load batch data
    try:
        batch_data = load_batch_json(args.json)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        sys.exit(1)
    
    if not batch_data:
        print("Error: JSON file is empty or contains no requests")
        sys.exit(1)
    
    # Process batch
    try:
        results = process_batch(batch_data, args.base_dir)
        
        # Output results
        output_data = {
            "results": results,
            "summary": {
                "total_documents": len(batch_data),
                "successful": len([r for r in results if r.get('extracted_data') is not None]),
                "failed": len([r for r in results if r.get('error') is not None])
            }
        }
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to: {args.output}")
        else:
            print("\nResults:")
            print(json.dumps(output_data, indent=2, ensure_ascii=False))
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError processing batch: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

