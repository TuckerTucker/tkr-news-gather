"""
Unit tests for utility modules
Tests configuration, logging, security, and client utilities
"""

import pytest
import os
import logging
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import secrets

import jwt
from anthropic import APIError

from src.utils.config import Config
from src.utils.logger import get_logger
from src.utils.anthropic_client import AnthropicClient
from src.utils.security import (
    SecurityConfig, AuthenticationHandler, SecureUrlValidator,
    InputValidator, SecureNewsRequest, SecureUrlScrapeRequest,
    SecureProcessRequest
)


class TestConfig:
    """Test configuration management"""

    def test_default_values(self):
        """Test that config loads with default values"""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            
            assert config.ANTHROPIC_MODEL == "claude-3-haiku-20240307"
            assert config.LLM_TEMP == 0.7
            assert config.LLM_MAX_TOKENS == 2000
            assert config.LOG_LEVEL == "INFO"
            assert config.DEFAULT_NEWS_LIMIT == 10
            assert config.SCRAPE_TIMEOUT == 30
            assert config.API_HOST == "0.0.0.0"
            assert config.API_PORT == 8000

    def test_environment_override(self):
        """Test that environment variables override defaults"""
        test_env = {
            'ANTHROPIC_MODEL': 'test-model',
            'LLM_TEMP': '0.5',
            'LLM_MAX_TOKENS': '1000',
            'DEFAULT_NEWS_LIMIT': '20',
            'API_PORT': '9000',
            'DEBUG': 'true',
            'RATE_LIMIT_PER_MINUTE': '200'
        }
        
        with patch.dict(os.environ, test_env):
            config = Config()
            
            assert config.ANTHROPIC_MODEL == "test-model"
            assert config.LLM_TEMP == 0.5
            assert config.LLM_MAX_TOKENS == 1000
            assert config.DEFAULT_NEWS_LIMIT == 20
            assert config.API_PORT == 9000
            assert config.DEBUG is True
            assert config.RATE_LIMIT_PER_MINUTE == 200

    def test_type_conversion(self):
        """Test that string environment variables are properly converted"""
        test_env = {
            'LLM_TEMP': 'invalid',
            'API_PORT': 'not_a_number'
        }
        
        with patch.dict(os.environ, test_env):
            with pytest.raises(ValueError):
                Config()


class TestLogger:
    """Test logging utilities"""

    def test_get_logger_creates_logger(self):
        """Test that get_logger creates a logger with correct name"""
        logger = get_logger("test_logger")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_get_logger_default_level(self):
        """Test that logger uses INFO level by default"""
        logger = get_logger("test_logger")
        
        assert logger.level == logging.INFO

    def test_get_logger_custom_level(self):
        """Test that logger respects custom level"""
        logger = get_logger("test_logger", "DEBUG")
        
        assert logger.level == "DEBUG"

    def test_logger_has_formatter(self):
        """Test that logger has proper formatter"""
        logger = get_logger("test_logger")
        
        assert len(logger.handlers) > 0
        handler = logger.handlers[0]
        assert handler.formatter is not None

    def test_logger_singleton_behavior(self):
        """Test that multiple calls return same logger instance"""
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        
        assert logger1 is logger2


class TestAnthropicClient:
    """Test Anthropic client functionality"""

    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.ANTHROPIC_API_KEY = "test-key"
        config.ANTHROPIC_MODEL = "claude-3-haiku-20240307"
        config.LLM_TEMP = 0.7
        config.LLM_MAX_TOKENS = 2000
        return config

    @pytest.fixture
    def client(self, mock_config):
        with patch('src.utils.anthropic_client.Anthropic') as mock_anthropic:
            return AnthropicClient(mock_config)

    def test_initialization(self, mock_config):
        """Test client initialization with config"""
        with patch('src.utils.anthropic_client.Anthropic') as mock_anthropic:
            client = AnthropicClient(mock_config)
            
            mock_anthropic.assert_called_once_with(api_key="test-key")
            assert client.model == "claude-3-haiku-20240307"
            assert client.temperature == 0.7
            assert client.max_tokens == 2000

    @pytest.mark.asyncio
    async def test_generate_completion_success(self, client):
        """Test successful completion generation"""
        # Mock response
        mock_response = Mock()
        mock_response.content = [Mock(text="Generated response")]
        client.client.messages.create.return_value = mock_response
        
        result = await client.generate_completion(
            "System prompt",
            "User prompt"
        )
        
        assert result == "Generated response"
        client.client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_completion_with_custom_temperature(self, client):
        """Test completion with custom temperature"""
        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        client.client.messages.create.return_value = mock_response
        
        await client.generate_completion(
            "System", "User", temperature=0.9
        )
        
        call_args = client.client.messages.create.call_args
        assert call_args.kwargs['temperature'] == 0.9

    @pytest.mark.asyncio
    async def test_generate_completion_api_error(self, client):
        """Test handling of Anthropic API errors"""
        client.client.messages.create.side_effect = APIError("API Error")
        
        with pytest.raises(APIError):
            await client.generate_completion("System", "User")


class TestSecurityConfig:
    """Test security configuration"""

    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.JWT_SECRET_KEY = "test-secret-key"
        config.API_KEYS = "key1,key2,key3"
        return config

    def test_initialization(self, mock_config):
        """Test security config initialization"""
        sec_config = SecurityConfig(mock_config)
        
        assert sec_config.secret_key == "test-secret-key"
        assert sec_config.api_keys == ["key1", "key2", "key3"]

    def test_generate_secret_key(self):
        """Test secret key generation when not provided"""
        config = Mock()
        config.JWT_SECRET_KEY = None
        config.API_KEYS = ""
        
        sec_config = SecurityConfig(config)
        
        assert sec_config.secret_key is not None
        assert len(sec_config.secret_key) > 20  # Should be reasonably long

    def test_empty_api_keys(self):
        """Test handling of empty API keys"""
        config = Mock()
        config.JWT_SECRET_KEY = "secret"
        config.API_KEYS = ""
        
        sec_config = SecurityConfig(config)
        
        assert sec_config.api_keys == []


class TestAuthenticationHandler:
    """Test authentication handler"""

    @pytest.fixture
    def security_config(self):
        config = Mock()
        config.secret_key = "test-secret-key-32-characters-long"
        config.api_keys = ["key1", "key2", "key3"]
        return config

    @pytest.fixture
    def auth_handler(self, security_config):
        return AuthenticationHandler(security_config)

    def test_password_hashing(self, auth_handler):
        """Test password hashing and verification"""
        password = "test_password"
        
        # Hash password
        hashed = auth_handler.get_password_hash(password)
        
        # Verify correct password
        assert auth_handler.verify_password(password, hashed)
        
        # Verify incorrect password
        assert not auth_handler.verify_password("wrong_password", hashed)

    def test_create_access_token(self, auth_handler):
        """Test JWT token creation"""
        data = {"sub": "testuser", "scopes": ["read"]}
        
        token = auth_handler.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 20

    def test_create_access_token_with_expiry(self, auth_handler):
        """Test JWT token creation with custom expiry"""
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=10)
        
        token = auth_handler.create_access_token(data, expires_delta)
        
        # Decode token to verify expiry
        decoded = jwt.decode(
            token, 
            auth_handler.config.secret_key, 
            algorithms=["HS256"]
        )
        
        assert "exp" in decoded
        assert decoded["sub"] == "testuser"

    def test_verify_token_success(self, auth_handler):
        """Test successful token verification"""
        data = {"sub": "testuser", "scopes": ["read", "write"]}
        token = auth_handler.create_access_token(data)
        
        token_data = auth_handler.verify_token(token)
        
        assert token_data.username == "testuser"
        assert token_data.scopes == ["read", "write"]

    def test_verify_token_invalid(self, auth_handler):
        """Test verification of invalid token"""
        with pytest.raises(Exception):  # Should raise HTTPException
            auth_handler.verify_token("invalid_token")

    def test_verify_api_key_success(self, auth_handler):
        """Test successful API key verification"""
        assert auth_handler.verify_api_key("key1")
        assert auth_handler.verify_api_key("key2")
        assert auth_handler.verify_api_key("key3")

    def test_verify_api_key_failure(self, auth_handler):
        """Test API key verification failure"""
        assert not auth_handler.verify_api_key("invalid_key")
        assert not auth_handler.verify_api_key("")

    def test_verify_api_key_timing_safe(self, auth_handler):
        """Test that API key verification uses constant-time comparison"""
        # This test ensures secrets.compare_digest is used
        with patch('src.utils.security.secrets.compare_digest') as mock_compare:
            mock_compare.return_value = True
            
            auth_handler.verify_api_key("test_key")
            
            assert mock_compare.called


class TestSecureUrlValidator:
    """Test URL validation for SSRF protection"""

    def test_valid_urls(self):
        """Test that valid URLs are accepted"""
        valid_urls = [
            "https://example.com/article",
            "http://news.site.com/story",
            "https://subdomain.example.org/page"
        ]
        
        for url in valid_urls:
            assert SecureUrlValidator.validate_url(url)

    def test_blocked_schemes(self):
        """Test that dangerous schemes are blocked"""
        blocked_urls = [
            "file:///etc/passwd",
            "ftp://example.com/file",
            "gopher://example.com",
            "data:text/plain,hello"
        ]
        
        for url in blocked_urls:
            assert not SecureUrlValidator.validate_url(url)

    def test_blocked_hosts(self):
        """Test that dangerous hosts are blocked"""
        blocked_urls = [
            "http://localhost/test",
            "https://127.0.0.1/api",
            "http://0.0.0.0/endpoint",
            "https://169.254.169.254/metadata",
            "http://metadata.google.internal/compute"
        ]
        
        for url in blocked_urls:
            assert not SecureUrlValidator.validate_url(url)

    def test_private_networks(self):
        """Test that private network IPs are blocked"""
        private_urls = [
            "http://10.0.0.1/test",
            "https://172.16.0.1/api",
            "http://192.168.1.1/admin"
        ]
        
        for url in private_urls:
            assert not SecureUrlValidator.validate_url(url)

    def test_localhost_variants(self):
        """Test that localhost variants are blocked"""
        localhost_urls = [
            "http://localhost.local/test",
            "https://internal.company.com/api",
            "http://intranet.site.com/admin"
        ]
        
        for url in localhost_urls:
            assert not SecureUrlValidator.validate_url(url)

    def test_malformed_urls(self):
        """Test handling of malformed URLs"""
        malformed_urls = [
            "not-a-url",
            "://missing-scheme",
            "http://",
            ""
        ]
        
        for url in malformed_urls:
            assert not SecureUrlValidator.validate_url(url)


class TestInputValidator:
    """Test input validation"""

    def test_valid_provinces(self):
        """Test validation of valid province names"""
        valid_provinces = [
            "ontario", "Ontario", "ONTARIO",
            "quebec", "Quebec", "QUEBEC",
            "british columbia", "British Columbia"
        ]
        
        for province in valid_provinces:
            result = InputValidator.validate_province(province)
            assert isinstance(result, str)
            assert result.lower() == province.lower().strip()

    def test_invalid_provinces(self):
        """Test rejection of invalid province names"""
        invalid_provinces = [
            "california", "texas", "invalid", "", "   "
        ]
        
        for province in invalid_provinces:
            with pytest.raises(ValueError):
                InputValidator.validate_province(province)

    def test_valid_limits(self):
        """Test validation of valid article limits"""
        valid_limits = [1, 5, 10, 25, 50]
        
        for limit in valid_limits:
            result = InputValidator.validate_limit(limit)
            assert result == limit

    def test_invalid_limits(self):
        """Test rejection of invalid limits"""
        invalid_limits = [0, -1, 51, 100, "not_a_number"]
        
        for limit in invalid_limits:
            with pytest.raises(ValueError):
                InputValidator.validate_limit(limit)

    def test_valid_host_types(self):
        """Test validation of valid host types"""
        valid_hosts = ["anchor", "friend", "newsreel"]
        
        for host_type in valid_hosts:
            result = InputValidator.validate_host_type(host_type)
            assert result == host_type

    def test_invalid_host_types(self):
        """Test rejection of invalid host types"""
        invalid_hosts = ["invalid", "broadcaster", "", "ANCHOR"]
        
        for host_type in invalid_hosts:
            with pytest.raises(ValueError):
                InputValidator.validate_host_type(host_type)


class TestSecurePydanticModels:
    """Test secure Pydantic validation models"""

    def test_secure_news_request_valid(self):
        """Test valid news request validation"""
        valid_data = {
            "province": "ontario",
            "limit": 10,
            "scrape": True
        }
        
        request = SecureNewsRequest(**valid_data)
        
        assert request.province == "ontario"
        assert request.limit == 10
        assert request.scrape is True

    def test_secure_news_request_invalid_province(self):
        """Test news request with invalid province"""
        invalid_data = {
            "province": "invalid_province",
            "limit": 10
        }
        
        with pytest.raises(ValueError):
            SecureNewsRequest(**invalid_data)

    def test_secure_news_request_invalid_limit(self):
        """Test news request with invalid limit"""
        invalid_data = {
            "province": "ontario",
            "limit": 100  # Too high
        }
        
        with pytest.raises(ValueError):
            SecureNewsRequest(**invalid_data)

    def test_secure_url_scrape_request_valid(self):
        """Test valid URL scrape request"""
        valid_data = {
            "urls": [
                "https://example.com/article1",
                "https://example.com/article2"
            ]
        }
        
        request = SecureUrlScrapeRequest(**valid_data)
        
        assert len(request.urls) == 2

    def test_secure_url_scrape_request_too_many_urls(self):
        """Test URL scrape request with too many URLs"""
        invalid_data = {
            "urls": [f"https://example.com/article{i}" for i in range(25)]
        }
        
        with pytest.raises(ValueError, match="Maximum 20 URLs"):
            SecureUrlScrapeRequest(**invalid_data)

    def test_secure_url_scrape_request_blocked_url(self):
        """Test URL scrape request with blocked URL"""
        invalid_data = {
            "urls": ["http://localhost/dangerous"]
        }
        
        with pytest.raises(ValueError, match="not allowed"):
            SecureUrlScrapeRequest(**invalid_data)

    def test_secure_process_request_valid(self):
        """Test valid process request"""
        valid_data = {
            "articles": [{"title": "Test", "content": "Content"}],
            "host_type": "anchor",
            "province": "ontario"
        }
        
        request = SecureProcessRequest(**valid_data)
        
        assert request.host_type == "anchor"
        assert request.province == "ontario"

    def test_secure_process_request_too_many_articles(self):
        """Test process request with too many articles"""
        invalid_data = {
            "articles": [{"title": f"Article {i}"} for i in range(60)],
            "host_type": "anchor",
            "province": "ontario"
        }
        
        with pytest.raises(ValueError, match="Maximum 50 articles"):
            SecureProcessRequest(**invalid_data)