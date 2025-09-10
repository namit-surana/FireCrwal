#!/usr/bin/env python3

import requests
import time
import os

API_KEY = "ddVOBV7Wb1IXCCBvutoTki7sMhI5edmpYbqGeJNKuRI"
API_URL = "https://www.datalab.to/api/v1/marker"

def convert_to_markdown(input_path):
    # Check if input is URL
    if input_path.startswith('http://') or input_path.startswith('https://'):
        print(f"Processing URL: {input_path}")
        
        # Use file_url parameter for URLs
        response = requests.post(
            API_URL,
            headers={"X-API-Key": API_KEY},
            data={
                'file_url': input_path,
                'output_format': 'markdown',
                'use_llm': 'True',
                'disable_image_extraction': 'True'
            }
        )
    else:
        # Local file
        if not os.path.exists(input_path):
            print(f"Error: File not found: {input_path}")
            return None
        
        print(f"Uploading local file: {input_path}")
        
        # Get file extension
        file_ext = os.path.splitext(input_path)[1].lower()
        mime_type = 'application/pdf' if file_ext == '.pdf' else f'image/{file_ext[1:]}'
        
        # Upload file
        with open(input_path, 'rb') as f:
            response = requests.post(
                API_URL,
                headers={"X-API-Key": API_KEY},
                files={'file': (os.path.basename(input_path), f, mime_type)},
                data={
                    'output_format': 'markdown',
                    'use_llm': 'True',
                    'disable_image_extraction': 'True'
                }
            )
    
    if response.status_code != 200:
        print(f"Upload failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    result = response.json()
    if not result.get('success'):
        print(f"Error: {result.get('error')}")
        return None
    
    request_id = result['request_id']
    check_url = f"{API_URL}/{request_id}"
    print(f"Processing... Request ID: {request_id}")
    
    # Poll for completion (with longer wait times)
    wait_time = 10  # Start with 10 seconds
    max_attempts = 30  # Max 5 minutes total
    
    for attempt in range(max_attempts):
        time.sleep(wait_time)
        check_response = requests.get(check_url, headers={"X-API-Key": API_KEY})
        
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

if __name__ == "__main__":
    # Example with URL:
    # markdown = convert_to_markdown("https://example.com/document.pdf")
    
    # Example with local file:
    markdown = convert_to_markdown("https://environment.ec.europa.eu/document/download/f1f65e3d-1b90-4dd1-a0d4-797bd6cabe98_en?filename=Guidance_Document.pdf")
    if markdown:
        print(markdown)