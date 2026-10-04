import pytest
from unittest.mock import patch, MagicMock
from backend.llm.router import get_llm


class TestLLMRouter:
    @patch('backend.llm.router.settings')
    def test_get_llm_ollama_primary(self, mock_settings):
        """Test Ollama as primary provider"""
        mock_settings.PRIMARY_LLM_PROVIDER = "ollama"
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_settings.OLLAMA_MODEL = "llama3.1:8b"
        
        llm = get_llm()
        assert llm is not None
    
    @patch('backend.llm.router.settings')
    @patch('backend.llm.router.ChatAnthropic')
    def test_get_llm_anthropic_success(self, mock_anthropic, mock_settings):
        """Test Anthropic as primary provider"""
        mock_settings.PRIMARY_LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.LLM_MAX_TOKENS = 4096
        
        mock_instance = MagicMock()
        mock_anthropic.return_value = mock_instance
        
        llm = get_llm()
        assert llm == mock_instance
        mock_anthropic.assert_called_once()
    
    @patch('backend.llm.router.settings')
    @patch('backend.llm.router.ChatAnthropic')
    @patch('backend.llm.router.ChatOpenAI')
    def test_get_llm_fallback_to_openai(self, mock_openai, mock_anthropic, mock_settings):
        """Test fallback from Anthropic to OpenAI"""
        mock_settings.PRIMARY_LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.FALLBACK_LLM_PROVIDER = "openai"
        mock_settings.OPENAI_API_KEY = "test-key"
        mock_settings.LLM_MAX_TOKENS = 4096
        
        # Anthropic fails
        mock_anthropic.side_effect = Exception("API Error")
        
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance
        
        llm = get_llm()
        assert llm == mock_openai_instance
        mock_openai.assert_called_once()
    
    @patch('backend.llm.router.settings')
    @patch('backend.llm.router.ChatAnthropic')
    @patch('backend.llm.router.ChatOpenAI')
    @patch('backend.llm.router.Ollama')
    def test_get_llm_fallback_to_ollama(self, mock_ollama, mock_openai, mock_anthropic, mock_settings):
        """Test fallback to Ollama when both Anthropic and OpenAI fail"""
        mock_settings.PRIMARY_LLM_PROVIDER = "anthropic"
        mock_settings.FALLBACK_LLM_PROVIDER = "openai"
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_settings.OLLAMA_MODEL = "llama3.1:8b"
        
        mock_anthropic.side_effect = Exception("API Error")
        mock_openai.side_effect = Exception("API Error")
        
        mock_ollama_instance = MagicMock()
        mock_ollama.return_value = mock_ollama_instance
        
        llm = get_llm()
        assert llm == mock_ollama_instance