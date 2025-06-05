import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from .logger import get_logger

logger = get_logger(__name__)

class LocalStorage:
    def __init__(self, base_path: str = "news_data"):
        self.base_path = Path(base_path)
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self):
        """Ensure the base directory exists"""
        self.base_path.mkdir(exist_ok=True)
        logger.info(f"Local storage directory ready: {self.base_path}")
    
    def save_news_session(self, province: str, articles: List[Dict], metadata: Dict = None) -> Optional[str]:
        """Save news articles to local filesystem"""
        try:
            # Create province-specific directory
            province_dir = self.base_path / province.lower()
            province_dir.mkdir(exist_ok=True)
            
            # Generate session ID based on timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = f"{province}_{timestamp}"
            
            # Create session data
            session_data = {
                "session_id": session_id,
                "province": province,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {},
                "article_count": len(articles),
                "articles": articles
            }
            
            # Save to JSON file
            filename = f"{session_id}.json"
            filepath = province_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(articles)} articles to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error saving news session locally: {str(e)}")
            return None
    
    def get_latest_session(self, province: str) -> Optional[Dict]:
        """Get the latest news session for a province"""
        try:
            province_dir = self.base_path / province.lower()
            if not province_dir.exists():
                return None
            
            # Get all JSON files and sort by modification time
            json_files = list(province_dir.glob("*.json"))
            if not json_files:
                return None
            
            latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error reading latest session: {str(e)}")
            return None
    
    def list_sessions(self, province: str = None) -> List[Dict]:
        """List all saved sessions, optionally filtered by province"""
        sessions = []
        
        try:
            if province:
                provinces = [province.lower()]
            else:
                # List all province directories
                provinces = [d.name for d in self.base_path.iterdir() if d.is_dir()]
            
            for prov in provinces:
                province_dir = self.base_path / prov
                if not province_dir.exists():
                    continue
                
                for json_file in province_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            sessions.append({
                                "session_id": data.get("session_id"),
                                "province": data.get("province"),
                                "timestamp": data.get("timestamp"),
                                "article_count": data.get("article_count", 0),
                                "filepath": str(json_file)
                            })
                    except Exception as e:
                        logger.error(f"Error reading {json_file}: {str(e)}")
            
            # Sort by timestamp descending
            sessions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return sessions
            
        except Exception as e:
            logger.error(f"Error listing sessions: {str(e)}")
            return []
    
    def delete_old_sessions(self, days_to_keep: int = 30) -> int:
        """Delete sessions older than specified days"""
        deleted_count = 0
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        try:
            for province_dir in self.base_path.iterdir():
                if not province_dir.is_dir():
                    continue
                
                for json_file in province_dir.glob("*.json"):
                    if json_file.stat().st_mtime < cutoff_date:
                        json_file.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old session: {json_file}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error deleting old sessions: {str(e)}")
            return deleted_count