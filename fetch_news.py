#!/usr/bin/env python3
"""
TKR News Gather - RunPod Client
Fetches news from the deployed RunPod endpoint and saves data locally.
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Load environment variables
def load_env():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"\'')

load_env()

class TKRNewsClient:
    """Client for TKR News Gather RunPod endpoint"""
    
    def __init__(self, endpoint_url: str = None, api_key: str = None):
        self.endpoint_url = endpoint_url or os.environ.get('ENDPOINT_URL')
        self.api_key = api_key or os.environ.get('RUNPOD_API_KEY')
        
        if not self.api_key:
            raise ValueError("RUNPOD_API_KEY not found. Set it in .env or pass as parameter")
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Create output directory
        self.output_dir = Path(__file__).parent / 'news_data'
        self.output_dir.mkdir(exist_ok=True)
        
        print(f"📡 TKR News Client initialized")
        if self.endpoint_url:
            print(f"   Endpoint: {self.endpoint_url}")
        else:
            print(f"   No endpoint URL provided - will try to find active endpoints")
        print(f"   Output: {self.output_dir}")
        
        # Auto-discover endpoint if not provided
        if not self.endpoint_url:
            self.endpoint_url = self._discover_endpoint()
    
    def _discover_endpoint(self) -> Optional[str]:
        """Try to discover an active endpoint"""
        try:
            print(f"🔍 Discovering active endpoints...")
            
            # List endpoints via REST API
            rest_url = "https://rest.runpod.io/v1/endpoints"
            response = requests.get(rest_url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                endpoints = response.json()
                
                if isinstance(endpoints, list) and len(endpoints) > 0:
                    # Find the first endpoint that looks like ours
                    for endpoint in endpoints:
                        if endpoint.get('name', '').startswith('tkr-news'):
                            endpoint_id = endpoint.get('id')
                            if endpoint_id:
                                discovered_url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"
                                print(f"✅ Found endpoint: {endpoint.get('name')} ({endpoint_id})")
                                return discovered_url
                    
                    # If no TKR endpoint found, use the first available
                    first_endpoint = endpoints[0]
                    endpoint_id = first_endpoint.get('id')
                    if endpoint_id:
                        discovered_url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"
                        print(f"⚠️  Using first available endpoint: {first_endpoint.get('name')} ({endpoint_id})")
                        return discovered_url
                        
            print(f"❌ No active endpoints found")
            return None
            
        except Exception as e:
            print(f"❌ Endpoint discovery failed: {str(e)}")
            return None
    
    def _make_request(self, action: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the RunPod endpoint"""
        payload = {
            "input": {
                "action": action,
                **kwargs
            }
        }
        
        try:
            print(f"📤 Requesting: {action}")
            if kwargs:
                print(f"   Parameters: {kwargs}")
            
            response = requests.post(
                self.endpoint_url,
                json=payload,
                headers=self.headers,
                timeout=300  # 5 minute timeout for processing
            )
            
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 404:
                print(f"❌ Endpoint not found (404)")
                print(f"   URL: {self.endpoint_url}")
                print(f"   The endpoint may not be ready or URL is incorrect")
                return {"error": "Endpoint not found (404)"}
            
            response.raise_for_status()
            result = response.json()
            print(f"📊 Response received: {result.get('status', 'Unknown status')}")
            
            status = result.get("status")
            
            if status == "COMPLETED":
                print(f"✅ Success: {action}")
                return result.get("output", {})
            elif status == "IN_QUEUE":
                print(f"⏳ Request queued, waiting for processing...")
                # For sync endpoints, we should wait and poll
                return {"error": "Request is queued but endpoint returned immediately. Try async endpoint or wait.", "status": status}
            elif status == "IN_PROGRESS":
                print(f"🔄 Request in progress...")
                return {"error": "Request in progress but endpoint returned immediately. Try async endpoint.", "status": status}
            else:
                error_msg = result.get("error", f"Unexpected status: {status}")
                print(f"❌ Failed: {action} - {error_msg}")
                return {"error": error_msg, "status": status}
        
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout: {action} took longer than 5 minutes")
            return {"error": "Request timeout"}
        except requests.exceptions.RequestException as e:
            print(f"🔥 Request failed: {str(e)}")
            return {"error": str(e)}
        except Exception as e:
            print(f"💥 Unexpected error: {str(e)}")
            return {"error": str(e)}
    
    def get_provinces(self) -> List[Dict]:
        """Get list of available provinces"""
        result = self._make_request("get_provinces")
        if "error" in result:
            return []
        return result.get("provinces", [])
    
    def get_news(self, province: str, limit: int = 10, scrape: bool = True) -> Dict[str, Any]:
        """Get news for a specific province"""
        return self._make_request("get_news", 
                                province=province, 
                                limit=limit, 
                                scrape=scrape)
    
    def process_news(self, articles: List[Dict], host_type: str, province: str) -> Dict[str, Any]:
        """Process news articles with AI"""
        return self._make_request("process_news", 
                                articles=articles, 
                                host_type=host_type, 
                                province=province)
    
    def scrape_urls(self, urls: List[str]) -> Dict[str, Any]:
        """Scrape content from URLs"""
        return self._make_request("scrape_urls", urls=urls)
    
    def fetch_and_process(self, province: str, host_type: str, limit: int = 5, scrape: bool = True) -> Dict[str, Any]:
        """Fetch news and process with AI in one step"""
        return self._make_request("fetch_and_process", 
                                province=province, 
                                host_type=host_type, 
                                limit=limit, 
                                scrape=scrape)
    
    def save_data(self, data: Dict[str, Any], filename: str, format_type: str = "json") -> Path:
        """Save data to local file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == "json":
            filepath = self.output_dir / f"{timestamp}_{filename}.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        elif format_type == "txt":
            filepath = self.output_dir / f"{timestamp}_{filename}.txt"
            with open(filepath, 'w', encoding='utf-8') as f:
                if isinstance(data, dict):
                    f.write(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    f.write(str(data))
        
        print(f"💾 Saved: {filepath}")
        return filepath

def main():
    parser = argparse.ArgumentParser(description="TKR News Gather - RunPod Client")
    parser.add_argument("--province", type=str, help="Province to fetch news for")
    parser.add_argument("--host-type", type=str, choices=["anchor", "friend", "newsreel"], 
                       default="anchor", help="AI host personality")
    parser.add_argument("--limit", type=int, default=5, help="Number of articles to fetch")
    parser.add_argument("--no-scrape", action="store_true", help="Don't scrape full article content")
    parser.add_argument("--list-provinces", action="store_true", help="List available provinces")
    parser.add_argument("--action", type=str, 
                       choices=["get_news", "fetch_and_process", "get_provinces"],
                       default="fetch_and_process",
                       help="Action to perform")
    parser.add_argument("--endpoint-url", type=str, help="RunPod endpoint URL")
    parser.add_argument("--api-key", type=str, help="RunPod API key")
    parser.add_argument("--format", type=str, choices=["json", "txt"], default="json",
                       help="Output format")
    parser.add_argument("--all-provinces", action="store_true", 
                       help="Fetch news for all provinces")
    
    args = parser.parse_args()
    
    try:
        # Initialize client
        client = TKRNewsClient(
            endpoint_url=args.endpoint_url,
            api_key=args.api_key
        )
        
        # List provinces if requested
        if args.list_provinces:
            print("\n📍 Available Provinces:")
            provinces = client.get_provinces()
            if provinces:
                for i, province in enumerate(provinces, 1):
                    print(f"  {i}. {province['name']} ({province['code']})")
            else:
                print("❌ No provinces found")
            return
        
        # Fetch news for all provinces
        if args.all_provinces:
            print("\n🌐 Fetching news for all provinces...")
            provinces = client.get_provinces()
            all_results = {}
            
            for province in provinces:
                province_name = province['name']
                print(f"\n📰 Processing {province_name}...")
                
                if args.action == "fetch_and_process":
                    result = client.fetch_and_process(
                        province=province_name,
                        host_type=args.host_type,
                        limit=args.limit,
                        scrape=not args.no_scrape
                    )
                elif args.action == "get_news":
                    result = client.get_news(
                        province=province_name,
                        limit=args.limit,
                        scrape=not args.no_scrape
                    )
                
                all_results[province_name] = result
            
            # Save combined results
            filename = f"all_provinces_{args.action}"
            client.save_data(all_results, filename, args.format)
            return
        
        # Single province operation
        if not args.province:
            print("❌ Province required. Use --province or --list-provinces or --all-provinces")
            return
        
        print(f"\n📰 Fetching news for {args.province}...")
        
        if args.action == "get_provinces":
            result = client.get_provinces()
            filename = "provinces"
            
        elif args.action == "get_news":
            result = client.get_news(
                province=args.province,
                limit=args.limit,
                scrape=not args.no_scrape
            )
            filename = f"{args.province.lower().replace(' ', '_')}_news"
            
        elif args.action == "fetch_and_process":
            result = client.fetch_and_process(
                province=args.province,
                host_type=args.host_type,
                limit=args.limit,
                scrape=not args.no_scrape
            )
            filename = f"{args.province.lower().replace(' ', '_')}_processed_{args.host_type}"
        
        # Save results
        if result and "error" not in result:
            client.save_data(result, filename, args.format)
            
            # Show summary
            if args.action == "fetch_and_process":
                if "news" in result and "results" in result["news"]:
                    news_count = len(result["news"]["results"])
                    print(f"\n📊 Summary:")
                    print(f"   Articles fetched: {news_count}")
                    print(f"   Host type: {args.host_type}")
                    print(f"   Province: {args.province}")
                    if "processed" in result:
                        print(f"   AI processing: ✅ Complete")
            elif args.action == "get_news":
                if "results" in result:
                    news_count = len(result["results"])
                    print(f"\n📊 Summary:")
                    print(f"   Articles fetched: {news_count}")
                    print(f"   Province: {args.province}")
        else:
            print(f"❌ Operation failed: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)