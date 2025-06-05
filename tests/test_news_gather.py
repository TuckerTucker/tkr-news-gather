import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.api import NewsGatherAPI
from src.news import GoogleNewsClient, NewsProcessor, get_all_provinces
from src.utils import Config

class TestNewsGatherAPI:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.api = NewsGatherAPI()
    
    def test_get_provinces(self):
        """Test getting list of provinces"""
        result = self.api.get_provinces()
        
        assert "provinces" in result
        assert len(result["provinces"]) == 13  # 13 Canadian provinces/territories
        
        # Check that Alberta is in the list
        province_names = [p["name"] for p in result["provinces"]]
        assert "Alberta" in province_names
        assert "Ontario" in province_names
        assert "Quebec" in province_names

class TestGoogleNewsClient:
    
    def setup_method(self):
        """Setup test fixtures"""
        self.client = GoogleNewsClient()
    
    def test_generate_wtkr_id(self):
        """Test WTKR ID generation"""
        article = {
            "link": "https://example.com/article",
            "title": "Test Article"
        }
        
        wtkr_id = self.client.generate_wtkr_id(article)
        
        assert wtkr_id.startswith("wtkr-")
        assert len(wtkr_id) == 13  # "wtkr-" + 8 character hash
    
    def test_generate_wtkr_id_consistency(self):
        """Test that same article generates same ID"""
        article = {
            "link": "https://example.com/article",
            "title": "Test Article"
        }
        
        id1 = self.client.generate_wtkr_id(article)
        id2 = self.client.generate_wtkr_id(article)
        
        assert id1 == id2

class TestNewsProcessor:
    
    def setup_method(self):
        """Setup test fixtures"""
        mock_anthropic = Mock()
        self.processor = NewsProcessor(mock_anthropic)
    
    def test_host_personalities(self):
        """Test that all expected host personalities are available"""
        expected_hosts = ["anchor", "friend", "newsreel"]
        
        for host in expected_hosts:
            assert host in self.processor.host_personalities
            personality = self.processor.host_personalities[host]
            
            # Check required fields
            assert "name" in personality
            assert "style" in personality
            assert "tone" in personality
            assert "instructions" in personality
    
    @pytest.mark.asyncio
    async def test_process_articles_invalid_host(self):
        """Test processing with invalid host type"""
        articles = [{"title": "Test", "content": "Test content"}]
        
        with pytest.raises(ValueError, match="Unknown host type"):
            await self.processor.process_articles(articles, "invalid_host", "Alberta")

class TestProvinces:
    
    def test_get_all_provinces(self):
        """Test getting all provinces"""
        provinces = get_all_provinces()
        
        assert len(provinces) == 13
        
        # Check that each province has required fields
        for province in provinces:
            assert "name" in province
            assert "abbr" in province
            assert "cities" in province
            assert "regions" in province
            assert "search_terms" in province
    
    def test_province_search_terms(self):
        """Test that provinces have proper search terms"""
        provinces = get_all_provinces()
        
        for province in provinces:
            search_terms = province["search_terms"]
            assert len(search_terms) > 0
            
            # Each search term should contain the province name or abbreviation
            province_name = province["name"].lower()
            province_abbr = province["abbr"].lower()
            
            # At least one search term should contain province identifier
            has_province_ref = any(
                province_name.split()[0] in term.lower() or 
                province_abbr in term.lower()
                for term in search_terms
            )
            assert has_province_ref, f"No search terms reference {province['name']}"

class TestConfig:
    
    def test_config_defaults(self):
        """Test configuration defaults"""
        config = Config()
        
        # Test default values
        assert config.LLM_TEMP == 0.7
        assert config.LLM_MAX_TOKENS == 2000
        assert config.DEFAULT_NEWS_LIMIT == 10
        assert config.SCRAPE_TIMEOUT == 30
        assert config.API_HOST == "0.0.0.0"
        assert config.API_PORT == 8000

@pytest.mark.asyncio
class TestIntegration:
    """Integration tests that don't require external APIs"""
    
    async def test_api_initialization(self):
        """Test that API can be initialized"""
        api = NewsGatherAPI()
        
        assert api.config is not None
        assert api.news_client is not None
        assert api.processor is not None
    
    def test_provinces_data_integrity(self):
        """Test provinces data integrity"""
        provinces = get_all_provinces()
        
        # Test unique abbreviations
        abbrs = [p["abbr"] for p in provinces]
        assert len(abbrs) == len(set(abbrs)), "Province abbreviations must be unique"
        
        # Test unique names
        names = [p["name"] for p in provinces]
        assert len(names) == len(set(names)), "Province names must be unique"
        
        # Test that all have cities
        for province in provinces:
            assert len(province["cities"]) > 0, f"{province['name']} must have cities"

# Mock test data
MOCK_GOOGLE_NEWS_RESPONSE = {
    "entries": [
        {
            "id": "test-article-1",
            "title": "Test News Article",
            "link": "https://example.com/article1",
            "source": {"title": "Test Source"},
            "published": "2024-01-01T12:00:00Z",
            "summary": "This is a test article summary"
        }
    ]
}

MOCK_SCRAPED_CONTENT = {
    "url": "https://example.com/article1",
    "title": "Test News Article",
    "content": "This is the full article content from scraping",
    "summary": "This is a test article summary",
    "scraped_at": "2024-01-01T12:00:00Z"
}

@pytest.mark.asyncio
class TestMockedAPI:
    """Tests using mocked external services"""
    
    @patch('src.news.google_news_client.GoogleNews')
    async def test_get_news_mocked(self, mock_google_news):
        """Test get_news with mocked Google News"""
        # Setup mock
        mock_instance = mock_google_news.return_value
        mock_instance.search.return_value = MOCK_GOOGLE_NEWS_RESPONSE
        
        # Test
        api = NewsGatherAPI()
        result = await api.get_news("Alberta", limit=1, scrape=False)
        
        assert result["status"] == "success"
        assert result["totalResults"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["title"] == "Test News Article"
    
    @patch('src.utils.anthropic_client.Anthropic')
    async def test_process_news_mocked(self, mock_anthropic):
        """Test process_news with mocked Anthropic API"""
        # Setup mock
        mock_instance = mock_anthropic.return_value
        mock_response = Mock()
        mock_response.content = [Mock(text="Processed news content with anchor personality")]
        mock_instance.messages.create.return_value = mock_response
        
        # Test data
        articles = [{
            "title": "Test Article",
            "content": "Test content",
            "source_name": "Test Source",
            "link": "https://example.com",
            "wtkr_id": "wtkr-test123"
        }]
        
        # Test
        api = NewsGatherAPI()
        result = await api.process_news(articles, "anchor", "Alberta")
        
        assert result["status"] == "success"
        assert result["host_type"] == "anchor"
        assert len(result["articles"]) == 1
        assert "processed" in result["processed_at"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])