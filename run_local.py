#!/usr/bin/env python3
import asyncio
import json
from src.api import NewsGatherAPI
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def test_news_gather():
    """Test the news gathering functionality"""
    api = NewsGatherAPI()
    
    print("\n=== Testing News Gather ===\n")
    
    # Test 1: Get available provinces
    print("1. Getting available provinces...")
    provinces = api.get_provinces()
    print(f"Found {len(provinces['provinces'])} provinces")
    print(f"Sample: {provinces['provinces'][0]['name']}\n")
    
    # Test 2: Get news for Alberta
    print("2. Fetching news for Alberta...")
    news = await api.get_news("Alberta", limit=3, scrape=True)
    print(f"Status: {news['status']}")
    print(f"Found {news['totalResults']} articles")
    
    if news['results']:
        for i, article in enumerate(news['results']):
            print(f"\nArticle {i+1}:")
            print(f"  Title: {article['title']}")
            print(f"  Source: {article['source_name']}")
            print(f"  URL: {article['link']}")
            print(f"  Content: {article.get('content', 'No content')[:200]}...")
    
    # Test 3: Process with different host personalities
    if news['results']:
        print("\n3. Processing articles with different personalities...\n")
        
        for host_type in ["anchor", "friend", "newsreel"]:
            print(f"\n--- {host_type.upper()} PERSONALITY ---")
            processed = await api.process_news(
                news['results'][:1],  # Just process first article
                host_type=host_type,
                province="Alberta"
            )
            
            if processed['status'] == 'success' and processed['articles']:
                article = processed['articles'][0]
                print(f"Title: {article['title']}")
                print(f"Processed Content:\n{article['content']}\n")

async def test_specific_url():
    """Test scraping a specific URL"""
    api = NewsGatherAPI()
    
    print("\n=== Testing Specific URL Scraping ===\n")
    
    test_url = "https://www.cbc.ca/news/canada/calgary/latest"
    result = await api.scrape_urls([test_url])
    
    if result['status'] == 'success' and result['results']:
        scraped = result['results'][0]
        print(f"URL: {scraped['url']}")
        print(f"Title: {scraped['title']}")
        print(f"Content Preview: {scraped['content'][:500]}...")

def main():
    """Main entry point"""
    print("Starting TKR News Gather Tests...")
    
    # Run the tests
    asyncio.run(test_news_gather())
    
    # Uncomment to test specific URL scraping
    # asyncio.run(test_specific_url())

if __name__ == "__main__":
    main()