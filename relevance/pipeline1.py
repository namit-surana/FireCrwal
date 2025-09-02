"""
URL Relevance Scoring Pipeline

This module processes URLs against certification data to determine their relevance.
It provides two modes:
1. Batch processing: Process URLs in batches using LLM
2. Individual scoring: Score each URL individually for better accuracy

Dependencies:
- OpenAI API for LLM processing
- Custom prompt module for generating prompts
- Loguru for logging
"""

from prompt import build_batch_prompt, build_relevance_scoring_prompt, build_prompt
from openai import OpenAI
import json 
from loguru import logger
import os


# ============================================================================
# BATCH PROCESSING FUNCTIONS
# ============================================================================

def preprocessing(data, batch_size=50):
    """
    Process URLs in batches using LLM for relevance analysis.
    
    This function loads certification data and URLs, then processes them in batches
    through the LLM to determine relevance. Note: Only returns the last batch result.
    
    Args:
        data (str): Path to JSON file containing certification info and URLs
        batch_size (int): Number of URLs to process per batch (default: 50)
    
    Returns:
        str: Raw LLM output from the last processed batch
        
    Note:
        This function has a bug - it only returns the last batch result.
        Consider using score_all_urls_individually() for complete processing.
    """
    # Load input data from JSON file
    with open(data, "r", encoding='utf-8') as f:
        input = json.load(f)
    
    # Extract certification context and URL list
    certification_info = input['certification']
    all_urls = input.get('links', [])

    logger.info(f"Finished loading {len(all_urls)} URLs from {data}")

    # Initialize OpenAI client
    client = OpenAI()
    
    # Process URLs in batches
    for i in range(0, len(all_urls), batch_size):
        # Extract current batch of URLs
        urls_batch = all_urls[i:i + batch_size]
        
        # Build prompt for current batch
        prompt = build_batch_prompt(certification_info, urls_batch)
        
        logger.info(f"Batch {i//batch_size + 1}: Processing {len(urls_batch)} URLs")
        logger.info("Agent sending prompt to LLM...")

        # Send batch to LLM for processing
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,  # Deterministic responses
        )
        
        logger.info("Agent received response from LLM.")
        raw_output = response.choices[0].message.content
        
    logger.info("Finished processing all batches.")
    return raw_output  # BUG: Only returns last batch result

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def parse_and_save_json(raw_output, output_path):
    """
    Parse the LLM response and save it as a JSON file.
    
    Args:
        raw_output (str): Raw string output from LLM
        output_path (str): Path where to save the JSON file
    
    Returns:
        list: Parsed JSON data
    """
    try:
        # Extract JSON from the response, handling markdown code blocks
        # LLM often wraps JSON in ```json...``` blocks
        if "```json" in raw_output:
            json_start = raw_output.find("```json") + 7
            json_end = raw_output.find("```", json_start)
            json_str = raw_output[json_start:json_end].strip()
        else:
            # Use raw output if no markdown formatting
            json_str = raw_output.strip()
        
        # Parse the JSON string into Python data structure
        parsed_data = json.loads(json_str)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save parsed data to JSON file with proper encoding
        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Successfully saved {len(parsed_data)} items to {output_path}")
        return parsed_data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        logger.debug(f"Raw output preview: {raw_output[:500]}...")
        return []
    except Exception as e:
        logger.error(f"Error saving JSON file: {e}")
        return []

# ============================================================================
# INDIVIDUAL URL SCORING FUNCTIONS
# ============================================================================

def score_individual_url(certification_info, url_data, client=None):
    """
    Score a single URL for relevance to the certification.
    
    Args:
        certification_info (dict): Certification context
        url_data (dict): Single URL object with url, title, description
        client (OpenAI): OpenAI client instance
    
    Returns:
        dict: URL data with relevance_score, reasoning, and cleaned desc
    """
    # Initialize OpenAI client if not provided
    if client is None:
        client = OpenAI()
    
    # Build prompt for scoring this specific URL
    prompt = build_relevance_scoring_prompt(certification_info, url_data)
    
    try:
        # Send URL to LLM for relevance scoring
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that evaluates URL relevance."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,  # Deterministic scoring
        )
        
        raw_output = response.choices[0].message.content
        
        # Parse JSON response (same logic as parse_and_save_json)
        if "```json" in raw_output:
            json_start = raw_output.find("```json") + 7
            json_end = raw_output.find("```", json_start)
            json_str = raw_output[json_start:json_end].strip()
        else:
            json_str = raw_output.strip()
        
        # Parse scored URL data
        scored_url = json.loads(json_str)
        return scored_url
        
    except Exception as e:
        # Return error fallback with original URL data
        logger.error(f"Error scoring URL {url_data.get('url', '')}: {e}")
        return {
            **url_data,  # Preserve original URL data
            "relevance_score": 0,  # Default score for errors
            "reasoning": f"Error during scoring: {str(e)}",
            "desc": url_data.get("description", "")
        }

def score_all_urls_individually(data_path, output_path=None):
    """
    Score all URLs individually for relevance.
    
    Args:
        data_path (str): Path to input JSON file
        output_path (str): Path to save scored URLs (optional)
    
    Returns:
        list: List of URLs with relevance scores
    """
    # Load input data containing certification info and URLs
    with open(data_path, "r", encoding='utf-8') as f:
        input_data = json.load(f)
    
    # Extract certification context and URL list
    certification_info = input_data['certification']
    all_urls = input_data.get('links', [])
    
    # Initialize OpenAI client for all scoring requests
    client = OpenAI()
    scored_urls = []
    
    logger.info(f"Starting individual scoring for {len(all_urls)} URLs")
    
    # Score each URL individually (more accurate than batch processing)
    for i, url_data in enumerate(all_urls, 1):
        logger.info(f"Scoring URL {i}/{len(all_urls)}: {url_data.get('url', '')}")
        scored_url = score_individual_url(certification_info, url_data, client)
        scored_urls.append(scored_url)
    
    # Sort URLs by relevance score in descending order (best first)
    scored_urls.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    # Save results to file if output path specified
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(scored_urls, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Saved {len(scored_urls)} scored URLs to {output_path}")
    
    return scored_urls

# ============================================================================
# URL SELECTION FUNCTIONS
# ============================================================================

def select_top_urls(scored_urls, top_n=15):
    """
    Select top N URLs based on relevance scores.
    
    Args:
        scored_urls (list): List of URLs with relevance scores
        top_n (int): Number of top URLs to select
    
    Returns:
        list: Top N URLs
    """
    # Apply quality filter: prefer URLs with score >= 30 (considered relevant)
    relevant_urls = [url for url in scored_urls if url.get('relevance_score', 0) >= 30]
    
    # If not enough high-quality URLs, include lower-scored ones
    if len(relevant_urls) < top_n:
        logger.warning(f"Only {len(relevant_urls)} URLs with score >= 30, including lower scored URLs")
        selected_urls = scored_urls[:top_n]  # Take best available regardless of score
    else:
        selected_urls = relevant_urls[:top_n]  # Take top N from high-quality URLs
    
    # Log selection summary
    scores_preview = [url.get('relevance_score', 0) for url in selected_urls[:5]]
    logger.info(f"Selected top {len(selected_urls)} URLs (top 5 scores: {scores_preview}...)")
    return selected_urls


def interactive_url_selection(scored_urls):
    """
    Interactive selection of URLs with user input.
    
    Args:
        scored_urls (list): List of URLs with relevance scores
    
    Returns:
        list: User-selected URLs
    """
    # Display header for URL selection interface
    print("\n" + "="*80)
    print("URL RELEVANCE SCORES")
    print("="*80)
    
    # Display each URL with its score, title, and reasoning
    for i, url in enumerate(scored_urls, 1):
        score = url.get('relevance_score', 0)
        title = url.get('title', 'No Title')[:60]  # Truncate long titles
        reasoning = url.get('reasoning', 'No reasoning')[:80]  # Truncate long reasoning
        
        print(f"{i:3d}. [{score:3d}] {title}")
        print(f"     {reasoning}")
        print(f"     {url.get('url', '')}")
        print()
    
    # Get user input for number of URLs to select
    while True:
        try:
            prompt_msg = f"\nSelect top N URLs (default: 15, max: {len(scored_urls)}): "
            choice = input(prompt_msg).strip()
            
            # Use default if no input provided
            if not choice:
                top_n = 15
            else:
                top_n = int(choice)
            
            # Validate input range
            if 1 <= top_n <= len(scored_urls):
                break
            else:
                print(f"Please enter a number between 1 and {len(scored_urls)}")
        except ValueError:
            print("Please enter a valid number")
    
    # Select top N URLs (already sorted by score)
    selected_urls = scored_urls[:top_n]
    
    print(f"\n✅ Selected top {top_n} URLs")
    return selected_urls


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Check command line arguments to determine execution mode
    if len(sys.argv) > 1 and sys.argv[1] == "score":
        # INDIVIDUAL SCORING MODE (Recommended)
        # This mode scores each URL individually for better accuracy
        print("🔍 Individual URL Scoring Mode")
        print("-" * 50)
        
        # Step 1: Score all URLs individually using LLM
        scored_urls = score_all_urls_individually(
            'certification_map_FSSAI_License_Registration.json',  # Input file
            'relevance/data/scored_urls.json'  # Output file for all scored URLs
        )
        
        # Step 2: Interactive user selection of top URLs
        selected_urls = interactive_url_selection(scored_urls)
        
        # Step 3: Save final selected URLs to file
        output_path = "relevance/data/selected_top_urls.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(selected_urls, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Saved {len(selected_urls)} selected URLs to {output_path}")
        
    else:
        # BATCH PROCESSING MODE (Legacy - has bugs)
        # This mode processes URLs in batches but only returns last batch
        print("📦 Batch Processing Mode")
        print("-" * 50)
        
        # Initialize LLM client
        client = OpenAI()

        # Run batch preprocessing (WARNING: Only returns last batch)
        raw_output = preprocessing(
            'certification_map_FSSAI_License_Registration.json', 
            batch_size=50
        )

        # Parse LLM output and save to file
        output_path = "relevance/data/processed/processed_output.json"
        parsed_data = parse_and_save_json(raw_output, output_path)
        
        # Recommend using the better scoring mode
        print("\n💡 Tip: Use 'python pipeline1.py score' for individual URL scoring and selection")