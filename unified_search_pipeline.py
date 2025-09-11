#!/usr/bin/env python3
"""
Unified Search and PDF Processing Pipeline
Combines existing Firecrawl search with PDF enhancement functions
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Import existing functions
from Seach_Internet.simple_firecrawl_search_clean import SimpleFirecrawlSearch
from Pdf_scarping.simple_pdf_enhancer import SimplePDFEnhancer

# Load environment variables
load_dotenv()


class UnifiedSearchPipeline:
    """
    Unified pipeline that reuses existing search and PDF processing functions
    """
    
    def __init__(self):
        """Initialize the pipeline using existing components"""
        try:
            # Initialize existing search component
            self.search_api = SimpleFirecrawlSearch()
            
            # Initialize existing PDF enhancer component
            self.pdf_enhancer = SimplePDFEnhancer()
            
            print("✅ Unified Search Pipeline initialized using existing components")
            
        except Exception as e:
            print(f"❌ Failed to initialize pipeline: {e}")
            raise
    
    def _categorize_url(self, url: str) -> str:
        """Categorize URL by file extension"""
        try:
            if url.lower().endswith('.pdf') or 'pdf' in url.lower():
                return 'pdf'
            return 'other'
        except:
            return 'other'
    
    def _separate_pdfs_and_non_pdfs(self, data: List[Dict[str, Any]]) -> tuple:
        """Separate PDFs from non-PDFs"""
        pdf_documents = []
        non_pdf_content = []
        
        for item in data:
            url = item.get('url', '')
            if self._categorize_url(url) == 'pdf':
                pdf_documents.append(item)
            else:
                non_pdf_content.append(item)
        
        return pdf_documents, non_pdf_content
    
    def run_pipeline(self, query: str, limit: int, output_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Run the complete pipeline using existing functions
        
        Args:
            query: Search query
            limit: Number of results
            output_file: Optional output file path
            
        Returns:
            Flat array of items with url and markdown
        """
        print("🚀 Starting Unified Search Pipeline")
        print("=" * 50)
        
        # Step 1: Search using existing search function
        print(f"🔍 Searching: '{query}' (limit: {limit})")
        search_result = self.search_api.search(query, limit)
        
        if not search_result['success']:
            print(f"❌ Search failed: {search_result.get('error')}")
            return []
        
        # Get search data
        search_data = search_result.get('data', [])
        print(f"📊 Search completed: {len(search_data)} results found")
        
        # Step 2: Separate PDFs from non-PDFs
        pdf_documents, non_pdf_content = self._separate_pdfs_and_non_pdfs(search_data)
        
        print(f"📊 Content separation:")
        print(f"   📄 PDF documents: {len(pdf_documents)}")
        print(f"   🌐 Non-PDF content: {len(non_pdf_content)}")
        
        # Step 3: Enhance PDFs using existing PDF enhancer
        if pdf_documents:
            print(f"🚀 Enhancing {len(pdf_documents)} PDFs using existing PDF enhancer...")
            enhanced_pdfs = self.pdf_enhancer.enhance_pdfs_in_data(pdf_documents)
        else:
            enhanced_pdfs = []
        
        # Step 4: Combine all results
        all_items = enhanced_pdfs + non_pdf_content
        
        print(f"\n✅ Pipeline completed!")
        print(f"   📊 Total results: {len(all_items)}")
        
        # Step 5: Save if requested
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
        # Initialize pipeline using existing components
        pipeline = UnifiedSearchPipeline()
        
        # Example usage - try a simpler query first
        query = "site:https://foscos.fssai.gov.in/ \"FSSAI License/Registration"
        limit = 20
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"unified_search_results_{timestamp}.json"
        
        # Run pipeline using existing functions
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
