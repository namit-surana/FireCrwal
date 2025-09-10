#!/usr/bin/env python3
import json
import os
import sys
from urllib.parse import urlparse
from marker_convert import convert_to_markdown


def parse_eu_compliance_json(json_file_path):
    """
    Parse EU compliance JSON file and return processed data.
    
    For non-PDF URLs: keep url and markdown as is
    For PDF URLs: use convert_to_markdown and save markdown for PDF url
    
    Args:
        json_file_path (str): Path to the JSON file
        
    Returns:
        list: List of dictionaries with 'url' and 'markdown' keys
    """
    
    # Load the JSON file
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {json_file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format: {e}")
        return []
    
    # Extract results from the JSON structure
    if 'results' not in data or 'data' not in data['results']:
        print("Error: Invalid JSON structure - missing 'results.data'")
        return []
    
    results = []
    items = data['results']['data']
    
    print(f"Processing {len(items)} items...")
    
    for i, item in enumerate(items):
        if 'url' not in item:
            print(f"Warning: Item {i+1} missing URL, skipping...")
            continue
        
        url = item['url']
        print(f"\nProcessing item {i+1}: {url}")
        
        # Check if URL is a PDF (case insensitive)
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        # Check multiple indicators for PDF files
        is_pdf = (path.endswith('.pdf') or 
                 'pdf' in url.lower() or 
                 ('content-type' in item and 'pdf' in item.get('content-type', '').lower()))
        
        if is_pdf:
            print(f"  -> PDF detected, converting to markdown...")
            
            # Use convert_to_markdown for PDF URLs with retry logic
            max_retries = 2
            markdown_content = None
            
            for retry in range(max_retries + 1):
                try:
                    if retry > 0:
                        print(f"  -> Retry attempt {retry}/{max_retries}")
                    
                    markdown_content = convert_to_markdown(url)
                    if markdown_content and len(markdown_content.strip()) > 0:
                        print(f"  -> Successfully converted PDF to markdown ({len(markdown_content)} chars)")
                        break
                    else:
                        print(f"  -> PDF conversion returned empty content")
                        if retry < max_retries:
                            continue
                except Exception as e:
                    print(f"  -> Error converting PDF (attempt {retry+1}): {e}")
                    if retry < max_retries:
                        continue
            
            # Save result if conversion was successful
            if markdown_content and len(markdown_content.strip()) > 0:
                results.append({
                    'url': url,
                    'markdown': markdown_content
                })
            else:
                print(f"  -> Failed to convert PDF after {max_retries + 1} attempts")
                # Fall back to existing markdown if available
                if 'markdown' in item and item['markdown'].strip():
                    print(f"  -> Using existing markdown as fallback")
                    results.append({
                        'url': url,
                        'markdown': item['markdown']
                    })
                else:
                    print(f"  -> No fallback available, skipping item")
        else:
            print(f"  -> Non-PDF, using existing markdown")
            # For non-PDF URLs, use existing markdown
            markdown_content = item.get('markdown', '')
            results.append({
                'url': url,
                'markdown': markdown_content
            })
    
    print(f"\nCompleted processing. Total results: {len(results)}")
    return results


def save_processed_data(results, output_file_path):
    """
    Save processed results to a JSON file.
    
    Args:
        results (list): List of processed data
        output_file_path (str): Output file path
    """
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Processed data saved to: {output_file_path}")
    except Exception as e:
        print(f"Error saving processed data: {e}")


if __name__ == "__main__":
    # Default file path
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    default_input = "eu_compliance_results.json"
    
    # Use command line argument if provided, otherwise use default
    input_file = sys.argv[1] if len(sys.argv) > 1 else default_input
    
    # Generate output file name
    input_dir = os.path.dirname(input_file)
    input_name = os.path.basename(input_file)
    output_name = input_name.replace('.json', '_processed.json')
    output_file = os.path.join(input_dir, output_name)
    
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    
    # Process the data
    processed_results = parse_eu_compliance_json(input_file)
    
    if processed_results:
        # Save processed data
        save_processed_data(processed_results, output_file)
        
        # Display summary
        pdf_count = 0
        non_pdf_count = 0
        
        for item in processed_results:
            url = item['url'].lower()
            if (url.endswith('.pdf') or 'pdf' in url):
                pdf_count += 1
            else:
                non_pdf_count += 1
        
        print(f"\nSummary:")
        print(f"  Total items processed: {len(processed_results)}")
        print(f"  PDF items: {pdf_count}")
        print(f"  Non-PDF items: {non_pdf_count}")
        print(f"  Items with successful markdown: {sum(1 for item in processed_results if item.get('markdown', '').strip())}")
    else:
        print("No data processed.")