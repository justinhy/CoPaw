"""Unit tests for TTS client implementations."""

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from copaw_desktop.core.tts import (
    TTSAuthenticationError,
    TTSClient,
    TTSConnectionError,
    TTSError,
    TTSQuotaExceededError,
    EdgeTTSClient,
    OpenAITTSClient,
)


class TestTTSClientBase:
    """Tests for TTSClient base class methods."""
    
    @pytest.mark.asyncio
    async def test_save_audio(self):
        """Test audio file saving."""
        audio_data = b'\xff\xfb\x90\x44' * 1000  # Fake MP3 data
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_audio.mp3")
            
            await TTSClient.save_audio(audio_data, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'rb') as f:
                saved_data = f.read()
            
            assert saved_data == audio_data
    
    @pytest.mark.asyncio
    async def test_save_audio_creates_directories(self):
        """Test that save_audio creates parent directories."""
        audio_data = b'test audio'
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir", "nested", "audio.mp3")
            
            await TTSClient.save_audio(audio_data, output_path)
            
            assert os.path.exists(output_path)


class TestEdgeTTSClient:
    """Tests for Edge TTS client."""
    
    def test_init_with_defaults(self):
        """Test initialization with default values."""
        client = EdgeTTSClient()
        
        assert client.default_voice == "zh-CN-XiaoxiaoNeural"
        assert client.default_speed == 1.0
    
    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        client = EdgeTTSClient(
            default_voice="en-US-JennyNeural",
            default_speed=1.5,
        )
        
        assert client.default_voice == "en-US-JennyNeural"
        assert client.default_speed == 1.5
    
    @pytest.mark.asyncio
    async def test_synthesize_success(self):
        """Test successful synthesis."""
        client = EdgeTTSClient()
        
        # Mock edge_tts.Communicate
        mock_communicate = MagicMock()
        mock_communicate.save = AsyncMock()
        
        # Create fake audio file
        fake_audio = b'fake mp3 audio data'
        
        with patch('edge_tts.Communicate', return_value=mock_communicate):
            # Mock file operations
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = fake_audio
                
                result = await client.synthesize("你好世界", voice="zh-CN-XiaoxiaoNeural")
                
                assert result == fake_audio
                assert mock_communicate.save.called
    
    @pytest.mark.asyncio
    async def test_synthesize_without_edge_tts_library(self):
        """Test error when edge-tts is not installed."""
        client = EdgeTTSClient()
        
        with patch.dict('sys.modules', {'edge_tts': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module")):
                with pytest.raises(TTSError, match="edge-tts library is not installed"):
                    await client.synthesize("test")
    
    @pytest.mark.asyncio
    async def test_synthesize_speed_clamping(self):
        """Test that speed is clamped to valid range."""
        client = EdgeTTSClient()
        
        mock_communicate = MagicMock()
        mock_communicate.save = AsyncMock()
        
        fake_audio = b'fake audio'
        
        with patch('edge_tts.Communicate', return_value=mock_communicate):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = fake_audio
                
                # Test speed too low
                await client.synthesize("test", speed=0.1)
                
                # Test speed too high
                await client.synthesize("test", speed=5.0)
    
    def test_list_voices_chinese(self):
        """Test listing Chinese voices."""
        voices = EdgeTTSClient.list_voices(language="zh")
        
        assert "xiaoxiao" in voices
        assert voices["xiaoxiao"] == "zh-CN-XiaoxiaoNeural"
    
    def test_list_voices_english(self):
        """Test listing English voices."""
        voices = EdgeTTSClient.list_voices(language="en")
        
        assert "jenny" in voices
        assert voices["jenny"] == "en-US-JennyNeural"
    
    def test_list_voices_all(self):
        """Test listing all voices."""
        voices = EdgeTTSClient.list_voices()
        
        # Should include both Chinese and English
        assert "xiaoxiao" in voices
        assert "jenny" in voices


class TestOpenAITTSClient:
    """Tests for OpenAI TTS client."""
    
    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        client = OpenAITTSClient(api_key="test-api-key")
        
        assert client.api_key == "test-api-key"
        assert client.default_voice == "alloy"
        assert client.model == "tts-1"
    
    def test_init_without_api_key(self):
        """Test initialization without API key raises error."""
        old_value = os.environ.pop("OPENAI_API_KEY", None)
        
        try:
            with pytest.raises(ValueError, match="API key is required"):
                OpenAITTSClient()
        finally:
            if old_value:
                os.environ["OPENAI_API_KEY"] = old_value
    
    def test_init_with_env_var(self):
        """Test initialization from environment variable."""
        os.environ["OPENAI_API_KEY"] = "env-api-key"
        
        try:
            client = OpenAITTSClient()
            assert client.api_key == "env-api-key"
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
    
    def test_init_with_custom_base_url(self):
        """Test initialization with custom base URL."""
        client = OpenAITTSClient(
            api_key="test-key",
            base_url="https://custom.openai.com/v1",
        )
        
        assert client.base_url == "https://custom.openai.com/v1"
    
    @pytest.mark.asyncio
    async def test_synthesize_success(self):
        """Test successful synthesis."""
        client = OpenAITTSClient(api_key="test-key")
        
        fake_audio = b'fake mp3 audio data'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fake_audio
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await client.synthesize("Hello world", voice="alloy")
            
            assert result == fake_audio
            assert mock_post.called
    
    @pytest.mark.asyncio
    async def test_synthesize_authentication_error(self):
        """Test authentication error handling."""
        client = OpenAITTSClient(api_key="invalid-key")
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(TTSAuthenticationError, match="Invalid API key"):
                await client.synthesize("test")
    
    @pytest.mark.asyncio
    async def test_synthesize_quota_exceeded(self):
        """Test quota exceeded error handling."""
        client = OpenAITTSClient(api_key="test-key")
        
        mock_response = MagicMock()
        mock_response.status_code = 429
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(TTSQuotaExceededError, match="API quota exceeded"):
                await client.synthesize("test")
    
    @pytest.mark.asyncio
    async def test_synthesize_connection_error(self):
        """Test connection error handling."""
        client = OpenAITTSClient(api_key="test-key")
        
        import httpx
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(TTSConnectionError, match="Cannot connect to OpenAI"):
                await client.synthesize("test")
    
    @pytest.mark.asyncio
    async def test_synthesize_voice_validation(self):
        """Test voice validation."""
        client = OpenAITTSClient(api_key="test-key")
        
        fake_audio = b'audio'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fake_audio
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            # Test with invalid voice (should use default "alloy")
            await client.synthesize("test", voice="invalid_voice")
            
            # Verify request was made with valid voice
            call_args = mock_post.call_args
            assert "json" in call_args.kwargs
            assert call_args.kwargs["json"]["voice"] == "alloy"
    
    @pytest.mark.asyncio
    async def test_synthesize_text_truncation(self):
        """Test text length truncation."""
        client = OpenAITTSClient(api_key="test-key")
        
        fake_audio = b'audio'
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fake_audio
        
        # Create text longer than 4096 characters
        long_text = "a" * 5000
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            await client.synthesize(long_text)
            
            # Verify text was truncated
            call_args = mock_post.call_args
            assert len(call_args.kwargs["json"]["input"]) == 4096
    
    def test_list_voices(self):
        """Test listing available voices."""
        voices = OpenAITTSClient.list_voices()
        
        assert isinstance(voices, list)
        assert "alloy" in voices
        assert "echo" in voices
        assert len(voices) == 6


class TestTTSErrors:
    """Tests for TTS error types."""
    
    def test_tts_error_hierarchy(self):
        """Test TTS error exception hierarchy."""
        assert issubclass(TTSConnectionError, TTSError)
        assert issubclass(TTSAuthenticationError, TTSError)
        assert issubclass(TTSQuotaExceededError, TTSError)
        assert issubclass(TTSError, Exception)
    
    def test_tts_error_message(self):
        """Test TTS error messages."""
        error = TTSError("Test error")
        assert str(error) == "Test error"
        
        auth_error = TTSAuthenticationError("Invalid key")
        assert str(auth_error) == "Invalid key"
