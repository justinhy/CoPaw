"""Audio playback module for TTS output.

This module provides audio playback functionality for TTS synthesized
audio, using pygame for cross-platform support.
"""
from __future__ import annotations

import logging
from typing import Optional

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False

logger = logging.getLogger(__name__)


class AudioPlayer:
    """Audio player for TTS synthesized audio.
    
    Provides:
    - MP3/WAV playback using pygame.mixer
    - Volume control and mute functionality
    - Async playback support
    - Error handling for unsupported formats
    """
    
    def __init__(self) -> None:
        """Initialize audio player."""
        self._is_initialized = False
        self._current_sound: Optional[pygame.mixer.Sound] = None
        self._is_playing = False
        self._volume = 1.0  # Volume range: 0.0 to 1.0
        self._is_muted = False
        
        logger.debug("AudioPlayer initialized (pygame available: %s)", PYGAME_AVAILABLE)
    
    def initialize(self) -> bool:
        """Initialize pygame mixer.
        
        Returns:
            True if initialization successful.
        """
        if not PYGAME_AVAILABLE:
            logger.error("Pygame not available for audio playback")
            return False
        
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2)
            self._is_initialized = True
            
            logger.info("AudioPlayer initialized with pygame.mixer")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize pygame.mixer: {e}")
            return False
    
    def play_audio(self, audio_data: bytes) -> bool:
        """Play audio from bytes.
        
        Args:
            audio_data: Audio bytes (MP3/WAV format).
        
        Returns:
            True if playback started successfully.
        """
        if not self._is_initialized:
            if not self.initialize():
                return False
        
        try:
            # Stop current playback
            self.stop()
            
            # Create sound object from bytes
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_file_path = tmp_file.name
            
            self._current_sound = pygame.mixer.Sound(tmp_file_path)
            
            # Play the sound
            self._current_sound.play()
            self._is_playing = True
            
            logger.debug(f"Playing audio: {len(audio_data)} bytes")
            return True
        
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            return False
    
    def stop(self) -> None:
        """Stop current playback."""
        if not self._is_playing:
            return
        
        try:
            if self._current_sound:
                self._current_sound.stop()
                self._current_sound = None
            
            self._is_playing = False
            logger.debug("Audio playback stopped")
        
        except Exception as e:
            logger.error(f"Failed to stop audio: {e}")
    
    def set_volume(self, volume: float) -> bool:
        """Set playback volume (0.0 to 1.0).
        
        Args:
            volume: Volume level (0.0 = mute, 1.0 = max).
        
        Returns:
            True if volume set successfully.
        """
        if not self._is_initialized:
            return False
        
        try:
            # Clamp volume to valid range
            volume = max(0.0, min(1.0, volume))
            self._volume = volume
            
            # Set pygame mixer volume
            pygame.mixer.music.set_volume(volume if not self._is_muted else 0.0)
            
            logger.debug(f"Volume set to: {volume}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False
    
    def mute(self) -> None:
        """Mute audio playback."""
        self._is_muted = True
        
        if self._is_initialized:
            pygame.mixer.music.set_volume(0.0)
            logger.debug("Audio muted")
    
    def unmute(self) -> None:
        """Unmute audio playback."""
        self._is_muted = False
        
        if self._is_initialized:
            pygame.mixer.music.set_volume(self._volume)
            logger.debug(f"Audio unmuted (volume: {self._volume})")
    
    def toggle_mute(self) -> None:
        """Toggle mute state."""
        if self._is_muted:
            self.unmute()
        else:
            self.mute()
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        if not PYGAME_AVAILABLE:
            return False
        
        if self._is_initialized and self._current_sound:
            return pygame.mixer.Channel(self._current_sound.get_num_channels()).get_busy()
        
        return self._is_playing
    
    def get_volume(self) -> float:
        """Get current volume."""
        return self._volume
    
    def is_muted(self) -> bool:
        """Check if audio is muted."""
        return self._is_muted
    
    def cleanup(self) -> None:
        """Cleanup audio player resources."""
        if self._is_initialized:
            try:
                self.stop()
                pygame.mixer.quit()
                self._is_initialized = False
                logger.debug("AudioPlayer cleaned up")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
    
    @staticmethod
    def is_available() -> bool:
        """Check if pygame is available for audio playback.
        
        Returns:
            True if pygame is available.
        """
        return PYGAME_AVAILABLE


class AsyncAudioPlayer:
    """Async audio player wrapper for TTS.
    
    Provides async methods for better integration
    with the asyncio event loop.
    """
    
    def __init__(self, loop=None) -> None:
        """Initialize async audio player.
        
        Args:
            loop: Optional asyncio event loop.
        """
        self.player = AudioPlayer()
        self._loop = loop or asyncio.get_event_loop()
    
    async def play_async(self, audio_data: bytes) -> bool:
        """Play audio asynchronously.
        
        Args:
            audio_data: Audio bytes to play.
        
        Returns:
            True if playback started successfully.
        """
        def play_task():
            return self.player.play_audio(audio_data)
        
        # Run in executor to avoid blocking
        try:
            loop = self._loop
            await loop.run_in_executor(None, play_task)
            return True
        except Exception as e:
            logger.error(f"Async playback failed: {e}")
            return False
    
    async def stop_async(self) -> None:
        """Stop audio asynchronously."""
        def stop_task():
            self.player.stop()
        
        try:
            loop = self._loop
            await loop.run_in_executor(None, stop_task)
        except Exception as e:
            logger.error(f"Async stop failed: {e}")
    
    def get_player(self) -> AudioPlayer:
        """Get the underlying AudioPlayer instance."""
        return self.player