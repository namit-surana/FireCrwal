from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
from openai import OpenAI
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.prompts import (
    SYSTEM_PROMPT_P3_PARAMETER,
    build_webpage_ingestion_prompt,
    get_certification_state
)
from functions import (
    parse_url_list_json,
    convert_to_markdown
)

app = FastAPI(title="Certification Ingestion API", version="1.0.0")

# ================================
# PYDANTIC MODELS
# ================================

class CertificationInput(BaseModel):
    webpage_data: str = Field(..., description="Webpage content to process")
    current_state: Optional[Dict[str, Any]] = Field(default=None, description="Current certification state to update")

class BatchCertificationInput(BaseModel):
    items: List[Dict[str, Any]] = Field(..., description="List of items with markdown content to process")

class ProcessFileInput(BaseModel):
    file_path: str = Field(..., description="Path to JSON file containing certification data")

class ConvertToMarkdownInput(BaseModel):
    url: str = Field(..., description="URL or file path to convert to markdown")

class ParseUrlListInput(BaseModel):
    file_path: str = Field(..., description="Path to JSON file containing URLs to process")

class FullPipelineInput(BaseModel):
    file_path: str = Field(..., description="Path to JSON file containing URLs to process")
    output_file: Optional[str] = Field(None, description="Optional output file path for results")

class CertificationResponse(BaseModel):
    artifact_type: Optional[str] = None
    name: Optional[str] = None
    aliases: List[str] = []
    issuing_body: Optional[str] = None
    region: Optional[str] = None
    mandatory: Optional[bool] = None
    validity_period_months: Optional[int] = None
    overview: Optional[str] = None
    full_description: Optional[str] = None
    legal_reference: Optional[str] = None
    domain_tags: List[str] = []
    scope_tags: List[str] = []
    harmonized_standards: List[str] = []
    fee: Optional[str] = None
    application_process: Optional[str] = None
    official_link: Optional[str] = None
    updated_at: Optional[str] = None
    sources: List[str] = []
    lead_time_days: Optional[int] = None
    processing_time_days: Optional[int] = None
    prerequisites: List[str] = []
    audit_scope: List[str] = []
    test_items: List[str] = []
    other_relevant_info: Optional[str] = None

# ================================
# UTILITY FUNCTIONS
# ================================

def validate_openai_key() -> OpenAI:
    """Validate OpenAI API key and return client."""
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
        )
    return OpenAI(api_key=openai_key)

def process_llm_request(client: OpenAI, prompt: str) -> dict:
    """Process a single LLM request and return parsed JSON result."""
    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_P3_PARAMETER},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse LLM response as JSON: {str(e)}"
        )

# ================================
# INFO ENDPOINTS
# ================================

@app.get("/")
async def root():
    return {
        "message": "Certification Ingestion API",
        "endpoints": {
            "/process_certification": "Process a single certification webpage",
            "/batch_process": "Process multiple certifications", 
            "/process_file": "Process certifications from a JSON file",
            "/convert_to_markdown": "Convert URL/PDF to markdown",
            "/parse_urls": "Parse JSON file with URLs and extract PDFs",
            "/full_pipeline": "Complete pipeline: Parse → Convert → Process with LLM"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }



# ================================
# SINGLE CERTIFICATION PROCESSING
# ================================

@app.post("/process_certification", response_model=CertificationResponse)
async def process_certification(
    input_data: CertificationInput
):
    """
    Process a single certification webpage and extract structured data.
    
    Requires:
    - OPENAI_API_KEY environment variable to be set
    - Valid API key in Authorization header (Bearer token)
    """
    try:
        client = validate_openai_key()
        current_state = input_data.current_state or get_certification_state()
        prompt = build_webpage_ingestion_prompt(current_state, input_data.webpage_data)
        result = process_llm_request(client, prompt)
        return CertificationResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing certification: {str(e)}"
        )

# ================================
# BATCH PROCESSING
# ================================

@app.post("/batch_process")
async def batch_process_certifications(
    input_data: BatchCertificationInput
):
    """
    Process multiple certification webpages in batch.
    
    Requires:
    - OPENAI_API_KEY environment variable to be set
    - Valid API key in Authorization header (Bearer token)
    """
    try:
        client = validate_openai_key()
        results = []
        errors = []
        
        for idx, item in enumerate(input_data.items):
            try:
                markdown_content = item.get('markdown', '')
                if not markdown_content:
                    errors.append({
                        "index": idx,
                        "error": "No markdown content found in item"
                    })
                    continue
                
                prompt = build_webpage_ingestion_prompt(get_certification_state(), markdown_content)
                result = process_llm_request(client, prompt)
                results.append({
                    "index": idx,
                    "data": result
                })
                
            except Exception as e:
                errors.append({
                    "index": idx,
                    "error": str(e)
                })
        
        return {
            "processed": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in batch processing: {str(e)}"
        )

# ================================
# FILE PROCESSING
# ================================

@app.post("/process_file")
async def process_file_endpoint(
    input_data: ProcessFileInput
):
    """
    Process certifications from a JSON file.
    
    File should contain an array of objects with 'markdown' field.
    """
    try:
        with open(input_data.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise HTTPException(
                status_code=400,
                detail="File must contain a JSON array"
            )
        
        batch_input = BatchCertificationInput(items=data)
        return await batch_process_certifications(batch_input)
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {input_data.file_path}"
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON in file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

# ================================
# DOCUMENT CONVERSION
# ================================

@app.post("/convert_to_markdown")
async def convert_url_to_markdown(
    input_data: ConvertToMarkdownInput
):
    """
    Convert a URL (especially PDFs) or local file to markdown format.
    Uses the Datalab API for conversion.
    """
    try:
        markdown_content = convert_to_markdown(input_data.url)
        
        if markdown_content:
            return {
                "success": True,
                "url": input_data.url,
                "markdown": markdown_content,
                "length": len(markdown_content)
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to convert content to markdown"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error converting to markdown: {str(e)}"
        )

class ParseUrlListInput(BaseModel):
    file_path: str = Field(..., description="Path to JSON file containing URLs to process")

# ================================
# URL PROCESSING
# ================================

@app.post("/parse_urls")
async def parse_url_list_endpoint(
    input_data: ParseUrlListInput
):
    """
    Parse JSON file containing URLs and extract markdown from PDFs.
    Returns list of items with URL and markdown content.
    """
    try:
        results = parse_url_list_json(input_data.file_path)
        
        return {
            "success": True,
            "total_items": len(results),
            "items": results,
            "pdf_count": sum(1 for item in results 
                           if item['url'].lower().endswith('.pdf') or 'pdf' in item['url'].lower()),
            "non_pdf_count": sum(1 for item in results 
                               if not (item['url'].lower().endswith('.pdf') or 'pdf' in item['url'].lower()))
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing URL list file: {str(e)}"
        )

class FullPipelineInput(BaseModel):
    file_path: str = Field(..., description="Path to JSON file containing URLs to process")
    output_file: Optional[str] = Field(None, description="Optional output file path for results")

@app.post("/full_pipeline")
async def full_pipeline_process(
    input_data: FullPipelineInput
):
    """
    Complete pipeline: Parse URL list file → Convert PDFs → Process with LLM.
    This combines parse_url_list and batch certification processing.
    """
    try:
        # Step 1: Parse URL list file and convert PDFs
        print(f"Step 1: Parsing URL list file: {input_data.file_path}")
        parsed_items = parse_url_list_json(input_data.file_path)
        
        if not parsed_items:
            raise HTTPException(
                status_code=400,
                detail="No items found in URL list file"
            )
        
        # Step 2: Process each item through the LLM
        print(f"Step 2: Processing {len(parsed_items)} items through LLM")
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
            )
        
        client = OpenAI(api_key=openai_key)
        
        results = []
        errors = []
        
        for idx, item in enumerate(parsed_items):
            try:
                markdown_content = item.get('markdown', '')
                url = item.get('url', '')
                
                if not markdown_content:
                    errors.append({
                        "index": idx,
                        "url": url,
                        "error": "No markdown content available"
                    })
                    continue
                
                # Build prompt and call LLM
                prompt = build_webpage_ingestion_prompt(
                    certification_state.copy(), 
                    markdown_content
                )
                
                response = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_P3_PARAMETER},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,
                )
                
                result = json.loads(response.choices[0].message.content)
                
                # Add source URL to the result
                result['sources'] = [url] if url else []
                
                results.append({
                    "index": idx,
                    "url": url,
                    "certification_data": result
                })
                
                print(f"  Processed item {idx+1}/{len(parsed_items)}: {result.get('name', 'Unknown')}")
                
            except Exception as e:
                errors.append({
                    "index": idx,
                    "url": item.get('url', ''),
                    "error": str(e)
                })
                print(f"  Error processing item {idx+1}: {str(e)}")
        
        # Step 3: Save results if output file specified
        if input_data.output_file:
            try:
                with open(input_data.output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "processed": len(results),
                        "failed": len(errors),
                        "results": results,
                        "errors": errors
                    }, f, indent=2, ensure_ascii=False)
                print(f"Results saved to: {input_data.output_file}")
            except Exception as e:
                print(f"Warning: Could not save to file: {e}")
        
        return {
            "processed": len(results),
            "failed": len(errors),
            "total_items": len(parsed_items),
            "results": results,
            "errors": errors
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in full pipeline processing: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)