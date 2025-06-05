from supabase import create_client, Client
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from .logger import get_logger

logger = get_logger(__name__)

class SupabaseClient:
    def __init__(self, config):
        if not config.SUPABASE_URL or not config.SUPABASE_ANON_KEY:
            logger.warning("Supabase credentials not found. Database operations will be skipped.")
            self.client = None
            return
            
        self.client: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_ANON_KEY
        )
    
    def is_available(self) -> bool:
        """Check if Supabase client is available"""
        return self.client is not None
    
    async def create_news_session(self, province: str, metadata: Dict = None) -> Optional[str]:
        """Create a new news session and return the session ID"""
        if not self.is_available():
            return None
            
        try:
            data = {
                "province": province,
                "metadata": metadata or {}
            }
            
            result = self.client.table("news_sessions").insert(data).execute()
            
            if result.data:
                session_id = result.data[0]["id"]
                logger.info(f"Created news session: {session_id} for province: {province}")
                return session_id
            return None
            
        except Exception as e:
            logger.error(f"Error creating news session: {str(e)}")
            return None
    
    async def save_articles(self, session_id: str, articles: List[Dict]) -> bool:
        """Save articles to the database"""
        if not self.is_available():
            return False
            
        try:
            # Prepare articles for insertion
            articles_data = []
            for article in articles:
                article_data = {
                    "session_id": session_id,
                    "wtkr_id": article.get("wtkr_id"),
                    "article_id": article.get("article_id"),
                    "title": article.get("title"),
                    "url": article.get("link", article.get("url")),
                    "source_name": article.get("source_name"),
                    "content": article.get("content"),
                    "summary": article.get("summary"),
                    "pub_date": article.get("pub_date"),
                    "scraped_at": article.get("scraped_at")
                }
                articles_data.append(article_data)
            
            result = self.client.table("articles").insert(articles_data).execute()
            
            if result.data:
                logger.info(f"Saved {len(result.data)} articles for session: {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error saving articles: {str(e)}")
            return False
    
    async def save_processed_articles(self, article_ids: List[str], processed_articles: List[Dict], host_type: str) -> bool:
        """Save processed articles to the database"""
        if not self.is_available():
            return False
            
        try:
            processed_data = []
            for article_id, processed in zip(article_ids, processed_articles):
                processed_data.append({
                    "article_id": article_id,
                    "host_type": host_type,
                    "processed_content": processed.get("content"),
                    "processing_metadata": {
                        "original_title": processed.get("title"),
                        "source": processed.get("source"),
                        "wtkr_id": processed.get("wtkr_id")
                    }
                })
            
            result = self.client.table("processed_articles").insert(processed_data).execute()
            
            if result.data:
                logger.info(f"Saved {len(result.data)} processed articles")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error saving processed articles: {str(e)}")
            return False
    
    async def get_latest_session(self, province: str) -> Optional[Dict]:
        """Get the latest news session for a province"""
        if not self.is_available():
            return None
            
        try:
            result = self.client.rpc("get_latest_session", {"p_province": province}).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting latest session: {str(e)}")
            return None
    
    async def get_session_articles(self, session_id: str, include_processed: bool = False) -> List[Dict]:
        """Get all articles for a session, optionally including processed content"""
        if not self.is_available():
            return []
            
        try:
            if include_processed:
                # Use the view for complete data
                result = self.client.table("news_with_audio").select("*").eq("session_id", session_id).execute()
            else:
                # Just get raw articles
                result = self.client.table("articles").select("*").eq("session_id", session_id).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting session articles: {str(e)}")
            return []
    
    async def get_provinces_with_data(self) -> List[Dict]:
        """Get list of provinces that have news data"""
        if not self.is_available():
            return []
            
        try:
            result = self.client.table("news_sessions").select("province, created_at").order("created_at", desc=True).execute()
            
            if result.data:
                # Group by province and get latest session date
                provinces = {}
                for session in result.data:
                    province = session["province"]
                    if province not in provinces:
                        provinces[province] = session["created_at"]
                
                return [{"province": k, "last_updated": v} for k, v in provinces.items()]
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting provinces with data: {str(e)}")
            return []