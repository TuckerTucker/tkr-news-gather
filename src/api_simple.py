import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from .news import NewsProcessor, get_all_provinces, SimpleNewsClient
from .news.simple_scraper import SimpleArticleScraper as ArticleScraper
from .utils import Config, get_logger, AnthropicClient

logger = get_logger(__name__)

class SimpleNewsGatherAPI:
    """Simplified version of NewsGatherAPI using RSS feeds instead of pygooglenews"""
    
    def __init__(self):
        self.config = Config()
        self.news_client = SimpleNewsClient()
        self.anthropic = AnthropicClient(self.config)
        self.processor = NewsProcessor(self.anthropic)
    
    async def get_news(
        self, 
        province: str, 
        limit: int = 10, 
        scrape: bool = True
    ) -> Dict:
        """Get news for a province with optional scraping"""
        try:
            # Fetch news from RSS feeds
            logger.info(f"Fetching news for {province}, limit={limit}")
            articles = self.news_client.get_news_by_province(province, limit)
            
            if not articles:
                return {
                    "status": "success",
                    "totalResults": 0,
                    "results": [],
                    "metadata": {
                        "province": province,
                        "timestamp": datetime.utcnow().isoformat(),
                        "limit": limit
                    }
                }
            
            # Scrape full content if requested
            if scrape:
                logger.info(f"Scraping {len(articles)} articles")
                urls = [article['link'] for article in articles]
                
                async with ArticleScraper() as scraper:
                    scraped_data = await scraper.scrape_multiple(urls)
                
                # Merge scraped content with articles
                scraped_by_url = {item['url']: item for item in scraped_data}
                
                for article in articles:
                    scraped = scraped_by_url.get(article['link'])
                    if scraped:
                        article['content'] = scraped['content']
                        article['summary'] = scraped['summary'] or article.get('summary', '')
                        article['scraped_at'] = scraped['scraped_at']
            
            return {
                "status": "success",
                "totalResults": len(articles),
                "results": articles,
                "metadata": {
                    "province": province,
                    "timestamp": datetime.utcnow().isoformat(),
                    "limit": limit,
                    "scraped": scrape
                }
            }
            
        except Exception as e:
            logger.error(f"Error in get_news: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "results": [],
                "metadata": {
                    "province": province,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
    
    async def process_news(
        self, 
        articles: List[Dict], 
        host_type: str, 
        province: str
    ) -> Dict:
        """Process articles with host personality"""
        try:
            logger.info(f"Processing {len(articles)} articles with {host_type} personality")
            
            processed = await self.processor.process_articles(
                articles, 
                host_type,
                province
            )
            
            return {
                "status": "success",
                "host_type": host_type,
                "articles": processed,
                "processed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in process_news: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "host_type": host_type,
                "articles": [],
                "processed_at": datetime.utcnow().isoformat()
            }
    
    async def scrape_urls(self, urls: List[str]) -> Dict:
        """Scrape multiple URLs"""
        try:
            logger.info(f"Scraping {len(urls)} URLs")
            
            async with ArticleScraper() as scraper:
                results = await scraper.scrape_multiple(urls)
            
            return {
                "status": "success",
                "results": results,
                "scraped_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in scrape_urls: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "results": [],
                "scraped_at": datetime.utcnow().isoformat()
            }
    
    def get_provinces(self) -> Dict:
        """Get available provinces"""
        return {
            "provinces": get_all_provinces()
        }