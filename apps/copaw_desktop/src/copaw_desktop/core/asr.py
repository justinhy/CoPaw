"""Automatic Speech Recognition (ASR) client implementations.

This module provides ASR clients for converting audio to text
using cloud services like Alibaba Cloud, OpenAI, etc.
"""
from __future__ import annotations

import asyncio
import io
import logging
import os
import wave
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ASRError(Exception):
    """Base exception for ASR-related errors."""
    pass


class ASRConnectionError(ASRError):
    """Network connection error during ASR."""
    pass


class ASRAuthenticationError(ASRError):
    """Authentication failed (invalid API key)."""
    pass


class ASRQuotaExceededError(ASRError):
    """API quota exceeded."""
    pass


class ASRClient(ABC):
    """Abstract base class for ASR clients.
    
    All ASR implementations (Alibaba Cloud, OpenAI, Google) should inherit
    from this class and implement the transcribe method.
    """
    
    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Transcribe audio bytes to text.
        
        Args:
            audio_bytes: Raw audio data (typically PCM or WAV format).
            language: Optional language code (e.g., "zh", "en").
            **kwargs: Additional provider-specific parameters.
        
        Returns:
            Transcribed text string.
        
        Raises:
            ASRConnectionError: Network connection failed.
            ASRAuthenticationError: Invalid API key.
            ASRQuotaExceededError: API quota exceeded.
            ASRError: Other ASR-related errors.
        """
        pass
    
    @staticmethod
    def convert_to_wav(
        audio_bytes: bytes,
        sample_rate: int = 16000,
        channels: int = 1,
        sample_width: int = 2,
    ) -> bytes:
        """Convert raw PCM audio bytes to WAV format.
        
        Args:
            audio_bytes: Raw PCM audio data.
            sample_rate: Audio sample rate (default: 16000 Hz).
            channels: Number of audio channels (default: 1 for mono).
            sample_width: Sample width in bytes (default: 2 for 16-bit).
        
        Returns:
            WAV-formatted audio bytes.
        """
        # Create a WAV file in memory
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_bytes)
        
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    @staticmethod
    def extract_pcm_from_wav(wav_bytes: bytes) -> bytes:
        """Extract raw PCM data from WAV format.
        
        Args:
            wav_bytes: WAV-formatted audio bytes.
        
        Returns:
            Raw PCM audio data.
        """
        wav_buffer = io.BytesIO(wav_bytes)
        
        with wave.open(wav_buffer, 'rb') as wav_file:
            return wav_file.readframes(wav_file.getnframes())


class AlibabaCloudASRClient(ASRClient):
    """Alibaba Cloud ASR client using DashScope API.
    
    This client uses Alibaba Cloud's Paraformer model for speech recognition.
    
    Example:
        client = AlibabaCloudASRClient(api_key="sk-...")
        text = await client.transcribe(audio_bytes, language="zh")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "paraformer-realtime-v2",
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize Alibaba Cloud ASR client.
        
        Args:
            api_key: DashScope API key. If None, reads from DASHSCOPE_API_KEY env var.
            model: ASR model to use (default: paraformer-realtime-v2).
            retry_attempts: Number of retry attempts on failure.
            retry_delay: Delay in seconds between retries.
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set DASHSCOPE_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.model = model
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
    
    async def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Transcribe audio using Alibaba Cloud DashScope ASR.
        
        Args:
            audio_bytes: Audio data (WAV or PCM format).
            language: Language code (e.g., "zh", "en"). Defaults to auto-detect.
            **kwargs: Additional parameters (format, sample_rate, etc.).
        
        Returns:
            Transcribed text.
        
        Raises:
            ASRConnectionError: Network connection failed.
            ASRAuthenticationError: Invalid API key.
            ASRQuotaExceededError: API quota exceeded.
            ASRError: Other ASR errors.
        """
        # Ensure audio is in WAV format
        if not self._is_wav_format(audio_bytes):
            logger.debug("Converting PCM to WAV format")
            audio_bytes = self.convert_to_wav(audio_bytes)
        
        # Prepare request
        url = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        # For file upload, we need to use multipart/form-data
        # DashScope expects audio file uploaded via form
        import aiofiles
        import tempfile
        
        # Create temporary file for upload
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_file_path = tmp_file.name
        
        try:
            # Retry logic
            last_error = None
            
            for attempt in range(self.retry_attempts):
                try:
                    result = await self._make_request(
                        url,
                        headers,
                        tmp_file_path,
                        language,
                        **kwargs
                    )
                    return result
                except (ASRConnectionError, ASRQuotaExceededError) as e:
                    last_error = e
                    if attempt < self.retry_attempts - 1:
                        logger.warning(
                            f"ASR attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {self.retry_delay}s..."
                        )
                        await asyncio.sleep(self.retry_delay)
                    continue
                except ASRAuthenticationError:
                    # Don't retry auth errors
                    raise
            
            # All retries failed
            raise last_error or ASRError("ASR transcription failed")
        
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_file_path)
            except Exception:
                pass
    
    async def _make_request(
        self,
        url: str,
        headers: Dict[str, str],
        audio_file_path: str,
        language: Optional[str],
        **kwargs: Any,
    ) -> str:
        """Make HTTP request to DashScope API.
        
        Args:
            url: API endpoint URL.
            headers: HTTP headers.
            audio_file_path: Path to audio file.
            language: Language code.
            **kwargs: Additional parameters.
        
        Returns:
            Transcribed text.
        """
        try:
            import httpx
        except ImportError:
            raise ASRError("httpx library is not installed")
        
        # Prepare multipart form data
        files = {
            "file": ("audio.wav", open(audio_file_path, "rb"), "audio/wav"),
        }
        
        # Build form data
        data = {
            "model": self.model,
        }
        
        if language:
            data["language"] = language
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if value is not None:
                data[key] = str(value)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    files=files,
                    data=data,
                )
            
            # Handle HTTP status codes
            if response.status_code == 401:
                raise ASRAuthenticationError("Invalid API key")
            elif response.status_code == 429:
                raise ASRQuotaExceededError("API quota exceeded")
            elif response.status_code >= 500:
                raise ASRConnectionError(
                    f"Server error: {response.status_code}"
                )
            elif response.status_code != 200:
                error_msg = f"ASR request failed: {response.status_code}"
                try:
                    error_data = response.json()
                    if "message" in error_data:
                        error_msg = f"{error_msg} - {error_data['message']}"
                except Exception:
                    pass
                raise ASRError(error_msg)
            
            # Parse response
            result = response.json()
            
            # DashScope response format
            if "output" in result and "results" in result["output"]:
                # Realtime ASR response format
                transcripts = []
                for item in result["output"]["results"]:
                    if "transcription_text" in item:
                        transcripts.append(item["transcription_text"])
                return " ".join(transcripts)
            elif "output" in result and "sentence" in result["output"]:
                # File transcription response format
                return result["output"]["sentence"]["text"]
            else:
                logger.warning(f"Unexpected response format: {result}")
                raise ASRError("Unexpected API response format")
        
        except httpx.ConnectError:
            raise ASRConnectionError(
                "Cannot connect to DashScope. Please check network connection."
            )
        except httpx.TimeoutException:
            raise ASRConnectionError("DashScope request timed out")
        except ASRError:
            raise
        except Exception as e:
            logger.exception("Unexpected error during ASR")
            raise ASRError(f"ASR failed: {str(e)}") from e
    
    @staticmethod
    def _is_wav_format(audio_bytes: bytes) -> bool:
        """Check if audio bytes are in WAV format.
        
        Args:
            audio_bytes: Audio data to check.
        
        Returns:
            True if WAV format, False otherwise.
        """
        # WAV files start with "RIFF" header
        return audio_bytes[:4] == b'RIFF'


class OpenAIASRClient(ASRClient):
    """OpenAI Whisper ASR client.
    
    This client uses OpenAI's Whisper model for speech recognition.
    
    Example:
        client = OpenAIASRClient(api_key="sk-...")
        text = await client.transcribe(audio_bytes, language="zh")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "whisper-1",
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize OpenAI ASR client.
        
        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
            base_url: OpenAI API base URL (for custom endpoints).
            model: Whisper model to use (default: whisper-1).
            retry_attempts: Number of retry attempts on failure.
            retry_delay: Delay in seconds between retries.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        self.model = model
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
    
    async def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Transcribe audio using OpenAI Whisper.
        
        Args:
            audio_bytes: Audio data (WAV, MP3, etc.).
            language: Language code (e.g., "zh", "en").
            **kwargs: Additional parameters (prompt, temperature, etc.).
        
        Returns:
            Transcribed text.
        """
        # Ensure audio is in WAV format
        if not AlibabaCloudASRClient._is_wav_format(audio_bytes):
            logger.debug("Converting PCM to WAV format")
            audio_bytes = AlibabaCloudASRClient.convert_to_wav(audio_bytes)
        
        url = f"{self.base_url.rstrip('/')}/audio/transcriptions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        # Retry logic
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                result = await self._make_request(
                    url,
                    headers,
                    audio_bytes,
                    language,
                    **kwargs
                )
                return result
            except (ASRConnectionError, ASRQuotaExceededError) as e:
                last_error = e
                if attempt < self.retry_attempts - 1:
                    logger.warning(
                        f"ASR attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {self.retry_delay}s..."
                    )
                    await asyncio.sleep(self.retry_delay)
                continue
            except ASRAuthenticationError:
                raise
        
        raise last_error or ASRError("ASR transcription failed")
    
    async def _make_request(
        self,
        url: str,
        headers: Dict[str, str],
        audio_bytes: bytes,
        language: Optional[str],
        **kwargs: Any,
    ) -> str:
        """Make HTTP request to OpenAI API."""
        try:
            import httpx
        except ImportError:
            raise ASRError("httpx library is not installed")
        
        # Prepare multipart form data
        files = {
            "file": ("audio.wav", audio_bytes, "audio/wav"),
        }
        
        data = {
            "model": self.model,
        }
        
        if language:
            data["language"] = language
        
        # Add optional parameters
        for key in ["prompt", "temperature"]:
            if key in kwargs and kwargs[key] is not None:
                data[key] = kwargs[key]
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    files=files,
                    data=data,
                )
            
            if response.status_code == 401:
                raise ASRAuthenticationError("Invalid API key")
            elif response.status_code == 429:
                raise ASRQuotaExceededError("API quota exceeded")
            elif response.status_code >= 500:
                raise ASRConnectionError(f"Server error: {response.status_code}")
            elif response.status_code != 200:
                error_msg = f"ASR request failed: {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = f"{error_msg} - {error_data['error'].get('message', '')}"
                except Exception:
                    pass
                raise ASRError(error_msg)
            
            result = response.json()
            return result.get("text", "")
        
        except httpx.ConnectError:
            raise ASRConnectionError(
                "Cannot connect to OpenAI. Please check network connection."
            )
        except httpx.TimeoutException:
            raise ASRConnectionError("OpenAI request timed out")
        except ASRError:
            raise
        except Exception as e:
            logger.exception("Unexpected error during ASR")
            raise ASRError(f"ASR failed: {str(e)}") from e
