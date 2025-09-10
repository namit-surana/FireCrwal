"""
Improved Multi-Agent Orchestration Pipeline with Token Management
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import tiktoken

# LangChain imports
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool, StructuredTool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage
from langchain.memory import ConversationBufferMemory
from langgraph.graph import StateGraph, END
# from langgraph.checkpoint import MemorySaver

# Firecrawl imports
from firecrawl import FirecrawlApp

# Local imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.discovery.firecrawl_client import FirecrawlClient
from relevance.prompt import (
    SYSTEM_PROMPT, 
    SYSTEM_PROMPT_PARAMETERS,
    SYSTEM_PROMPT_P3_PARAMETER,
    SYSTEM_PROMPT_P3_Links
)

# Logging
from loguru import logger


# ============================================================================
# Token Management Utilities
# ============================================================================

class TokenManager:
    """Manages token counting and content chunking for API calls"""
    
    # Token limits for different models
    MODEL_LIMITS = {
        "gpt-4o": 128000,  # GPT-4o has 128k context window
        "gpt-4": 8192,
        "gpt-3.5-turbo": 16384,
        "gpt-3.5-turbo-16k": 16384
    }
    
    # Reserve tokens for response
    RESPONSE_BUFFER = 2000
    
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.max_tokens = self.MODEL_LIMITS.get(model_name, 8192)
        try:
            self.encoder = tiktoken.encoding_for_model(model_name)
        except:
            # Fallback to cl100k_base encoding for newer models
            self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoder.encode(text))
    
    def get_available_tokens(self, system_prompt: str, existing_content: str = "") -> int:
        """Calculate available tokens for new content"""
        used_tokens = self.count_tokens(system_prompt) + self.count_tokens(existing_content)
        available = self.max_tokens - used_tokens - self.RESPONSE_BUFFER
        return max(0, available)
    
    def chunk_content(self, content: str, chunk_size: int = 3000) -> List[str]:
        """Split content into manageable chunks based on token count"""
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs:
            para_tokens = self.count_tokens(paragraph)
            
            if current_tokens + para_tokens > chunk_size:
                # Save current chunk
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                # Start new chunk
                current_chunk = [paragraph]
                current_tokens = para_tokens
            else:
                current_chunk.append(paragraph)
                current_tokens += para_tokens
        
        # Add remaining chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def truncate_to_fit(self, content: str, max_tokens: int) -> str:
        """Truncate content to fit within token limit"""
        tokens = self.encoder.encode(content)
        if len(tokens) <= max_tokens:
            return content
        
        # Truncate and decode
        truncated_tokens = tokens[:max_tokens]
        return self.encoder.decode(truncated_tokens)


# ============================================================================
# Data Models (same as original)
# ============================================================================

class AgentRole(Enum):
    """Enum for different agent roles in the pipeline"""
    SEARCH = "search"
    EXTRACTION = "extraction"
    CATEGORIZATION = "categorization"
    FORMATTING = "formatting"
    ORCHESTRATOR = "orchestrator"


@dataclass
class CertificationInfo:
    """Certification information structure"""
    name: str
    issuing_body: str
    region: str
    official_link: str
    artifact_type: Optional[str] = None
    mandatory: Optional[bool] = None
    validity_period_months: Optional[int] = None
    overview: Optional[str] = None
    full_description: Optional[str] = None
    legal_reference: Optional[str] = None
    domain_tags: List[str] = field(default_factory=list)
    scope_tags: List[str] = field(default_factory=list)
    harmonized_standards: List[str] = field(default_factory=list)
    fee: Optional[str] = None
    application_process: Optional[str] = None
    lead_time_days: Optional[int] = None
    processing_time_days: Optional[int] = None
    prerequisites: List[str] = field(default_factory=list)
    audit_scope: List[str] = field(default_factory=list)
    test_items: List[str] = field(default_factory=list)


@dataclass
class SearchResult:
    """Structure for search results from Firecrawl"""
    url: str
    title: str
    description: str
    markdown: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    relevance_score: Optional[int] = None
    
    
@dataclass
class ProcessedLink:
    """Structure for processed links with categorization"""
    url: str
    title: str
    description: str
    category: str
    importance: int
    is_pdf: bool


@dataclass
class PipelineState:
    """State management for the agent pipeline"""
    certification_info: CertificationInfo
    search_query: str
    search_results: List[SearchResult] = field(default_factory=list)
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    categorized_links: Dict[str, List[ProcessedLink]] = field(default_factory=dict)
    formatted_output: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# Improved Agent Implementations with Token Management
# ============================================================================

class SearchAgent:
    """Agent responsible for searching using Firecrawl API"""
    
    def __init__(self, firecrawl_client: FirecrawlClient):
        self.firecrawl_client = firecrawl_client
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.token_manager = TokenManager("gpt-4o")
        
    async def search(self, state: PipelineState) -> PipelineState:
        """
        Perform search using Firecrawl API
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated pipeline state with search results
        """
        try:
            logger.info(f"SearchAgent: Starting search for {state.certification_info.name}")
            
            # Perform Firecrawl search
            search_result = self.firecrawl_client.search_website(
                url=state.certification_info.official_link,
                query=state.search_query
            )
            
            if search_result and 'data' in search_result:
                # Process web search results
                web_results = search_result.get('data', {}).get('web', [])
                
                for result in web_results:
                    search_res = SearchResult(
                        url=result.get('url', ''),
                        title=result.get('title', ''),
                        description=result.get('description', ''),
                        markdown=result.get('markdown', ''),
                        metadata=result.get('metadata', {})
                    )
                    state.search_results.append(search_res)
                    
                logger.info(f"SearchAgent: Found {len(state.search_results)} results")
            else:
                # Fallback to mapping if search fails
                logger.warning("SearchAgent: Search failed, falling back to mapping")
                map_result = self.firecrawl_client.map_website_simple(
                    url=state.certification_info.official_link,
                    search=state.search_query
                )
                
                for link in map_result:
                    search_res = SearchResult(
                        url=link['url'],
                        title=link['title'],
                        description=link['description']
                    )
                    state.search_results.append(search_res)
                    
        except Exception as e:
            error_msg = f"SearchAgent error: {str(e)}"
            logger.error(error_msg)
            state.errors.append(error_msg)
            
        return state


class ImprovedDataExtractionAgent:
    """Improved agent with token management for data extraction"""
    
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.token_manager = TokenManager(model_name)
        
    async def extract(self, state: PipelineState) -> PipelineState:
        """
        Extract structured information from search results with token management
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated pipeline state with extracted data
        """
        try:
            logger.info("ImprovedDataExtractionAgent: Starting data extraction")
            
            # Calculate available tokens for content
            base_prompt = f"""
            {SYSTEM_PROMPT_P3_PARAMETER}
            
            Current certification state:
            {json.dumps(state.certification_info.__dict__, indent=2)}
            
            Content to extract from:
            """
            
            available_tokens = self.token_manager.get_available_tokens(
                SYSTEM_PROMPT_P3_PARAMETER,
                base_prompt
            )
            
            logger.info(f"Available tokens for content: {available_tokens}")
            
            # Collect markdown content
            all_content = []
            for result in state.search_results:
                if result.markdown:
                    all_content.append(f"URL: {result.url}\nTitle: {result.title}\nContent:\n{result.markdown}")
            
            combined_content = "\n\n---\n\n".join(all_content)
            
            # Process content based on token limits
            if self.token_manager.count_tokens(combined_content) <= available_tokens:
                # Content fits within limits
                await self._process_content(state, combined_content)
            else:
                # Need to chunk or truncate content
                logger.info("Content exceeds token limit, using chunking strategy")
                await self._process_chunked_content(state, all_content, available_tokens)
            
            logger.info("ImprovedDataExtractionAgent: Extraction complete")
                
        except Exception as e:
            error_msg = f"ImprovedDataExtractionAgent error: {str(e)}"
            logger.error(error_msg)
            state.errors.append(error_msg)
            
        return state
    
    async def _process_content(self, state: PipelineState, content: str):
        """Process content that fits within token limits"""
        extraction_prompt = f"""
        {SYSTEM_PROMPT_P3_PARAMETER}
        
        Current certification state:
        {json.dumps(state.certification_info.__dict__, indent=2)}
        
        Content to extract from:
        {content}
        
        Task: Extract and update certification information from the content.
        Return only valid JSON matching the certification state structure.
        """
        
        # Extract information using LLM
        response = await self.llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT_P3_PARAMETER),
            HumanMessage(content=extraction_prompt)
        ])
        
        # Parse extracted data
        try:
            extracted_data = json.loads(response.content)
            state.extracted_data = extracted_data
            
            # Update certification info with extracted data
            for key, value in extracted_data.items():
                if hasattr(state.certification_info, key) and value is not None:
                    setattr(state.certification_info, key, value)
                    
            logger.info("Successfully extracted and updated certification data")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            state.errors.append(f"Data extraction JSON parse error: {e}")
    
    async def _process_chunked_content(self, state: PipelineState, content_list: List[str], available_tokens: int):
        """Process content in chunks when it exceeds token limits"""
        # Strategy 1: Prioritize content by relevance
        # Take the most relevant pieces first
        chunk_size = available_tokens // 2  # Use half the available tokens per chunk
        
        accumulated_data = {}
        
        for i, content in enumerate(content_list[:5]):  # Process up to 5 most relevant results
            logger.info(f"Processing chunk {i+1}/{min(5, len(content_list))}")
            
            # Truncate individual content if needed
            truncated_content = self.token_manager.truncate_to_fit(content, chunk_size)
            
            extraction_prompt = f"""
            {SYSTEM_PROMPT_P3_PARAMETER}
            
            Current certification state:
            {json.dumps(state.certification_info.__dict__, indent=2)}
            
            Content to extract from (Part {i+1}):
            {truncated_content}
            
            Task: Extract certification information from this content.
            Return only valid JSON matching the certification state structure.
            Focus on fields not yet filled in the current state.
            """
            
            try:
                response = await self.llm.ainvoke([
                    SystemMessage(content=SYSTEM_PROMPT_P3_PARAMETER),
                    HumanMessage(content=extraction_prompt)
                ])
                
                chunk_data = json.loads(response.content)
                
                # Merge chunk data into accumulated data
                for key, value in chunk_data.items():
                    if value is not None and (key not in accumulated_data or accumulated_data[key] is None):
                        accumulated_data[key] = value
                        
            except Exception as e:
                logger.warning(f"Failed to process chunk {i+1}: {e}")
                continue
        
        # Update state with accumulated data
        state.extracted_data = accumulated_data
        for key, value in accumulated_data.items():
            if hasattr(state.certification_info, key) and value is not None:
                setattr(state.certification_info, key, value)
        
        logger.info(f"Completed chunked extraction with {len(accumulated_data)} fields")


class ImprovedLinkCategorizationAgent:
    """Improved agent with token management for link categorization"""
    
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        self.token_manager = TokenManager(model_name)
        
    async def categorize(self, state: PipelineState) -> PipelineState:
        """
        Categorize and prioritize links with token management
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated pipeline state with categorized links
        """
        try:
            logger.info("ImprovedLinkCategorizationAgent: Starting link categorization")
            
            # Prepare links for categorization
            links_data = []
            for result in state.search_results:
                links_data.append({
                    "url": result.url,
                    "title": result.title,
                    "description": result.description
                })
            
            # Check token limits
            links_json = json.dumps(links_data, indent=2)
            base_prompt = f"""
            Certification Context:
            - Name: {state.certification_info.name}
            - Issuing Body: {state.certification_info.issuing_body}
            - Region: {state.certification_info.region}
            - Official Link: {state.certification_info.official_link}
            
            Task: Categorize these links according to the system prompt rules.
            Return JSON with PDF and non-PDF categorization.
            
            Links to categorize:
            """
            
            available_tokens = self.token_manager.get_available_tokens(
                SYSTEM_PROMPT_P3_Links,
                base_prompt
            )
            
            # Process in batches if needed
            if self.token_manager.count_tokens(links_json) <= available_tokens:
                await self._categorize_links(state, links_data)
            else:
                # Process in batches
                batch_size = 20  # Process 20 links at a time
                for i in range(0, len(links_data), batch_size):
                    batch = links_data[i:i+batch_size]
                    logger.info(f"Processing batch {i//batch_size + 1}")
                    await self._categorize_links(state, batch)
                    
            logger.info(f"Categorized {sum(len(links) for links in state.categorized_links.values())} links")
                
        except Exception as e:
            error_msg = f"ImprovedLinkCategorizationAgent error: {str(e)}"
            logger.error(error_msg)
            state.errors.append(error_msg)
            
        return state
    
    async def _categorize_links(self, state: PipelineState, links_batch: List[Dict]):
        """Categorize a batch of links"""
        categorization_prompt = f"""
        Certification Context:
        - Name: {state.certification_info.name}
        - Issuing Body: {state.certification_info.issuing_body}
        - Region: {state.certification_info.region}
        - Official Link: {state.certification_info.official_link}
        
        Links to categorize:
        {json.dumps(links_batch, indent=2)}
        
        Task: Categorize these links according to the system prompt rules.
        Return JSON with PDF and non-PDF categorization.
        """
        
        # Categorize using LLM
        response = await self.llm.ainvoke([
            SystemMessage(content=SYSTEM_PROMPT_P3_Links),
            HumanMessage(content=categorization_prompt)
        ])
        
        # Parse categorized data
        try:
            categorized_data = json.loads(response.content)
            
            # Process categorized links
            for file_type in ['pdf', 'non-pdf']:
                if file_type in categorized_data.get('categories', {}):
                    for category, links in categorized_data['categories'][file_type].items():
                        if category not in state.categorized_links:
                            state.categorized_links[category] = []
                        
                        for link in links:
                            processed_link = ProcessedLink(
                                url=link['url'],
                                title=link['title'],
                                description=link['description'],
                                category=category,
                                importance=self._calculate_importance(category),
                                is_pdf=(file_type == 'pdf')
                            )
                            state.categorized_links[category].append(processed_link)
                            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse categorization JSON: {e}")
            state.errors.append(f"Link categorization JSON parse error: {e}")
    
    def _calculate_importance(self, category: str) -> int:
        """Calculate importance score based on category"""
        importance_map = {
            'application': 10,
            'requirements': 9,
            'documentation': 8,
            'fees': 8,
            'renewal': 8,
            'guidelines': 7,
            'support': 6,
            'compliance': 7,
            'tracking': 7,
            'special': 7
        }
        return importance_map.get(category, 5)


class FormattingAgent:
    """Agent responsible for formatting the final output"""
    
    def __init__(self, output_format: str = "markdown"):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.output_format = output_format
        
    async def format(self, state: PipelineState) -> PipelineState:
        """
        Format the extracted data and categorized links into final output
        
        Args:
            state: Current pipeline state
            
        Returns:
            Updated pipeline state with formatted output
        """
        try:
            logger.info(f"FormattingAgent: Formatting output as {self.output_format}")
            
            if self.output_format == "markdown":
                output = self._format_markdown(state)
            elif self.output_format == "json":
                output = self._format_json(state)
            elif self.output_format == "structured":
                output = self._format_structured(state)
            else:
                output = self._format_text(state)
                
            state.formatted_output = output
            logger.info("FormattingAgent: Formatting complete")
            
        except Exception as e:
            error_msg = f"FormattingAgent error: {str(e)}"
            logger.error(error_msg)
            state.errors.append(error_msg)
            
        return state
    
    def _format_markdown(self, state: PipelineState) -> str:
        """Format output as Markdown"""
        md_lines = []
        
        # Header
        md_lines.append(f"# {state.certification_info.name}")
        md_lines.append(f"**Issuing Body:** {state.certification_info.issuing_body}")
        md_lines.append(f"**Region:** {state.certification_info.region}")
        md_lines.append(f"**Official Link:** [{state.certification_info.official_link}]({state.certification_info.official_link})")
        md_lines.append("")
        
        # Overview
        if state.certification_info.overview:
            md_lines.append("## Overview")
            md_lines.append(state.certification_info.overview)
            md_lines.append("")
        
        # Description
        if state.certification_info.full_description:
            md_lines.append("## Description")
            md_lines.append(state.certification_info.full_description)
            md_lines.append("")
        
        # Key Information
        md_lines.append("## Key Information")
        if state.certification_info.mandatory is not None:
            md_lines.append(f"- **Mandatory:** {'Yes' if state.certification_info.mandatory else 'No'}")
        if state.certification_info.validity_period_months:
            md_lines.append(f"- **Validity Period:** {state.certification_info.validity_period_months} months")
        if state.certification_info.fee:
            md_lines.append(f"- **Fee:** {state.certification_info.fee}")
        if state.certification_info.lead_time_days:
            md_lines.append(f"- **Lead Time:** {state.certification_info.lead_time_days} days")
        md_lines.append("")
        
        # Application Process
        if state.certification_info.application_process:
            md_lines.append("## Application Process")
            md_lines.append(state.certification_info.application_process)
            md_lines.append("")
        
        # Prerequisites
        if state.certification_info.prerequisites:
            md_lines.append("## Prerequisites")
            for prereq in state.certification_info.prerequisites:
                md_lines.append(f"- {prereq}")
            md_lines.append("")
        
        # Important Links
        if state.categorized_links:
            md_lines.append("## Important Links")
            
            # Group by PDF and non-PDF
            pdf_links = {}
            non_pdf_links = {}
            
            for category, links in state.categorized_links.items():
                for link in links:
                    if link.is_pdf:
                        if category not in pdf_links:
                            pdf_links[category] = []
                        pdf_links[category].append(link)
                    else:
                        if category not in non_pdf_links:
                            non_pdf_links[category] = []
                        non_pdf_links[category].append(link)
            
            # Non-PDF Links
            if non_pdf_links:
                md_lines.append("### Web Resources")
                for category, links in non_pdf_links.items():
                    md_lines.append(f"#### {category.title().replace('_', ' ')}")
                    for link in sorted(links, key=lambda x: x.importance, reverse=True):
                        md_lines.append(f"- [{link.title}]({link.url})")
                        if link.description:
                            md_lines.append(f"  - {link.description}")
                    md_lines.append("")
            
            # PDF Links
            if pdf_links:
                md_lines.append("### PDF Documents")
                for category, links in pdf_links.items():
                    md_lines.append(f"#### {category.title().replace('_', ' ')}")
                    for link in sorted(links, key=lambda x: x.importance, reverse=True):
                        md_lines.append(f"- [{link.title}]({link.url}) 📄")
                        if link.description:
                            md_lines.append(f"  - {link.description}")
                    md_lines.append("")
        
        # Metadata
        md_lines.append("---")
        md_lines.append(f"*Generated: {state.timestamp}*")
        if state.errors:
            md_lines.append(f"*Errors encountered: {len(state.errors)}*")
        
        return "\n".join(md_lines)
    
    def _format_json(self, state: PipelineState) -> str:
        """Format output as JSON"""
        output_data = {
            "certification": state.certification_info.__dict__,
            "extracted_data": state.extracted_data,
            "categorized_links": {
                category: [link.__dict__ for link in links]
                for category, links in state.categorized_links.items()
            },
            "search_results_count": len(state.search_results),
            "timestamp": state.timestamp,
            "errors": state.errors
        }
        return json.dumps(output_data, indent=2, ensure_ascii=False)
    
    def _format_structured(self, state: PipelineState) -> str:
        """Format output as structured text"""
        lines = []
        
        # Certification Info Section
        lines.append("=" * 80)
        lines.append(f"CERTIFICATION: {state.certification_info.name}")
        lines.append("=" * 80)
        lines.append(f"Issuing Body: {state.certification_info.issuing_body}")
        lines.append(f"Region: {state.certification_info.region}")
        lines.append(f"Official Link: {state.certification_info.official_link}")
        lines.append("")
        
        # Extracted Information
        if state.extracted_data:
            lines.append("-" * 40)
            lines.append("EXTRACTED INFORMATION")
            lines.append("-" * 40)
            for key, value in state.extracted_data.items():
                if value is not None:
                    lines.append(f"{key}: {value}")
            lines.append("")
        
        # Categorized Links
        if state.categorized_links:
            lines.append("-" * 40)
            lines.append("IMPORTANT LINKS")
            lines.append("-" * 40)
            for category, links in state.categorized_links.items():
                lines.append(f"\n[{category.upper()}]")
                for link in sorted(links, key=lambda x: x.importance, reverse=True):
                    prefix = "📄" if link.is_pdf else "🔗"
                    lines.append(f"  {prefix} {link.title}")
                    lines.append(f"     URL: {link.url}")
                    if link.description:
                        lines.append(f"     Description: {link.description}")
                    lines.append("")
        
        return "\n".join(lines)
    
    def _format_text(self, state: PipelineState) -> str:
        """Format output as plain text"""
        return self._format_structured(state).replace("📄", "[PDF]").replace("🔗", "[WEB]")


# ============================================================================
# Improved Multi-Agent Orchestrator
# ============================================================================

class ImprovedMultiAgentOrchestrator:
    """Improved orchestrator with token management for coordinating multiple agents"""
    
    def __init__(self, firecrawl_api_key: Optional[str] = None, output_format: str = "markdown", model_name: str = "gpt-4o"):
        # Initialize Firecrawl client
        if firecrawl_api_key:
            os.environ["FIRECRAWL_API_KEY"] = firecrawl_api_key
        self.firecrawl_client = FirecrawlClient()
        
        # Initialize agents with improved versions
        self.search_agent = SearchAgent(self.firecrawl_client)
        self.extraction_agent = ImprovedDataExtractionAgent(model_name)
        self.categorization_agent = ImprovedLinkCategorizationAgent(model_name)
        self.formatting_agent = FormattingAgent(output_format=output_format)
        
        # Initialize LangGraph workflow
        self.workflow = self._create_workflow()
        
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for agent coordination"""
        workflow = StateGraph(PipelineState)
        
        # Add nodes for each agent
        workflow.add_node("search", self.search_agent.search)
        workflow.add_node("extract", self.extraction_agent.extract)
        workflow.add_node("categorize", self.categorization_agent.categorize)
        workflow.add_node("format", self.formatting_agent.format)
        
        # Define edges
        workflow.set_entry_point("search")
        workflow.add_edge("search", "extract")
        workflow.add_edge("extract", "categorize")
        workflow.add_edge("categorize", "format")
        workflow.add_edge("format", END)
        
        return workflow.compile()
    
    async def process(
        self,
        certification_info: Dict[str, Any],
        search_query: str,
        output_format: Optional[str] = None
    ) -> Tuple[str, PipelineState]:
        """
        Process certification search through the multi-agent pipeline
        
        Args:
            certification_info: Dictionary with certification information
            search_query: Search query for Firecrawl
            output_format: Optional output format override
            
        Returns:
            Tuple of (formatted_output, final_state)
        """
        try:
            # Create certification info object
            cert_info = CertificationInfo(**certification_info)
            
            # Initialize pipeline state
            initial_state = PipelineState(
                certification_info=cert_info,
                search_query=search_query
            )
            
            # Update output format if specified
            if output_format:
                self.formatting_agent.output_format = output_format
            
            logger.info(f"Starting improved pipeline for {cert_info.name}")
            
            # Run the workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Log any errors
            if final_state.errors:
                for error in final_state.errors:
                    logger.error(f"Pipeline error: {error}")
            
            logger.info("Improved pipeline completed successfully")
            
            return final_state.formatted_output, final_state
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise
    
    def process_sync(
        self,
        certification_info: Dict[str, Any],
        search_query: str,
        output_format: Optional[str] = None
    ) -> Tuple[str, PipelineState]:
        """
        Synchronous wrapper for process method
        
        Args:
            certification_info: Dictionary with certification information
            search_query: Search query for Firecrawl
            output_format: Optional output format override
            
        Returns:
            Tuple of (formatted_output, final_state)
        """
        return asyncio.run(self.process(certification_info, search_query, output_format))


# ============================================================================
# Main Pipeline Function
# ============================================================================

def run_improved_pipeline(
    certification_data: Dict[str, Any],
    search_terms: List[str],
    output_format: str = "markdown",
    save_to_file: bool = True,
    output_dir: str = "output",
    model_name: str = "gpt-4o"
) -> Dict[str, Any]:
    """
    Main function to run the improved multi-agent pipeline with token management
    
    Args:
        certification_data: Dictionary with certification information
        search_terms: List of search terms to use
        output_format: Output format (markdown, json, structured, text)
        save_to_file: Whether to save output to file
        output_dir: Directory to save output files
        model_name: OpenAI model to use
        
    Returns:
        Dictionary with results and metadata
    """
    try:
        # Create output directory if needed
        if save_to_file:
            os.makedirs(output_dir, exist_ok=True)
        
        # Initialize improved orchestrator
        orchestrator = ImprovedMultiAgentOrchestrator(
            output_format=output_format,
            model_name=model_name
        )
        
        results = {}
        
        # Process each search term
        for search_term in search_terms:
            logger.info(f"Processing search term: {search_term}")
            
            # Run pipeline
            formatted_output, final_state = orchestrator.process_sync(
                certification_info=certification_data,
                search_query=search_term
            )
            
            # Save to file if requested
            if save_to_file and formatted_output:
                filename = f"{certification_data['name'].replace(' ', '_')}_{search_term.replace(' ', '_')}"
                if output_format == "markdown":
                    filepath = os.path.join(output_dir, f"{filename}.md")
                elif output_format == "json":
                    filepath = os.path.join(output_dir, f"{filename}.json")
                else:
                    filepath = os.path.join(output_dir, f"{filename}.txt")
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(formatted_output)
                
                logger.info(f"Saved output to {filepath}")
            
            # Store results
            results[search_term] = {
                "output": formatted_output,
                "search_results_count": len(final_state.search_results),
                "extracted_fields_count": len(final_state.extracted_data),
                "categorized_links_count": sum(len(links) for links in final_state.categorized_links.values()),
                "errors": final_state.errors
            }
        
        return {
            "success": True,
            "certification": certification_data,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example certification data
    certification_info = {
        "name": "FSSAI License/Registration",
        "issuing_body": "Food Safety and Standards Authority of India",
        "region": "India",
        "official_link": "https://foscos.fssai.gov.in/"
    }
    
    # Search terms to explore
    search_terms = [
        "application process",
        "eligibility requirements",
        "required documents",
        "fees structure",
        "renewal process"
    ]
    
    # Run the improved pipeline
    results = run_improved_pipeline(
        certification_data=certification_info,
        search_terms=search_terms,
        output_format="markdown",
        save_to_file=True,
        output_dir="relevance/output",
        model_name="gpt-4o"  # Can switch to "gpt-3.5-turbo" for faster/cheaper processing
    )
    
    # Print summary
    if results["success"]:
        print(f"✓ Pipeline completed successfully")
        for search_term, result in results["results"].items():
            print(f"  - {search_term}: {result['search_results_count']} results, {result['categorized_links_count']} links")
            if result['errors']:
                print(f"    ⚠ Errors: {', '.join(result['errors'])}")
    else:
        print(f"✗ Pipeline failed: {results.get('error')}")