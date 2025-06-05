import asyncio
import aiohttp
try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    AsyncWebCrawler = None
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
from datetime import datetime
from urllib.parse import urlparse
import re
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ArticleScraper:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.crawler = None
    
    async def __aenter__(self):
        self.crawler = AsyncWebCrawler()
        await self.crawler.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc_val, exc_tb)
    
    async def scrape_article(self, url: str) -> Optional[Dict]:
        """Scrape full article content from URL"""
        try:
            logger.info(f"Scraping: {url}")
            
            # Use crawl4ai for JavaScript-heavy sites
            result = await self.crawler.arun(
                url=url,
                config={
                    "timeout": self.timeout,
                    "wait_for": "body",
                    "remove_selectors": ["script", "style", "nav", "header", "footer", "aside"]
                }
            )
            
            if result.success:
                # Parse with BeautifulSoup for better text extraction
                soup = BeautifulSoup(result.html, 'html.parser')
                
                # Extract title
                title = None
                for selector in ['h1', 'title', 'meta[property="og:title"]']:
                    element = soup.select_one(selector)
                    if element:
                        title = element.get_text() if selector != 'meta[property="og:title"]' else element.get('content')
                        if title:
                            break
                
                # Extract main content
                content = self._extract_content(soup)
                
                # Generate summary (first 2-3 sentences)
                summary = self._generate_summary(content)
                
                return {
                    'url': url,
                    'domain': urlparse(url).netloc,
                    'title': title or 'No title found',
                    'content': content,
                    'summary': summary,
                    'scraped_at': datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"Failed to scrape {url}: {result.error}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    async def scrape_multiple(self, urls: List[str]) -> List[Dict]:
        """Scrape multiple URLs concurrently"""
        tasks = [self.scrape_article(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        scraped_articles = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to scrape {url}: {str(result)}")
            elif result:
                scraped_articles.append(result)
        
        return scraped_articles
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try to find main content area
        content_areas = soup.find_all(['article', 'main', 'div'], class_=re.compile('content|article|post|entry'))
        
        if content_areas:
            # Get the largest content area
            largest_area = max(content_areas, key=lambda x: len(x.get_text(strip=True)))
            content = largest_area.get_text(separator='\n', strip=True)
        else:
            # Fallback to body content
            body = soup.find('body')
            content = body.get_text(separator='\n', strip=True) if body else ''
        
        # Clean up content
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        content = '\n'.join(lines)
        
        return content[:5000]  # Limit content length
    
    def _generate_summary(self, content: str) -> str:
        """Generate a simple summary from content"""
        if not content:
            return ""
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
        
        # Take first 2-3 sentences
        summary_sentences = sentences[:3]
        summary = '. '.join(summary_sentences)
        
        if summary and not summary.endswith('.'):
            summary += '.'
        
        return summary[:500]  # Limit summary length