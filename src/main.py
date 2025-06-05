from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime

from .api import NewsGatherAPI
from .utils import Config, SupabaseClient, get_logger
from .news import get_all_provinces

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TKR News Gatherer API",
    description="Canadian news collection and AI processing service",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
config = Config()
news_api = NewsGatherAPI()
supabase = SupabaseClient(config)

# Pydantic models for request/response
class NewsRequest(BaseModel):
    province: str
    limit: int = 10
    scrape: bool = True

class ProcessRequest(BaseModel):
    articles: List[Dict[str, Any]]
    host_type: str
    province: str

class UrlScrapeRequest(BaseModel):
    urls: List[str]

class NewsResponse(BaseModel):
    status: str
    totalResults: int
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class ProcessedResponse(BaseModel):
    status: str
    host_type: str
    articles: List[Dict[str, Any]]
    processed_at: str

# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "service": "TKR News Gatherer",
        "version": "0.1.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    health_status = {
        "service": "TKR News Gatherer",
        "version": "0.1.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": "healthy",
            "anthropic": "unknown",
            "supabase": "available" if supabase.is_available() else "unavailable"
        }
    }
    
    # Test Anthropic connection
    try:
        if config.ANTHROPIC_API_KEY:
            health_status["components"]["anthropic"] = "available"
        else:
            health_status["components"]["anthropic"] = "no_api_key"
    except Exception:
        health_status["components"]["anthropic"] = "error"
    
    return health_status

# Province endpoints
@app.get("/provinces", tags=["Provinces"])
async def get_provinces():
    """Get list of all available Canadian provinces"""
    try:
        return news_api.get_provinces()
    except Exception as e:
        logger.error(f"Error getting provinces: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/provinces/with-data", tags=["Provinces"])
async def get_provinces_with_data():
    """Get provinces that have news data in the database"""
    try:
        provinces = await supabase.get_provinces_with_data()
        return {
            "provinces": provinces,
            "total": len(provinces)
        }
    except Exception as e:
        logger.error(f"Error getting provinces with data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# News endpoints
@app.get("/news/{province}", response_model=NewsResponse, tags=["News"])
async def get_news(
    province: str,
    limit: int = Query(10, ge=1, le=50, description="Number of articles to fetch"),
    scrape: bool = Query(True, description="Whether to scrape full article content"),
    save_to_db: bool = Query(False, description="Whether to save results to database")
):
    """Get news for a specific Canadian province"""
    try:
        # Fetch news
        result = await news_api.get_news(province, limit, scrape)
        
        # Save to database if requested and available
        if save_to_db and supabase.is_available() and result.get("status") == "success":
            session_id = await supabase.create_news_session(province, result.get("metadata", {}))
            if session_id and result.get("results"):
                await supabase.save_articles(session_id, result["results"])
                result["metadata"]["session_id"] = session_id
        
        return result
    except Exception as e:
        logger.error(f"Error getting news for {province}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/news", response_model=NewsResponse, tags=["News"])
async def get_news_post(request: NewsRequest):
    """Get news using POST request (for complex requests)"""
    try:
        result = await news_api.get_news(request.province, request.limit, request.scrape)
        return result
    except Exception as e:
        logger.error(f"Error getting news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Processing endpoints
@app.post("/process", response_model=ProcessedResponse, tags=["Processing"])
async def process_articles(request: ProcessRequest):
    """Process articles with AI host personality"""
    try:
        # Validate host type
        valid_hosts = ["anchor", "friend", "newsreel"]
        if request.host_type not in valid_hosts:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid host_type. Must be one of: {valid_hosts}"
            )
        
        result = await news_api.process_news(
            request.articles, 
            request.host_type, 
            request.province
        )
        return result
    except Exception as e:
        logger.error(f"Error processing articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/process/{province}/{host_type}", response_model=ProcessedResponse, tags=["Processing"])
async def process_latest_news(
    province: str,
    host_type: str,
    limit: int = Query(5, ge=1, le=20, description="Number of articles to process")
):
    """Fetch and process latest news for a province with specific host personality"""
    try:
        # Validate host type
        valid_hosts = ["anchor", "friend", "newsreel"]
        if host_type not in valid_hosts:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid host_type. Must be one of: {valid_hosts}"
            )
        
        # Fetch news first
        news_result = await news_api.get_news(province, limit, scrape=True)
        
        if news_result.get("status") != "success" or not news_result.get("results"):
            raise HTTPException(
                status_code=404, 
                detail=f"No news found for {province}"
            )
        
        # Process with AI
        result = await news_api.process_news(
            news_result["results"], 
            host_type, 
            province
        )
        return result
    except Exception as e:
        logger.error(f"Error processing latest news: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Scraping endpoints
@app.post("/scrape", tags=["Scraping"])
async def scrape_urls(request: UrlScrapeRequest):
    """Scrape content from specific URLs"""
    try:
        if len(request.urls) > 20:
            raise HTTPException(
                status_code=400,
                detail="Maximum 20 URLs allowed per request"
            )
        
        result = await news_api.scrape_urls(request.urls)
        return result
    except Exception as e:
        logger.error(f"Error scraping URLs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Database endpoints
@app.get("/sessions/{province}/latest", tags=["Database"])
async def get_latest_session(province: str):
    """Get the latest news session for a province"""
    try:
        if not supabase.is_available():
            raise HTTPException(
                status_code=503,
                detail="Database not available"
            )
        
        session = await supabase.get_latest_session(province)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"No sessions found for {province}"
            )
        
        return session
    except Exception as e:
        logger.error(f"Error getting latest session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}/articles", tags=["Database"])
async def get_session_articles(
    session_id: str,
    include_processed: bool = Query(False, description="Include processed content")
):
    """Get all articles for a specific session"""
    try:
        if not supabase.is_available():
            raise HTTPException(
                status_code=503,
                detail="Database not available"
            )
        
        articles = await supabase.get_session_articles(session_id, include_processed)
        return {
            "session_id": session_id,
            "articles": articles,
            "total": len(articles)
        }
    except Exception as e:
        logger.error(f"Error getting session articles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for full news pipeline
async def full_pipeline_task(province: str, host_types: List[str], limit: int):
    """Background task to run full news pipeline"""
    try:
        logger.info(f"Starting full pipeline for {province}")
        
        # 1. Fetch news
        news_result = await news_api.get_news(province, limit, scrape=True)
        if news_result.get("status") != "success":
            logger.error(f"Failed to fetch news for {province}")
            return
        
        # 2. Save to database
        session_id = None
        if supabase.is_available():
            session_id = await supabase.create_news_session(province, news_result.get("metadata", {}))
            if session_id:
                await supabase.save_articles(session_id, news_result["results"])
        
        # 3. Process with each host type
        for host_type in host_types:
            try:
                processed_result = await news_api.process_news(
                    news_result["results"], 
                    host_type, 
                    province
                )
                logger.info(f"Processed {len(processed_result.get('articles', []))} articles with {host_type}")
            except Exception as e:
                logger.error(f"Error processing with {host_type}: {str(e)}")
        
        logger.info(f"Completed full pipeline for {province}")
        
    except Exception as e:
        logger.error(f"Error in full pipeline for {province}: {str(e)}")

@app.post("/pipeline/{province}", tags=["Pipeline"])
async def run_full_pipeline(
    province: str,
    background_tasks: BackgroundTasks,
    host_types: List[str] = Query(["anchor", "friend", "newsreel"], description="Host personalities to process"),
    limit: int = Query(10, ge=1, le=20, description="Number of articles to process")
):
    """Run the full news processing pipeline for a province"""
    try:
        # Validate host types
        valid_hosts = ["anchor", "friend", "newsreel"]
        invalid_hosts = [h for h in host_types if h not in valid_hosts]
        if invalid_hosts:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid host types: {invalid_hosts}. Valid types: {valid_hosts}"
            )
        
        # Add background task
        background_tasks.add_task(full_pipeline_task, province, host_types, limit)
        
        return {
            "status": "started",
            "province": province,
            "host_types": host_types,
            "limit": limit,
            "message": "Pipeline started in background. Check logs for progress."
        }
    except Exception as e:
        logger.error(f"Error starting pipeline: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)