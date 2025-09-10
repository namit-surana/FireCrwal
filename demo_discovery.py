#!/usr/bin/env python3
"""
Simple Demo script for BlueJay TIC Certification Database Discovery Engine
"""

import os
import sys
import json
from pathlib import Path


# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from discovery.firecrawl_client import FirecrawlClient


def main():
    """Main demo function"""
    print("🚀 BlueJay TIC Certification Database - Discovery Engine Demo")
    print("=" * 70)
    
    try:
        print("✅ Core modules imported successfully")
        
        # Initialize Firecrawl client
        print("\n🌐 Initializing Firecrawl client...")
        firecrawl_client, success, error_msg = FirecrawlClient.create_client(test_connection=False)
        
        if not success:
            print(f"❌ {error_msg}")
            if "Configuration validation failed" in error_msg:
                print("Please check your environment variables and API keys")
            return False
        
        print("✅ Firecrawl client ready")
        
        # Get certification data from user
        print("\n📝 Enter certification details:")
        
        certification_data = {}
        certification_data["name"] = input("Enter certification name (e.g., FSSAI License/Registration): ").strip()
        certification_data["issuing_body"] = input("Enter issuing body (e.g., Food Safety and Standards Authority of India): ").strip()
        certification_data["region"] = input("Enter region/country (e.g., India): ").strip()
        certification_data["description"] = input("Enter description (optional): ").strip()
        certification_data["official_link"] = input("Enter official website URL (e.g., https://foscos.fssai.gov.in/): ").strip()
        
        # Validate required fields
        if not certification_data["name"] or not certification_data["issuing_body"] or not certification_data["official_link"]:
            print("❌ Missing required fields. Please provide name, issuing body, and official link.")
            return False
        
        print(f"\n🎯 Starting discovery for: {certification_data['name']}")
        print(f"   Issuing Body: {certification_data['issuing_body']}")
        print(f"   Region: {certification_data['region']}")
        print(f"   Official Link: {certification_data['official_link']}")
        
        # Ask if user wants to map the website
        print(f"\n🗺️  Website Mapping")
        print("=" * 50)
        
        map_website = input("Do you want to map the official website? (y/n): ").strip().lower()
        
        if map_website in ['y', 'yes']:
            print(f"\n🚀 Starting website mapping for: {certification_data['official_link']}")
            
            # Ask for optional search term
            search_term = input("Enter optional search term to filter URLs (press Enter to skip): ").strip()
            
            # Call the website mapping function
            try:
                print("   This may take a few minutes depending on website size...")
                
                # Use the simple mapping function
                links = firecrawl_client.map_website_simple(
                    url=certification_data["official_link"],
                    search=search_term if search_term else None
                )
                
                if not links:
                    print("❌ No links found")
                else:
                    print("✅ Website mapping completed successfully!")
                    
                    print(f"\n📊 Website Map Results")
                    print("=" * 50)
                    print(f"Total links discovered: {len(links)}")
                    
                    # Show first 10 links with metadata
                    print(f"\n📋 Sample Discovered Links:")
                    print("-" * 50)
                    for i, link in enumerate(links[:10], 1):
                        print(f"{i:3d}. {link['url']}")
                        if link['title']:
                            print(f"     Title: {link['title']}")
                        if link['description']:
                            print(f"     Description: {link['description'][:100]}...")
                        print()
                    
                    if len(links) > 10:
                        print(f"     ... and {len(links) - 10} more links")
                    
                    # Save results with certification data
                    output_file = f"certification_map_{certification_data['name'].replace(' ', '_').replace('/', '_')}.json"
                    export_data = {
                        "certification": certification_data,
                        "search_term": search_term if search_term else None,
                        "mapping_timestamp": str(Path().cwd()),
                        "total_links": len(links),
                        "links": links
                    }
                    
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"\n💾 Results exported to: {output_file}")
                    
            except Exception as e:
                print(f"❌ Website mapping failed: {e}")
        else:
            print("⏭️  Skipping website mapping")
        
        # Display summary
        print(f"\n🎉 Discovery demo completed successfully!")
        print(f"📊 Summary:")
        print(f"   • Certification: {certification_data['name']}")
        print(f"   • Issuing Body: {certification_data['issuing_body']}")
        print(f"   • Region: {certification_data['region']}")
        print(f"   • Official Link: {certification_data['official_link']}")
        
        if map_website in ['y', 'yes'] and 'links' in locals():
            print(f"   • Search Term: {search_term if search_term else 'None (all URLs)'}")
            print(f"   • Links Discovered: {len(links)}")
            print(f"   • Export File: {output_file}")
        
        print("\nNext steps:")
        print("1. Review the exported results")
        print("2. Use the discovered URLs for further analysis")
        print("3. Extract content from relevant pages")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your API keys in environment variables")
        print("2. Verify internet connectivity")
        print("3. Check Firecrawl API status")
        print("4. Review error logs for details")
        return False
'''
{'data': {'api_key': 'qwertyuiop'}}
'''
@app.post("/function_llm")
def function_llm(item: data):

    '''
    run llm using the data

    this section will be doing the main function of the llm work 
    '''
    resp = clause.run(data)

    return {"body":resp}

# ========
# test using python code
import requests
resp = resquest.post("xxxxxx/function_llm", json={"data":{"api_key":"qwertyuiop"}})


'''
test using local cmd
curl -X POST "http://localhost:8000/function_llm" -H "Content-Type: application/json" -d '{"data": {"api_key": "qwertyuiop"}}'
'''

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)