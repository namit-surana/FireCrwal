"""
Quality scorer for BlueJay TIC Certification Database discovery results
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse


class QualityScorer:
    """
    Assesses the quality of discovery results with comprehensive metrics
    """
    
    def __init__(self):
        """Initialize the quality scorer"""
        
        # Quality metrics weights
        self.quality_weights = {
            "relevance": 0.35,
            "completeness": 0.30,
            "freshness": 0.20,
            "accessibility": 0.15
        }
        
        # Expected content types for each category
        self.expected_content = {
            "main_certification_pages": {
                "min_pages": 1,
                "expected_elements": ["overview", "requirements", "process", "benefits"],
                "content_quality_indicators": ["detailed", "comprehensive", "official"]
            },
            "application_forms": {
                "min_pages": 1,
                "expected_elements": ["form", "instructions", "requirements", "submission"],
                "content_quality_indicators": ["downloadable", "fillable", "clear_instructions"]
            },
            "training_materials": {
                "min_pages": 1,
                "expected_elements": ["course", "curriculum", "duration", "certification"],
                "content_quality_indicators": ["structured", "comprehensive", "practical"]
            },
            "audit_guidelines": {
                "min_pages": 1,
                "expected_elements": ["procedure", "checklist", "criteria", "timeline"],
                "content_quality_indicators": ["detailed", "step_by_step", "compliance_focused"]
            },
            "fee_structures": {
                "min_pages": 1,
                "expected_elements": ["fee", "cost", "payment", "schedule"],
                "content_quality_indicators": ["clear", "detailed", "up_to_date"]
            },
            "regional_offices": {
                "min_pages": 1,
                "expected_elements": ["location", "contact", "address", "hours"],
                "content_quality_indicators": ["complete", "accurate", "accessible"]
            }
        }
        
        print("Quality scorer initialized successfully")
    
    def assess_discovery_quality(
        self,
        website_structure: Dict[str, Any],
        discovered_content: Dict[str, List[Dict[str, Any]]],
        certification_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess the overall quality of discovery results
        
        Args:
            website_structure: Discovered website structure
            discovered_content: Categorized discovered content
            certification_data: Original certification data
            
        Returns:
            Comprehensive quality assessment
        """
        try:
            print("Starting quality assessment of discovery results")
            
            # Calculate individual quality metrics
            relevance_score = self._calculate_relevance_score(discovered_content, certification_data)
            completeness_score = self._calculate_completeness_score(discovered_content, website_structure)
            freshness_score = self._calculate_freshness_score(discovered_content)
            accessibility_score = self._calculate_accessibility_score(discovered_content, website_structure)
            
            # Calculate weighted overall score
            overall_score = (
                relevance_score * self.quality_weights["relevance"] +
                completeness_score * self.quality_weights["completeness"] +
                freshness_score * self.quality_weights["freshness"] +
                accessibility_score * self.quality_weights["accessibility"]
            )
            
            # Generate quality insights
            quality_insights = self._generate_quality_insights(
                discovered_content, website_structure, certification_data
            )
            
            # Compile quality assessment
            quality_assessment = {
                "overall_score": round(overall_score, 2),
                "score_breakdown": {
                    "relevance": round(relevance_score, 2),
                    "completeness": round(completeness_score, 2),
                    "freshness": round(freshness_score, 2),
                    "accessibility": round(accessibility_score, 2)
                },
                "quality_metrics": {
                    "total_pages_discovered": website_structure.get("total_pages", 0),
                    "relevant_pages_found": website_structure.get("relevant_pages", {}),
                    "content_categories_found": len(discovered_content),
                    "coverage_percentage": self._calculate_coverage_percentage(discovered_content),
                    "depth_score": self._calculate_depth_score(discovered_content)
                },
                "quality_insights": quality_insights,
                "recommendations": self._generate_recommendations(quality_assessment),
                "assessment_timestamp": datetime.now(datetime.timezone.utc).isoformat()
            }
            
            print(f"Quality assessment completed. Overall score: {overall_score:.2f}")
            return quality_assessment
            
        except Exception as e:
            print(f"Quality assessment failed: {e}")
            raise Exception(f"Quality assessment failed: {e}")
    
    def _calculate_relevance_score(
        self,
        discovered_content: Dict[str, List[Dict[str, Any]]],
        certification_data: Dict[str, Any]
    ) -> float:
        """
        Calculate relevance score based on content alignment with certification
        
        Args:
            discovered_content: Categorized discovered content
            certification_data: Original certification data
            
        Returns:
            Relevance score (0-100)
        """
        try:
            total_relevance = 0
            total_items = 0
            
            for category, content_list in discovered_content.items():
                category_relevance = 0
                
                for content_item in content_list:
                    item_relevance = self._calculate_item_relevance(
                        content_item, certification_data, category
                    )
                    category_relevance += item_relevance
                
                if content_list:
                    category_relevance /= len(content_list)
                    total_relevance += category_relevance
                    total_items += 1
            
            if total_items == 0:
                return 0.0
            
            return min(100.0, (total_relevance / total_items) * 100)
            
        except Exception as e:
            print(f"Relevance score calculation failed: {e}")
            return 0.0
    
    def _calculate_item_relevance(
        self,
        content_item: Dict[str, Any],
        certification_data: Dict[str, Any],
        category: str
    ) -> float:
        """
        Calculate relevance score for a single content item
        
        Args:
            content_item: Individual content item
            certification_data: Original certification data
            category: Content category
            
        Returns:
            Item relevance score (0-1)
        """
        try:
            relevance_score = 0.0
            
            # Check certification name relevance
            cert_name = certification_data.get("name", "").lower()
            if cert_name:
                title = content_item.get("title", "").lower()
                url = content_item.get("url", "").lower()
                content_preview = content_item.get("content_preview", "").lower()
                
                # Calculate name match score
                name_matches = 0
                if cert_name in title:
                    name_matches += 0.4
                if cert_name in url:
                    name_matches += 0.3
                if cert_name in content_preview:
                    name_matches += 0.3
                
                relevance_score += min(1.0, name_matches)
            
            # Check issuing body relevance
            issuing_body = certification_data.get("issuing_body", "").lower()
            if issuing_body:
                # Extract acronyms
                acronyms = re.findall(r'\b[A-Z]{2,}\b', certification_data.get("issuing_body", ""))
                for acronym in acronyms:
                    if acronym.lower() in content_item.get("title", "").lower():
                        relevance_score += 0.2
                    if acronym.lower() in content_item.get("url", "").lower():
                        relevance_score += 0.2
            
            # Check category alignment
            if category in self.expected_content:
                relevance_score += 0.3
            
            return min(1.0, relevance_score)
            
        except Exception as e:
            print(f"Item relevance calculation failed: {e}")
            return 0.0
    
    def _calculate_completeness_score(
        self,
        discovered_content: Dict[str, List[Dict[str, Any]]],
        website_structure: Dict[str, Any]
    ) -> float:
        """
        Calculate completeness score based on content coverage
        
        Args:
            discovered_content: Categorized discovered content
            website_structure: Discovered website structure
            
        Returns:
            Completeness score (0-100)
        """
        try:
            total_completeness = 0
            total_categories = len(self.expected_content)
            
            for category_name, category_info in self.expected_content.items():
                category_score = 0
                
                if category_name in discovered_content:
                    content_list = discovered_content[category_name]
                    
                    # Check minimum page requirement
                    if len(content_list) >= category_info["min_pages"]:
                        category_score += 0.4
                    
                    # Check content quality indicators
                    quality_indicators = category_info["content_quality_indicators"]
                    for indicator in quality_indicators:
                        for content_item in content_list:
                            if indicator.lower() in content_item.get("title", "").lower():
                                category_score += 0.2
                                break
                    
                    # Check expected elements
                    expected_elements = category_info["expected_elements"]
                    for element in expected_elements:
                        for content_item in content_list:
                            if element.lower() in content_item.get("title", "").lower():
                                category_score += 0.1
                                break
                
                total_completeness += min(1.0, category_score)
            
            return min(100.0, (total_completeness / total_categories) * 100)
            
        except Exception as e:
            print(f"Completeness score calculation failed: {e}")
            return 0.0
    
    def _calculate_freshness_score(
        self,
        discovered_content: Dict[str, List[Dict[str, Any]]]
    ) -> float:
        """
        Calculate freshness score based on content timestamps and metadata
        
        Args:
            discovered_content: Categorized discovered content
            
        Returns:
            Freshness score (0-100)
        """
        try:
            total_freshness = 0
            total_items = 0
            
            for content_list in discovered_content.values():
                for content_item in content_list:
                    item_freshness = self._calculate_item_freshness(content_item)
                    total_freshness += item_freshness
                    total_items += 1
            
            if total_items == 0:
                return 0.0
            
            return min(100.0, (total_freshness / total_items) * 100)
            
        except Exception as e:
            print(f"Freshness score calculation failed: {e}")
            return 0.0
    
    def _calculate_item_freshness(self, content_item: Dict[str, Any]) -> float:
        """
        Calculate freshness score for a single content item
        
        Args:
            content_item: Individual content item
            
        Returns:
            Item freshness score (0-1)
        """
        try:
            freshness_score = 0.5  # Base score for unknown freshness
            
            # Check for extraction timestamp
            extraction_timestamp = content_item.get("extraction_timestamp")
            if extraction_timestamp:
                try:
                    extraction_time = datetime.fromisoformat(extraction_timestamp.replace('Z', '+00:00'))
                    current_time = datetime.now(timezone.utc)
                    time_diff = current_time - extraction_time
                    
                    # Score based on recency (higher score for more recent content)
                    if time_diff.days <= 1:
                        freshness_score = 1.0
                    elif time_diff.days <= 7:
                        freshness_score = 0.9
                    elif time_diff.days <= 30:
                        freshness_score = 0.8
                    elif time_diff.days <= 90:
                        freshness_score = 0.7
                    elif time_diff.days <= 365:
                        freshness_score = 0.6
                    else:
                        freshness_score = 0.5
                        
                except Exception as e:
                    print(f"Timestamp parsing failed: {e}")
            
            # Check for metadata freshness indicators
            metadata = content_item.get("metadata", {})
            if metadata.get("lastModified"):
                freshness_score += 0.2
            if metadata.get("updatedAt"):
                freshness_score += 0.2
            
            return min(1.0, freshness_score)
            
        except Exception as e:
            print(f"Item freshness calculation failed: {e}")
            return 0.5
    
    def _calculate_accessibility_score(
        self,
        discovered_content: Dict[str, List[Dict[str, Any]]],
        website_structure: Dict[str, Any]
    ) -> float:
        """
        Calculate accessibility score based on content availability and structure
        
        Args:
            discovered_content: Categorized discovered content
            website_structure: Discovered website structure
            
        Returns:
            Accessibility score (0-100)
        """
        try:
            total_accessibility = 0
            total_items = 0
            
            for content_list in discovered_content.values():
                for content_item in content_list:
                    item_accessibility = self._calculate_item_accessibility(content_item)
                    total_accessibility += item_accessibility
                    total_items += 1
            
            if total_items == 0:
                return 0.0
            
            # Add bonus for website structure quality
            structure_bonus = 0
            if website_structure.get("total_pages", 0) > 0:
                structure_bonus = min(0.2, website_structure.get("total_pages", 0) / 1000)
            
            base_score = (total_accessibility / total_items) * 100
            final_score = min(100.0, base_score + (structure_bonus * 100))
            
            return final_score
            
        except Exception as e:
            print(f"Accessibility score calculation failed: {e}")
            return 0.0
    
    def _calculate_item_accessibility(self, content_item: Dict[str, Any]) -> float:
        """
        Calculate accessibility score for a single content item
        
        Args:
            content_item: Individual content item
            
        Returns:
            Item accessibility score (0-1)
        """
        try:
            accessibility_score = 0.0
            
            # Check URL accessibility
            url = content_item.get("url", "")
            if url:
                parsed_url = urlparse(url)
                if parsed_url.scheme in ["http", "https"]:
                    accessibility_score += 0.3
                
                # Check for common accessibility issues
                if "login" not in url.lower() and "auth" not in url.lower():
                    accessibility_score += 0.2
            
            # Check content availability
            if content_item.get("content"):
                accessibility_score += 0.3
            
            if content_item.get("content_preview"):
                accessibility_score += 0.2
            
            # Check for metadata
            if content_item.get("metadata"):
                accessibility_score += 0.1
            
            return min(1.0, accessibility_score)
            
        except Exception as e:
            print(f"Item accessibility calculation failed: {e}")
            return 0.0
    
    def _calculate_coverage_percentage(
        self,
        discovered_content: Dict[str, List[Dict[str, Any]]]
    ) -> float:
        """
        Calculate coverage percentage of expected content categories
        
        Args:
            discovered_content: Categorized discovered content
            
        Returns:
            Coverage percentage (0-100)
        """
        try:
            expected_categories = len(self.expected_content)
            found_categories = len([
                category for category in discovered_content.keys()
                if category in self.expected_content and discovered_content[category]
            ])
            
            return (found_categories / expected_categories) * 100 if expected_categories > 0 else 0.0
            
        except Exception as e:
            print(f"Coverage percentage calculation failed: {e}")
            return 0.0
    
    def _calculate_depth_score(
        self,
        discovered_content: Dict[str, List[Dict[str, Any]]]
    ) -> float:
        """
        Calculate depth score based on content richness
        
        Args:
            discovered_content: Categorized discovered content
            
        Returns:
            Depth score (0-100)
        """
        try:
            total_depth = 0
            total_categories = 0
            
            for category, content_list in discovered_content.items():
                if category in self.expected_content:
                    category_depth = 0
                    
                    # Score based on number of pages
                    if len(content_list) >= 5:
                        category_depth = 1.0
                    elif len(content_list) >= 3:
                        category_depth = 0.8
                    elif len(content_list) >= 2:
                        category_depth = 0.6
                    elif len(content_list) >= 1:
                        category_depth = 0.4
                    
                    # Score based on content quality
                    for content_item in content_list:
                        if content_item.get("content_preview") and len(content_item["content_preview"]) > 100:
                            category_depth += 0.1
                        if content_item.get("metadata"):
                            category_depth += 0.1
                    
                    total_depth += min(1.0, category_depth)
                    total_categories += 1
            
            return (total_depth / total_categories) * 100 if total_categories > 0 else 0.0
            
        except Exception as e:
            print(f"Depth score calculation failed: {e}")
            return 0.0
    
    def _generate_quality_insights(
        self,
        discovered_content: Dict[str, List[Dict[str, Any]]],
        website_structure: Dict[str, Any],
        certification_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate insights about discovery quality
        
        Args:
            discovered_content: Categorized discovered content
            website_structure: Discovered website structure
            certification_data: Original certification data
            
        Returns:
            Quality insights
        """
        try:
            insights = {
                "strengths": [],
                "weaknesses": [],
                "opportunities": [],
                "threats": []
            }
            
            # Analyze strengths
            if len(discovered_content) >= 4:
                insights["strengths"].append("Comprehensive content coverage across multiple categories")
            
            total_pages = website_structure.get("total_pages", 0)
            if total_pages >= 100:
                insights["strengths"].append("Deep website exploration with extensive page discovery")
            
            # Analyze weaknesses
            missing_categories = [
                category for category in self.expected_content.keys()
                if category not in discovered_content or not discovered_content[category]
            ]
            
            if missing_categories:
                insights["weaknesses"].append(f"Missing content in categories: {', '.join(missing_categories)}")
            
            if total_pages < 50:
                insights["weaknesses"].append("Limited website exploration depth")
            
            # Analyze opportunities
            if len(discovered_content) < 6:
                insights["opportunities"].append("Potential for additional content category discovery")
            
            if total_pages < 200:
                insights["opportunities"].append("Room for deeper website crawling and exploration")
            
            # Analyze threats
            if len(discovered_content) == 0:
                insights["threats"].append("No relevant content discovered - may indicate website changes or access issues")
            
            return insights
            
        except Exception as e:
            print(f"Quality insights generation failed: {e}")
            return {"error": f"Insights generation failed: {e}"}
    
    def _generate_recommendations(self, quality_assessment: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on quality assessment
        
        Args:
            quality_assessment: Quality assessment results
            
        Returns:
            List of recommendations
        """
        try:
            recommendations = []
            
            overall_score = quality_assessment.get("overall_score", 0)
            
            if overall_score < 50:
                recommendations.append("Consider re-running discovery with different parameters")
                recommendations.append("Verify website accessibility and availability")
                recommendations.append("Check for website structure changes")
            
            elif overall_score < 75:
                recommendations.append("Expand crawling depth for better coverage")
                recommendations.append("Add more specific search terms for content discovery")
                recommendations.append("Consider manual review of discovered content")
            
            else:
                recommendations.append("Discovery quality is good - consider moving to content extraction phase")
                recommendations.append("Monitor for content updates and changes")
            
            # Specific recommendations based on scores
            score_breakdown = quality_assessment.get("score_breakdown", {})
            
            if score_breakdown.get("relevance", 0) < 70:
                recommendations.append("Review and refine content categorization for better relevance")
            
            if score_breakdown.get("completeness", 0) < 70:
                recommendations.append("Increase crawling depth to discover missing content categories")
            
            if score_breakdown.get("freshness", 0) < 70:
                recommendations.append("Implement regular content freshness monitoring")
            
            if score_breakdown.get("accessibility", 0) < 70:
                recommendations.append("Check for website access restrictions or technical issues")
            
            return recommendations
            
        except Exception as e:
            print(f"Recommendations generation failed: {e}")
            return ["Unable to generate recommendations due to error"]
