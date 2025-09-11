#!/usr/bin/env python3
"""
Unified Search and PDF Processing Pipeline
Combines Firecrawl search with Marker API PDF enhancement
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()


class UnifiedSearchPipeline:
    """
    Unified pipeline for search and PDF processing
    """
    
    def __init__(self):
        """Initialize the pipeline with API keys"""
        # Firecrawl API
        self.firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY')
        if not self.firecrawl_api_key:
            raise ValueError("FIRECRAWL_API_KEY environment variable is required. Please check your .env file.")
        
        # Marker API
        self.marker_api_key = os.getenv('MARKER_API_KEY')
        if not self.marker_api_key:
            raise ValueError("MARKER_API_KEY environment variable is required. Please check your .env file.")
        
        self.firecrawl_base_url = "https://api.firecrawl.dev/v2"
        self.marker_api_url = "https://www.datalab.to/api/v1/marker"
        
        self.firecrawl_headers = {
            "Authorization": f"Bearer {self.firecrawl_api_key}",
            "Content-Type": "application/json"
        }
        
        print("✅ Unified Search Pipeline initialized")
    
    def search(self, query: str, limit: int) -> Dict[str, Any]:
        """
        Search using Firecrawl API
        
        Args:
            query: Search query
            limit: Number of results
            
        Returns:
            Search results with PDF/Non-PDF separation
        """
        try:
            print(f"🔍 Searching: '{query}' (limit: {limit})")
            
            search_params = {
                "query": query,
                "limit": limit,
                "sources": [{"type": "web"}],
                "scrapeOptions": {
                    "onlyMainContent": True,
                    "formats": [{"type": "markdown"}]
                }
            }
            
            response = requests.post(
                f"{self.firecrawl_base_url}/search",
                headers=self.firecrawl_headers,
                json=search_params,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"🔍 API Response received: {len(result.get('data', {}).get('web', []))} items")
                return self._process_search_results(result)
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "data": []
                }
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }
    
    def _categorize_url(self, url: str) -> str:
        """Categorize URL by file extension"""
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            
            if '.' in path:
                extension = path.split('.')[-1]
            else:
                extension = 'no_extension'
            
            document_extensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf']
            
            return 'pdf' if extension == 'pdf' else 'other'
        except:
            return 'other'
    
    def _process_search_results(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process search results and separate PDFs from non-PDFs"""
        try:
            web_data = result.get('data', {}).get('web', [])
            print(f"📊 Processing {len(web_data)} web results...")
            
            pdf_documents = []
            non_pdf_content = []
            
            for item in web_data:
                url = item.get('url', '')
                markdown = item.get('markdown', '')
                
                item_data = {
                    "url": url,
                    "markdown": markdown
                }
                
                if self._categorize_url(url) == 'pdf':
                    pdf_documents.append(item_data)
                else:
                    non_pdf_content.append(item_data)
            
            return {
                "success": True,
                "pdf_documents": pdf_documents,
                "non_pdf_content": non_pdf_content,
                "total_pdf": len(pdf_documents),
                "total_non_pdf": len(non_pdf_content),
                "total_results": len(web_data)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process results: {str(e)}",
                "pdf_documents": [],
                "non_pdf_content": [],
                "total_pdf": 0,
                "total_non_pdf": 0,
                "total_results": 0
            }
    
    def _convert_pdf_to_markdown(self, url: str) -> str:
        """Convert PDF URL to markdown using Marker API"""
        try:
            print(f"📄 Converting PDF: {url}")
            
            response = requests.post(
                self.marker_api_url,
                headers={"X-API-Key": self.marker_api_key},
                data={
                    'file_url': url,
                    'output_format': 'markdown',
                    'use_llm': 'True',
                    'disable_image_extraction': 'True'
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Marker API failed: {response.status_code}")
                return None
            
            result = response.json()
            if not result.get('success'):
                print(f"❌ Marker API error: {result.get('error')}")
                return None
            
            request_id = result['request_id']
            check_url = f"{self.marker_api_url}/{request_id}"
            
            # Poll for completion
            for attempt in range(30):  # Max 5 minutes
                import time
                time.sleep(10)
                
                check_response = requests.get(check_url, headers={"X-API-Key": self.marker_api_key})
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
    
    def _process_single_pdf(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single PDF item"""
        url = item.get('url', '')
        
        # Try to convert PDF with Marker API
        enhanced_markdown = self._convert_pdf_to_markdown(url)
        
        if enhanced_markdown and len(enhanced_markdown.strip()) > 0:
            return {
                'url': url,
                'markdown': enhanced_markdown
            }
        else:
            # Fallback to original markdown
            return {
                'url': url,
                'markdown': item.get('markdown', '')
            }
    
    def enhance_pdfs(self, pdf_documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance PDF documents using Marker API in parallel"""
        if not pdf_documents:
            return []
        
        print(f"🚀 Enhancing {len(pdf_documents)} PDFs in parallel...")
        
        enhanced_pdfs = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_item = {executor.submit(self._process_single_pdf, item): item for item in pdf_documents}
            
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
        
        return enhanced_pdfs
    
    def run_pipeline(self, query: str, limit: int, output_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Run the complete pipeline: search -> enhance PDFs -> return flat array
        
        Args:
            query: Search query
            limit: Number of results
            output_file: Optional output file path
            
        Returns:
            Flat array of items with url and markdown
        """
        print("🚀 Starting Unified Search Pipeline")
        print("=" * 50)
        
        # Step 1: Search
        search_results = self.search(query, limit)
        
        if not search_results['success']:
            print(f"❌ Search failed: {search_results.get('error')}")
            return []
        
        pdf_docs = search_results.get('pdf_documents', [])
        non_pdf_content = search_results.get('non_pdf_content', [])
        
        print(f"📊 Search completed:")
        print(f"   📄 PDF documents: {len(pdf_docs)}")
        print(f"   🌐 Non-PDF content: {len(non_pdf_content)}")
        
        # Step 2: Enhance PDFs
        enhanced_pdfs = self.enhance_pdfs(pdf_docs)
        
        # Step 3: Combine all results
        all_items = enhanced_pdfs + non_pdf_content
        
        print(f"\n✅ Pipeline completed!")
        print(f"   📊 Total results: {len(all_items)}")
        
        # Step 4: Save if requested
        if output_file:
            self._save_results(all_items, output_file)
        
        return all_items
    
    def _save_results(self, results: List[Dict[str, Any]], output_file: str):
        """Save results to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving results: {e}")


def main():
    """Main function to run the pipeline"""
    print("🔍 Unified Search and PDF Processing Pipeline")
    print("=" * 60)
    
    try:
        # Initialize pipeline
        pipeline = UnifiedSearchPipeline()
        
        # Example usage - try a simpler query first
        query = 'ROHS Certification environment'
        limit = 10
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"unified_search_results_{timestamp}.json"
        
        # Run pipeline
        print(f"🔍 Testing with query: '{query}'")
        results = pipeline.run_pipeline(query, limit, output_file)
        
        # If no results, try a different query
        if not results:
            print("\n🔄 No results found, trying alternative query...")
            query2 = 'environmental certification'
            results = pipeline.run_pipeline(query2, limit, output_file)
        
        if results:
            # Display summary
            pdf_count = sum(1 for item in results if item.get('url', '').lower().endswith('.pdf'))
            non_pdf_count = len(results) - pdf_count
            
            print(f"\n📊 Final Summary:")
            print(f"   📄 PDF documents: {pdf_count}")
            print(f"   🌐 Non-PDF content: {non_pdf_count}")
            print(f"   📊 Total results: {len(results)}")
            
            # Show sample URLs
            print(f"\n📋 Sample URLs:")
            for i, item in enumerate(results[:3], 1):
                print(f"   {i}. {item.get('url', 'Unknown')}")
            if len(results) > 3:
                print(f"   ... and {len(results) - 3} more")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")


if __name__ == "__main__":
    main()
