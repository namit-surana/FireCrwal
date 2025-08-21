"""
Website mapper component for discovering website structure and relevant pages
"""

import re
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse


class WebsiteMapper:
    """
    Maps website structure and discovers relevant pages for certification discovery
    """
    
    def __init__(self, firecrawl_client):
        """
        Initialize website mapper
        
        Args:
            firecrawl_client: Initialized Firecrawl client
        """
        self.firecrawl_client = firecrawl_client
        
        # Common patterns for certification-related content
        self.certification_patterns = {
            "main_certification": [
                r"certif", r"licen", r"regist", r"approv", r"accred",
                r"standar", r"complian", r"regulat", r"requir"
            ],
            "application_forms": [
                r"form", r"applic", r"submi", r"regist", r"enroll",
                r"download", r"fill", r"complete", r"apply"
            ],
            "training_materials": [
                r"train", r"educat", r"learn", r"course", r"workshop",
                r"seminar", r"certif", r"qualif", r"skill"
            ],
            "audit_guidelines": [
                r"audit", r"inspect", r"assess", r"evaluat", r"review",
                r"check", r"verif", r"validat", r"compliance"
            ],
            "fee_structures": [
                r"fee", r"cost", r"price", r"charg", r"payment",
                r"billing", r"tariff", r"rate", r"amount"
            ],
            "regional_offices": [
                r"office", r"branch", r"locat", r"address", r"contact",
                r"region", r"state", r"city", r"area"
            ]
        }
        
        print("Website mapper initialized successfully")
    
    def discover_website_structure(
        self,
        official_link: str,
        certification_data: Dict[str, Any],
        discovery_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Discover the complete website structure for a certification
        
        Args:
            official_link: Official website URL
            certification_data: Certification information
            discovery_options: Optional discovery configuration
            
        Returns:
            Website structure information
        """
        try:
            print(f"Starting website structure discovery for: {official_link}")
            
            # Step 1: Map the website structure
            website_map = self._map_website_structure(official_link, certification_data)
            
            # Step 2: Discover additional pages through crawling
            discovered_pages = self._crawl_website_pages(official_link, certification_data, discovery_options)
            
            # Step 3: Analyze and categorize discovered pages
            categorized_pages = self._categorize_discovered_pages(discovered_pages, certification_data)
            
            # Step 4: Compile website structure
            website_structure = {
                "official_url": official_link,
                "domain": urlparse(official_link).netloc,
                "total_pages": len(discovered_pages),
                "relevant_pages": categorized_pages,
                "page_categories": {
                    category: len(pages) for category, pages in categorized_pages.items()
                },
                "discovery_metadata": {
                    "mapping_method": "firecrawl_map_and_crawl",
                    "certification_name": certification_data.get("name", "Unknown"),
                    "issuing_body": certification_data.get("issuing_body", "Unknown"),
                    "region": certification_data.get("region", "Unknown")
                }
            }
            
            print(f"Website structure discovery completed. Found {len(discovered_pages)} total pages")
            return website_structure
            
        except Exception as e:
            print(f"Website structure discovery failed: {e}")
            raise Exception(f"Website structure discovery failed: {e}")
    
    def _map_website_structure(
        self,
        official_link: str,
        certification_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map the basic website structure using Firecrawl Map endpoint
        
        Args:
            official_link: Official website URL
            certification_data: Certification information
            
        Returns:
            Basic website structure
        """
        try:
            print("Mapping website structure using Firecrawl Map endpoint")
            
            # Generate search terms based on certification data
            search_terms = self._generate_search_terms(certification_data)
            
            website_map = {}
            
            # Map with different search terms to get comprehensive coverage
            for search_term in search_terms:
                try:
                    print(f"Mapping with search term: {search_term}")
                    
                    map_result = self.firecrawl_client.map_website(
                        url=official_link,
                        search=search_term
                    )
                    
                    if map_result and isinstance(map_result, dict):
                        # Extract links from map result
                        links = map_result.get("links", []) or map_result.get("urls", [])
                        
                        if links:
                            website_map[search_term] = {
                                "search_term": search_term,
                                "links_found": len(links),
                                "urls": links[:50]  # Limit to first 50 URLs per search
                            }
                    
                except Exception as e:
                    print(f"Mapping failed for search term '{search_term}': {e}")
                    continue
            
            print(f"Website mapping completed. Found {len(website_map)} search results")
            return website_map
            
        except Exception as e:
            print(f"Website mapping failed: {e}")
            raise Exception(f"Website mapping failed: {e}")
    
    def _crawl_website_pages(
        self,
        official_link: str,
        certification_data: Dict[str, Any],
        discovery_options: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Crawl the website to discover additional pages
        
        Args:
            official_link: Official website URL
            certification_data: Certification information
            discovery_options: Optional discovery configuration
            
        Returns:
            List of discovered pages
        """
        try:
            print("Crawling website to discover additional pages")
            
            # Prepare crawl options
            crawl_options = self._prepare_crawl_options(certification_data, discovery_options)
            
            # Start crawling
            crawl_result = self.firecrawl_client.crawl_website(
                url=official_link,
                **crawl_options
            )
            
            if not crawl_result:
                print("Crawl failed, falling back to basic discovery")
                return self._fallback_page_discovery(official_link, certification_data)
            
            # Extract page information from crawl result
            discovered_pages = self._extract_pages_from_crawl(crawl_result)
            
            print(f"Website crawling completed. Found {len(discovered_pages)} pages")
            return discovered_pages
            
        except Exception as e:
            print(f"Website crawling failed: {e}")
            print("Falling back to basic page discovery")
            return self._fallback_page_discovery(official_link, certification_data)
    
    def _prepare_crawl_options(
        self,
        certification_data: Dict[str, Any],
        discovery_options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Prepare crawl options based on certification data and discovery options
        
        Args:
            certification_data: Certification information
            discovery_options: Optional discovery configuration
            
        Returns:
            Crawl options dictionary
        """
        # Default crawl options
        crawl_options = {
            "limit": discovery_options.get("max_pages", 200) if discovery_options else 200,
            "max_depth": discovery_options.get("max_depth", 8) if discovery_options else 8,
            "include_paths": [],
            "exclude_paths": []
        }
        
        # Generate include paths based on certification patterns
        for category, patterns in self.certification_patterns.items():
            for pattern in patterns:
                crawl_options["include_paths"].extend([
                    f"*/{pattern}*",
                    f"*/{pattern}*/**"
                ])
        
        # Add certification-specific include paths
        cert_name = certification_data.get("name", "").lower()
        issuing_body = certification_data.get("issuing_body", "").lower()
        
        if cert_name:
            crawl_options["include_paths"].extend([
                f"*/{cert_name.replace(' ', '*')}*",
                f"*/{cert_name.replace(' ', '-')}*"
            ])
        
        if issuing_body:
            # Extract acronyms and key terms
            acronyms = re.findall(r'\b[A-Z]{2,}\b', issuing_body)
            for acronym in acronyms:
                crawl_options["include_paths"].append(f"*/{acronym}*")
        
        # Common exclude paths
        crawl_options["exclude_paths"] = [
            "*/news/*", "*/press/*", "*/events/*", "*/blog/*",
            "*/about/*", "*/contact/*", "*/privacy/*", "*/terms/*",
            "*/sitemap*", "*/robots*", "*/404*", "*/error*"
        ]
        
        # Remove duplicates
        crawl_options["include_paths"] = list(set(crawl_options["include_paths"]))
        crawl_options["exclude_paths"] = list(set(crawl_options["exclude_paths"]))
        
        return crawl_options
    
    def _extract_pages_from_crawl(self, crawl_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract page information from crawl result
        
        Args:
            crawl_result: Result from Firecrawl crawl
            
        Returns:
            List of page information
        """
        try:
            pages = []
            
            # Extract from different possible result structures
            if "data" in crawl_result and isinstance(crawl_result["data"], list):
                for page_data in crawl_result["data"]:
                    page_info = self._extract_page_info(page_data)
                    if page_info:
                        pages.append(page_info)
            
            elif "pages" in crawl_result and isinstance(crawl_result["pages"], list):
                for page_data in crawl_result["pages"]:
                    page_info = self._extract_page_info(page_data)
                    if page_info:
                        pages.append(page_info)
            
            return pages
            
        except Exception as e:
            print(f"Failed to extract pages from crawl result: {e}")
            return []
    
    def _extract_page_info(self, page_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract page information from page data
        
        Args:
            page_data: Page data from crawl result
            
        Returns:
            Page information dictionary or None
        """
        try:
            if not isinstance(page_data, dict):
                return None
            
            # Extract URL
            url = page_data.get("url") or page_data.get("sourceURL")
            if not url:
                return None
            
            # Extract title
            title = page_data.get("title") or page_data.get("metadata", {}).get("title", "Unknown")
            
            # Extract description
            description = page_data.get("description") or page_data.get("metadata", {}).get("description", "")
            
            # Extract content preview
            content_preview = ""
            if "markdown" in page_data:
                content_preview = page_data["markdown"][:200] + "..." if len(page_data["markdown"]) > 200 else page_data["markdown"]
            elif "html" in page_data:
                # Simple HTML to text conversion
                content_preview = re.sub(r'<[^>]+>', '', page_data["html"])[:200] + "..."
            
            return {
                "url": url,
                "title": title,
                "description": description,
                "content_preview": content_preview,
                "metadata": page_data.get("metadata", {}),
                "discovery_method": "crawl"
            }
            
        except Exception as e:
            print(f"Failed to extract page info: {e}")
            return None
    
    def _fallback_page_discovery(
        self,
        official_link: str,
        certification_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Fallback page discovery when crawling fails
        
        Args:
            official_link: Official website URL
            certification_data: Certification information
            
        Returns:
            List of discovered pages
        """
        try:
            print("Using fallback page discovery method")
            
            # Try to scrape the main page to get basic information
            try:
                main_page = self.firecrawl_client.scrape_url(
                    url=official_link,
                    formats=["markdown", "html"]
                )
                
                if main_page:
                    return [{
                        "url": official_link,
                        "title": "Main Page",
                        "description": "Main certification page",
                        "content_preview": "Main page content",
                        "metadata": {},
                        "discovery_method": "fallback_scrape"
                    }]
                    
            except Exception as e:
                print(f"Fallback scraping failed: {e}")
            
            # Return basic page info
            return [{
                "url": official_link,
                "title": "Official Website",
                "description": "Certification official website",
                "content_preview": "Website content not accessible",
                "metadata": {},
                "discovery_method": "fallback_basic"
            }]
            
        except Exception as e:
            print(f"Fallback page discovery failed: {e}")
            return []
    
    def _categorize_discovered_pages(
        self,
        discovered_pages: List[Dict[str, Any]],
        certification_data: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize discovered pages based on content and patterns
        
        Args:
            discovered_pages: List of discovered pages
            certification_data: Certification information
            
        Returns:
            Categorized pages by type
        """
        try:
            categorized_pages = {
                "main_certification_pages": [],
                "application_forms": [],
                "training_materials": [],
                "audit_guidelines": [],
                "fee_structures": [],
                "regional_offices": [],
                "other_relevant_content": []
            }
            
            for page in discovered_pages:
                category = self._categorize_single_page(page, certification_data)
                
                if category in categorized_pages:
                    categorized_pages[category].append(page)
                else:
                    categorized_pages["other_relevant_content"].append(page)
            
            # Remove empty categories
            categorized_pages = {
                k: v for k, v in categorized_pages.items() 
                if v  # Only keep non-empty lists
            }
            
            print(f"Page categorization completed. Found {len(categorized_pages)} categories")
            return categorized_pages
            
        except Exception as e:
            print(f"Page categorization failed: {e}")
            return {"other_relevant_content": discovered_pages}
    
    def _categorize_single_page(
        self,
        page: Dict[str, Any],
        certification_data: Dict[str, Any]
    ) -> str:
        """
        Categorize a single page based on its content and metadata
        
        Args:
            page: Page information
            certification_data: Certification information
            
        Returns:
            Category name
        """
        try:
            url = page.get("url", "").lower()
            title = page.get("title", "").lower()
            description = page.get("description", "").lower()
            content_preview = page.get("content_preview", "").lower()
            
            # Combine all text for analysis
            combined_text = f"{url} {title} {description} {content_preview}"
            
            # Score each category based on pattern matches
            category_scores = {}
            
            for category, patterns in self.certification_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, combined_text, re.IGNORECASE))
                    score += matches * 2  # Pattern matches get higher weight
                    
                    # URL path matches get bonus points
                    if re.search(pattern, url, re.IGNORECASE):
                        score += 5
                    
                    # Title matches get bonus points
                    if re.search(pattern, title, re.IGNORECASE):
                        score += 3
                
                category_scores[category] = score
            
            # Find the category with the highest score
            if category_scores:
                best_category = max(category_scores, key=category_scores.get)
                if category_scores[best_category] > 0:
                    return best_category
            
            # Default to main certification if no clear category
            return "main_certification_pages"
            
        except Exception as e:
            print(f"Page categorization failed: {e}")
            return "other_relevant_content"
    
    def _generate_search_terms(self, certification_data: Dict[str, Any]) -> List[str]:
        """
        Generate search terms for website mapping based on certification data
        
        Args:
            certification_data: Certification information
            
        Returns:
            List of search terms
        """
        search_terms = []
        
        # Extract key terms from certification name
        cert_name = certification_data.get("name", "")
        if cert_name:
            # Split by common separators and add to search terms
            name_parts = re.split(r'[\/\-\s]+', cert_name)
            for part in name_parts:
                if len(part) > 2:  # Only add meaningful parts
                    search_terms.append(part.lower())
        
        # Add issuing body terms
        issuing_body = certification_data.get("issuing_body", "")
        if issuing_body:
            # Extract acronyms
            acronyms = re.findall(r'\b[A-Z]{2,}\b', issuing_body)
            for acronym in acronyms:
                search_terms.append(acronym.lower())
            
            # Extract key words
            body_words = re.findall(r'\b\w{4,}\b', issuing_body)
            for word in body_words:
                if word.lower() not in ["authority", "administration", "department", "ministry"]:
                    search_terms.append(word.lower())
        
        # Add common certification terms
        common_terms = ["certification", "license", "registration", "approval", "compliance"]
        search_terms.extend(common_terms)
        
        # Remove duplicates and limit length
        search_terms = list(set(search_terms))[:10]
        
        return search_terms
