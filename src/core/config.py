"""
Simple configuration for BlueJay TIC Certification Database
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Simple configuration class"""
    
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        
        # Basic configuration
        self.app_name: str = "BlueJay TIC Database"
        self.app_version: str = "1.0.0"
        self.debug: bool = False
        
        # Firecrawl API key
        if test_mode:
            self.firecrawl_api_key: str = "test_key"
        else:
            self.firecrawl_api_key: str = os.getenv("FIRECRAWL_API_KEY", "")
        
        # Rate limiting - adjusted for free tier
        self.max_requests_per_minute: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "5"))  # Free tier: 5 req/min
        self.max_concurrent_jobs: int = int(os.getenv("MAX_CONCURRENT_JOBS", "1"))  # Free tier: 1 concurrent job
    
    def validate(self) -> bool:
        """Simple validation"""
        if self.test_mode:
            return True
        return bool(self.firecrawl_api_key)
    
    def get_api_key(self) -> str:
        """Get API key"""
        return self.firecrawl_api_key

def get_config(test_mode: bool = False) -> Config:
    """Get configuration instance"""
    return Config(test_mode=test_mode)
