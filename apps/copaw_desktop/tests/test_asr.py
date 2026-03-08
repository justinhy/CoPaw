"""Unit tests for ASR client implementations."""

import os
import tempfile
import wave
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from copaw_desktop.core.asr import (
    ASRAuthenticationError,
    ASRClient,
    ASRConnectionError,
    ASRError,
    ASRQuotaExceededError,
    AlibabaCloudASRClient,
    OpenAIASRClient,
)


class TestASRClientBase:
    """Tests for ASRClient base class methods."""
    
    def test_convert_to_wav(self):
        """Test PCM to WAV conversion."""
        # Generate simple PCM audio data (1 second of silence)
        sample_rate = 16000
        channels = 1
        sample_width = 2
        duration_seconds = 1
        
        num_samples = sample_rate * duration_seconds
        pcm_data = b'\x00\x00' * num_samples  # 16-bit silence
        
        wav_data = ASRClient.convert_to_wav(
            pcm_data,
            sample_rate=sample_rate,
            channels=channels,
            sample_width=sample_width,
        )
        
        # Verify WAV format
        assert wav_data[:4] == b'RIFF'
        assert wav_data[8:12] == b'WAVE'
        
        # Verify we can read it back
        import io
        with wave.open(io.BytesIO(wav_data), 'rb') as wav_file:
            assert wav_file.getnchannels() == channels
            assert wav_file.getsampwidth() == sample_width
            assert wav_file.getframerate() == sample_rate
    
    def test_extract_pcm_from_wav(self):
        """Test PCM extraction from WAV."""
        # Create a WAV file in memory
        import io
        
        sample_rate = 16000
        pcm_data = b'\x01\x02\x03\x04' * 100
        
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)
        
        wav_buffer.seek(0)
        wav_data = wav_buffer.read()
        
        # Extract PCM
        extracted_pcm = ASRClient.extract_pcm_from_wav(wav_data)
        
        assert extracted_pcm == pcm_data


class TestAlibabaCloudASRClient:
    """Tests for Alibaba Cloud ASR client."""
    
    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        client = AlibabaCloudASRClient(api_key="test-api-key")
        
        assert client.api_key == "test-api-key"
        assert client.model == "paraformer-realtime-v2"
        assert client.retry_attempts == 3
    
    def test_init_without_api_key(self):
        """Test initialization without API key raises error."""
        # Clear environment variable
        old_value = os.environ.pop("DASHSCOPE_API_KEY", None)
        
        try:
            with pytest.raises(ValueError, match="API key is required"):
                AlibabaCloudASRClient()
        finally:
            if old_value:
                os.environ["DASHSCOPE_API_KEY"] = old_value
    
    def test_init_with_env_var(self):
        """Test initialization from environment variable."""
        os.environ["DASHSCOPE_API_KEY"] = "env-api-key"
        
        try:
            client = AlibabaCloudASRClient()
            assert client.api_key == "env-api-key"
        finally:
            os.environ.pop("DASHSCOPE_API_KEY", None)
    
    @pytest.mark.asyncio
    async def test_transcribe_success(self):
        """Test successful transcription."""
        client = AlibabaCloudASRClient(api_key="test-key")
        
        # Generate test PCM audio
        pcm_data = b'\x00\x00' * 16000  # 1 second of silence
        
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "results": [
                    {"transcription_text": "你好世界"}
                ]
            }
        }
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await client.transcribe(pcm_data, language="zh")
            
            assert result == "你好世界"
            assert mock_post.called
    
    @pytest.mark.asyncio
    async def test_transcribe_authentication_error(self):
        """Test authentication error handling."""
        client = AlibabaCloudASRClient(api_key="invalid-key")
        
        pcm_data = b'\x00\x00' * 16000
        
        mock_response = MagicMock()
        mock_response.status_code = 401
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(ASRAuthenticationError, match="Invalid API key"):
                await client.transcribe(pcm_data)
    
    @pytest.mark.asyncio
    async def test_transcribe_quota_exceeded(self):
        """Test quota exceeded error handling."""
        client = AlibabaCloudASRClient(api_key="test-key", retry_attempts=1)
        
        pcm_data = b'\x00\x00' * 16000
        
        mock_response = MagicMock()
        mock_response.status_code = 429
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            with pytest.raises(ASRQuotaExceededError, match="API quota exceeded"):
                await client.transcribe(pcm_data)
    
    @pytest.mark.asyncio
    async def test_transcribe_connection_error(self):
        """Test connection error handling."""
        client = AlibabaCloudASRClient(api_key="test-key", retry_attempts=1)
        
        pcm_data = b'\x00\x00' * 16000
        
        import httpx
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(ASRConnectionError, match="Cannot connect"):
                await client.transcribe(pcm_data)
    
    @pytest.mark.asyncio
    async def test_transcribe_retry_on_failure(self):
        """Test retry logic on transient failures."""
        client = AlibabaCloudASRClient(
            api_key="test-key",
            retry_attempts=3,
            retry_delay=0.1,
        )
        
        pcm_data = b'\x00\x00' * 16000
        
        import httpx
        
        # Mock to fail twice then succeed
        call_count = [0]
        
        async def mock_post(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                raise httpx.ConnectError("Connection failed")
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "output": {
                    "results": [
                        {"transcription_text": "success"}
                    ]
                }
            }
            return mock_response
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post_method:
            mock_post_method.side_effect = mock_post
            
            result = await client.transcribe(pcm_data)
            
            assert result == "success"
            assert call_count[0] == 3  # Failed twice, succeeded on third
    
    def test_is_wav_format(self):
        """Test WAV format detection."""
        # WAV format starts with RIFF
        wav_data = b'RIFF....WAVE'
        assert AlibabaCloudASRClient._is_wav_format(wav_data) is True
        
        # PCM format doesn't start with RIFF
        pcm_data = b'\x00\x01\x02\x03'
        assert AlibabaCloudASRClient._is_wav_format(pcm_data) is False


class TestOpenAIASRClient:
    """Tests for OpenAI ASR client."""
    
    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        client = OpenAIASRClient(api_key="test-api-key")
        
        assert client.api_key == "test-api-key"
        assert client.model == "whisper-1"
        assert client.base_url == "https://api.openai.com/v1"
    
    def test_init_with_custom_base_url(self):
        """Test initialization with custom base URL."""
        client = OpenAIASRClient(
            api_key="test-key",
            base_url="https://custom.openai.com/v1",
        )
        
        assert client.base_url == "https://custom.openai.com/v1"
    
    @pytest.mark.asyncio
    async def test_transcribe_success(self):
        """Test successful transcription."""
        client = OpenAIASRClient(api_key="test-key")
        
        pcm_data = b'\x00\x00' * 16000
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "text": "Hello world"
        }
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            result = await client.transcribe(pcm_data, language="en")
            
            assert result == "Hello world"
            assert mock_post.called
    
    @pytest.mark.asyncio
    async def test_transcribe_with_prompt(self):
        """Test transcription with prompt parameter."""
        client = OpenAIASRClient(api_key="test-key")
        
        pcm_data = b'\x00\x00' * 16000
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "result"}
        
        with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            await client.transcribe(pcm_data, prompt="Technical discussion about AI")
            
            # Verify prompt was included in form data
            call_args = mock_post.call_args
            assert "data" in call_args.kwargs
            assert "prompt" in call_args.kwargs["data"]


class TestASRErrors:
    """Tests for ASR error types."""
    
    def test_asr_error_hierarchy(self):
        """Test ASR error exception hierarchy."""
        assert issubclass(ASRConnectionError, ASRError)
        assert issubclass(ASRAuthenticationError, ASRError)
        assert issubclass(ASRQuotaExceededError, ASRError)
        assert issubclass(ASRError, Exception)
    
    def test_asr_error_message(self):
        """Test ASR error messages."""
        error = ASRError("Test error")
        assert str(error) == "Test error"
        
        auth_error = ASRAuthenticationError("Invalid key")
        assert str(auth_error) == "Invalid key"
