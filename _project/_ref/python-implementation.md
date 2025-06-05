# Python News Gather Implementation

## 1. src/utils/logger.py
```python
import logging
import sys
from typing import Optional

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get a configured logger instance"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    log_level = level or logging.INFO
    logger.setLevel(log_level)
    
    return logger
```

## 2. src/utils/anthropic_client.py
```python
from anthropic import Anthropic
from typing import Dict, List, Optional
from ..utils.logger import get_logger

logger = get_logger(__name__)

class AnthropicClient:
    def __init__(self, config):
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.ANTHROPIC_MODEL
        self.temperature = config.LLM_TEMP
        self.max_tokens = config.LLM_MAX_TOKENS
    
    async def generate_completion(
        self, 
        system_prompt: str, 
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> str:
        """Generate completion using Anthropic API"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=temperature or self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise
```

## 3. src/news/provinces.py
```python
PROVINCES = {
    "Alberta": {
        "name": "Alberta",
        "abbr": "AB",
        "cities": ["Edmonton", "Calgary", "Red Deer", "Lethbridge", "Fort McMurray", "Medicine Hat", "Grande Prairie"],
        "regions": ["Southern Alberta", "Northern Alberta", "Central Alberta", "Rocky Mountains", "Badlands"],
        "search_terms": ["Alberta news", "Calgary news", "Edmonton news", "Alberta Canada"]
    },
    "British Columbia": {
        "name": "British Columbia",
        "abbr": "BC",
        "cities": ["Vancouver", "Victoria", "Kelowna", "Kamloops", "Prince George", "Nanaimo", "Abbotsford"],
        "regions": ["Lower Mainland", "Vancouver Island", "Interior BC", "Northern BC", "Sunshine Coast"],
        "search_terms": ["BC news", "British Columbia news", "Vancouver news", "Victoria BC news"]
    },
    "Manitoba": {
        "name": "Manitoba",
        "abbr": "MB",
        "cities": ["Winnipeg", "Brandon", "Steinbach", "Thompson", "Portage la Prairie", "Selkirk"],
        "regions": ["Winnipeg Capital Region", "Western Manitoba", "Northern Manitoba", "Eastern Manitoba"],
        "search_terms": ["Manitoba news", "Winnipeg news", "Manitoba Canada news"]
    },
    "New Brunswick": {
        "name": "New Brunswick",
        "abbr": "NB",
        "cities": ["Fredericton", "Saint John", "Moncton", "Dieppe", "Miramichi", "Bathurst"],
        "regions": ["Greater Moncton", "Greater Saint John", "Fredericton Region", "Northern NB"],
        "search_terms": ["New Brunswick news", "NB news", "Moncton news", "Saint John news"]
    },
    "Newfoundland and Labrador": {
        "name": "Newfoundland and Labrador",
        "abbr": "NL",
        "cities": ["St. John's", "Mount Pearl", "Corner Brook", "Conception Bay South", "Grand Falls-Windsor"],
        "regions": ["Avalon Peninsula", "Central Newfoundland", "Western Newfoundland", "Labrador"],
        "search_terms": ["Newfoundland news", "NL news", "St Johns news", "Newfoundland and Labrador"]
    },
    "Northwest Territories": {
        "name": "Northwest Territories",
        "abbr": "NT",
        "cities": ["Yellowknife", "Hay River", "Inuvik", "Fort Smith", "Behchokǫ̀"],
        "regions": ["North Slave", "South Slave", "Dehcho", "Sahtu", "Beaufort Delta"],
        "search_terms": ["Northwest Territories news", "NWT news", "Yellowknife news", "Arctic news"]
    },
    "Nova Scotia": {
        "name": "Nova Scotia",
        "abbr": "NS",
        "cities": ["Halifax", "Dartmouth", "Sydney", "Truro", "New Glasgow", "Glace Bay"],
        "regions": ["Halifax Regional Municipality", "Cape Breton", "South Shore", "Annapolis Valley"],
        "search_terms": ["Nova Scotia news", "Halifax news", "Cape Breton news", "NS news"]
    },
    "Nunavut": {
        "name": "Nunavut",
        "abbr": "NU",
        "cities": ["Iqaluit", "Rankin Inlet", "Arviat", "Baker Lake", "Cambridge Bay"],
        "regions": ["Qikiqtaaluk", "Kivalliq", "Kitikmeot"],
        "search_terms": ["Nunavut news", "Iqaluit news", "Arctic Canada news", "Nunavut territory"]
    },
    "Ontario": {
        "name": "Ontario",
        "abbr": "ON",
        "cities": ["Toronto", "Ottawa", "Mississauga", "Hamilton", "London", "Kitchener", "Windsor"],
        "regions": ["Greater Toronto Area", "Ottawa Valley", "Southwestern Ontario", "Northern Ontario"],
        "search_terms": ["Ontario news", "Toronto news", "Ottawa news", "GTA news"]
    },
    "Prince Edward Island": {
        "name": "Prince Edward Island",
        "abbr": "PE",
        "cities": ["Charlottetown", "Summerside", "Stratford", "Cornwall", "Montague"],
        "regions": ["Queens County", "Prince County", "Kings County"],
        "search_terms": ["PEI news", "Prince Edward Island news", "Charlottetown news", "Island news"]
    },
    "Quebec": {
        "name": "Quebec",
        "abbr": "QC",
        "cities": ["Montreal", "Quebec City", "Laval", "Gatineau", "Longueuil", "Sherbrooke"],
        "regions": ["Greater Montreal", "Quebec City Region", "Eastern Townships", "Laurentides"],
        "search_terms": ["Quebec news", "Montreal news", "Quebec City news", "Quebec Canada"]
    },
    "Saskatchewan": {
        "name": "Saskatchewan",
        "abbr": "SK",
        "cities": ["Saskatoon", "Regina", "Prince Albert", "Moose Jaw", "Swift Current"],
        "regions": ["Southern Saskatchewan", "Central Saskatchewan", "Northern Saskatchewan"],
        "search_terms": ["Saskatchewan news", "Regina news", "Saskatoon news", "Sask news"]
    },
    "Yukon": {
        "name": "Yukon",
        "abbr": "YT",
        "cities": ["Whitehorse", "Dawson City", "Watson Lake", "Haines Junction", "Carmacks"],
        "regions": ["Southern Yukon", "Central Yukon", "Northern Yukon"],
        "search_terms": ["Yukon news", "Whitehorse news", "Yukon territory news", "Northern Canada news"]
    }
}

def get_province_info(province_name: str) -> dict:
    """Get province information by name (case-insensitive)"""
    for key, value in PROVINCES.items():
        if key.lower() == province_name.lower():
            return value
    return None

def get_all_provinces() -> list:
    """Get list of all provinces with their info"""
    return list(PROVINCES.values())
```

## 4. src/news/google_news_decoder.py
```python
import re
from urllib.parse import urlparse, parse_qs
import base64

def decode_google_news_url(google_url: str) -> str:
    """Decode Google News URL to get the actual article URL"""
    try:
        # Extract the article parameter from Google News URL
        parsed = urlparse(google_url)
        
        # For Google News URLs that use the 'articles/' format
        if '/articles/' in google_url:
            match = re.search(r'/articles/([^?]+)', google_url)
            if match:
                article_id = match.group(1)
                # Google News URLs often encode the actual URL
                # This is a simplified decoder - may need enhancement
                return google_url
        
        # For URLs with 'url' parameter
        query_params = parse_qs(parsed.query)
        if 'url' in query_params:
            return query_params['url'][0]
        
        # Return original if can't decode
        return google_url
    except Exception:
        return google_url
```

## 5. src/news/google_news_client.py
```python
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
```

## 6. src/news/article_scraper.py
```python
import asyncio
import aiohttp
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
from datetime import datetime
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

from urllib.parse import urlparse
import re
```

## 7. src/news/news_processor.py
```python
from typing import List, Dict
import json
from ..utils.anthropic_client import AnthropicClient
from ..utils.logger import get_logger

logger = get_logger(__name__)

class NewsProcessor:
    def __init__(self, anthropic_client: AnthropicClient):
        self.client = anthropic_client
        self.host_personalities = {
            "anchor": {
                "name": "Professional News Anchor",
                "style": "Professional, authoritative, and trustworthy",
                "tone": "Clear, measured, and objective",
                "instructions": """You are a professional news anchor delivering the news with authority and clarity. 
                Your delivery should be:
                - Concise and to the point
                - Objective and balanced
                - Professional but approachable
                - Using broadcast-style language
                - Including relevant context
                - Maintaining journalistic integrity"""
            },
            "friend": {
                "name": "Friendly Neighbor",
                "style": "Warm, conversational, and relatable",
                "tone": "Casual, friendly, and engaging",
                "instructions": """You are everyone's friendly neighbor sharing local news over the fence. 
                Your delivery should be:
                - Conversational and warm
                - Using everyday language
                - Adding personal touches and local relevance
                - Showing genuine interest and concern
                - Making complex topics accessible
                - Including "did you hear?" style introductions"""
            },
            "newsreel": {
                "name": "1940s Newsreel Announcer",
                "style": "Dramatic, theatrical, and vintage",
                "tone": "Bold, emphatic, and larger-than-life",
                "instructions": """You are a 1940s newsreel announcer with a dramatic flair. 
                Your delivery should be:
                - Theatrical and bombastic
                - Using vintage expressions and terminology
                - Adding dramatic emphasis and exclamations
                - Speaking in a rapid-fire, energetic style
                - Including phrases like "This just in!" and "Extraordinary developments!"
                - Making everything sound momentous and historic"""
            }
        }
    
    async def process_articles(
        self, 
        articles: List[Dict], 
        host_type: str,
        province: str = None
    ) -> List[Dict]:
        """Process articles with AI host personality"""
        if host_type not in self.host_personalities:
            raise ValueError(f"Unknown host type: {host_type}")
        
        personality = self.host_personalities[host_type]
        processed_articles = []
        
        for article in articles:
            try:
                processed_content = await self._process_single_article(
                    article, 
                    personality,
                    province
                )
                
                processed_articles.append({
                    'title': article['title'],
                    'url': article.get('link', article.get('url', '')),
                    'source': article.get('source_name', ''),
                    'content': processed_content,
                    'wtkr_id': article.get('wtkr_id', ''),
                    'original_content': article.get('content', article.get('summary', ''))
                })
                
            except Exception as e:
                logger.error(f"Error processing article {article.get('title', 'Unknown')}: {str(e)}")
                # Include original content as fallback
                processed_articles.append({
                    'title': article['title'],
                    'url': article.get('link', article.get('url', '')),
                    'source': article.get('source_name', ''),
                    'content': article.get('content', article.get('summary', '')),
                    'wtkr_id': article.get('wtkr_id', ''),
                    'original_content': article.get('content', article.get('summary', ''))
                })
        
        return processed_articles
    
    async def _process_single_article(
        self, 
        article: Dict, 
        personality: Dict,
        province: str = None
    ) -> str:
        """Process a single article with host personality"""
        
        system_prompt = f"""You are a {personality['name']} for a local news broadcast.
        Style: {personality['style']}
        Tone: {personality['tone']}
        
        {personality['instructions']}
        
        Important guidelines:
        1. Rewrite the news content in your unique style
        2. Keep all factual information accurate
        3. Maintain appropriate length (30-60 seconds when read aloud)
        4. Make it engaging for radio/podcast listeners
        5. Include the source attribution naturally
        {f"6. Add local relevance for {province} when appropriate" if province else ""}
        """
        
        user_prompt = f"""Please rewrite this news article for your broadcast:

        Title: {article['title']}
        Source: {article.get('source_name', 'Local News')}
        
        Content:
        {article.get('content', article.get('summary', ''))}
        
        Remember to:
        - Start with an attention-grabbing introduction
        - Present the key facts clearly
        - Include source attribution
        - End with a natural transition or closing
        """
        
        processed_content = await self.client.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        return processed_content.strip()
```

## 8. src/api.py
```python
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from .news import GoogleNewsClient, ArticleScraper, NewsProcessor, get_all_provinces
from .utils import Config, get_logger, AnthropicClient

logger = get_logger(__name__)

class NewsGatherAPI:
    def __init__(self):
        self.config = Config()
        self.news_client = GoogleNewsClient()
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
            # Fetch news from Google News
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
```

## 9. run_local.py
```python
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
    print("Starting WTKR News Gather Tests...")
    
    # Run the tests
    asyncio.run(test_news_gather())
    
    # Uncomment to test specific URL scraping
    # asyncio.run(test_specific_url())

if __name__ == "__main__":
    main()
```

## 10. requirements.txt
```
# Google News
pygooglenews==0.1.2

# Web Scraping
crawl4ai>=0.2.0
beautifulsoup4==4.12.2
lxml==4.9.3

# AI/LLM
anthropic>=0.18.0

# Async
aiohttp==3.9.1
asyncio==3.4.3

# Utils
python-dotenv==1.0.0
pydantic==2.5.3

# For RunPod deployment (add later)
# runpod>=1.0.0

# For Supabase integration (optional for Python)
# supabase>=2.0.0
```

## 11. .env.example
```bash
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-3-haiku-20240307
LLM_TEMP=0.7
LLM_MAX_TOKENS=2000

# Logging
LOG_LEVEL=INFO

# News settings
DEFAULT_NEWS_LIMIT=10
SCRAPE_TIMEOUT=30

# Supabase (optional for Python integration)
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## 12. setup.py
```python
from setuptools import setup, find_packages

setup(
    name="tkr-news-gather",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pygooglenews==0.1.2",
        "crawl4ai>=0.2.0",
        "beautifulsoup4==4.12.2",
        "anthropic>=0.18.0",
        "aiohttp==3.9.1",
        "python-dotenv==1.0.0",
        "pydantic==2.5.3",
    ],
    python_requires=">=3.8",
    author="WTKR Team",
    description="News gathering and processing API for WTKR",
)
```

## Next Steps

1. **Create the project structure** and copy these files
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Set up .env** with your API keys
4. **Run tests**: `python run_local.py`
5. **Add RunPod handler** for serverless deployment later

The implementation is ready to use! Would you like me to:
1. Add the RunPod handler for deployment?
2. Create integration tests?
3. Move on to building the JavaScript app in Bolt.new?
