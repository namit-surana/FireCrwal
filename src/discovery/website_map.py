#!/usr/bin/env python3
"""
Simple Website Map Generator using Firecrawl
Creates a map of all URLs found on a website
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from discovery.firecrawl_client import FirecrawlClient


def main():
    """Main function to create website map"""
    print("🗺️  Website Map Generator")
    print("=" * 50)
    
    try:
        print("✅ Core modules imported successfully")
        
        # Initialize Firecrawl client
        print("\n🌐 Initializing Firecrawl client...")
        firecrawl_client, success, error_msg = FirecrawlClient.create_client(test_connection=True)
        
        if not success:
            print(f"❌ {error_msg}")
            if "Configuration validation failed" in error_msg:
                print("Please check your environment variables and API keys")
            return False
        
        print("✅ Firecrawl client ready")
        print("✅ Firecrawl connection successful")
        
        # Get website URL from user
        print("\n📝 Enter website details:")
        website_url = input("Enter website URL to map (e.g., https://example.com): ").strip()
        
        if not website_url:
            print("❌ No URL provided")
            return False
        
        # Add protocol if missing
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        
        print(f"\n🎯 Mapping website: {website_url}")
        
        # Optional search term
        search_term = input("Enter optional search term to filter URLs (press Enter to skip): ").strip()
        
        # Map the website
        print("\n🚀 Starting website mapping...")
        print("   This may take a few minutes depending on website size...")
        
        result = firecrawl_client.map_website_complete(
            url=website_url,
            search_term=search_term if search_term else None,
            include_sitemap=True,
            include_subdomains=True,
            ignore_query_params=True,
            save_files=True
        )
        
        if "error" in result:
            print(f"❌ {result['error']}")
            return False
        
        print("✅ Website mapping completed successfully!")
        
        # Process and display results
        print("\n📊 Website Map Results")
        print("=" * 50)
        
        unique_urls = result.get("urls", [])
        categories = result.get("categories", {})
        links_with_metadata = result.get("links_with_metadata", [])
        
        print(f"Total URLs discovered: {len(unique_urls)}")
        print(f"Unique URLs: {len(unique_urls)}")
        print(f"Links with metadata: {len(links_with_metadata)}")
        
        # Display URLs with metadata if available
        if links_with_metadata:
            print(f"\n📋 Discovered URLs with Metadata:")
            print("-" * 50)
            
            for i, link in enumerate(links_with_metadata, 1):
                print(f"{i:3d}. {link['url']}")
                if link.get('title'):
                    print(f"     Title: {link['title']}")
                if link.get('description'):
                    print(f"     Description: {link['description']}")
                print()
        else:
            # Fallback to simple URL list
            print(f"\n📋 Discovered URLs:")
            print("-" * 50)
            
            for i, url in enumerate(unique_urls, 1):
                print(f"{i:3d}. {url}")
        
        # Categorize URLs
        print(f"\n📂 URL Categories:")
        print("-" * 50)
        
        for category, category_urls in categories.items():
            print(f"{category}: {len(category_urls)} URLs")
            for url in category_urls[:5]:  # Show first 5 URLs in each category
                print(f"  • {url}")
            if len(category_urls) > 5:
                print(f"  ... and {len(category_urls) - 5} more")
            print()
        
        # Display file information
        if "files" in result:
            file_info = result["files"]
            print("💾 Export Results")
            print("=" * 50)
            print(f"✅ Website map exported to: {file_info['json_file']}")
            print(f"   File size: {file_info['json_size']} characters")
            print(f"✅ URL list exported to: {file_info['txt_file']}")
        
        # Display summary
        print(f"\n🎉 Website mapping completed successfully!")
        print(f"📊 Summary:")
        print(f"   • Website: {website_url}")
        print(f"   • Total URLs: {len(unique_urls)}")
        print(f"   • Categories: {len(categories)}")
        if "files" in result:
            print(f"   • JSON export: {result['files']['json_file']}")
            print(f"   • URL list: {result['files']['txt_file']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Website mapping failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your API keys in environment variables")
        print("2. Verify internet connectivity")
        print("3. Check Firecrawl API status")
        print("4. Review error logs for details")
        return False


def map_website_simple(url: str, search_term: str = None) -> dict:
    """
    Simple function to map a website and return results
    
    Args:
        url: Website URL to map
        search_term: Optional search term to filter URLs
        
    Returns:
        Dictionary with mapping results
    """
    try:
        # Create client without connection test for simple usage
        firecrawl_client, success, error_msg = FirecrawlClient.create_client(test_connection=False)
        
        if not success:
            return {"error": error_msg}
        
        # Map the website with basic options
        result = firecrawl_client.map_website_complete(
            url=url,
            search_term=search_term,
            include_sitemap=False,
            include_subdomains=False,
            ignore_query_params=False,
            save_files=False
        )
        
        return result
        
    except Exception as e:
        return {"error": f"Website mapping failed: {str(e)}"}


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)