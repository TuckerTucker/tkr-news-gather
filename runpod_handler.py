#!/usr/bin/env python3
"""
RunPod Serverless Handler for TKR News Gatherer

This handler provides a RunPod-compatible interface for the TKR News Gatherer API.
It supports multiple actions for news fetching, processing, and scraping.

Usage:
    POST /run with JSON payload:
    {
        "input": {
            "action": "get_news|get_provinces|process_news|scrape_urls",
            "province": "Alberta",
            "limit": 10,
            "scrape": true,
            "host_type": "anchor",
            "articles": [...],
            "urls": [...]
        }
    }
"""

import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api import NewsGatherAPI
from utils import Config, get_logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)

# Global API instance (initialized once)
news_api = None

def init_api():
    """Initialize the NewsGatherAPI instance"""
    global news_api
    if news_api is None:
        try:
            logger.info("Initializing NewsGatherAPI...")
            news_api = NewsGatherAPI()
            logger.info("NewsGatherAPI initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NewsGatherAPI: {str(e)}")
            raise
    return news_api

async def handle_get_provinces(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get_provinces action"""
    try:
        api = init_api()
        result = api.get_provinces()
        return {
            "status": "success",
            "output": result
        }
    except Exception as e:
        logger.error(f"Error in get_provinces: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

async def handle_get_news(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get_news action"""
    try:
        api = init_api()
        
        # Extract parameters
        province = job_input.get("province")
        if not province:
            return {
                "status": "error",
                "error": "Province is required for get_news action"
            }
        
        limit = job_input.get("limit", 10)
        scrape = job_input.get("scrape", True)
        
        # Validate limit
        if not isinstance(limit, int) or limit < 1 or limit > 50:
            limit = 10
        
        result = await api.get_news(province, limit, scrape)
        return {
            "status": "success",
            "output": result
        }
        
    except Exception as e:
        logger.error(f"Error in get_news: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

async def handle_process_news(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """Handle process_news action"""
    try:
        api = init_api()
        
        # Extract parameters
        articles = job_input.get("articles")
        host_type = job_input.get("host_type")
        province = job_input.get("province")
        
        # Validate required parameters
        if not articles:
            return {
                "status": "error",
                "error": "Articles list is required for process_news action"
            }
        
        if not host_type:
            return {
                "status": "error",
                "error": "Host type is required for process_news action"
            }
        
        if not province:
            return {
                "status": "error",
                "error": "Province is required for process_news action"
            }
        
        # Validate host type
        valid_hosts = ["anchor", "friend", "newsreel"]
        if host_type not in valid_hosts:
            return {
                "status": "error",
                "error": f"Invalid host_type. Must be one of: {valid_hosts}"
            }
        
        # Validate articles format
        if not isinstance(articles, list):
            return {
                "status": "error",
                "error": "Articles must be a list"
            }
        
        result = await api.process_news(articles, host_type, province)
        return {
            "status": "success",
            "output": result
        }
        
    except Exception as e:
        logger.error(f"Error in process_news: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

async def handle_scrape_urls(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """Handle scrape_urls action"""
    try:
        api = init_api()
        
        # Extract parameters
        urls = job_input.get("urls")
        
        # Validate required parameters
        if not urls:
            return {
                "status": "error",
                "error": "URLs list is required for scrape_urls action"
            }
        
        # Validate URLs format
        if not isinstance(urls, list):
            return {
                "status": "error",
                "error": "URLs must be a list"
            }
        
        # Limit number of URLs
        if len(urls) > 20:
            return {
                "status": "error",
                "error": "Maximum 20 URLs allowed per request"
            }
        
        result = await api.scrape_urls(urls)
        return {
            "status": "success",
            "output": result
        }
        
    except Exception as e:
        logger.error(f"Error in scrape_urls: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

async def handle_fetch_and_process(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """Handle fetch_and_process action - combines get_news and process_news"""
    try:
        api = init_api()
        
        # Extract parameters
        province = job_input.get("province")
        host_type = job_input.get("host_type")
        limit = job_input.get("limit", 5)
        scrape = job_input.get("scrape", True)
        
        # Validate required parameters
        if not province:
            return {
                "status": "error",
                "error": "Province is required for fetch_and_process action"
            }
        
        if not host_type:
            return {
                "status": "error",
                "error": "Host type is required for fetch_and_process action"
            }
        
        # Validate host type
        valid_hosts = ["anchor", "friend", "newsreel"]
        if host_type not in valid_hosts:
            return {
                "status": "error",
                "error": f"Invalid host_type. Must be one of: {valid_hosts}"
            }
        
        # Validate limit
        if not isinstance(limit, int) or limit < 1 or limit > 20:
            limit = 5
        
        # Fetch news first
        news_result = await api.get_news(province, limit, scrape)
        
        if news_result.get("status") != "success" or not news_result.get("results"):
            return {
                "status": "error",
                "error": f"No news found for {province}",
                "news_result": news_result
            }
        
        # Process with AI
        process_result = await api.process_news(
            news_result["results"], 
            host_type, 
            province
        )
        
        return {
            "status": "success",
            "output": {
                "news": news_result,
                "processed": process_result,
                "combined_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in fetch_and_process: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

async def process_job(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """Main job processing function"""
    try:
        logger.info(f"Processing job with input: {job_input}")
        
        # Extract action
        action = job_input.get("action")
        if not action:
            return {
                "status": "error",
                "error": "Action is required in job input"
            }
        
        # Route to appropriate handler
        if action == "get_provinces":
            return await handle_get_provinces(job_input)
        elif action == "get_news":
            return await handle_get_news(job_input)
        elif action == "process_news":
            return await handle_process_news(job_input)
        elif action == "scrape_urls":
            return await handle_scrape_urls(job_input)
        elif action == "fetch_and_process":
            return await handle_fetch_and_process(job_input)
        else:
            return {
                "status": "error",
                "error": f"Unknown action: {action}. Valid actions: get_provinces, get_news, process_news, scrape_urls, fetch_and_process"
            }
    
    except Exception as e:
        logger.error(f"Error processing job: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

def handler(event):
    """
    RunPod handler function - entry point for serverless execution
    
    Args:
        event: Dictionary containing the job input
        
    Returns:
        Dictionary with job results
    """
    try:
        # Extract input from event
        job_input = event.get("input", {})
        
        if not job_input:
            return {
                "status": "error",
                "error": "No input provided in event"
            }
        
        # Run async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(process_job(job_input))
            return result
        finally:
            loop.close()
    
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# For local testing
def test_handler():
    """Test the handler locally"""
    test_cases = [
        # Test get_provinces
        {
            "input": {
                "action": "get_provinces"
            }
        },
        # Test get_news
        {
            "input": {
                "action": "get_news",
                "province": "Alberta",
                "limit": 3,
                "scrape": False
            }
        },
        # Test fetch_and_process
        {
            "input": {
                "action": "fetch_and_process",
                "province": "Alberta",
                "host_type": "anchor",
                "limit": 2,
                "scrape": True
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n=== Test Case {i + 1}: {test_case['input']['action']} ===")
        result = handler(test_case)
        print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    # Run local tests
    import argparse
    
    parser = argparse.ArgumentParser(description="TKR News Gatherer RunPod Handler")
    parser.add_argument("--test", action="store_true", help="Run local tests")
    parser.add_argument("--action", type=str, help="Action to test")
    parser.add_argument("--province", type=str, help="Province for testing")
    parser.add_argument("--host-type", type=str, help="Host type for testing")
    parser.add_argument("--limit", type=int, default=5, help="Limit for testing")
    
    args = parser.parse_args()
    
    if args.test:
        test_handler()
    elif args.action:
        # Custom test
        test_input = {
            "input": {
                "action": args.action
            }
        }
        
        if args.province:
            test_input["input"]["province"] = args.province
        if args.host_type:
            test_input["input"]["host_type"] = args.host_type
        if args.limit:
            test_input["input"]["limit"] = args.limit
        
        print(f"Testing with input: {json.dumps(test_input, indent=2)}")
        result = handler(test_input)
        print(f"Result: {json.dumps(result, indent=2)}")
    else:
        print("Use --test to run all tests or --action to test specific action")
        print("Example: python runpod_handler.py --test")
        print("Example: python runpod_handler.py --action get_provinces")
        print("Example: python runpod_handler.py --action get_news --province Alberta --limit 3")