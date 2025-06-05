import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
from datetime import datetime
from urllib.parse import urlparse
import re
from ..utils.logger import get_logger

logger = get_logger(__name__)

class SimpleArticleScraper:
    """Simplified article scraper using just aiohttp and BeautifulSoup"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scrape_article(self, url: str) -> Optional[Dict]:
        """Scrape article content from URL"""
        try:
            logger.info(f"Scraping: {url}")
            
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract title
                    title = None
                    title_element = soup.find('h1') or soup.find('title')
                    if title_element:
                        title = title_element.get_text(strip=True)
                    
                    # Try meta og:title
                    if not title:
                        og_title = soup.find('meta', property='og:title')
                        if og_title:
                            title = og_title.get('content', '')
                    
                    # Extract main content
                    content = self._extract_content(soup)
                    
                    # Generate summary
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
                    logger.error(f"Failed to scrape {url}: HTTP {response.status}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout scraping {url}")
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
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            element.decompose()
        
        # Try to find main content area
        content = ""
        
        # Common article containers
        article_selectors = [
            'article',
            'main',
            '[role="main"]',
            '.article-content',
            '.entry-content',
            '.post-content',
            '.content',
            '#content'
        ]
        
        for selector in article_selectors:
            content_area = soup.select_one(selector)
            if content_area:
                content = content_area.get_text(separator='\n', strip=True)
                if len(content) > 200:  # Minimum content length
                    break
        
        # Fallback to body
        if not content or len(content) < 200:
            body = soup.find('body')
            if body:
                # Get all paragraphs
                paragraphs = body.find_all('p')
                content = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        
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