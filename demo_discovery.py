#!/usr/bin/env python3
"""
Demo script for BlueJay TIC Certification Database Discovery Engine
"""

import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Main demo function"""
    print("🚀 BlueJay TIC Certification Database - Discovery Engine Demo")
    print("=" * 70)
    
    try:
        # Import required modules
        from core.config import get_config
        from discovery.discovery_engine import DiscoveryEngine
        from discovery.firecrawl_client import FirecrawlClient
        
        print("✅ Core modules imported successfully")
        
        # Create configuration
        config = get_config(test_mode=False)
        
        # Check configuration
        if not config.validate():
            print("❌ Configuration validation failed")
            print("Please check your environment variables and API keys")
            return False
        
        print("✅ Configuration validated successfully")
        
        # Initialize Firecrawl client
        print("\n🌐 Initializing Firecrawl client...")
        firecrawl_client = FirecrawlClient()
        print("✅ Firecrawl client ready")
        
        # Initialize discovery engine
        print("\n🔍 Initializing discovery engine...")
        discovery_engine = DiscoveryEngine(firecrawl_client)
        print("✅ Discovery engine ready")
        
        # FSSAI certification data
        fssai_certification = {
            "name": "FSSAI License/Registration",
            "issuing_body": "Food Safety and Standards Authority of India (FSSAI)",
            "region": "India",
            "description": "Mandatory license for any food business in India, including honey export, proving compliance with Indian food safety and quality standards. Required for production, packaging, storage, and export of honey.",
            "classifications": ["product", "market_access"],
            "mandatory": True,
            "validity": "5 years, renewable",
            "official_link": "https://foscos.fssai.gov.in/"
        }
        
        print(f"\n🎯 Starting discovery for: {fssai_certification['name']}")
        print(f"   Issuing Body: {fssai_certification['issuing_body']}")
        print(f"   Region: {fssai_certification['region']}")
        print(f"   Official Link: {fssai_certification['official_link']}")
        
        # Discovery options
        discovery_options = {
            "max_pages": 100,  # Limit for demo
            "max_depth": 5,    # Limit depth for demo
            "timeout": 300     # 5 minutes timeout
        }
        
        print(f"\n⚙️  Discovery options: {json.dumps(discovery_options, indent=2)}")
        
        # Start discovery
        print("\n🚀 Starting discovery process...")
        print("   This may take several minutes depending on website size...")
        
        discovery_result = discovery_engine.discover_certification(
            fssai_certification,
            discovery_options
        )
        
        print("✅ Discovery completed successfully!")
        
        # Display discovery summary
        print("\n📊 Discovery Summary")
        print("=" * 50)
        
        summary = discovery_engine.get_discovery_summary(discovery_result)
        
        print(f"Certification: {summary['certification']['name']}")
        print(f"Issuing Body: {summary['certification']['issuing_body']}")
        print(f"Region: {summary['certification']['region']}")
        print()
        
        print("Discovery Statistics:")
        print(f"  Total Pages Discovered: {summary['discovery_stats']['total_pages_discovered']}")
        print(f"  Relevant Pages Found: {summary['discovery_stats']['relevant_pages_found']}")
        print(f"  Content Categories Found: {summary['discovery_stats']['content_categories_found']}")
        print(f"  Discovery Time: {summary['discovery_stats']['discovery_time_seconds']:.2f} seconds")
        print()
        
        print("Content Summary:")
        for category, count in summary['content_summary'].items():
            print(f"  {category}: {count} pages")
        print()
        
        print(f"Overall Quality Score: {summary['quality_score']:.2f}/100")
        
        # Display quality metrics
        print("\n🔍 Quality Metrics")
        print("=" * 50)
        
        quality_metrics = discovery_result.quality_metrics
        print(f"Overall Score: {quality_metrics['overall_score']:.2f}/100")
        print()
        
        score_breakdown = quality_metrics['score_breakdown']
        print("Score Breakdown:")
        print(f"  Relevance: {score_breakdown['relevance']:.2f}/100")
        print(f"  Completeness: {score_breakdown['completeness']:.2f}/100")
        print(f"  Freshness: {score_breakdown['freshness']:.2f}/100")
        print(f"  Accessibility: {score_breakdown['accessibility']:.2f}/100")
        print()
        
        print("Quality Metrics:")
        print(f"  Coverage Percentage: {quality_metrics['coverage_percentage']:.1f}%")
        print(f"  Depth Score: {quality_metrics['depth_score']:.1f}/100")
        print()
        
        # Display quality insights
        print("💡 Quality Insights")
        print("=" * 50)
        
        insights = quality_metrics['quality_insights']
        
        if insights.get('strengths'):
            print("Strengths:")
            for strength in insights['strengths']:
                print(f"  ✅ {strength}")
            print()
        
        if insights.get('weaknesses'):
            print("Weaknesses:")
            for weakness in insights['weaknesses']:
                print(f"  ❌ {weakness}")
            print()
        
        if insights.get('opportunities'):
            print("Opportunities:")
            for opportunity in insights['opportunities']:
                print(f"  🚀 {opportunity}")
            print()
        
        if insights.get('threats'):
            print("Threats:")
            for threat in insights['threats']:
                print(f"  ⚠️  {threat}")
            print()
        
        # Display recommendations
        print("📋 Recommendations")
        print("=" * 50)
        
        recommendations = quality_metrics['recommendations']
        for i, recommendation in enumerate(recommendations, 1):
            print(f"  {i}. {recommendation}")
        print()
        
        # Export results
        print("💾 Exporting Results")
        print("=" * 50)
        
        # Export to JSON
        json_output = discovery_engine.export_discovery_result(discovery_result, "json")
        
        # Save to file
        output_file = "fssai_discovery_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(json_output)
        
        print(f"✅ Results exported to: {output_file}")
        print(f"   File size: {len(json_output)} characters")
        
        # Display sample discovered content
        print("\n📄 Sample Discovered Content")
        print("=" * 50)
        
        for category, content_list in discovery_result.discovered_content.items():
            if content_list:
                print(f"\n{category.upper()} ({len(content_list)} pages):")
                for i, content_item in enumerate(content_list[:3], 1):  # Show first 3 items
                    print(f"  {i}. {content_item['title']}")
                    print(f"     URL: {content_item['url']}")
                    if content_item.get('content_preview'):
                        preview = content_item['content_preview'][:100] + "..." if len(content_item['content_preview']) > 100 else content_item['content_preview']
                        print(f"     Preview: {preview}")
                    print()
        
        print("🎉 Discovery demo completed successfully!")
        print("\nNext steps:")
        print("1. Review the JSON output file")
        print("2. Analyze quality metrics and insights")
        print("3. Use recommendations to improve discovery")
        print("4. Move to content extraction phase")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your API keys in environment variables")
        print("2. Verify internet connectivity")
        print("3. Check Firecrawl API status")
        print("4. Review error logs for details")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
