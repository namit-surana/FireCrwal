#!/usr/bin/env python3
"""
Simple startup script for BlueJay TIC Certification Database
"""

import sys
import os
from pathlib import Path

def main():
    """Main startup function"""
    print("🚀 BlueJay TIC Certification Database")
    print("=" * 50)
    
    try:
        # Get the absolute path to src directory
        current_dir = Path(__file__).parent.absolute()
        src_path = current_dir / "src"
        
        print(f"Current directory: {current_dir}")
        print(f"Source path: {src_path}")
        
        # Check if src directory exists
        if not src_path.exists():
            print(f"❌ Source directory not found: {src_path}")
            return False
        
        # Add src to Python path
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
            print(f"✅ Added {src_path} to Python path")
        
        print(f"Python path: {sys.path[0]}")
        
        # Test imports
        print("\n🧪 Testing imports...")
        
        from core.config import get_config
        print("✅ Config imported")
        
        from discovery.discovery_engine import DiscoveryEngine
        print("✅ Discovery engine imported")
        
        from discovery.firecrawl_client import FirecrawlClient
        print("✅ Firecrawl client imported")
        
        from discovery.website_mapper import WebsiteMapper
        print("✅ Website mapper imported")
        
        from discovery.content_categorizer import ContentCategorizer
        print("✅ Content categorizer imported")
        
        from discovery.quality_scorer import QualityScorer
        print("✅ Quality scorer imported")
        
        print("\n✅ All modules imported successfully")
        
        # Test configuration
        print("\n🧪 Testing configuration...")
        config = get_config(test_mode=True)
        if config.validate():
            print("✅ Configuration working")
        else:
            print("❌ Configuration validation failed")
        
        print("\n🎉 System is ready!")
        print("\nTo run the discovery demo:")
        print("1. Set your FIRECRAWL_API_KEY in .env file")
        print("2. Run: python demo_discovery.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
