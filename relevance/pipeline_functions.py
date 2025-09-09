from prompt import SYSTEM_PROMPT_P3_Links, p3_process_web_search_results, SYSTEM_PROMPT_P3_PARAMETER, build_webpage_ingestion_prompt
from openai import OpenAI
import json
from loguru import logger
import argparse
import sys

# Configure loguru - will be reconfigured in main() if needed
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# ============================================================================
# Data Loading 
# ============================================================================


def certification_info_to_string(certification_path):
    with open(certification_path, 'r') as f:
        certification_info = json.load(f)
    return certification_info


def serach_results_to_string(search_results_path):
    with open(search_results_path, 'r') as f:
        search_results = f.read()
    return search_results


def certification_state_to_string(certification_state_path):
    with open(certification_state_path, 'r') as f:
        certification_state = f.read()
    return certification_state

# ============================================================================
# LLM_1 : Important Links Extraction
# ============================================================================


def important_links(certification_info: dict, search_results_links: dict):
    # Initialize OpenAI client
    client = OpenAI()

    # Prepare data items
    data_items = search_results_links['results']['data']

    # Process each url 
    output = None
    total_items = len(data_items)
    
    logger.info(f"Starting to process {total_items} URLs for important links extraction")
    
    for idx, data in enumerate(data_items, 1):
            logger.info(f"Processing URL {idx}/{total_items}...")
            
            try:
                data_content = data['url'] + data['markdown']
                prompt = p3_process_web_search_results(certification_info, data_content, output)
                
                logger.debug("Sending request to OpenAI API")
                response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT_P3_Links},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0,)
                output = response.choices[0].message.content
                logger.success(f"Successfully processed URL {idx}/{total_items}")
                
            except Exception as e:
                logger.error(f"Error processing URL {idx}: {str(e)}")
                continue

    logger.info(f"Completed processing all {total_items} URLs")
    return output


# ============================================================================
# LLM_2 : Webpage Ingestion
# ============================================================================

def webpage_ingestion(certification_info: dict, search_results: dict, certification_state: str):
    # Initialize OpenAI client
    client = OpenAI()

    # Prepare data items
    categorized_results = search_results['results']['categories']

    # Process each url 
    for category, category_data in categorized_results.items():
        logger.info(f"Processing category: {category.upper()}")
        for item in category_data['data']:
            processed_content = f"{item.get('markdown', None)}, {item.get('summary', None)}" 
            prompt = build_webpage_ingestion_prompt(certification_state, processed_content)
            response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_P3_PARAMETER},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,)
            certification_state = response.choices[0].message.content

    return certification_state


# ============================================================================
# Main Function
# ============================================================================

def main():
    """Main pipeline execution function"""
    # Setup argument parser
    parser = argparse.ArgumentParser(
        description='Process certification data pipeline'
    )
    parser.add_argument(
        '--certification-info',
        type=str,
        required=True,
        help='Path to certification info JSON file'
    )
    parser.add_argument(
        '--search-results',
        type=str,
        required=True,
        help='Path to search results JSON file'
    )
    parser.add_argument(
        '--certification-state',
        type=str,
        default='certification_state.json',
        help='Path to certification state JSON file'
    )
    parser.add_argument(
        '--output-links',
        type=str,
        default='important_links_output.json',
        help='Output path for important links'
    )
    parser.add_argument(
        '--output-state',
        type=str,
        default='updated_certification_state.json',
        help='Output path for updated certification state'
    )
    parser.add_argument(
        '--pipeline',
        type=str,
        choices=['links', 'ingestion', 'both'],
        default='both',
        help='Which pipeline to run'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        help='Optional log file path for saving logs'
    )
    
    args = parser.parse_args()
    
    # Reconfigure logger based on arguments
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=args.log_level
    )
    
    # Add file logger if specified
    if args.log_file:
        logger.add(
            args.log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=args.log_level,
            rotation="10 MB"
        )
    
    try:
        # Load certification info
        logger.info(f"Loading certification info from {args.certification_info}")
        certification_info = certification_info_to_string(args.certification_info)
        
        # Load search results
        logger.info(f"Loading search results from {args.search_results}")
        with open(args.search_results, 'r') as f:
            search_results = json.load(f)
        
        # Run pipelines based on selection
        if args.pipeline in ['links', 'both']:
            logger.info("Running important links extraction pipeline")
            links_output = important_links(certification_info, search_results)
            
            # Save important links output
            logger.info(f"Saving important links to {args.output_links}")
            with open(args.output_links, 'w') as f:
                json.dump(json.loads(links_output), f, indent=2)
            logger.info("Important links extraction completed")
        
        if args.pipeline in ['ingestion', 'both']:
            logger.info("Running webpage ingestion pipeline")
            
            # Load certification state
            logger.info(f"Loading certification state from {args.certification_state}")
            certification_state = certification_state_to_string(args.certification_state)
            
            updated_state = webpage_ingestion(certification_info, search_results, certification_state)
            
            # Save updated certification state
            logger.info(f"Saving updated state to {args.output_state}")
            with open(args.output_state, 'w') as f:
                json.dump(json.loads(updated_state), f, indent=2)
            logger.info("Webpage ingestion completed")
        
        logger.info("Pipeline execution completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()