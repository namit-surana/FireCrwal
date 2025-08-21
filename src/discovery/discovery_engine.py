"""
Main discovery engine for BlueJay TIC Certification Database
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from .website_mapper import WebsiteMapper
from .content_categorizer import ContentCategorizer
from .quality_scorer import QualityScorer


@dataclass
class DiscoveryResult:
    """Result of a discovery operation"""
    certification_name: str
    issuing_body: str
    region: str
    discovery_timestamp: str
    website_structure: Dict[str, Any]
    discovered_content: Dict[str, List[Dict[str, Any]]]
    quality_metrics: Dict[str, Any]
    metadata: Dict[str, Any]


class DiscoveryEngine:
    """
    Main discovery engine that orchestrates the entire discovery process
    for any certification
    """
    
    def __init__(self, firecrawl_client):
        """
        Initialize the discovery engine
        
        Args:
            firecrawl_client: Initialized Firecrawl client
        """
        self.firecrawl_client = firecrawl_client
        self.website_mapper = WebsiteMapper(firecrawl_client)
        self.content_categorizer = ContentCategorizer()
        self.quality_scorer = QualityScorer()
        
        print("Discovery engine initialized successfully")
    
    def discover_certification(
        self,
        certification_data: Dict[str, Any],
        discovery_options: Optional[Dict[str, Any]] = None
    ) -> DiscoveryResult:
        """
        Discover comprehensive information for a certification
        
        Args:
            certification_data: Basic certification information
            discovery_options: Optional discovery configuration
            
        Returns:
            DiscoveryResult with comprehensive discovered information
        """
        start_time = time.time()
        
        try:
            print(f"Starting discovery for: {certification_data.get('name', 'Unknown')}")
            
            # Extract basic information
            cert_name = certification_data.get('name', 'Unknown Certification')
            issuing_body = certification_data.get('issuing_body', 'Unknown Body')
            region = certification_data.get('region', 'Unknown Region')
            official_link = certification_data.get('official_link')
            
            if not official_link:
                raise Exception("Official link is required for discovery")
            
            # Step 1: Website Structure Discovery
            print("Phase 1: Discovering website structure")
            website_structure = self.website_mapper.discover_website_structure(
                official_link,
                certification_data,
                discovery_options
            )
            
            # Step 2: Content Discovery and Categorization
            print("Phase 2: Discovering and categorizing content")
            discovered_content = self._discover_and_categorize_content(
                website_structure,
                certification_data,
                discovery_options
            )
            
            # Step 3: Quality Assessment
            print("Phase 3: Assessing content quality")
            quality_metrics = self.quality_scorer.assess_discovery_quality(
                website_structure,
                discovered_content,
                certification_data
            )
            
            # Step 4: Compile Results
            discovery_time = time.time() - start_time
            print(f"Discovery completed in {discovery_time:.2f} seconds")
            
            result = DiscoveryResult(
                certification_name=cert_name,
                issuing_body=issuing_body,
                region=region,
                discovery_timestamp=datetime.now(datetime.timezone.utc).isoformat(),
                website_structure=website_structure,
                discovered_content=discovered_content,
                quality_metrics=quality_metrics,
                metadata={
                    "discovery_time_seconds": discovery_time,
                    "total_pages_discovered": website_structure.get("total_pages", 0),
                    "relevant_pages_found": website_structure.get("relevant_pages", 0),
                    "content_categories_found": len(discovered_content),
                    "discovery_options_used": discovery_options or {}
                }
            )
            
            print(f"Discovery completed successfully for {cert_name}")
            return result
            
        except Exception as e:
            print(f"Discovery failed: {e}")
            raise Exception(f"Discovery failed: {e}")
    
    def _discover_and_categorize_content(
        self,
        website_structure: Dict[str, Any],
        certification_data: Dict[str, Any],
        discovery_options: Optional[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Discover and categorize content from the website structure
        
        Args:
            website_structure: Discovered website structure
            certification_data: Original certification data
            discovery_options: Discovery configuration
            
        Returns:
            Categorized content by type
        """
        try:
            discovered_content = {
                "main_certification_pages": [],
                "application_forms": [],
                "training_materials": [],
                "audit_guidelines": [],
                "fee_structures": [],
                "regional_offices": [],
                "other_relevant_content": []
            }
            
            # Get relevant pages for content extraction
            relevant_pages = website_structure.get("relevant_pages", [])
            
            if not relevant_pages:
                print("No relevant pages found for content extraction")
                return discovered_content
            
            # Extract content from relevant pages
            for page_info in relevant_pages:
                try:
                    page_url = page_info.get("url")
                    if not page_url:
                        continue
                    
                    print(f"Extracting content from: {page_url}")
                    
                    # Extract content using Firecrawl
                    content = self.firecrawl_client.scrape_url(
                        url=page_url,
                        formats=["markdown", "html"],
                        parsePDF=True,
                        actions=[
                            {"type": "wait", "milliseconds": 3000},
                            {"type": "screenshot"}
                        ]
                    )
                    
                    if not content:
                        continue
                    
                    # Categorize the content
                    content_category = self.content_categorizer.categorize_content(
                        content,
                        page_info,
                        certification_data
                    )
                    
                    # Add to appropriate category
                    if content_category in discovered_content:
                        discovered_content[content_category].append({
                            "url": page_url,
                            "title": page_info.get("title", "Unknown"),
                            "category": content_category,
                            "content": content,
                            "page_info": page_info,
                            "extraction_timestamp": datetime.now(datetime.timezone.utc).isoformat()
                        })
                    else:
                        discovered_content["other_relevant_content"].append({
                            "url": page_url,
                            "title": page_info.get("title", "Unknown"),
                            "category": content_category,
                            "content": content,
                            "page_info": page_info,
                            "extraction_timestamp": datetime.now(datetime.timezone.utc).isoformat()
                        })
                    
                except Exception as e:
                    print(f"Failed to extract content from {page_url}: {e}")
                    continue
            
            # Remove empty categories
            discovered_content = {
                k: v for k, v in discovered_content.items() 
                if v  # Only keep non-empty lists
            }
            
            print(f"Content discovery completed. Found {len(discovered_content)} categories")
            return discovered_content
            
        except Exception as e:
            print(f"Content discovery and categorization failed: {e}")
            raise Exception(f"Content discovery failed: {e}")
    
    def get_discovery_summary(self, result: DiscoveryResult) -> Dict[str, Any]:
        """
        Get a summary of the discovery results
        
        Args:
            result: Discovery result
            
        Returns:
            Summary of discovery results
        """
        try:
            summary = {
                "certification": {
                    "name": result.certification_name,
                    "issuing_body": result.issuing_body,
                    "region": result.region
                },
                "discovery_stats": {
                    "total_pages_discovered": result.metadata.get("total_pages_discovered", 0),
                    "relevant_pages_found": result.metadata.get("relevant_pages_found", 0),
                    "content_categories_found": result.metadata.get("content_categories_found", 0),
                    "discovery_time_seconds": result.metadata.get("discovery_time_seconds", 0)
                },
                "content_summary": {
                    category: len(content_list) 
                    for category, content_list in result.discovered_content.items()
                },
                "quality_score": result.quality_metrics.get("overall_score", 0),
                "discovery_timestamp": result.discovery_timestamp
            }
            
            return summary
            
        except Exception as e:
            print(f"Failed to generate discovery summary: {e}")
            return {"error": f"Summary generation failed: {e}"}
    
    def export_discovery_result(self, result: DiscoveryResult, format: str = "json") -> str:
        """
        Export discovery result in specified format
        
        Args:
            result: Discovery result to export
            format: Export format (json, dict)
            
        Returns:
            Exported result
        """
        try:
            if format.lower() == "json":
                import json
                return json.dumps(asdict(result), indent=2, default=str)
            elif format.lower() == "dict":
                return asdict(result)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            print(f"Export failed: {e}")
            raise Exception(f"Export failed: {e}")
