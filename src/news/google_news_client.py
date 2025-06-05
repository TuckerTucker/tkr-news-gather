from .google_news_client_improved import ImprovedGoogleNewsClient
from typing import List, Dict, Optional
import hashlib
import asyncio
from datetime import datetime
from .google_news_decoder import decode_google_news_url
from .provinces import get_province_info
from ..utils.logger import get_logger

logger = get_logger(__name__)

class GoogleNewsClient:
    def __init__(self):
        self.client = None
    
    async def _get_client(self):
        """Get or create the improved client"""
        if self.client is None:
            self.client = ImprovedGoogleNewsClient()
        return self.client

    def get_news_by_province(self, province: str, limit: int = 10) -> List[Dict]:
        """Fetch news for a specific Canadian province (sync wrapper)"""
        return asyncio.run(self.get_news_by_province_async(province, limit))

    async def get_news_by_province_async(self, province: str, limit: int = 10) -> List[Dict]:
        """Fetch news for a specific Canadian province"""
        province_info = get_province_info(province)
        if not province_info:
            raise ValueError(f"Unknown province: {province}")
        
        all_results = []
        seen_urls = set()
        
        client = await self._get_client()
        
        # Search using different terms to get diverse results
        for search_term in province_info['search_terms']:
            try:
                logger.info(f"Searching for: {search_term}")
                articles = await client.search(search_term, country='CA', language='en')
                
                for article in articles:
                    # Skip if we've seen this URL
                    if article.link in seen_urls:
                        continue
                    
                    seen_urls.add(article.link)
                    
                    article_dict = {
                        'article_id': article.guid or '',
                        'wtkr_id': self.generate_wtkr_id({'link': article.link, 'title': article.title}),
                        'title': article.title,
                        'link': article.link,
                        'original_link': article.link,  # Improved client already decodes URLs
                        'source_name': article.source,
                        'pub_date': article.published.isoformat(),
                        'summary': article.summary,
                        'language': 'en',
                        'country': 'ca'
                    }
                    
                    all_results.append(article_dict)
                    
                    if len(all_results) >= limit:
                        return all_results[:limit]
                        
            except Exception as e:
                logger.error(f"Error searching for {search_term}: {str(e)}")
                continue
        
        return all_results[:limit]
    
    def generate_wtkr_id(self, article: Dict) -> str:
        """Generate unique WTKR ID for article"""
        # Create a unique ID from URL and title
        unique_string = f"{article.get('link', '')}{article.get('title', '')}"
        hash_object = hashlib.md5(unique_string.encode())
        return f"wtkr-{hash_object.hexdigest()[:8]}"