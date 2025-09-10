#!/usr/bin/env python3
"""
Functions for processing certification data and converting documents to markdown.
"""

import requests
import time
import os
import json
import sys
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.prompts import SYSTEM_PROMPT_P3_PARAMETER, build_webpage_ingestion_prompt, get_certification_state

# Keep backward compatibility
certification_state = get_certification_state()


def convert_to_markdown(input_path):
    """
    Convert a URL or local file to markdown format using Datalab API.
    
    Args:
        input_path (str): URL or local file path to convert
        
    Returns:
        str: Markdown content or None if conversion fails
    """
    if not DATALAB_API_KEY:
        print("Error: DATALAB_API_KEY not set in environment variables")
        return None
    
    # Check if input is URL
    if input_path.startswith('http://') or input_path.startswith('https://'):
        print(f"Processing URL: {input_path}")
        
        # Use file_url parameter for URLs
        response = requests.post(
            DATALAB_API_URL,
            headers={"X-API-Key": DATALAB_API_KEY},
            data={
                'file_url': input_path,
                'output_format': 'markdown',
                'use_llm': 'True',
                'disable_image_extraction': 'True'
            }
        )
    else:
        # Local file processing
        if not os.path.exists(input_path):
            print(f"Error: File not found: {input_path}")
            return None
        
        print(f"Uploading local file: {input_path}")
        
        # Get file extension and determine MIME type
        file_ext = os.path.splitext(input_path)[1].lower()
        mime_type = 'application/pdf' if file_ext == '.pdf' else f'image/{file_ext[1:]}'
        
        # Upload file
        with open(input_path, 'rb') as f:
            response = requests.post(
                DATALAB_API_URL,
                headers={"X-API-Key": DATALAB_API_KEY},
                files={'file': (os.path.basename(input_path), f, mime_type)},
                data={
                    'output_format': 'markdown',
                    'use_llm': 'True',
                    'disable_image_extraction': 'True'
                }
            )
    
    # Check initial response
    if response.status_code != 200:
        print(f"Upload failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    result = response.json()
    if not result.get('success'):
        print(f"Error: {result.get('error')}")
        return None
    
    # Get request ID for polling
    request_id = result['request_id']
    check_url = f"{DATALAB_API_URL}/{request_id}"
    print(f"Processing... Request ID: {request_id}")
    
    # Poll for completion
    wait_time = 10  # Start with 10 seconds
    max_attempts = 30  # Max 5 minutes total
    
    for attempt in range(max_attempts):
        time.sleep(wait_time)
        check_response = requests.get(check_url, headers={"X-API-Key": DATALAB_API_KEY})
        
        if check_response.status_code != 200:
            print(f"Check failed: {check_response.status_code}")
            continue
            
        result = check_response.json()
        status = result.get('status')
        print(f"Status: {status} (attempt {attempt+1}/{max_attempts})")
        
        if status in ['completed', 'complete']:
            return result.get('markdown', '')
        elif status == 'failed':
            print(f"Processing failed: {result.get('error')}")
            return None
    
    print("Timeout: Processing took too long")
    return None


def parse_url_list_json(json_file_path):
    """
    Parse JSON file containing URLs and return processed data.
    
    For non-PDF URLs: keeps URL and markdown as is.
    For PDF URLs: uses convert_to_markdown and saves markdown for PDF URL.
    
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
        
        # Check if URL is a PDF
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        # Check multiple indicators for PDF files
        is_pdf = (
            path.endswith('.pdf') or 
            'pdf' in url.lower() or 
            ('content-type' in item and 'pdf' in item.get('content-type', '').lower())
        )
        
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


def process_certification_with_llm(markdown_content, current_state=None):
    """
    Process markdown content through LLM to extract certification data.
    
    Args:
        markdown_content (str): Markdown content to process
        current_state (dict): Optional current state to update
        
    Returns:
        dict: Structured certification data
    """
    from openai import OpenAI
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        raise ValueError("OPENAI_API_KEY not set in environment variables")
    
    client = OpenAI(api_key=openai_key)
    
    # Use provided state or create new one
    state = current_state or get_certification_state()
    
    # Build prompt
    prompt = build_webpage_ingestion_prompt(state, markdown_content)
    
    # Call LLM
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_P3_PARAMETER},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
    )
    
    # Parse and return result
    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as e:
        print(f"Error parsing LLM response: {e}")
        return state


# Command-line interface
if __name__ == "__main__":
    # Check if environment variables are set
    if not DATALAB_API_KEY:
        print("Warning: DATALAB_API_KEY not set. Please create a .env file.")
        print("See .env.example for required variables.")
    
    # Default file path
    default_input = "eu_compliance_results.json"
    
    # Use command line argument if provided, otherwise use default
    input_file = sys.argv[1] if len(sys.argv) > 1 else default_input
    
    # Generate output file name
    input_dir = os.path.dirname(input_file) or '.'
    input_name = os.path.basename(input_file)
    output_name = input_name.replace('.json', '_processed.json')
    output_file = os.path.join(input_dir, output_name)
    
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    
    # Process the data
    processed_results = parse_url_list_json(input_file)
    
    if processed_results:
        # Save processed data
        save_processed_data(processed_results, output_file)
        
        # Display summary
        pdf_count = sum(1 for item in processed_results 
                       if item['url'].lower().endswith('.pdf') or 'pdf' in item['url'].lower())
        non_pdf_count = len(processed_results) - pdf_count
        markdown_count = sum(1 for item in processed_results 
                           if item.get('markdown', '').strip())
        
        print(f"\nSummary:")
        print(f"  Total items processed: {len(processed_results)}")
        print(f"  PDF items: {pdf_count}")
        print(f"  Non-PDF items: {non_pdf_count}")
        print(f"  Items with successful markdown: {markdown_count}")
    else:
        print("No data processed.")