import requests
import feedparser
from typing import List, Dict, Optional
import hashlib
from datetime import datetime
from urllib.parse import quote_plus, urlparse
from .provinces import get_province_info
from ..utils.logger import get_logger

logger = get_logger(__name__)

class SimpleNewsClient:
    """Alternative news client using direct RSS feeds and search APIs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TKR-NewsBot/1.0 (News Aggregation Service)'
        })
    
    def get_news_by_province(self, province: str, limit: int = 10) -> List[Dict]:
        """Fetch news for a specific Canadian province using RSS feeds"""
        province_info = get_province_info(province)
        if not province_info:
            raise ValueError(f"Unknown province: {province}")
        
        all_results = []
        seen_urls = set()
        
        # Try different RSS sources
        rss_sources = self._get_province_rss_feeds(province)
        
        for source_name, feed_url in rss_sources.items():
            try:
                logger.info(f"Fetching from {source_name}: {feed_url}")
                
                # Fetch and parse RSS feed
                response = self.session.get(feed_url, timeout=30)
                if response.status_code == 200:
                    feed = feedparser.parse(response.content)
                    
                    for entry in feed.entries[:limit]:
                        url = entry.get('link', '')
                        
                        # Skip if we've seen this URL
                        if url in seen_urls:
                            continue
                        
                        seen_urls.add(url)
                        
                        # Parse published date
                        pub_date = ''
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6]).isoformat()
                        elif hasattr(entry, 'published'):
                            pub_date = entry.published
                        
                        article = {
                            'article_id': entry.get('id', url),
                            'wtkr_id': self._generate_wtkr_id({'link': url, 'title': entry.get('title', '')}),
                            'title': entry.get('title', ''),
                            'link': url,
                            'original_link': url,
                            'source_name': source_name,
                            'pub_date': pub_date,
                            'summary': entry.get('summary', entry.get('description', '')),
                            'language': 'en',
                            'country': 'ca'
                        }
                        
                        all_results.append(article)
                        
                        if len(all_results) >= limit:
                            return all_results[:limit]
                            
            except Exception as e:
                logger.error(f"Error fetching from {source_name}: {str(e)}")
                continue
        
        return all_results[:limit]
    
    def _get_province_rss_feeds(self, province: str) -> Dict[str, str]:
        """Get RSS feed URLs for a province"""
        # Major Canadian news RSS feeds by province
        feeds = {
            'CBC News': 'https://www.cbc.ca/cmlink/rss-topstories',
            'Global News': 'https://globalnews.ca/feed/',
        }
        
        # Province-specific feeds
        province_feeds = {
            'Alberta': {
                'CBC Calgary': 'https://www.cbc.ca/cmlink/rss-canada-calgary',
                'CBC Edmonton': 'https://www.cbc.ca/cmlink/rss-canada-edmonton',
                'Global Calgary': 'https://globalnews.ca/calgary/feed/',
                'Global Edmonton': 'https://globalnews.ca/edmonton/feed/',
            },
            'British Columbia': {
                'CBC BC': 'https://www.cbc.ca/cmlink/rss-canada-britishcolumbia',
                'Global Vancouver': 'https://globalnews.ca/vancouver/feed/',
                'Global BC': 'https://globalnews.ca/bc/feed/',
            },
            'Ontario': {
                'CBC Toronto': 'https://www.cbc.ca/cmlink/rss-canada-toronto',
                'CBC Ottawa': 'https://www.cbc.ca/cmlink/rss-canada-ottawa',
                'Global Toronto': 'https://globalnews.ca/toronto/feed/',
            },
            'Quebec': {
                'CBC Montreal': 'https://www.cbc.ca/cmlink/rss-canada-montreal',
                'Global Montreal': 'https://globalnews.ca/montreal/feed/',
            },
            'Nova Scotia': {
                'CBC Nova Scotia': 'https://www.cbc.ca/cmlink/rss-canada-novascotia',
                'Global Halifax': 'https://globalnews.ca/halifax/feed/',
            },
            'New Brunswick': {
                'CBC New Brunswick': 'https://www.cbc.ca/cmlink/rss-canada-newbrunswick',
                'Global New Brunswick': 'https://globalnews.ca/new-brunswick/feed/',
            },
            'Manitoba': {
                'CBC Manitoba': 'https://www.cbc.ca/cmlink/rss-canada-manitoba',
                'Global Winnipeg': 'https://globalnews.ca/winnipeg/feed/',
            },
            'Saskatchewan': {
                'CBC Saskatchewan': 'https://www.cbc.ca/cmlink/rss-canada-saskatchewan',
                'Global Saskatchewan': 'https://globalnews.ca/saskatchewan/feed/',
            },
            'Prince Edward Island': {
                'CBC PEI': 'https://www.cbc.ca/cmlink/rss-canada-pei',
            },
            'Newfoundland and Labrador': {
                'CBC Newfoundland': 'https://www.cbc.ca/cmlink/rss-canada-newfoundland',
            },
            'Northwest Territories': {
                'CBC North': 'https://www.cbc.ca/cmlink/rss-canada-north',
            },
            'Yukon': {
                'CBC North': 'https://www.cbc.ca/cmlink/rss-canada-north',
            },
            'Nunavut': {
                'CBC North': 'https://www.cbc.ca/cmlink/rss-canada-north',
            }
        }
        
        # Combine general feeds with province-specific ones
        result_feeds = feeds.copy()
        if province in province_feeds:
            result_feeds.update(province_feeds[province])
        
        return result_feeds
    
    def _generate_wtkr_id(self, article: Dict) -> str:
        """Generate unique WTKR ID for article"""
        unique_string = f"{article.get('link', '')}{article.get('title', '')}"
        hash_object = hashlib.md5(unique_string.encode())
        return f"wtkr-{hash_object.hexdigest()[:8]}"
    
    def search_news(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for news using a simple approach"""
        # This is a simplified implementation
        # In production, you might want to use proper news APIs
        results = []
        
        try:
            # Use CBC search as an example
            search_url = f"https://www.cbc.ca/search?q={quote_plus(query)}"
            logger.info(f"Searching: {search_url}")
            
            # For now, return empty results as we'd need to scrape search results
            # This could be enhanced with proper search API integration
            
        except Exception as e:
            logger.error(f"Error searching for {query}: {str(e)}")
        
        return results