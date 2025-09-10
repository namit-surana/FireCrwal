# Certification Ingestion API

A FastAPI-based service for processing certification documents and extracting structured data using LLM processing.

## Overview

This API provides endpoints for:
- Converting PDFs and web pages to markdown
- Processing certification data through LLM extraction
- Batch processing of multiple certifications
- Full pipeline processing from EU compliance files

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key
DATALAB_API_KEY=your_datalab_api_key
DATALAB_API_URL=your_datalab_api_url
```

### Batch Processing

#### `POST /batch_process`
Process multiple certifications in batch through LLM extraction.

**Request Body:**
```json
{
  "items": [
    {"url_1": "url", "markdown": "certification content..."},
    {"url_2": "url", "markdown": "certification content..."}
  ]
}
```

**Function:** `parse_url_list_json`

**Use Case:** When you retrieve top N links from Firecrawl results and need to:
- Convert PDF URLs to markdown using Datalab API
- Keep non-PDF URLs with their original markdown content from the JSON data
- Prepare data for LLM processing

**Input JSON Format:**
```json
{
  "results": {
    "data": [
      {
        "url": "https://example.com/document.pdf",
        "markdown": "existing content (will be replaced with PDF conversion)"
      },
      {
        "url": "https://example.com/webpage.html", 
        "markdown": "existing webpage content (will be preserved)"
      }
    ]
  }
}
```

**Output:** List of items with `url` and `markdown` fields, where PDF URLs have fresh markdown from conversion.

### Full Pipeline

#### `POST /full_pipeline`
Complete end-to-end pipeline: Parse URLs → Convert PDFs → Process with LLM.

**Request Body:**
```json
{
  "file_path": "/path/to/urls.json",
  "output_file": "/path/to/output.json" // optional
}
```

**Use Case:** Full automation from Firecrawl results to final certification data:
1. Parse URL list file and convert PDFs to markdown
2. Process all items through LLM for certification extraction
3. Optionally save results to output file

**Workflow:**
```
Firecrawl Results → parse_url_list_json → LLM Processing → Multiple Structured Certification Data → Agentic Framework for Aggregation (In Progress)
```