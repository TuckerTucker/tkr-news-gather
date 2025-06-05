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