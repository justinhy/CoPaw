"""Text-to-Speech (TTS) client implementations.

This module provides TTS clients for converting text to audio
using cloud services like Edge TTS, OpenAI, etc.
"""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TTSError(Exception):
    """Base exception for TTS-related errors."""
    pass


class TTSConnectionError(TTSError):
    """Network connection error during TTS."""
    pass


class TTSAuthenticationError(TTSError):
    """Authentication failed (invalid API key)."""
    pass


class TTSQuotaExceededError(TTSError):
    """API quota exceeded."""
    pass


class TTSClient(ABC):
    """Abstract base class for TTS clients.
    
    All TTS implementations (Edge TTS, OpenAI, Google) should inherit
    from this class and implement the synthesize method.
    """
    
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        **kwargs: Any,
    ) -> bytes:
        """Synthesize text to audio bytes.
        
        Args:
            text: Text to convert to speech.
            voice: Optional voice identifier (e.g., "zh-CN-XiaoxiaoNeural").
            speed: Speech speed multiplier (default: 1.0).
            **kwargs: Additional provider-specific parameters.
        
        Returns:
            Audio data bytes (typically MP3 or WAV format).
        
        Raises:
            TTSConnectionError: Network connection failed.
            TTSAuthenticationError: Invalid API key.
            TTSQuotaExceededError: API quota exceeded.
            TTSError: Other TTS-related errors.
        """
        pass
    
    @staticmethod
    async def save_audio(audio_bytes: bytes, output_path: str) -> None:
        """Save audio bytes to file.
        
        Args:
            audio_bytes: Audio data to save.
            output_path: Path to save audio file.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'wb') as f:
            f.write(audio_bytes)
        
        logger.debug(f"Saved audio to {output_path}")


class EdgeTTSClient(TTSClient):
    """Edge TTS client using Microsoft Edge's free TTS service.
    
    This client uses edge-tts library which provides free access to
    Microsoft's Azure TTS voices.
    
    Example:
        client = EdgeTTSClient()
        audio = await client.synthesize("你好世界", voice="zh-CN-XiaoxiaoNeural")
    """
    
    # Common Chinese voices
    CHINESE_VOICES = {
        "xiaoxiao": "zh-CN-XiaoxiaoNeural",
        "yunxi": "zh-CN-YunxiNeural",
        "yunjian": "zh-CN-YunjianNeural",
        "xiaoyi": "zh-CN-XiaoyiNeural",
        "yunfeng": "zh-CN-YunfengNeural",
    }
    
    # Common English voices
    ENGLISH_VOICES = {
        "jenny": "en-US-JennyNeural",
        "guy": "en-US-GuyNeural",
        "aria": "en-US-AriaNeural",
        "davis": "en-US-DavisNeural",
    }
    
    def __init__(
        self,
        default_voice: str = "zh-CN-XiaoxiaoNeural",
        default_speed: float = 1.0,
    ) -> None:
        """Initialize Edge TTS client.
        
        Args:
            default_voice: Default voice to use (default: zh-CN-XiaoxiaoNeural).
            default_speed: Default speech speed (default: 1.0).
        """
        self.default_voice = default_voice
        self.default_speed = default_speed
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        **kwargs: Any,
    ) -> bytes:
        """Synthesize text using Edge TTS.
        
        Args:
            text: Text to convert to speech.
            voice: Voice identifier (e.g., "zh-CN-XiaoxiaoNeural").
            speed: Speech speed multiplier (0.5 to 2.0).
            **kwargs: Additional parameters (pitch, volume, etc.).
        
        Returns:
            MP3 audio bytes.
        
        Raises:
            TTSConnectionError: Network connection failed.
            TTSError: Other TTS errors.
        """
        try:
            import edge_tts
        except ImportError:
            raise TTSError(
                "edge-tts library is not installed. "
                "Install it with: pip install edge-tts"
            )
        
        # Use defaults if not provided
        voice = voice or self.default_voice
        speed = speed or self.default_speed
        
        # Validate speed range
        if not 0.5 <= speed <= 2.0:
            logger.warning(
                f"Speed {speed} out of range [0.5, 2.0], clamping to valid range"
            )
            speed = max(0.5, min(2.0, speed))
        
        # Convert speed multiplier to percentage string for edge-tts
        # speed=1.0 -> "+0%", speed=0.5 -> "-50%", speed=2.0 -> "+100%"
        speed_percent = int((speed - 1.0) * 100)
        speed_str = f"{'+' if speed_percent >= 0 else ''}{speed_percent}%"
        
        try:
            # Create Communicate instance
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=speed_str,
            )
            
            # Generate audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                # Stream audio to file
                await communicate.save(tmp_path)
                
                # Read audio bytes
                with open(tmp_path, 'rb') as f:
                    audio_bytes = f.read()
                
                logger.debug(
                    f"Synthesized {len(text)} chars to {len(audio_bytes)} bytes "
                    f"using voice {voice}"
                )
                
                return audio_bytes
            
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        
        except Exception as e:
            error_msg = str(e).lower()
            
            if "connection" in error_msg or "network" in error_msg:
                raise TTSConnectionError(
                    f"Cannot connect to Edge TTS service: {str(e)}"
                )
            else:
                logger.exception("Unexpected error during TTS synthesis")
                raise TTSError(f"TTS synthesis failed: {str(e)}") from e
    
    @classmethod
    def list_voices(
        cls,
        language: Optional[str] = None,
    ) -> Dict[str, str]:
        """List available voices, optionally filtered by language.
        
        Args:
            language: Language code to filter (e.g., "zh", "en").
        
        Returns:
            Dictionary mapping voice names to voice IDs.
        """
        if language and language.startswith("zh"):
            return cls.CHINESE_VOICES
        elif language and language.startswith("en"):
            return cls.ENGLISH_VOICES
        else:
            # Return all voices
            all_voices = {}
            all_voices.update(cls.CHINESE_VOICES)
            all_voices.update(cls.ENGLISH_VOICES)
            return all_voices


class OpenAITTSClient(TTSClient):
    """OpenAI TTS client using GPT-4 Audio API.
    
    This client uses OpenAI's TTS API for text-to-speech synthesis.
    
    Example:
        client = OpenAITTSClient(api_key="sk-...")
        audio = await client.synthesize("Hello world", voice="alloy")
    """
    
    AVAILABLE_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_voice: str = "alloy",
        default_speed: float = 1.0,
        model: str = "tts-1",
    ) -> None:
        """Initialize OpenAI TTS client.
        
        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
            base_url: OpenAI API base URL (for custom endpoints).
            default_voice: Default voice (default: alloy).
            default_speed: Default speech speed (default: 1.0).
            model: TTS model to use (default: tts-1).
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        self.default_voice = default_voice
        self.default_speed = default_speed
        self.model = model
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        **kwargs: Any,
    ) -> bytes:
        """Synthesize text using OpenAI TTS.
        
        Args:
            text: Text to convert to speech (max 4096 characters).
            voice: Voice identifier (alloy, echo, fable, onyx, nova, shimmer).
            speed: Speech speed multiplier (0.25 to 4.0).
            **kwargs: Additional parameters (response_format, etc.).
        
        Returns:
            MP3 audio bytes.
        """
        try:
            import httpx
        except ImportError:
            raise TTSError("httpx library is not installed")
        
        # Use defaults if not provided
        voice = voice or self.default_voice
        speed = speed or self.default_speed
        
        # Validate voice
        if voice not in self.AVAILABLE_VOICES:
            logger.warning(
                f"Unknown voice '{voice}', using default 'alloy'. "
                f"Available: {', '.join(self.AVAILABLE_VOICES)}"
            )
            voice = "alloy"
        
        # Validate speed
        if not 0.25 <= speed <= 4.0:
            logger.warning(
                f"Speed {speed} out of range [0.25, 4.0], clamping"
            )
            speed = max(0.25, min(4.0, speed))
        
            # Play audio using AudioPlayer
            from .audio_player import AsyncAudioPlayer
            
            # Create async player with current event loop
            player = AsyncAudioPlayer()
            
            # Initialize and play
            if await player.player.initialize():
                await player.play_async(audio_bytes)
                
                # Wait for playback to complete
                # In a real implementation, we'd wait for is_playing() to become False
                # For now, just log the start
                logger.info(f"Playing TTS audio: {len(audio_bytes)} bytes")
                return True
            else:
                logger.warning("Failed to initialize audio player")
                return False
            text = text[:4096]
        
        url = f"{self.base_url.rstrip('/')}/audio/speech"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "input": text,
            "voice": voice,
            "speed": speed,
        }
        
        # Add optional response format
        if "response_format" in kwargs:
            payload["response_format"] = kwargs["response_format"]
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )
            
            if response.status_code == 401:
                raise TTSAuthenticationError("Invalid API key")
            elif response.status_code == 429:
                raise TTSQuotaExceededError("API quota exceeded")
            elif response.status_code >= 500:
                raise TTSConnectionError(
                    f"Server error: {response.status_code}"
                )
            elif response.status_code != 200:
                error_msg = f"TTS request failed: {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = f"{error_msg} - {error_data['error'].get('message', '')}"
                except Exception:
                    pass
                raise TTSError(error_msg)
            
            audio_bytes = response.content
            
            logger.debug(
                f"Synthesized {len(text)} chars to {len(audio_bytes)} bytes "
                f"using voice {voice}"
            )
            
            return audio_bytes
        
        except httpx.ConnectError:
            raise TTSConnectionError(
                "Cannot connect to OpenAI. Please check network connection."
            )
        except httpx.TimeoutException:
            raise TTSConnectionError("OpenAI request timed out")
        except TTSError:
            raise
        except Exception as e:
            logger.exception("Unexpected error during TTS")
            raise TTSError(f"TTS failed: {str(e)}") from e
    
    @classmethod
    def list_voices(cls) -> List[str]:
        """List available OpenAI TTS voices.
        
        Returns:
            List of voice identifiers.
        """
        return cls.AVAILABLE_VOICES.copy()
