"""
Firecrawl client wrapper for BlueJay TIC Certification Database
"""

import time
from typing import List, Dict, Any, Optional
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
            
            # Rate limiting
            self.max_requests_per_minute = getattr(config, 'max_requests_per_minute', 60)
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
    
    def scrape_url(
        self,
        url: str,
        formats: Optional[List[str]] = None,
        parsePDF: bool = False,
        actions: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape a single URL using Firecrawl
        
        Args:
            url: URL to scrape
            formats: Output formats (markdown, html, etc.)
            parsePDF: Whether to parse PDF content
            actions: Browser actions to perform
            **kwargs: Additional Firecrawl options
            
        Returns:
            Scraped content or None if failed
        """
        try:
            self._check_rate_limit()
            
            print(f"Scraping URL: {url}")
            
            # Prepare scrape options
            scrape_options = V1ScrapeOptions(
                url=url,
                formats=formats or ["markdown"],
                parsePDF=parsePDF,
                actions=actions or []
            )
            
            # Add additional options
            for key, value in kwargs.items():
                if hasattr(scrape_options, key):
                    setattr(scrape_options, key, value)
            
            # Perform scraping
            result = self.client.scrape(scrape_options)
            
            if result:
                print(f"Successfully scraped: {url}")
                return result
            else:
                print(f"No content returned for: {url}")
                return None
                
        except Exception as e:
            print(f"Failed to scrape {url}: {e}")
            raise Exception(f"Scraping failed for {url}: {e}")
    
    def map_website(
        self,
        url: str,
        search: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Map website structure using Firecrawl
        
        Args:
            url: Base URL to map
            search: Optional search term
            **kwargs: Additional Firecrawl options
            
        Returns:
            Website map or None if failed
        """
        try:
            self._check_rate_limit()
            
            print(f"Mapping website: {url}")
            
            # Prepare map options
            map_options = {
                "url": url,
                **kwargs
            }
            
            if search:
                map_options["search"] = search
            
            # Perform mapping
            result = self.client.map(**map_options)
            
            if result:
                print(f"Successfully mapped: {url}")
                return result
            else:
                print(f"No map data returned for: {url}")
                return None
                
        except Exception as e:
            print(f"Failed to map {url}: {e}")
            raise Exception(f"Website mapping failed for {url}: {e}")
    
    def crawl_website(
        self,
        url: str,
        limit: int = 100,
        max_depth: int = 8,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Crawl website using Firecrawl
        
        Args:
            url: Base URL to crawl
            limit: Maximum number of pages to crawl
            max_depth: Maximum crawl depth
            include_paths: Paths to include
            exclude_paths: Paths to exclude
            **kwargs: Additional Firecrawl options
            
        Returns:
            Crawl results or None if failed
        """
        try:
            self._check_rate_limit()
            
            print(f"Starting crawl for: {url}")
            print(f"Crawl parameters: limit={limit}, max_depth={max_depth}")
            
            # Prepare crawl options
            crawl_options = {
                "url": url,
                "limit": limit,
                "max_depth": max_depth,
                **kwargs
            }
            
            if include_paths:
                crawl_options["include_paths"] = include_paths
            
            if exclude_paths:
                crawl_options["exclude_paths"] = exclude_paths
            
            # Start crawling
            result = self.client.crawl(**crawl_options)
            
            if result:
                print(f"Successfully completed crawl for: {url}")
                return result
            else:
                print(f"No crawl data returned for: {url}")
                return None
                
        except Exception as e:
            print(f"Failed to crawl {url}: {e}")
            raise Exception(f"Website crawling failed for {url}: {e}")
    
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
                "query": query,
                **kwargs
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
            raise Exception(f"Website search failed for {url}: {e}")
    
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
            # Try a simple operation to test connection
            test_url = "https://httpbin.org/html"
            result = self.scrape_url(test_url, formats=["markdown"])
            return result is not None
            
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
