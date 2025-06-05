#!/usr/bin/env python3
"""
RunPod Serverless Handler for TKR News Gather

This handler provides a RunPod-compatible interface for the TKR News Gather API.
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

# Add the current directory to Python path so we can import src as a package
sys.path.insert(0, os.path.dirname(__file__))

# Import as a package
from src.api import NewsGatherAPI
from src.utils import Config, get_logger

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
    """Handle get_news action with local and database saving support"""
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
        save_to_local = job_input.get("save_to_local", False)
        save_to_db = job_input.get("save_to_db", False)
        
        # Validate limit
        if not isinstance(limit, int) or limit < 1 or limit > 50:
            limit = 10
        
        # Get the news
        result = await api.get_news(province, limit, scrape)
        
        if result.get("status") == "success" and result.get("results"):
            # Note: save_to_local is handled by the client script, not in RunPod
            # We just pass through the flag for the client to know local saving was requested
            if save_to_local:
                result["metadata"]["save_to_local_requested"] = True
            
            # Handle database saving (cloud to cloud makes sense)
            if save_to_db:
                try:
                    from src.utils import SupabaseClient, Config
                    config = Config()
                    supabase = SupabaseClient(config)
                    if supabase.is_available():
                        session_id = await supabase.create_news_session(province, result.get("metadata", {}))
                        if session_id and result.get("results"):
                            await supabase.save_articles(session_id, result["results"])
                            result["metadata"]["session_id"] = session_id
                            logger.info(f"Saved news session to database: {session_id}")
                    else:
                        logger.warning("Database save was requested but Supabase not available")
                except Exception as e:
                    logger.error(f"Error saving to database: {str(e)}")
        
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

async def handler(job):
    """
    RunPod handler function - entry point for serverless execution
    
    Args:
        job: Dictionary containing job id and input data
        
    Returns:
        Dictionary with job results
    """
    try:
        # Extract input from job
        job_input = job.get("input", {})
        
        if not job_input:
            return {
                "error": "No input provided in job"
            }
        
        # Run async processing (no need to create new event loop)
        result = await process_job(job_input)
        
        # Return just the output for RunPod format
        if result.get("status") == "success":
            return result.get("output", result)
        else:
            return {"error": result.get("error", "Unknown error")}
    
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        return {
            "error": str(e)
        }

# For local testing
def test_handler():
    """Test the handler locally"""
    test_cases = [
        # Test get_provinces
        {
            "id": "test-job-1",
            "input": {
                "action": "get_provinces"
            }
        },
        # Test get_news
        {
            "id": "test-job-2", 
            "input": {
                "action": "get_news",
                "province": "Alberta",
                "limit": 3,
                "scrape": False
            }
        },
        # Test fetch_and_process
        {
            "id": "test-job-3",
            "input": {
                "action": "fetch_and_process",
                "province": "Alberta",
                "host_type": "anchor",
                "limit": 2,
                "scrape": True
            }
        }
    ]
    
    async def run_tests():
        for i, test_case in enumerate(test_cases):
            print(f"\n=== Test Case {i + 1}: {test_case['input']['action']} ===")
            result = await handler(test_case)
            print(f"Result: {json.dumps(result, indent=2)}")
    
    # Run the async tests
    asyncio.run(run_tests())

if __name__ == "__main__":
    # Try to start RunPod serverless worker first
    try:
        import runpod
        print("=== Starting RunPod Serverless Worker ===")
        runpod.serverless.start({"handler": handler})
    except ImportError:
        print("=== RunPod SDK not available - Local Testing Mode ===")
        # Run local tests
        import argparse
        
        parser = argparse.ArgumentParser(description="TKR News Gather RunPod Handler")
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
                "id": "test-job-123",
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
            result = asyncio.run(handler(test_input))
            print(f"Result: {json.dumps(result, indent=2)}")
        else:
            print("Use --test to run all tests or --action to test specific action")
            print("Example: python runpod_handler.py --test")
            print("Example: python runpod_handler.py --action get_provinces")
            print("Example: python runpod_handler.py --action get_news --province Alberta --limit 3")
    except Exception as e:
        print(f"Error starting RunPod worker: {e}")
        print("Falling back to test mode")
        test_handler()