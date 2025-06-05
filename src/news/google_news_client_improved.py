"""
Improved Google News Client
Replacement for unmaintained pygooglenews package
Provides secure, maintained alternative for Google News RSS feeds
"""

import httpx
import feedparser
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus, urljoin
from datetime import datetime, timezone
import logging
import asyncio
from dataclasses import dataclass
from .google_news_decoder import decode_google_news_url

logger = logging.getLogger(__name__)

@dataclass
class NewsArticle:
    """Structured representation of a news article"""
    title: str
    link: str
    published: datetime
    summary: str
    source: str
    guid: Optional[str] = None
    media_content: Optional[List[Dict]] = None

class ImprovedGoogleNewsClient:
    """
    Modern, maintained replacement for pygooglenews
    
    Features:
    - Async HTTP requests using httpx
    - Better error handling and retry logic
    - Structured data models
    - Security-focused implementation
    - Support for all Google News RSS endpoints
    """
    
    BASE_URL = "https://news.google.com/rss"
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        # Decoder function imported above
        
        # Configure HTTP client with security headers
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                'User-Agent': 'TKRNewsGather/1.0 (https://github.com/tkr-news-gather)',
                'Accept': 'application/rss+xml, application/xml, text/xml',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'DNT': '1'  # Do Not Track
            },
            follow_redirects=True,
            verify=True  # Always verify SSL certificates
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def get_news(self, query: Optional[str] = None, 
                      location: Optional[str] = None,
                      topic: Optional[str] = None,
                      language: str = 'en',
                      country: str = 'CA') -> List[NewsArticle]:
        """
        Get news articles from Google News RSS
        
        Args:
            query: Search query (optional)
            location: Geographic location filter
            topic: Topic category (WORLD, NATION, BUSINESS, etc.)
            language: Language code (default: en)
            country: Country code (default: CA for Canada)
            
        Returns:
            List of NewsArticle objects
        """
        try:
            url = self._build_url(query, location, topic, language, country)
            logger.info(f"Fetching Google News from: {url}")
            
            response = await self._make_request(url)
            articles = self._parse_feed(response.text)
            
            logger.info(f"Successfully fetched {len(articles)} articles")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching Google News: {str(e)}")
            raise
    
    async def get_top_news(self, country: str = 'CA', language: str = 'en') -> List[NewsArticle]:
        """Get top news stories"""
        return await self.get_news(country=country, language=language)
    
    async def get_topic_news(self, topic: str, country: str = 'CA', language: str = 'en') -> List[NewsArticle]:
        """
        Get news for specific topic
        
        Topics: WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT, 
                SPORTS, SCIENCE, HEALTH
        """
        return await self.get_news(topic=topic, country=country, language=language)
    
    async def search(self, query: str, country: str = 'CA', language: str = 'en') -> List[NewsArticle]:
        """Search Google News for specific query"""
        return await self.get_news(query=query, country=country, language=language)
    
    async def get_location_news(self, location: str, country: str = 'CA', language: str = 'en') -> List[NewsArticle]:
        """Get news for specific location/region"""
        return await self.get_news(location=location, country=country, language=language)
    
    def _build_url(self, query: Optional[str] = None,
                   location: Optional[str] = None,
                   topic: Optional[str] = None,
                   language: str = 'en',
                   country: str = 'CA') -> str:
        """Build Google News RSS URL with parameters"""
        
        # Base URL with language and country
        url = f"{self.BASE_URL}?hl={language}&gl={country}&ceid={country}:{language}"
        
        if topic:
            # Topic-based news
            url = f"{self.BASE_URL}/headlines/section/topic/{topic}?hl={language}&gl={country}&ceid={country}:{language}"
        elif query:
            # Search query
            encoded_query = quote_plus(query)
            url = f"{self.BASE_URL}/search?q={encoded_query}&hl={language}&gl={country}&ceid={country}:{language}"
        elif location:
            # Location-based news
            encoded_location = quote_plus(location)
            url = f"{self.BASE_URL}/local/section/geo/{encoded_location}?hl={language}&gl={country}&ceid={country}:{language}"
        
        return url
    
    async def _make_request(self, url: str) -> httpx.Response:
        """Make HTTP request with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.get(url)
                response.raise_for_status()
                return response
                
            except httpx.HTTPStatusError as e:
                last_exception = e
                if e.response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                    await asyncio.sleep(wait_time)
                elif e.response.status_code >= 500:  # Server error
                    wait_time = 2 ** attempt
                    logger.warning(f"Server error {e.response.status_code}, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    # Client error, don't retry
                    raise
                    
            except (httpx.ConnectTimeout, httpx.ReadTimeout) as e:
                last_exception = e
                wait_time = 2 ** attempt
                logger.warning(f"Timeout error, retrying in {wait_time}s (attempt {attempt + 1})")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Unexpected error making request: {str(e)}")
                raise
        
        # All retries exhausted
        if last_exception:
            raise last_exception
        else:
            raise Exception("Max retries exceeded")
    
    def _parse_feed(self, feed_content: str) -> List[NewsArticle]:
        """Parse RSS feed content into NewsArticle objects"""
        try:
            # Parse RSS feed using feedparser
            feed = feedparser.parse(feed_content)
            
            if feed.bozo:
                logger.warning(f"Feed parsing warning: {feed.bozo_exception}")
            
            articles = []
            for entry in feed.entries:
                try:
                    article = self._parse_entry(entry)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.warning(f"Error parsing article entry: {str(e)}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed: {str(e)}")
            raise
    
    def _parse_entry(self, entry) -> Optional[NewsArticle]:
        """Parse individual RSS entry into NewsArticle"""
        try:
            # Extract title
            title = getattr(entry, 'title', 'Unknown Title').strip()
            
            # Extract and decode link
            link = getattr(entry, 'link', '')
            if link:
                # Decode Google News URL if needed
                link = decode_google_news_url(link)
            
            # Parse published date
            published = self._parse_date(entry)
            
            # Extract summary/description
            summary = getattr(entry, 'summary', '').strip()
            if summary:
                # Clean HTML tags from summary
                summary = self._clean_html(summary)
            
            # Extract source
            source = self._extract_source(entry)
            
            # Extract GUID
            guid = getattr(entry, 'id', getattr(entry, 'guid', None))
            
            # Extract media content
            media_content = self._extract_media(entry)
            
            return NewsArticle(
                title=title,
                link=link,
                published=published,
                summary=summary,
                source=source,
                guid=guid,
                media_content=media_content
            )
            
        except Exception as e:
            logger.warning(f"Error parsing entry: {str(e)}")
            return None
    
    def _parse_date(self, entry) -> datetime:
        """Parse entry date with fallback to current time"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                import time
                timestamp = time.mktime(entry.published_parsed)
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                import time
                timestamp = time.mktime(entry.updated_parsed)
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)
            else:
                # Fallback to current time
                return datetime.now(timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)
    
    def _extract_source(self, entry) -> str:
        """Extract news source from entry"""
        # Try different source fields
        if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
            return entry.source.title
        elif hasattr(entry, 'tags') and entry.tags:
            # Sometimes source is in tags
            for tag in entry.tags:
                if hasattr(tag, 'term'):
                    return tag.term
        elif hasattr(entry, 'author'):
            return entry.author
        else:
            return "Unknown Source"
    
    def _extract_media(self, entry) -> Optional[List[Dict]]:
        """Extract media content from entry"""
        media_content = []
        
        if hasattr(entry, 'media_content'):
            for media in entry.media_content:
                media_content.append({
                    'url': media.get('url', ''),
                    'type': media.get('type', ''),
                    'width': media.get('width'),
                    'height': media.get('height')
                })
        
        return media_content if media_content else None
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        import re
        # Simple HTML tag removal
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()

# Factory function for backward compatibility
async def create_google_news_client() -> ImprovedGoogleNewsClient:
    """Create and return a Google News client"""
    return ImprovedGoogleNewsClient()

# For compatibility with existing code
class GoogleNews:
    """Compatibility wrapper that mimics pygooglenews interface"""
    
    def __init__(self, lang='en', country='CA'):
        self.lang = lang
        self.country = country
        self._client = None
    
    async def _get_client(self) -> ImprovedGoogleNewsClient:
        """Get or create async client"""
        if self._client is None:
            self._client = ImprovedGoogleNewsClient()
        return self._client
    
    async def top_news(self):
        """Get top news (async)"""
        client = await self._get_client()
        articles = await client.get_top_news(country=self.country, language=self.lang)
        return {'entries': [self._article_to_dict(a) for a in articles]}
    
    async def topic_headlines(self, topic):
        """Get topic headlines (async)"""
        client = await self._get_client()
        articles = await client.get_topic_news(topic, country=self.country, language=self.lang)
        return {'entries': [self._article_to_dict(a) for a in articles]}
    
    async def geo_headlines(self, geo):
        """Get geo headlines (async)"""
        client = await self._get_client()
        articles = await client.get_location_news(geo, country=self.country, language=self.lang)
        return {'entries': [self._article_to_dict(a) for a in articles]}
    
    async def search(self, query):
        """Search news (async)"""
        client = await self._get_client()
        articles = await client.search(query, country=self.country, language=self.lang)
        return {'entries': [self._article_to_dict(a) for a in articles]}
    
    def _article_to_dict(self, article: NewsArticle) -> Dict:
        """Convert NewsArticle to dict for compatibility"""
        return {
            'title': article.title,
            'link': article.link,
            'published': article.published.isoformat(),
            'summary': article.summary,
            'source': {'title': article.source},
            'id': article.guid
        }
    
    async def close(self):
        """Close the client"""
        if self._client:
            await self._client.client.aclose()