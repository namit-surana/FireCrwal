"""
AI-powered content categorizer for BlueJay TIC Certification Database
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone


class ContentCategorizer:
    """
    AI-powered content categorizer that intelligently classifies discovered content
    """
    
    def __init__(self):
        """Initialize the content categorizer"""
        
        # Content category definitions with detailed patterns
        self.content_categories = {
            "main_certification_pages": {
                "description": "Core certification information and requirements",
                "patterns": [
                    r"certif", r"licen", r"regist", r"approv", r"accred",
                    r"standar", r"complian", r"regulat", r"requir", r"overview",
                    r"introduction", r"about", r"what.*is", r"definition"
                ],
                "keywords": [
                    "certification", "license", "registration", "approval", "accreditation",
                    "standard", "compliance", "regulation", "requirement", "overview"
                ]
            },
            "application_forms": {
                "description": "Forms, applications, and submission procedures",
                "patterns": [
                    r"form", r"applic", r"submi", r"regist", r"enroll",
                    r"download", r"fill", r"complete", r"apply", r"submit",
                    r"enrollment", r"registration", r"application.*process"
                ],
                "keywords": [
                    "form", "application", "submit", "registration", "enrollment",
                    "download", "fill", "complete", "apply", "process"
                ]
            },
            "training_materials": {
                "description": "Training courses, qualifications, and educational content",
                "patterns": [
                    r"train", r"educat", r"learn", r"course", r"workshop",
                    r"seminar", r"certif", r"qualif", r"skill", r"education",
                    r"training.*program", r"learning.*material", r"qualification.*requirement"
                ],
                "keywords": [
                    "training", "education", "learn", "course", "workshop",
                    "seminar", "certification", "qualification", "skill", "program"
                ]
            },
            "audit_guidelines": {
                "description": "Audit procedures, inspection guidelines, and compliance checks",
                "patterns": [
                    r"audit", r"inspect", r"assess", r"evaluat", r"review",
                    r"check", r"verif", r"validat", r"compliance", r"procedure",
                    r"guideline", r"checklist", r"inspection.*process", r"audit.*procedure"
                ],
                "keywords": [
                    "audit", "inspection", "assessment", "evaluation", "review",
                    "check", "verification", "validation", "compliance", "procedure"
                ]
            },
            "fee_structures": {
                "description": "Cost information, fee schedules, and payment details",
                "patterns": [
                    r"fee", r"cost", r"price", r"charg", r"payment",
                    r"billing", r"tariff", r"rate", r"amount", r"cost.*structure",
                    r"fee.*schedule", r"payment.*method", r"cost.*breakdown"
                ],
                "keywords": [
                    "fee", "cost", "price", "charge", "payment", "billing",
                    "tariff", "rate", "amount", "structure", "schedule"
                ]
            },
            "regional_offices": {
                "description": "Office locations, contact information, and regional details",
                "patterns": [
                    r"office", r"branch", r"locat", r"address", r"contact",
                    r"region", r"state", r"city", r"area", r"location",
                    r"contact.*information", r"office.*location", r"regional.*office"
                ],
                "keywords": [
                    "office", "branch", "location", "address", "contact",
                    "region", "state", "city", "area", "information"
                ]
            }
        }
        
        # Content type indicators
        self.content_type_indicators = {
            "pdf_document": [".pdf", "pdf", "document", "download"],
            "form": ["form", "application", "submit", "fill", "complete"],
            "guideline": ["guideline", "procedure", "manual", "instruction"],
            "contact": ["contact", "address", "phone", "email", "location"],
            "overview": ["overview", "introduction", "about", "what is", "definition"]
        }
        
        print("Content categorizer initialized successfully")
    
    def categorize_content(
        self,
        content: Dict[str, Any],
        page_info: Dict[str, Any],
        certification_data: Dict[str, Any]
    ) -> str:
        """
        Categorize content using AI-powered analysis and pattern matching
        
        Args:
            content: Extracted content from Firecrawl
            page_info: Page metadata and information
            certification_data: Original certification data
            
        Returns:
            Content category name
        """
        try:
            print(f"Categorizing content from: {page_info.get('url', 'Unknown URL')}")
            
            # Extract text content for analysis
            text_content = self._extract_text_content(content, page_info)
            
            # Perform AI-powered categorization
            ai_category = self._ai_categorize_content(text_content, page_info, certification_data)
            
            # Perform pattern-based categorization as backup
            pattern_category = self._pattern_based_categorization(text_content, page_info)
            
            # Combine AI and pattern results
            final_category = self._combine_categorization_results(
                ai_category, pattern_category, text_content, page_info
            )
            
            print(f"Content categorized as: {final_category}")
            return final_category
            
        except Exception as e:
            print(f"Content categorization failed: {e}")
            return "other_relevant_content"
    
    def _extract_text_content(
        self,
        content: Dict[str, Any],
        page_info: Dict[str, Any]
    ) -> str:
        """
        Extract and combine text content from various sources
        
        Args:
            content: Extracted content from Firecrawl
            page_info: Page metadata and information
            
        Returns:
            Combined text content for analysis
        """
        text_parts = []
        
        # Extract from page info
        if page_info.get("title"):
            text_parts.append(page_info["title"])
        
        if page_info.get("description"):
            text_parts.append(page_info["description"])
        
        if page_info.get("content_preview"):
            text_parts.append(page_info["content_preview"])
        
        # Extract from Firecrawl content
        if isinstance(content, dict):
            if "markdown" in content:
                text_parts.append(content["markdown"])
            
            if "html" in content:
                # Simple HTML to text conversion
                html_text = re.sub(r'<[^>]+>', '', content["html"])
                text_parts.append(html_text)
            
            if "metadata" in content:
                metadata = content["metadata"]
                if metadata.get("title"):
                    text_parts.append(metadata["title"])
                if metadata.get("description"):
                    text_parts.append(metadata["description"])
        
        # Combine all text parts
        combined_text = " ".join(text_parts)
        
        # Clean and normalize text
        cleaned_text = re.sub(r'\s+', ' ', combined_text).strip()
        
        return cleaned_text.lower()
    
    def _ai_categorize_content(
        self,
        text_content: str,
        page_info: Dict[str, Any],
        certification_data: Dict[str, Any]
    ) -> str:
        """
        AI-powered content categorization using advanced text analysis
        
        Args:
            text_content: Combined text content
            page_info: Page metadata
            certification_data: Original certification data
            
        Returns:
            AI-determined category
        """
        try:
            # Advanced text analysis for categorization
            category_scores = {}
            
            for category_name, category_info in self.content_categories.items():
                score = 0
                
                # Pattern matching with weighted scoring
                for pattern in category_info["patterns"]:
                    matches = len(re.findall(pattern, text_content, re.IGNORECASE))
                    score += matches * 3  # Pattern matches get high weight
                
                # Keyword matching
                for keyword in category_info["keywords"]:
                    if keyword.lower() in text_content:
                        score += 5  # Exact keyword matches get highest weight
                
                # URL path analysis
                url = page_info.get("url", "").lower()
                for pattern in category_info["patterns"]:
                    if re.search(pattern, url, re.IGNORECASE):
                        score += 8  # URL matches get very high weight
                
                # Title analysis
                title = page_info.get("title", "").lower()
                for pattern in category_info["patterns"]:
                    if re.search(pattern, title, re.IGNORECASE):
                        score += 6  # Title matches get high weight
                
                # Content type analysis
                content_type_score = self._analyze_content_type(text_content, page_info)
                score += content_type_score
                
                # Certification relevance scoring
                relevance_score = self._calculate_certification_relevance(
                    text_content, certification_data
                )
                score += relevance_score
                
                category_scores[category_name] = score
            
            # Find the category with the highest score
            if category_scores:
                best_category = max(category_scores, key=category_scores.get)
                if category_scores[best_category] > 10:  # Minimum threshold
                    return best_category
            
            # Default fallback
            return "other_relevant_content"
            
        except Exception as e:
            print(f"AI categorization failed: {e}")
            return "other_relevant_content"
    
    def _pattern_based_categorization(
        self,
        text_content: str,
        page_info: Dict[str, Any]
    ) -> str:
        """
        Pattern-based categorization as backup method
        
        Args:
            text_content: Combined text content
            page_info: Page metadata
            
        Returns:
            Pattern-determined category
        """
        try:
            # Simple pattern matching for backup categorization
            for category_name, category_info in self.content_categories.items():
                for pattern in category_info["patterns"]:
                    if re.search(pattern, text_content, re.IGNORECASE):
                        return category_name
            
            return "other_relevant_content"
            
        except Exception as e:
            print(f"Pattern-based categorization failed: {e}")
            return "other_relevant_content"
    
    def _analyze_content_type(
        self,
        text_content: str,
        page_info: Dict[str, Any]
    ) -> int:
        """
        Analyze content type and return relevance score
        
        Args:
            text_content: Combined text content
            page_info: Page metadata
            
        Returns:
            Content type relevance score
        """
        score = 0
        
        # Check for PDF indicators
        if any(indicator in text_content for indicator in self.content_type_indicators["pdf_document"]):
            score += 3
        
        # Check for form indicators
        if any(indicator in text_content for indicator in self.content_type_indicators["form"]):
            score += 4
        
        # Check for guideline indicators
        if any(indicator in text_content for indicator in self.content_type_indicators["guideline"]):
            score += 3
        
        # Check for contact indicators
        if any(indicator in text_content for indicator in self.content_type_indicators["contact"]):
            score += 2
        
        # Check for overview indicators
        if any(indicator in text_content for indicator in self.content_type_indicators["overview"]):
            score += 2
        
        return score
    
    def _calculate_certification_relevance(
        self,
        text_content: str,
        certification_data: Dict[str, Any]
    ) -> int:
        """
        Calculate how relevant the content is to the specific certification
        
        Args:
            text_content: Combined text content
            certification_data: Original certification data
            
        Returns:
            Relevance score
        """
        score = 0
        
        # Check for certification name matches
        cert_name = certification_data.get("name", "").lower()
        if cert_name and cert_name in text_content:
            score += 5
        
        # Check for issuing body matches
        issuing_body = certification_data.get("issuing_body", "").lower()
        if issuing_body:
            # Extract acronyms
            acronyms = re.findall(r'\b[A-Z]{2,}\b', issuing_body)
            for acronym in acronyms:
                if acronym.lower() in text_content:
                    score += 3
            
            # Check for key words from issuing body
            body_words = re.findall(r'\b\w{4,}\b', issuing_body)
            for word in body_words:
                if word.lower() in text_content:
                    score += 1
        
        # Check for region matches
        region = certification_data.get("region", "").lower()
        if region and region in text_content:
            score += 2
        
        return score
    
    def _combine_categorization_results(
        self,
        ai_category: str,
        pattern_category: str,
        text_content: str,
        page_info: Dict[str, Any]
    ) -> str:
        """
        Combine AI and pattern-based categorization results
        
        Args:
            ai_category: AI-determined category
            pattern_category: Pattern-determined category
            text_content: Combined text content
            page_info: Page metadata
            
        Returns:
            Final combined category
        """
        # If AI and pattern agree, use that category
        if ai_category == pattern_category and ai_category != "other_relevant_content":
            return ai_category
        
        # If AI found a specific category, prefer it
        if ai_category != "other_relevant_content":
            return ai_category
        
        # If pattern found a specific category, use it
        if pattern_category != "other_relevant_content":
            return pattern_category
        
        # Final fallback
        return "other_relevant_content"
    
    def get_category_description(self, category: str) -> str:
        """
        Get description for a content category
        
        Args:
            category: Category name
            
        Returns:
            Category description
        """
        return self.content_categories.get(category, {}).get("description", "Unknown category")
    
    def get_all_categories(self) -> List[str]:
        """
        Get list of all available content categories
        
        Returns:
            List of category names
        """
        return list(self.content_categories.keys())
    
    def analyze_categorization_confidence(
        self,
        text_content: str,
        page_info: Dict[str, Any],
        certification_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze confidence level of categorization
        
        Args:
            text_content: Combined text content
            page_info: Page metadata
            certification_data: Original certification data
            
        Returns:
            Confidence analysis results
        """
        try:
            confidence_analysis = {
                "text_length": len(text_content),
                "pattern_matches": {},
                "keyword_matches": {},
                "url_relevance": 0,
                "title_relevance": 0,
                "overall_confidence": 0
            }
            
            # Analyze pattern matches
            for category_name, category_info in self.content_categories.items():
                pattern_matches = 0
                for pattern in category_info["patterns"]:
                    matches = len(re.findall(pattern, text_content, re.IGNORECASE))
                    pattern_matches += matches
                
                confidence_analysis["pattern_matches"][category_name] = pattern_matches
            
            # Analyze keyword matches
            for category_name, category_info in self.content_categories.items():
                keyword_matches = 0
                for keyword in category_info["keywords"]:
                    if keyword.lower() in text_content:
                        keyword_matches += 1
                
                confidence_analysis["keyword_matches"][category_name] = keyword_matches
            
            # Analyze URL relevance
            url = page_info.get("url", "").lower()
            for category_name, category_info in self.content_categories.items():
                for pattern in category_info["patterns"]:
                    if re.search(pattern, url, re.IGNORECASE):
                        confidence_analysis["url_relevance"] += 1
            
            # Analyze title relevance
            title = page_info.get("title", "").lower()
            for category_name, category_info in self.content_categories.items():
                for pattern in category_info["patterns"]:
                    if re.search(pattern, title, re.IGNORECASE):
                        confidence_analysis["title_relevance"] += 1
            
            # Calculate overall confidence
            total_patterns = sum(confidence_analysis["pattern_matches"].values())
            total_keywords = sum(confidence_analysis["keyword_matches"].values())
            
            confidence_analysis["overall_confidence"] = (
                total_patterns * 0.4 +
                total_keywords * 0.3 +
                confidence_analysis["url_relevance"] * 0.2 +
                confidence_analysis["title_relevance"] * 0.1
            )
            
            return confidence_analysis
            
        except Exception as e:
            print(f"Confidence analysis failed: {e}")
            return {"error": f"Confidence analysis failed: {e}"}
