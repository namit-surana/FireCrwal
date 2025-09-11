#!/usr/bin/env python3
"""
Simplified PDF Enhancer - Clean Version
Basic PDF processing using Marker API
"""

import os
import json
import requests
import time
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SimplePDFEnhancer:
    """Simplified PDF enhancer using Marker API"""
    
    def __init__(self):
        """Initialize the PDF enhancer"""
        self.api_key = os.getenv('MARKER_API_KEY')
        if not self.api_key:
            raise ValueError("MARKER_API_KEY environment variable is required. Please check your .env file.")
        
        self.api_url = "https://www.datalab.to/api/v1/marker"
        print("✅ PDF Enhancer initialized")
    
    def convert_pdf_to_markdown(self, url: str) -> str:
        """Convert PDF URL to markdown using Marker API"""
        try:
            print(f"📄 Converting PDF: {url}")
            
            response = requests.post(
                self.api_url,
                headers={"X-API-Key": self.api_key},
                data={
                    'file_url': url,
                    'output_format': 'markdown',
                    'use_llm': 'True',
                    'disable_image_extraction': 'True'
                }
            )
            
            if response.status_code != 200:
                print(f"❌ API failed: {response.status_code}")
                return None
            
            result = response.json()
            if not result.get('success'):
                print(f"❌ API error: {result.get('error')}")
                return None
            
            request_id = result['request_id']
            check_url = f"{self.api_url}/{request_id}"
            
            # Poll for completion
            for attempt in range(30):  # Max 5 minutes
                time.sleep(10)
                
                check_response = requests.get(check_url, headers={"X-API-Key": self.api_key})
                if check_response.status_code != 200:
                    continue
                
                result = check_response.json()
                status = result.get('status')
                
                if status in ['completed', 'complete']:
                    print(f"✅ PDF converted successfully")
                    return result.get('markdown', '')
                elif status == 'failed':
                    print(f"❌ PDF conversion failed: {result.get('error')}")
                    return None
            
            print("⏰ PDF conversion timeout")
            return None
            
        except Exception as e:
            print(f"❌ Error converting PDF: {e}")
            return None
    
    def enhance_pdfs_in_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance PDFs in a flat array of data with parallel processing"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Separate PDFs and non-PDFs
        pdf_items = []
        non_pdf_items = []
        
        for item in data:
            url = item.get('url', '')
            if url.lower().endswith('.pdf') or 'pdf' in url.lower():
                pdf_items.append(item)
            else:
                non_pdf_items.append(item)
        
        if not pdf_items:
            print("📄 No PDFs found, returning original data")
            return data
        
        print(f"🚀 Processing {len(pdf_items)} PDFs in parallel...")
        
        # Process PDFs in parallel - dynamic worker allocation
        enhanced_pdfs = []
        max_workers = len(pdf_items)
        print(f"📊 Using {max_workers} parallel workers for {len(pdf_items)} PDFs")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_item = {executor.submit(self._process_single_pdf, item): item for item in pdf_items}
            
            for future in as_completed(future_to_item):
                try:
                    result = future.result()
                    enhanced_pdfs.append(result)
                    print(f"✅ Completed: {result['url']}")
                except Exception as e:
                    item = future_to_item[future]
                    print(f"❌ Failed: {item.get('url', 'Unknown')} - {e}")
                    # Add fallback
                    enhanced_pdfs.append({
                        'url': item.get('url', ''),
                        'markdown': item.get('markdown', '')
                    })
        
        # Combine enhanced PDFs with non-PDF items
        return enhanced_pdfs + non_pdf_items
    
    def _process_single_pdf(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single PDF item"""
        url = item.get('url', '')
        markdown = item.get('markdown', '')
        
        print(f"📄 Processing PDF: {url}")
        enhanced_markdown = self.convert_pdf_to_markdown(url)
        
        if enhanced_markdown and len(enhanced_markdown.strip()) > 0:
            return {
                'url': url,
                'markdown': enhanced_markdown
            }
        else:
            return {
                'url': url,
                'markdown': markdown  # Use original
            }
    
    def enhance_pdfs_in_data_sequential(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance PDFs in a flat array of data (sequential fallback)"""
        enhanced_data = []
        
        for item in data:
            url = item.get('url', '')
            markdown = item.get('markdown', '')
            
            # Check if it's a PDF
            if url.lower().endswith('.pdf') or 'pdf' in url.lower():
                print(f"📄 Processing PDF: {url}")
                enhanced_markdown = self.convert_pdf_to_markdown(url)
                
                if enhanced_markdown and len(enhanced_markdown.strip()) > 0:
                    enhanced_data.append({
                        'url': url,
                        'markdown': enhanced_markdown
                    })
                    print(f"✅ Enhanced PDF successfully")
                else:
                    enhanced_data.append({
                        'url': url,
                        'markdown': markdown  # Use original
                    })
                    print(f"⚠️ Using original markdown for PDF")
            else:
                # Non-PDF, keep as is
                enhanced_data.append({
                    'url': url,
                    'markdown': markdown
                })
        
        return enhanced_data
    
    def process_file(self, input_file: str, output_file: str = None) -> List[Dict[str, Any]]:
        """Process a JSON file and enhance PDFs"""
        try:
            # Load input file
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"📁 Loaded {len(data)} items from {input_file}")
            
            # Enhance PDFs
            enhanced_data = self.enhance_pdfs_in_data(data)
            
            # Save output
            if not output_file:
                output_file = input_file.replace('.json', '_enhanced.json')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Enhanced data saved to: {output_file}")
            
            return enhanced_data
            
        except Exception as e:
            print(f"❌ Error processing file: {e}")
            return []


def main():
    """Test the PDF enhancer"""
    print("📄 Simple PDF Enhancer")
    print("=" * 30)
    
    try:
        enhancer = SimplePDFEnhancer()
        
        # Example: process a file
        input_file = "../Seach_Internet/search_results.json"
        enhanced_data = enhancer.process_file(input_file)
        
        if enhanced_data:
            pdf_count = sum(1 for item in enhanced_data if item.get('url', '').lower().endswith('.pdf'))
            print(f"✅ Processed {len(enhanced_data)} items ({pdf_count} PDFs)")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
