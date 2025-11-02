#!/usr/bin/env python3
"""
Test script for PDF extraction system
Validates extraction with provided dataset
"""
import json
import os
import time
from pathlib import Path

from app.extraction_service import extraction_service


def test_extraction():
    """Test extraction with dataset.json"""
    
    # Load dataset
    dataset_path = "dataset.json"
    if not os.path.exists(dataset_path):
        print(f"Error: {dataset_path} not found")
        return False
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    print(f"Testing with {len(dataset)} documents from dataset.json")
    print("=" * 70)
    
    results = []
    total_cost = 0.0
    total_time = 0.0
    cache_hits = 0
    
    for i, item in enumerate(dataset, 1):
        label = item.get('label', 'unknown')
        schema = item.get('extraction_schema', {})
        pdf_path = item.get('pdf_path', '')
        
        # Construct full path
        full_path = os.path.join('files', pdf_path)
        if not os.path.exists(full_path):
            print(f"[{i}/{len(dataset)}] ERROR: PDF not found: {full_path}")
            results.append({
                'label': label,
                'pdf_path': pdf_path,
                'success': False,
                'error': 'PDF not found'
            })
            continue
        
        # Read PDF
        with open(full_path, 'rb') as f:
            pdf_content = f.read()
        
        # Extract
        start = time.time()
        try:
            result = extraction_service.extract(pdf_content, schema, label)
            elapsed = time.time() - start
            
            total_cost += result['cost']
            total_time += result['processing_time']
            if result['cache_hit']:
                cache_hits += 1
            
            # Count extracted fields
            extracted_fields = sum(1 for v in result['extracted_data'].values() if v is not None)
            total_fields = len(schema)
            
            status = "✓" if extracted_fields > 0 else "✗"
            
            print(f"[{i}/{len(dataset)}] {status} {label:20s} | "
                  f"{pdf_path:25s} | "
                  f"Time: {result['processing_time']:6.3f}s | "
                  f"Cost: ${result['cost']:8.6f} | "
                  f"Fields: {extracted_fields}/{total_fields} | "
                  f"Cache: {'HIT' if result['cache_hit'] else 'MISS'}")
            
            results.append({
                'label': label,
                'pdf_path': pdf_path,
                'success': True,
                'extracted_fields': extracted_fields,
                'total_fields': total_fields,
                'processing_time': result['processing_time'],
                'cost': result['cost'],
                'cache_hit': result['cache_hit'],
                'extracted_data': result['extracted_data']
            })
        except Exception as e:
            print(f"[{i}/{len(dataset)}] ✗ ERROR: {str(e)}")
            results.append({
                'label': label,
                'pdf_path': pdf_path,
                'success': False,
                'error': str(e)
            })
    
    # Save results to a JSON file
    with open(f'results_{i}.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to: results_{i}.json")
    
    # Summary
    print("=" * 70)
    print("\nSUMMARY:")
    print(f"  Total documents: {len(dataset)}")
    print(f"  Successful: {len([r for r in results if r.get('success')])}")
    print(f"  Failed: {len([r for r in results if not r.get('success')])}")
    print(f"  Total processing time: {total_time:.3f}s")
    print(f"  Average time per document: {total_time/len(dataset):.3f}s")
    print(f"  Total cost: ${total_cost:.6f}")
    print(f"  Average cost per document: ${total_cost/len(dataset):.6f}")
    print(f"  Cache hits: {cache_hits}/{len(dataset)} ({cache_hits*100/len(dataset):.1f}%)")
    
    # Check time requirement (<10s per document)
    avg_time = total_time / len(dataset)
    if avg_time < 10:
        print(f"  ✓ Time requirement (<10s per document) met!")
    else:
        print(f"  ✗ Average time exceeds 10s requirement")
    
    return True


if __name__ == "__main__":
    print("\nPDF Extraction System - Test Suite")
    print("=" * 70)
    print()
    
    success = test_extraction()
    
    if success:
        print("\n✓ Test completed")
    else:
        print("\n✗ Test failed")
        exit(1)

