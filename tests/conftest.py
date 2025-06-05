"""
Pytest configuration and shared fixtures for TKR News Gatherer tests
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any
import tempfile
import os

import factory
from factory import Faker
from freezegun import freeze_time
import responses

from src.utils.config import Config
from src.utils.logger import get_logger
from src.utils.anthropic_client import AnthropicClient
from src.utils.supabase_client import SupabaseClient
from src.utils.security import SecurityConfig, AuthenticationHandler
from src.news.google_news_client import GoogleNewsClient
from src.news.article_scraper import ArticleScraper
from src.news.news_processor import NewsProcessor
from src.api import NewsGatherAPI

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_config():
    """Test configuration with safe defaults"""
    with patch.dict(os.environ, {
        'ANTHROPIC_API_KEY': 'test-anthropic-key',
        'ANTHROPIC_MODEL': 'claude-3-haiku-20240307',
        'JWT_SECRET_KEY': 'test-jwt-secret-key-32-characters',
        'API_KEYS': 'test-key-1,test-key-2,test-key-3',
        'SUPABASE_URL': 'https://test-project.supabase.co',
        'SUPABASE_ANON_KEY': 'test-supabase-key',
        'LOG_LEVEL': 'ERROR',  # Reduce noise in tests
        'DEBUG': 'true',
        'RATE_LIMIT_PER_MINUTE': '1000',  # High limit for tests
    }):
        yield Config()

@pytest.fixture
def security_config(test_config):
    """Security configuration for testing"""
    return SecurityConfig(test_config)

# ============================================================================
# Data Factories
# ============================================================================

class ArticleFactory(factory.Factory):
    """Factory for creating test articles"""
    class Meta:
        model = dict
    
    article_id = factory.Sequence(lambda n: f"article-{n}")
    wtkr_id = factory.Sequence(lambda n: f"wtkr-{n:08d}")
    title = Faker('sentence', nb_words=6)
    link = Faker('url')
    original_link = Faker('url')
    source_name = Faker('company')
    pub_date = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    summary = Faker('paragraph', nb_sentences=3)
    language = 'en'
    country = 'ca'
    content = Faker('text', max_nb_chars=2000)

class GoogleNewsResponseFactory(factory.Factory):
    """Factory for Google News API responses"""
    class Meta:
        model = dict
    
    entries = factory.LazyFunction(
        lambda: [ArticleFactory() for _ in range(5)]
    )

class ProcessedArticleFactory(factory.Factory):
    """Factory for processed articles"""
    class Meta:
        model = dict
    
    title = Faker('sentence', nb_words=6)
    url = Faker('url')
    source = Faker('company')
    content = Faker('text', max_nb_chars=1000)
    wtkr_id = factory.Sequence(lambda n: f"wtkr-{n:08d}")
    original_content = Faker('text', max_nb_chars=500)

# ============================================================================
# Mock Data Fixtures
# ============================================================================

@pytest.fixture
def mock_article():
    """Single mock article"""
    return ArticleFactory()

@pytest.fixture
def mock_articles():
    """List of mock articles"""
    return ArticleFactory.build_batch(5)

@pytest.fixture
def mock_google_news_response():
    """Mock Google News API response"""
    return GoogleNewsResponseFactory()

@pytest.fixture
def mock_processed_articles():
    """Mock processed articles"""
    return ProcessedArticleFactory.build_batch(3)

@pytest.fixture
def mock_provinces_data():
    """Mock provinces data"""
    return [
        {
            "name": "Ontario",
            "abbr": "ON",
            "cities": ["Toronto", "Ottawa", "Hamilton"],
            "regions": ["Greater Toronto Area", "Eastern Ontario"],
            "search_terms": ["Ontario news", "Toronto news", "Ottawa news"]
        },
        {
            "name": "Quebec",
            "abbr": "QC", 
            "cities": ["Montreal", "Quebec City", "Laval"],
            "regions": ["Greater Montreal", "Quebec City Region"],
            "search_terms": ["Quebec news", "Montreal news", "Quebec City news"]
        }
    ]

# ============================================================================
# HTTP Mocking Fixtures
# ============================================================================

@pytest.fixture
def responses_mock():
    """HTTP responses mock"""
    with responses.RequestsMock() as rsps:
        yield rsps

@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response"""
    return "This is a processed news article in the anchor style. The news discusses important developments in the region, providing clear and authoritative information for listeners."

@pytest.fixture
def mock_scraped_content():
    """Mock scraped article content"""
    return {
        'url': 'https://example.com/article',
        'domain': 'example.com',
        'title': 'Test News Article',
        'content': 'This is the full content of a test news article with detailed information about current events.',
        'summary': 'Brief summary of the test article.',
        'scraped_at': datetime.now(timezone.utc).isoformat()
    }

# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def mock_supabase_client(test_config):
    """Mock Supabase client"""
    client = Mock(spec=SupabaseClient)
    client.is_available.return_value = True
    client.create_news_session = AsyncMock(return_value="test-session-id")
    client.save_articles = AsyncMock(return_value=True)
    client.get_latest_session = AsyncMock(return_value={
        "id": "test-session-id",
        "province": "ontario",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "article_count": 5
    })
    client.get_session_articles = AsyncMock(return_value=[])
    client.get_provinces_with_data = AsyncMock(return_value=[])
    return client

# ============================================================================
# Service Fixtures
# ============================================================================

@pytest.fixture
def mock_google_news_client():
    """Mock Google News client"""
    client = Mock(spec=GoogleNewsClient)
    client.get_news_by_province.return_value = ArticleFactory.build_batch(3)
    client.generate_wtkr_id.side_effect = lambda x: f"wtkr-{hash(str(x)) % 100000000:08d}"
    return client

@pytest.fixture
def mock_article_scraper():
    """Mock article scraper"""
    scraper = Mock(spec=ArticleScraper)
    scraper.scrape_article = AsyncMock(return_value={
        'url': 'https://example.com/article',
        'title': 'Test Article',
        'content': 'Article content',
        'summary': 'Article summary',
        'scraped_at': datetime.now(timezone.utc).isoformat()
    })
    scraper.scrape_multiple = AsyncMock(return_value=[
        {
            'url': 'https://example.com/article1',
            'title': 'Article 1',
            'content': 'Content 1',
            'summary': 'Summary 1',
            'scraped_at': datetime.now(timezone.utc).isoformat()
        }
    ])
    
    # Context manager support
    scraper.__aenter__ = AsyncMock(return_value=scraper)
    scraper.__aexit__ = AsyncMock(return_value=None)
    
    return scraper

@pytest.fixture
def mock_anthropic_client(mock_anthropic_response):
    """Mock Anthropic client"""
    client = Mock(spec=AnthropicClient)
    client.generate_completion = AsyncMock(return_value=mock_anthropic_response)
    return client

@pytest.fixture
def mock_news_processor(mock_anthropic_client):
    """Mock news processor"""
    processor = Mock(spec=NewsProcessor)
    processor.process_articles = AsyncMock(return_value=ProcessedArticleFactory.build_batch(3))
    return processor

@pytest.fixture
def mock_news_api(mock_google_news_client, mock_supabase_client, mock_news_processor):
    """Mock NewsGatherAPI with all dependencies"""
    api = Mock(spec=NewsGatherAPI)
    api.config = Mock()
    api.news_client = mock_google_news_client
    api.supabase = mock_supabase_client
    api.processor = mock_news_processor
    
    # Mock API methods
    api.get_news = AsyncMock(return_value={
        "status": "success",
        "totalResults": 3,
        "results": ArticleFactory.build_batch(3),
        "metadata": {
            "province": "ontario",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "limit": 10,
            "scraped": True
        }
    })
    
    api.process_news = AsyncMock(return_value={
        "status": "success",
        "host_type": "anchor",
        "articles": ProcessedArticleFactory.build_batch(3),
        "processed_at": datetime.now(timezone.utc).isoformat()
    })
    
    api.scrape_urls = AsyncMock(return_value={
        "status": "success",
        "results": [mock_scraped_content()],
        "scraped_at": datetime.now(timezone.utc).isoformat()
    })
    
    api.get_provinces = Mock(return_value={
        "provinces": [
            {"name": "Ontario", "abbr": "ON"},
            {"name": "Quebec", "abbr": "QC"}
        ]
    })
    
    return api

# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def auth_handler(security_config):
    """Authentication handler for testing"""
    return AuthenticationHandler(security_config)

@pytest.fixture
def valid_jwt_token(auth_handler):
    """Valid JWT token for testing"""
    return auth_handler.create_access_token(
        data={"sub": "testuser", "scopes": ["read", "write", "admin"]}
    )

@pytest.fixture
def valid_api_key():
    """Valid API key for testing"""
    return "test-key-1"

@pytest.fixture
def auth_headers(valid_jwt_token):
    """Authentication headers for API requests"""
    return {"Authorization": f"Bearer {valid_jwt_token}"}

@pytest.fixture
def api_key_headers(valid_api_key):
    """API key headers for requests"""
    return {"X-API-Key": valid_api_key}

# ============================================================================
# Time and State Fixtures
# ============================================================================

@pytest.fixture
def frozen_time():
    """Freeze time for consistent testing"""
    with freeze_time("2024-01-15 12:00:00") as frozen_time:
        yield frozen_time

@pytest.fixture
def temp_directory():
    """Temporary directory for file-based tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

# ============================================================================
# Error Simulation Fixtures
# ============================================================================

@pytest.fixture
def network_error():
    """Simulate network errors"""
    import aiohttp
    return aiohttp.ClientError("Network connection failed")

@pytest.fixture
def timeout_error():
    """Simulate timeout errors"""
    import asyncio
    return asyncio.TimeoutError("Operation timed out")

@pytest.fixture
def anthropic_error():
    """Simulate Anthropic API errors"""
    from anthropic import APIError
    return APIError("API request failed")

# ============================================================================
# Performance Testing Fixtures
# ============================================================================

@pytest.fixture
def performance_config():
    """Configuration for performance tests"""
    return {
        'max_response_time': 2.0,  # seconds
        'max_memory_usage': 100,   # MB
        'concurrent_requests': 10,
        'test_duration': 30,       # seconds
    }

# ============================================================================
# Test Utilities
# ============================================================================

class TestHelpers:
    """Helper utilities for tests"""
    
    @staticmethod
    def assert_article_structure(article: Dict[str, Any]):
        """Assert that an article has the expected structure"""
        required_fields = ['title', 'link', 'source_name', 'wtkr_id']
        for field in required_fields:
            assert field in article, f"Missing required field: {field}"
        
        assert isinstance(article['title'], str)
        assert isinstance(article['link'], str)
        assert article['title'].strip() != ""
        assert article['link'].startswith('http')
    
    @staticmethod
    def assert_api_response_structure(response: Dict[str, Any]):
        """Assert that an API response has the expected structure"""
        assert 'status' in response
        assert response['status'] in ['success', 'error']
        
        if response['status'] == 'success':
            assert 'results' in response or 'articles' in response
        else:
            assert 'error' in response

@pytest.fixture
def test_helpers():
    """Test helper utilities"""
    return TestHelpers()

# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow (may be skipped)"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file paths"""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        
        # Mark slow tests
        if hasattr(item, 'keywords'):
            if any(keyword in item.keywords for keyword in ['slow', 'performance', 'benchmark']):
                item.add_marker(pytest.mark.slow)