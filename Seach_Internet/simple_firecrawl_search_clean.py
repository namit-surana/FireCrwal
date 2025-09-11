#!/usr/bin/env python3
"""
Simplified Firecrawl Search - Clean Version
Basic search functionality without PDF processing
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SimpleFirecrawlSearch:
    """Simplified Firecrawl Search API"""
    
    def __init__(self, api_key: str = None):
        """Initialize the search API"""
        self.api_key = api_key or os.getenv('FIRECRAWL_API_KEY')
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY environment variable is required. Please check your .env file.")
        
        self.base_url = "https://api.firecrawl.dev/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        print("✅ Firecrawl Search API initialized")
    
    def search(self, query: str, limit: int) -> Dict[str, Any]:
        """Search with Firecrawl API"""
        try:
            print(f"🔍 Searching: '{query}' (limit: {limit})")
            
            search_params = {
                "query": query,
                "limit": limit,
                "sources": [{"type": "web"}],
                "timeout": 60000,
                "ignoreInvalidURLs": True,
                "scrapeOptions": {
                    "onlyMainContent": True,
                    "formats": [{"type": "markdown"}],
                  
                    "storeInCache": True,
                    "parsers": []
                }
            }
            
            response = requests.post(
                f"{self.base_url}/search",
                headers=self.headers,
                json=search_params,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._process_results(result)
            else:
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
    
    def _process_results(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process search results - simple flat array"""
        try:
            web_data = result.get('data', {}).get('web', [])
            
            processed_results = []
            for item in web_data:
                processed_results.append({
                    "url": item.get('url', ''),
                    "markdown": item.get('markdown', '')
                })
            
            return {
                "success": True,
                "data": processed_results,
                "total_results": len(processed_results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process results: {str(e)}",
                "data": []
            }
    
    def search_and_save(self, query: str, limit: int, filename: Optional[str] = None) -> Dict[str, Any]:
        """Search and save results to JSON file"""
        result = self.search(query, limit)
        
        if result['success']:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"search_results_{timestamp}.json"
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result['data'], f, indent=2, ensure_ascii=False)
                
                result['saved_to_file'] = filename
                print(f"💾 Results saved to: {filename}")
                
            except Exception as e:
                print(f"❌ Failed to save results: {e}")
                result['save_error'] = str(e)
        
        return result


def main():
    """Test the simplified search"""
    print("🔍 Simple Firecrawl Search")
    print("=" * 40)
    
    try:
        search_api = SimpleFirecrawlSearch()
        
        result = search_api.search_and_save(
            query='site:environment.ec.europa.eu/ "ROHS Certification"',
            limit=10
        )
        
        if result['success']:
            print(f"✅ Found {result['total_results']} results")
        else:
            print(f"❌ Search failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
