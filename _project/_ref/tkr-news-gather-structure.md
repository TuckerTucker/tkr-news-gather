# tkr-news-gather: Python News Gatherer Package

## Project Structure

```
tkr-news-gather/
├── src/
│   ├── __init__.py
│   ├── news/
│   │   ├── __init__.py
│   │   ├── google_news_client.py    # PyGoogleNews integration
│   │   ├── google_news_decoder.py   # Decode Google News URLs
│   │   ├── article_scraper.py       # Crawl4ai web scraping
│   │   ├── news_processor.py        # Anthropic API processing
│   │   └── provinces.py             # Canadian province data
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py                # Configuration management
│   │   ├── logger.py                # Logging utilities
│   │   └── anthropic_client.py      # Anthropic API wrapper
│   └── api.py                       # Main API logic
├── tests/
│   ├── __init__.py
│   └── test_news_gather.py         # Unit tests
├── requirements.txt
├── setup.py                         # Package setup
├── .env.example
├── README.md
└── run_local.py                     # Local testing script
```

## Key Components

### 1. provinces.py - Canadian Province Data
```python
PROVINCES = {
    "Alberta": {
        "abbr": "AB",
        "cities": ["Edmonton", "Calgary", "Red Deer", "Lethbridge", "Fort McMurray"],
        "regions": ["Southern Alberta", "Northern Alberta", "Central Alberta"],
        "search_terms": ["Alberta news", "Calgary news", "Edmonton news"]
    },
    "British Columbia": {
        "abbr": "BC",
        "cities": ["Vancouver", "Victoria", "Kelowna", "Kamloops", "Prince George"],
        "regions": ["Lower Mainland", "Vancouver Island", "Interior BC"],
        "search_terms": ["BC news", "Vancouver news", "Victoria news"]
    },
    # ... other provinces
}
```

### 2. config.py - Configuration Management
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Anthropic
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    LLM_TEMP = float(os.getenv("LLM_TEMP", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # News settings
    DEFAULT_NEWS_LIMIT = int(os.getenv("DEFAULT_NEWS_LIMIT", "10"))
    SCRAPE_TIMEOUT = int(os.getenv("SCRAPE_TIMEOUT", "30"))
```

### 3. google_news_client.py - News Fetching
```python
from pygooglenews import GoogleNews
from typing import List, Dict, Optional
import hashlib

class GoogleNewsClient:
    def __init__(self):
        self.gn = GoogleNews(lang='en', country='CA')
    
    def get_news_by_province(self, province: str, limit: int = 10) -> List[Dict]:
        """Fetch news for a specific Canadian province"""
        # Implementation
        
    def generate_wtkr_id(self, article: Dict) -> str:
        """Generate unique WTKR ID for article"""
        # Use hash of URL + title
```

### 4. article_scraper.py - Web Scraping
```python
from crawl4ai import WebCrawler
from bs4 import BeautifulSoup
from typing import Dict, Optional

class ArticleScraper:
    def __init__(self):
        self.crawler = WebCrawler()
    
    async def scrape_article(self, url: str) -> Optional[Dict]:
        """Scrape full article content from URL"""
        # Implementation with error handling
```

### 5. news_processor.py - AI Processing
```python
from typing import List, Dict
from ..utils.anthropic_client import AnthropicClient

class NewsProcessor:
    def __init__(self, anthropic_client: AnthropicClient):
        self.client = anthropic_client
        self.host_personalities = {
            "anchor": {
                "style": "Professional news anchor",
                "tone": "Authoritative yet approachable",
                "instructions": "Deliver news in clear, concise manner..."
            },
            "friend": {
                "style": "Friendly neighbor",
                "tone": "Warm and conversational",
                "instructions": "Share news like talking to a friend..."
            },
            "newsreel": {
                "style": "1940s newsreel announcer",
                "tone": "Dramatic and theatrical",
                "instructions": "Old-timey radio voice with dramatic flair..."
            }
        }
    
    async def process_articles(self, articles: List[Dict], host_type: str) -> List[Dict]:
        """Process articles with AI host personality"""
        # Implementation
```

### 6. api.py - Main API Logic
```python
from typing import Dict, List, Optional
from .news import GoogleNewsClient, ArticleScraper, NewsProcessor, PROVINCES
from .utils import Config, get_logger, AnthropicClient

logger = get_logger(__name__)

class NewsGatherAPI:
    def __init__(self):
        self.config = Config()
        self.news_client = GoogleNewsClient()
        self.scraper = ArticleScraper()
        self.anthropic = AnthropicClient(self.config)
        self.processor = NewsProcessor(self.anthropic)
    
    async def get_news(self, province: str, limit: int = 10, scrape: bool = True) -> Dict:
        """Get news for a province with optional scraping"""
        # Implementation
    
    async def process_news(self, articles: List[Dict], host_type: str, province: str) -> Dict:
        """Process articles with host personality"""
        # Implementation
    
    async def scrape_urls(self, urls: List[str]) -> Dict:
        """Scrape multiple URLs"""
        # Implementation
    
    def get_provinces(self) -> Dict:
        """Get available provinces"""
        return {"provinces": list(PROVINCES.values())}
```

### 7. run_local.py - Local Testing
```python
import asyncio
from src.api import NewsGatherAPI

async def test_news_gather():
    api = NewsGatherAPI()
    
    # Test getting news
    print("Fetching Alberta news...")
    news = await api.get_news("Alberta", limit=5, scrape=True)
    print(f"Found {len(news['results'])} articles")
    
    # Test processing with host
    print("\nProcessing with news anchor personality...")
    processed = await api.process_news(
        news['results'], 
        host_type="anchor",
        province="Alberta"
    )
    
    for article in processed['articles']:
        print(f"\nTitle: {article['title']}")
        print(f"Content preview: {article['content'][:200]}...")

if __name__ == "__main__":
    asyncio.run(test_news_gather())
```

## requirements.txt
```
pygooglenews==0.1.2
crawl4ai>=0.2.0
beautifulsoup4==4.12.2
anthropic>=0.18.0
python-dotenv==1.0.0
aiohttp==3.9.1
pydantic==2.5.3
```

## .env.example
```bash
# Anthropic API
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL=claude-3-haiku-20240307
LLM_TEMP=0.7
LLM_MAX_TOKENS=2000

# Logging
LOG_LEVEL=INFO

# News settings
DEFAULT_NEWS_LIMIT=10
SCRAPE_TIMEOUT=30
```

## Next Steps

1. **Create the package structure** and implement each module
2. **Test locally** with run_local.py
3. **Add RunPod handler** for serverless deployment
4. **Create Dockerfile** for containerization
5. **Deploy to RunPod** and get endpoint URL

Would you like me to:
1. Create the actual implementation code for each module?
2. Move on to the Supabase schema setup?
3. Start with a specific component of the news gatherer?
