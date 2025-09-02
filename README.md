# BlueJay TIC Certification Database

A simplified, efficient system that maps and extracts certification information from regulatory websites using Firecrawl's web scraping capabilities.

## 🎯 What This System Does

This system automatically:
1. **Maps** website structure to discover all available URLs
2. **Extracts** title, URL, and description for each discovered page
3. **Categorizes** URLs by their path structure
4. **Exports** results in structured JSON format for analysis

## 🏗️ System Architecture

```
BlueJay/
├── src/
│   ├── core/                    # Core utilities
│   │   ├── config.py           # Configuration management
│   │   └── __init__.py         # Package initialization
│   └── discovery/              # Discovery engine
│       ├── firecrawl_client.py    # Firecrawl API wrapper with mapping
│       └── website_map.py         # Simple website mapping script
├── demo_discovery.py            # Main demo script
├── requirements.txt             # Python dependencies
├── env.template                 # Environment variables template
└── README.md                    # This documentation
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Copy environment template
cp env.template .env

# Edit .env file with your API key
FIRECRAWL_API_KEY=your_actual_firecrawl_api_key_here
```

### 2. Install Dependencies
   ```bash
   pip install -r requirements.txt
   ```

### 3. Run Discovery Demo
```bash
python demo_discovery.py
```

### 4. Run Simple Website Mapping
```bash
python src/discovery/website_map.py
```

## ⚠️ Free Tier Limitations

**Important**: This system is configured for Firecrawl's free tier:
- **Rate Limit**: 5 requests per minute
- **Simple Mapping**: Basic URL discovery with metadata
- **No Complex Crawling**: Focused on efficient mapping only

For production use, consider upgrading your Firecrawl plan at [https://firecrawl.dev/pricing](https://firecrawl.dev/pricing)

## 🔍 Complete System Flow

```
Input: Website URL + Optional Search Term
    ↓
Firecrawl Map API Call
    ↓
URL Discovery with Metadata Extraction
    ↓
URL Categorization by Path Structure
    ↓
Result Compilation & Export
    ↓
Output: Structured Mapping Results
```

## 📚 Key Components

### Core System (`src/core/`)

#### `config.py` - Configuration Management

**Purpose**: Manages system configuration including API keys and settings.

**Key Functions**:
- **`get_config(test_mode=False)`** - Returns configuration instance
- **`Config.validate()`** - Validates configuration completeness
- **`Config.get_api_key()`** - Retrieves the configured API key

### Discovery Engine (`src/discovery/`)

#### `firecrawl_client.py` - Firecrawl API Wrapper

**Purpose**: Provides a clean interface to Firecrawl's web scraping API with rate limiting and error handling.

**Key Functions**:

- **`map_website_simple(url, search=None)`**
  - **Purpose**: Simple mapping function that returns title, URL, and description
  - **Parameters**:
    - `url`: Base URL to map
    - `search`: Optional search term
  - **Returns**: List of dictionaries with url, title, and description
  - **Features**: No fallbacks, clean and simple approach

- **`map_website_complete(url, search_term, ...)`**
  - **Purpose**: Complete website mapping with processing and optional file saving
  - **Returns**: Dictionary with complete mapping results including categorization

- **`_check_rate_limit()`**
  - **Purpose**: Enforces API rate limiting (5 requests per minute for free tier)
  - **Algorithm**: Automatic throttling and waiting

- **`extract_links_with_metadata(map_result)`**
  - **Purpose**: Extracts URLs with title and description from Firecrawl results
  - **Returns**: List of dictionaries with url, title, and description

- **`categorize_urls(urls, base_url)`**
  - **Purpose**: Categorizes URLs by their path structure
  - **Categories**: Homepage, Blog/News, Products/Services, About/Company, Contact, Documentation/Help, Other

#### `website_map.py` - Simple Website Mapping Script

**Purpose**: Standalone script for simple website mapping operations.

**Key Functions**:
- **`main()`** - Interactive website mapping with user input
- **`map_website_simple(url, search_term)`** - Simple function to map a website and return results

## 📊 Simple Data Flow

### Website Mapping Process
```
Input: Website URL + Optional Search Term
    ↓
Firecrawl Map API Call
    ↓
URL Discovery with Metadata (title, description)
    ↓
URL Categorization by Path Structure
    ↓
Result Compilation & Export (JSON/TXT)
    ↓
Output: Structured Mapping Results
```

## 🎯 Example Usage

### Simple Website Mapping
```python
from src.discovery.firecrawl_client import FirecrawlClient

# Initialize client
firecrawl_client, success, error_msg = FirecrawlClient.create_client()

if success:
    # Simple mapping - returns title, URL, and description
    links = firecrawl_client.map_website_simple(
        url="https://foscos.fssai.gov.in/",
        search="license"  # Optional search term
    )
    
    # Display results
    for link in links:
        print(f"URL: {link['url']}")
        print(f"Title: {link['title']}")
        print(f"Description: {link['description']}")
        print("---")
```

### Complete Website Mapping with Categorization
```python
# Complete mapping with file export
result = firecrawl_client.map_website_complete(
    url="https://foscos.fssai.gov.in/",
    search_term="license",
    save_files=True
)

print(f"Total URLs discovered: {result['total_urls']}")
print(f"Categories: {list(result['categories'].keys())}")
```

## 🔧 Configuration Options

### Environment Variables
```env
FIRECRAWL_API_KEY=your_api_key_here
MAX_REQUESTS_PER_MINUTE=5
```

### Mapping Options
- **search**: Optional search term to filter URLs
- **save_files**: Whether to save results to JSON/TXT files (default: True)
- **limit**: Maximum number of URLs to return (default: 0 for no limit)

## 📈 Output Structure

### Simple Mapping Result
```python
[
    {
        "url": "https://foscos.fssai.gov.in/",
        "title": "FSSAI License Registration",
        "description": "Official FSSAI license registration portal"
    },
    {
        "url": "https://foscos.fssai.gov.in/license",
        "title": "License Application",
        "description": "Apply for FSSAI license online"
    }
]
```

### Complete Mapping Result
```python
{
    "website_url": "https://foscos.fssai.gov.in/",
    "search_term": "license",
    "total_urls": 150,
    "unique_urls": 150,
    "urls": ["https://foscos.fssai.gov.in/", ...],
    "categories": {
        "Homepage": ["https://foscos.fssai.gov.in/"],
        "Products/Services": ["https://foscos.fssai.gov.in/license", ...],
        "Other": [...]
    },
    "links_with_metadata": [
        {
            "url": "https://foscos.fssai.gov.in/",
            "title": "FSSAI License Registration",
            "description": "Official FSSAI license registration portal"
        }
    ],
    "success": true,
    "files": {
        "json_file": "website_map_foscos.fssai.gov.in_.json",
        "txt_file": "urls_foscos.fssai.gov.in_.txt"
    }
}
```

## 🚨 Error Handling & Resilience

The system handles various error scenarios gracefully:

- **API Failures**: Graceful error handling with informative messages
- **Rate Limiting**: Automatic throttling and waiting (5 requests/minute)
- **Network Issues**: Connection timeout handling
- **Invalid Data**: Validation and error reporting
- **Empty Results**: Returns empty list instead of crashing

## 🔍 Troubleshooting

### Common Issues
1. **API Key Error**: Check `.env` file and API key validity
2. **Rate Limiting**: System automatically handles this with 5 requests/minute limit
3. **Network Issues**: Check internet connectivity
4. **Empty Results**: Website may not have discoverable links or search term too specific

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## 🎉 What You Get

After running website mapping, you'll have:

1. **Complete URL list** with titles and descriptions
2. **Categorized URLs** organized by path structure
3. **Structured data** ready for further processing
4. **Export files** in JSON and TXT formats
5. **Clean, simple results** without complex fallbacks

## 🚀 Performance Characteristics

- **Mapping Speed**: 100-500 URLs in 1-2 minutes
- **Rate Limiting**: 5 requests per minute (free tier)
- **Memory Usage**: Efficient processing for large websites
- **Simple Output**: Clean title, URL, and description format

## 🔮 Future Enhancements

- **Enhanced Metadata**: More detailed page information
- **Advanced Filtering**: Better search term handling
- **Batch Processing**: Multiple website mapping
- **API Endpoints**: REST API for integration
- **Dashboard**: Web interface for results visualization

---

**BlueJay TIC Certification Database** - Simple, efficient website mapping for certification discovery.

*Built with ❤️ using Firecrawl's powerful web scraping capabilities*
