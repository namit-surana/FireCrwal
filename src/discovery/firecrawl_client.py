"""
Firecrawl client wrapper for BlueJay TIC Certification Database
"""

import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from firecrawl import FirecrawlApp, V1ScrapeOptions

from core.config import get_config


class FirecrawlClient:
    """
    Wrapper for Firecrawl API client with rate limiting and error handling
    """
    
    def __init__(self):
        """Initialize Firecrawl client"""
        try:
            config = get_config()
            self.client = FirecrawlApp(api_key=config.firecrawl_api_key)
            print("Firecrawl client initialized successfully")
            
            # Rate limiting - reduced for free tier
            self.max_requests_per_minute = getattr(config, 'max_requests_per_minute', 5)  # Reduced to 5 for free tier
            self.request_timestamps = []
            
        except Exception as e:
            print(f"Failed to initialize Firecrawl client: {e}")
            raise Exception(f"Firecrawl client initialization failed: {e}")
    
    def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < 60
        ]
        
        # Check if we're at the limit
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.request_timestamps[0])
            if sleep_time > 0:
                print(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Add current timestamp
        self.request_timestamps.append(current_time)
   
    def map_website_simple(self, url: str, search: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Simple map function that returns title, URL, and description
        
        Args:
            url: Base URL to map
            search: Optional search term
            
        Returns:
            List of dictionaries with url, title, and description
        """
        try:
            self._check_rate_limit()
            
            # Prepare map options
            map_options = {"url": url}
            if search:
                map_options["search"] = search
            
            # Perform mapping
            result = self.client.map(**map_options)
            
            if not result:
                return []
            
            # Extract links with metadata
            links = []
            if hasattr(result, 'links'):
                for link in result.links:
                    if hasattr(link, 'url'):
                        links.append({
                            'url': link.url,
                            'title': getattr(link, 'title', ''),
                            'description': getattr(link, 'description', '')
                        })
            
            return links
                
        except Exception as e:
            print(f"Failed to map {url}: {e}")
            return []
    
    
    def search_website(
        self,
        url: str,
        query: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Search website content using Firecrawl
        
        Args:
            url: Base URL to search
            query: Search query
            **kwargs: Additional Firecrawl options
            
        Returns:
            Search results or None if failed
        """
        try:
            self._check_rate_limit()
            
            print(f"Searching website: {url} with query: {query}")
            
            # Prepare search options
            search_options = {
                "url": url,
                "query": query
            }
            
            # Perform search
            result = self.client.search(**search_options)
            
            if result:
                print(f"Successfully completed search for: {url}")
                return result
            else:
                print(f"No search results returned for: {url}")
                return None
                
        except Exception as e:
            print(f"Failed to search {url}: {e}")
            print(f"Returning fallback search structure...")
            # Return fallback structure instead of raising exception
            return {
                "results": [{"url": url, "title": "Search failed", "description": "Search operation failed"}],
                "error": str(e),
                "fallback": True
            }
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status
        
        Returns:
            Rate limit information
        """
        current_time = time.time()
        
        # Remove old timestamps
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < 60
        ]
        
        return {
            "current_requests": len(self.request_timestamps),
            "max_requests_per_minute": self.max_requests_per_minute,
            "remaining_requests": max(0, self.max_requests_per_minute - len(self.request_timestamps)),
            "reset_time_seconds": 60 - (current_time - self.request_timestamps[0]) if self.request_timestamps else 0
        }
    
    def wait_for_rate_limit_reset(self):
        """Wait for rate limit to reset"""
        status = self.get_rate_limit_status()
        if status["remaining_requests"] == 0:
            sleep_time = status["reset_time_seconds"]
            if sleep_time > 0:
                print(f"Waiting {sleep_time:.2f} seconds for rate limit reset")
                time.sleep(sleep_time)
    
    def test_connection(self) -> bool:
        """
        Test Firecrawl API connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try a simple map operation to test connection
            test_url = "https://example.com"
            result = self.map_website_simple(test_url)
            return len(result) > 0
            
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def extract_urls_from_map_result(self, map_result) -> List[str]:
        """
        Extract and process URLs from Firecrawl map result
        
        Args:
            map_result: The result from Firecrawl map operation
            
        Returns:
            List of processed URL strings
        """
        urls = []
        
        # Handle different response formats from Firecrawl
        if hasattr(map_result, 'links'):
            # MapData object with links attribute
            urls = map_result.links
        elif hasattr(map_result, 'urls'):
            # MapData object with urls attribute
            urls = map_result.urls
        elif isinstance(map_result, dict):
            # Dictionary format - check for playground response format first
            if 'links' in map_result and isinstance(map_result['links'], list):
                urls = map_result['links']
            elif 'urls' in map_result and isinstance(map_result['urls'], list):
                urls = map_result['urls']
            elif 'data' in map_result and isinstance(map_result['data'], list):
                urls = map_result['data']
            
            # If no URLs found in expected keys, check if it's a list directly
            if not urls and isinstance(map_result.get('data'), list):
                urls = [item.get('url', item) if isinstance(item, dict) else item for item in map_result['data']]
        elif isinstance(map_result, list):
            urls = map_result
        
        # Convert to list if it's not already
        if urls and not isinstance(urls, list):
            urls = list(urls)
        
        # Extract URLs from LinkResult objects or other complex objects
        processed_urls = []
        for item in urls:
            if hasattr(item, 'url'):
                # LinkResult object with url attribute
                processed_urls.append(item.url)
            elif hasattr(item, 'href'):
                # Link object with href attribute
                processed_urls.append(item.href)
            elif isinstance(item, str):
                # Already a string URL
                processed_urls.append(item)
            elif isinstance(item, dict) and 'url' in item:
                # Dictionary with url key (playground format)
                processed_urls.append(item['url'])
            else:
                # Convert to string as fallback
                processed_urls.append(str(item))
        
        # Remove duplicates and sort
        return sorted(list(set(processed_urls)))
    
    def extract_links_with_metadata(self, map_result) -> List[Dict[str, str]]:
        """
        Extract URLs with title and description from Firecrawl map result
        
        Args:
            map_result: The result from Firecrawl map operation (MapData object or dict)
            
        Returns:
            List of dictionaries with url, title, and description
        """
        links = []
        
        # Handle Firecrawl Python SDK format (MapData object with LinkResult objects)
        if hasattr(map_result, 'links'):
            for link in map_result.links:
                if hasattr(link, 'url'):
                    links.append({
                        'url': link.url,
                        'title': getattr(link, 'title', ''),
                        'description': getattr(link, 'description', '')
                    })
                elif isinstance(link, str):
                    links.append({
                        'url': link,
                        'title': '',
                        'description': ''
                    })
        
        # Handle playground/direct API format (dict with links array)
        elif isinstance(map_result, dict) and 'links' in map_result:
            for link in map_result['links']:
                if isinstance(link, dict):
                    links.append({
                        'url': link.get('url', ''),
                        'title': link.get('title', ''),
                        'description': link.get('description', '')
                    })
                elif isinstance(link, str):
                    links.append({
                        'url': link,
                        'title': '',
                        'description': ''
                    })
        
        return links
    
    def categorize_urls(self, urls: List[str], base_url: str) -> Dict[str, List[str]]:
        """
        Categorize URLs by their path structure
        
        Args:
            urls: List of URLs to categorize
            base_url: Base website URL
            
        Returns:
            Dictionary with categories and their URLs
        """
        categories = {
            "Homepage": [],
            "Blog/News": [],
            "Products/Services": [],
            "About/Company": [],
            "Contact": [],
            "Documentation/Help": [],
            "Other": []
        }
        
        # Extract domain from base URL
        base_domain = base_url.replace('https://', '').replace('http://', '').split('/')[0]
        
        for url in urls:
            # Skip if not from same domain
            if base_domain not in url:
                continue
                
            # Remove base URL to get path
            path = url.replace(base_url, '').strip('/')
            
            if not path or path == '':
                categories["Homepage"].append(url)
            elif any(keyword in path.lower() for keyword in ['blog', 'news', 'article', 'post']):
                categories["Blog/News"].append(url)
            elif any(keyword in path.lower() for keyword in ['product', 'service', 'shop', 'store', 'catalog']):
                categories["Products/Services"].append(url)
            elif any(keyword in path.lower() for keyword in ['about', 'company', 'team', 'mission', 'vision']):
                categories["About/Company"].append(url)
            elif any(keyword in path.lower() for keyword in ['contact', 'support', 'help']):
                categories["Contact"].append(url)
            elif any(keyword in path.lower() for keyword in ['doc', 'help', 'guide', 'manual', 'faq']):
                categories["Documentation/Help"].append(url)
            else:
                categories["Other"].append(url)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def serialize_map_result(self, map_result):
        """
        Serialize MapData object or other complex objects to JSON-serializable format
        
        Args:
            map_result: The result from Firecrawl map operation
            
        Returns:
            JSON-serializable representation of the result
        """
        try:
            # If it's already a dict or list, return as is
            if isinstance(map_result, (dict, list, str, int, float, bool, type(None))):
                return map_result
            
            # If it has a __dict__ attribute, convert to dict
            if hasattr(map_result, '__dict__'):
                result_dict = {}
                for key, value in map_result.__dict__.items():
                    if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                        result_dict[key] = value
                    elif hasattr(value, '__dict__'):
                        result_dict[key] = self.serialize_map_result(value)
                    else:
                        result_dict[key] = str(value)
                return result_dict
            
            # If it's iterable but not a string, convert to list
            if hasattr(map_result, '__iter__') and not isinstance(map_result, str):
                return [self.serialize_map_result(item) for item in map_result]
            
            # Fallback: convert to string
            return str(map_result)
            
        except Exception as e:
            return {"error": f"Serialization failed: {str(e)}", "type": str(type(map_result))}
    
    def create_export_data(self, website_url: str, search_term: str, unique_urls: List[str], 
                          categories: Dict[str, List[str]], map_result=None) -> Dict[str, Any]:
        """
        Create standardized export data structure
        
        Args:
            website_url: The website URL that was mapped
            search_term: Optional search term used
            unique_urls: List of discovered URLs
            categories: Categorized URLs
            map_result: Optional raw map result for serialization
            
        Returns:
            Dictionary with export data
        """
        export_data = {
            "website_url": website_url,
            "search_term": search_term if search_term else None,
            "mapping_timestamp": str(Path().cwd()),
            "total_urls": len(unique_urls),
            "unique_urls": len(unique_urls),
            "urls": unique_urls,
            "categories": categories
        }
        
        # Add raw result if provided
        if map_result is not None:
            export_data["raw_result"] = self.serialize_map_result(map_result)
        
        return export_data
    
    def save_export_files(self, website_url: str, export_data: Dict[str, Any], unique_urls: List[str]) -> Dict[str, str]:
        """
        Save export data to JSON and TXT files
        
        Args:
            website_url: The website URL (used for filename generation)
            export_data: The export data dictionary
            unique_urls: List of URLs for the TXT file
            
        Returns:
            Dictionary with file paths and sizes
        """
        # Generate filenames
        base_filename = website_url.replace('https://', '').replace('http://', '').replace('/', '_')
        json_file = f"website_map_{base_filename}.json"
        txt_file = f"urls_{base_filename}.txt"
        
        # Save JSON file
        try:
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            json_size = len(json.dumps(export_data))
        except TypeError as e:
            # If JSON serialization fails, create a simplified version
            print(f"⚠️  JSON serialization warning: {e}")
            simplified_data = {
                "website_url": export_data.get("website_url"),
                "search_term": export_data.get("search_term"),
                "mapping_timestamp": export_data.get("mapping_timestamp"),
                "total_urls": export_data.get("total_urls"),
                "unique_urls": export_data.get("unique_urls"),
                "urls": export_data.get("urls"),
                "categories": export_data.get("categories"),
                "raw_result_info": f"Raw result serialization failed: {e}"
            }
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(simplified_data, f, indent=2, ensure_ascii=False)
            json_size = len(json.dumps(simplified_data))
        
        # Save TXT file
        with open(txt_file, "w", encoding="utf-8") as f:
            for url in unique_urls:
                f.write(url + "\n")
        
        return {
            "json_file": json_file,
            "txt_file": txt_file,
            "json_size": json_size
        }
    
    def map_website_complete(self, url: str, search_term: str = None, 
                            include_sitemap: bool = True, 
                            include_subdomains: bool = True, 
                            ignore_query_params: bool = True,
                            limit: int = 0,
                            timeout: int = 120,
                            save_files: bool = True,
                            max_retries: int = 2) -> Dict[str, Any]:
        """
        Complete website mapping with processing and optional file saving
        
        Args:
            url: Website URL to map
            search_term: Optional search term to filter URLs
            include_sitemap: Whether to include sitemap in mapping
            include_subdomains: Whether to include subdomains
            ignore_query_params: Whether to ignore query parameters
            limit: Maximum number of URLs to return (default: 5000)
            timeout: Request timeout in seconds (default: 120)
            save_files: Whether to save results to files
            max_retries: Maximum number of retry attempts (default: 2)
            
        Returns:
            Dictionary with complete mapping results
        """
        for attempt in range(max_retries + 1):
            try:
                print(f"Mapping attempt {attempt + 1}/{max_retries + 1}")
                
                # Map the website with all parameters
                map_result = self.map_website(
                    url=url,
                    search=search_term,
                    sitemap="include" if include_sitemap else None,
                    includeSubdomains=include_subdomains,
                    ignoreQueryParameters=ignore_query_params,
                    limit=limit,
                    timeout=timeout
                )
                
                # If successful, break out of retry loop
                if map_result and not (isinstance(map_result, dict) and map_result.get('fallback')):
                    break
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries:
                    print(f"Retrying with reduced parameters...")
                    # Reduce parameters for retry
                    limit = max(50, limit // 2)
                    timeout = max(30, timeout // 2)
                else:
                    print(f"All attempts failed, using fallback")
                    map_result = None
            
        # Process the result (whether from successful mapping or fallback)
        if not map_result:
            return {"error": "Failed to create website map after all retry attempts"}
        
        # Extract URLs from result
        unique_urls = self.extract_urls_from_map_result(map_result)
        
        if not unique_urls:
            return {"error": "No URLs found in the mapping result"}
        
        # Extract links with metadata (playground format)
        links_with_metadata = self.extract_links_with_metadata(map_result)
        
        # Categorize URLs
        categories = self.categorize_urls(unique_urls, url)
        
        # Create export data
        export_data = self.create_export_data(
            website_url=url,
            search_term=search_term,
            unique_urls=unique_urls,
            categories=categories,
            map_result=map_result
        )
        
        # Add metadata if available
        if links_with_metadata:
            export_data["links_with_metadata"] = links_with_metadata
        
        # Add success flag
        export_data["success"] = True
        
        # Save files if requested
        if save_files:
            file_info = self.save_export_files(url, export_data, unique_urls)
            export_data["files"] = file_info
        
        return export_data
    
    @staticmethod
    def create_client(test_connection: bool = True) -> Tuple['FirecrawlClient', bool, str]:
        """
        Static method to create and initialize Firecrawl client
        
        Args:
            test_connection: Whether to test the connection after initialization
            
        Returns:
            Tuple of (firecrawl_client, success_flag, error_message)
        """
        try:
            # Create configuration
            config = get_config(test_mode=False)
            
            # Check configuration
            if not config.validate():
                return None, False, "Configuration validation failed"
            
            # Initialize Firecrawl client
            firecrawl_client = FirecrawlClient()
            
            # Test connection if requested
            if test_connection and not firecrawl_client.test_connection():
                return None, False, "Firecrawl connection test failed"
            
            return firecrawl_client, True, None
            
        except Exception as e:
            return None, False, f"Client initialization failed: {str(e)}"
