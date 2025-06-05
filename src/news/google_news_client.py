from pygooglenews import GoogleNews
from typing import List, Dict, Optional
import hashlib
from datetime import datetime
from .google_news_decoder import decode_google_news_url
from .provinces import get_province_info
from ..utils.logger import get_logger

logger = get_logger(__name__)

class GoogleNewsClient:
    def __init__(self):
        self.gn = GoogleNews(lang='en', country='CA')
    
    def get_news_by_province(self, province: str, limit: int = 10) -> List[Dict]:
        """Fetch news for a specific Canadian province"""
        province_info = get_province_info(province)
        if not province_info:
            raise ValueError(f"Unknown province: {province}")
        
        all_results = []
        seen_urls = set()
        
        # Search using different terms to get diverse results
        for search_term in province_info['search_terms']:
            try:
                logger.info(f"Searching for: {search_term}")
                search_results = self.gn.search(search_term, when='1d')
                
                if 'entries' in search_results:
                    for entry in search_results['entries']:
                        decoded_url = decode_google_news_url(entry.get('link', ''))
                        
                        # Skip if we've seen this URL
                        if decoded_url in seen_urls:
                            continue
                        
                        seen_urls.add(decoded_url)
                        
                        article = {
                            'article_id': entry.get('id', ''),
                            'wtkr_id': self.generate_wtkr_id(entry),
                            'title': entry.get('title', ''),
                            'link': decoded_url,
                            'original_link': entry.get('link', ''),
                            'source_name': entry.get('source', {}).get('title', ''),
                            'pub_date': entry.get('published', ''),
                            'summary': entry.get('summary', ''),
                            'language': 'en',
                            'country': 'ca'
                        }
                        
                        all_results.append(article)
                        
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