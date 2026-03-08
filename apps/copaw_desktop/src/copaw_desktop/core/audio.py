"""Audio recording and processing module.

This module provides audio recording with Voice Activity Detection (VAD)
for capturing user speech in the CoPaw Desktop application.
"""
from __future__ import annotations

import logging
import queue
import threading
from collections import deque
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Audio recorder with Voice Activity Detection (VAD).
    
    Records audio from microphone and detects speech segments using VAD.
    Automatically splits audio on silence for processing.
    
    Example:
        recorder = AudioRecorder(on_speech_detected=my_handler)
        recorder.start()
        # ... recording happens in background thread ...
        recorder.stop()
    """
    
    def __init__(
        self,
        on_speech_detected: Optional[Callable[[bytes], None]] = None,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1024,
        silence_duration: float = 1.5,
        vad_mode: int = 3,
    ) -> None:
        """Initialize AudioRecorder.
        
        Args:
            on_speech_detected: Callback for speech segments.
            sample_rate: Audio sample rate in Hz (default: 16000).
            channels: Number of audio channels (default: 1 for mono).
            chunk_size: Audio chunk size in frames (default: 1024).
            silence_duration: Silence duration in seconds to trigger split (default: 1.5).
            vad_mode: VAD aggressiveness mode 0-3 (default: 3 = most aggressive).
        """
        self.on_speech_detected = on_speech_detected
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.silence_duration = silence_duration
        self.vad_mode = vad_mode
        
        # State
        self._is_recording = False
        self._recording_thread: Optional[threading.Thread] = None
        self._audio_buffer: deque[bytes] = deque()
        self._speech_buffer: list[bytes] = []
        self._in_speech = False
        self._silence_frames = 0
        
        # Calculate silence threshold in frames
        self._silence_threshold = int(
            silence_duration * sample_rate / chunk_size
        )
        
        # PyAudio instance (initialized on start)
        self._pyaudio = None
        self._stream = None
        
        # VAD instance (initialized on start)
        self._vad = None
        
        logger.info(
            f"AudioRecorder initialized: "
            f"sample_rate={sample_rate}, "
            f"silence_duration={silence_duration}s"
        )
    
    def start(self) -> None:
        """Start recording audio."""
        if self._is_recording:
            logger.warning("AudioRecorder already recording")
            return
        
        try:
            import pyaudio
        except ImportError:
            logger.error("PyAudio not installed. Install with: pip install pyaudio")
            return
        
        try:
            import webrtcvad
            self._vad = webrtcvad.Vad(self.vad_mode)
        except ImportError:
            logger.warning(
                "webrtcvad not installed. Install with: pip install webrtcvad. "
                "Speech detection will be disabled."
            )
            self._vad = None
        
        # Initialize PyAudio
        self._pyaudio = pyaudio.PyAudio()
        
        try:
            # Open audio stream
            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )
        except Exception as e:
            logger.error(f"Failed to open audio stream: {e}")
            self._pyaudio.terminate()
            return
        
        # Start recording thread
        self._is_recording = True
        self._recording_thread = threading.Thread(
            target=self._recording_loop,
            daemon=True,
        )
        self._recording_thread.start()
        
        logger.info("AudioRecorder started")
    
    def stop(self) -> None:
        """Stop recording audio."""
        if not self._is_recording:
            return
        
        self._is_recording = False
        
        # Wait for recording thread to finish
        if self._recording_thread and self._recording_thread.is_alive():
            self._recording_thread.join(timeout=2.0)
        
        # Close stream
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        
        # Terminate PyAudio
        if self._pyaudio:
            self._pyaudio.terminate()
            self._pyaudio = None
        
        # Process any remaining speech
        if self._speech_buffer:
            self._emit_speech()
        
        logger.info("AudioRecorder stopped")
    
    def _recording_loop(self) -> None:
        """Main recording loop (runs in background thread)."""
        logger.debug("Recording loop started")
        
        while self._is_recording:
            try:
                # Read audio chunk
                audio_data = self._stream.read(
                    self.chunk_size,
                    exception_on_overflow=False,
                )
                
                # Add to buffer
                self._audio_buffer.append(audio_data)
                
                # Detect speech
                is_speech = self._detect_speech(audio_data)
                
                if is_speech:
                    self._handle_speech(audio_data)
                else:
                    self._handle_silence(audio_data)
            
            except Exception as e:
                logger.error(f"Error in recording loop: {e}")
                break
        
        logger.debug("Recording loop ended")
    
    def _detect_speech(self, audio_data: bytes) -> bool:
        """Detect if audio chunk contains speech.
        
        Args:
            audio_data: Audio chunk bytes.
        
        Returns:
            True if speech detected.
        """
        if not self._vad:
            # No VAD, treat all audio as speech
            return True
        
        try:
            # WebRTC VAD requires specific frame sizes
            # 16000 Hz * 10/20/30 ms = 160/320/480 samples
            # For 16-bit audio: 320/640/960 bytes
            frame_duration_ms = 30  # 30ms frames
            frame_size = int(
                self.sample_rate * frame_duration_ms / 1000 * 2
            )
            
            # Check if audio_data is the right size
            if len(audio_data) >= frame_size:
                return self._vad.is_speech(
                    audio_data[:frame_size],
                    self.sample_rate,
                )
        except Exception as e:
            logger.debug(f"VAD error: {e}")
        
        return False
    
    def _handle_speech(self, audio_data: bytes) -> None:
        """Handle speech audio chunk.
        
        Args:
            audio_data: Speech audio chunk.
        """
        self._speech_buffer.append(audio_data)
        self._in_speech = True
        self._silence_frames = 0
    
    def _handle_silence(self, audio_data: bytes) -> None:
        """Handle silence audio chunk.
        
        Args:
            audio_data: Silence audio chunk.
        """
        if self._in_speech:
            # Still in speech, add to buffer
            self._speech_buffer.append(audio_data)
            self._silence_frames += 1
            
            # Check if silence duration exceeded
            if self._silence_frames >= self._silence_threshold:
                # Emit speech segment
                self._emit_speech()
                self._in_speech = False
    
    def _emit_speech(self) -> None:
        """Emit collected speech segment."""
        if not self._speech_buffer:
            return
        
        # Combine all chunks
        speech_data = b''.join(self._speech_buffer)
        
        # Clear buffer
        self._speech_buffer.clear()
        
        # Emit via callback
        if self.on_speech_detected:
            try:
                self.on_speech_detected(speech_data)
                logger.debug(
                    f"Emitted speech segment: {len(speech_data)} bytes"
                )
            except Exception as e:
                logger.error(f"Error in speech callback: {e}")
    
    def get_buffer_size(self) -> int:
        """Get current audio buffer size.
        
        Returns:
            Number of buffered chunks.
        """
        return len(self._audio_buffer)
    
    def clear_buffer(self) -> None:
        """Clear audio buffer."""
        self._audio_buffer.clear()
        self._speech_buffer.clear()
        self._in_speech = False
        self._silence_frames = 0
