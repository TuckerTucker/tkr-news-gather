try:
    from .google_news_client import GoogleNewsClient
    GOOGLE_NEWS_AVAILABLE = True
except ImportError:
    GOOGLE_NEWS_AVAILABLE = False
    GoogleNewsClient = None

from .article_scraper import ArticleScraper
from .news_processor import NewsProcessor
from .provinces import PROVINCES, get_all_provinces

try:
    from .simple_news_client import SimpleNewsClient
    SIMPLE_NEWS_AVAILABLE = True
except ImportError:
    SIMPLE_NEWS_AVAILABLE = False
    SimpleNewsClient = None

__all__ = ['ArticleScraper', 'NewsProcessor', 'PROVINCES', 'get_all_provinces']
if GOOGLE_NEWS_AVAILABLE:
    __all__.append('GoogleNewsClient')
if SIMPLE_NEWS_AVAILABLE:
    __all__.append('SimpleNewsClient')