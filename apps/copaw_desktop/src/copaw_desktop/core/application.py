"""Application orchestrator for CoPaw Desktop.

This module provides the central coordination for all components,
managing the complete pipeline from audio to UI to TTS.
"""
from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Optional

from copaw_desktop.core.audio import AudioRecorder
from copaw_desktop.core.asr import ASRClient, ASRError
from copaw_desktop.core.tts import TTSClient, TTSError
from copaw_desktop.core.network import WebSocketClient, ConnectionState
from copaw_desktop.core.database import SessionDB

logger = logging.getLogger(__name__)


class AppState(Enum):
    """Application state machine states."""
    
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"


class Application:
    """Central orchestrator for CoPaw Desktop application.
    
    Manages the complete pipeline:
    Audio -> ASR -> WebSocket -> UI -> TTS
    
    State transitions:
    IDLE -> LISTENING (user starts speaking)
    LISTENING -> PROCESSING (speech detected, waiting for response)
    PROCESSING -> SPEAKING (response received, TTS playing)
    SPEAKING -> IDLE (TTS finished)
    
    Example:
        app = Application(
            asr_client=asr_client,
            tts_client=tts_client,
            ws_client=ws_client,
            session_db=session_db,
        )
        app.on_message_ready = lambda msg: chat_panel.add_message("user", msg)
        app.on_response_ready = lambda msg: chat_panel.add_message("assistant", msg)
        app.start()
    """
    
    def __init__(
        self,
        asr_client: ASRClient,
        tts_client: TTSClient,
        ws_client: WebSocketClient,
        session_db: SessionDB,
    ) -> None:
        """Initialize Application orchestrator.
        
        Args:
            asr_client: ASR client for speech recognition.
            tts_client: TTS client for text-to-speech.
            ws_client: WebSocket client for server communication.
            session_db: Session database for storage.
        """
        self.asr_client = asr_client
        self.tts_client = tts_client
        self.ws_client = ws_client
        self.session_db = session_db
        
        # State
        self.state = AppState.IDLE
        self.current_session_id: Optional[str] = None
        
        # Callbacks (to be set by UI)
        self.on_message_ready: Optional[callable] = None
        self.on_response_ready: Optional[callable] = None
        self.on_state_changed: Optional[callable] = None
        self.on_error: Optional[callable] = None
        
        # Components
        self.audio_recorder: Optional[AudioRecorder] = None
        
        logger.info("Application orchestrator initialized")
    
    def start(self) -> None:
        """Start the application."""
        # Create current session if needed
        if not self.current_session_id:
            self.current_session_id = self.session_db.create_session(
                title=f"Session {self._get_timestamp()}"
            )
            logger.info(f"Created session: {self.current_session_id}")
        
        # Initialize audio recorder
        self.audio_recorder = AudioRecorder(
            on_speech_detected=self._on_speech_detected,
            silence_duration=1.5,
        )
        
        # Set up WebSocket callbacks
        self.ws_client.on_message = self._on_ws_message
        self.ws_client.on_state_change = self._on_ws_state_change
        self.ws_client.on_error = self._on_ws_error
        
        # Start components
        self.audio_recorder.start()
        
        self._set_state(AppState.IDLE)
        logger.info("Application started")
    
    def stop(self) -> None:
        """Stop the application."""
        if self.audio_recorder:
            self.audio_recorder.stop()
        
        self._set_state(AppState.IDLE)
        logger.info("Application stopped")
    
    def _on_speech_detected(self, audio_data: bytes) -> None:
        """Handle speech segment from audio recorder.
        
        Args:
            audio_data: Speech audio bytes.
        """
        if self.state == AppState.SPEAKING:
            # Ignore speech while TTS is playing (echo cancellation)
            return
        
        self._set_state(AppState.PROCESSING)
        
        # Transcribe audio
        asyncio.create_task(self._transcribe_and_send(audio_data))
    
    async def _transcribe_and_send(self, audio_data: bytes) -> None:
        """Transcribe audio and send to server.
        
        Args:
            audio_data: Audio bytes to transcribe.
        """
        try:
            # Transcribe
            text = await self.asr_client.transcribe(audio_data)
            
            if not text or not text.strip():
                logger.warning("Empty transcription, skipping")
                self._set_state(AppState.IDLE)
                return
            
            logger.info(f"Transcribed: {text[:50]}...")
            
            # Notify UI
            if self.on_message_ready:
                self.on_message_ready(text)
            
            # Save to database
            if self.current_session_id:
                self.session_db.add_message(
                    self.current_session_id,
                    role="user",
                    content=text,
                )
            
            # Send to server via WebSocket
            await self.ws_client.send({
                "type": "text",
                "content": text,
                "session_id": self.current_session_id,
            })
            
        except ASRError as e:
            logger.error(f"ASR error: {e}")
            self._handle_error(f"Speech recognition failed: {e}")
            self._set_state(AppState.IDLE)
        
        except Exception as e:
            logger.exception(f"Unexpected error in transcription: {e}")
            self._handle_error(f"Unexpected error: {e}")
            self._set_state(AppState.IDLE)
    
    def _on_ws_message(self, message: dict) -> None:
        """Handle message from WebSocket server.
        
        Args:
            message: Message dictionary.
        """
        msg_type = message.get("type", "text")
        
        if msg_type == "text":
            content = message.get("content", "")
            self._handle_text_response(content)
        
        elif msg_type == "text_start":
            # Start of streaming response
            self._streaming_text = ""
            self._set_state(AppState.PROCESSING)
        
        elif msg_type == "text_delta":
            # Delta update for streaming
            delta = message.get("delta", "")
            self._streaming_text += delta
            
            if self.on_response_ready:
                # For streaming, call with delta flag
                self.on_response_ready(delta, is_delta=True)
        
        elif msg_type == "text_end":
            # End of streaming response
            self._handle_text_response(self._streaming_text)
    
    def _handle_text_response(self, text: str) -> None:
        """Handle text response from server.
        
        Args:
            text: Response text.
        """
        if not text or not text.strip():
            logger.warning("Empty response, skipping TTS")
            self._set_state(AppState.IDLE)
            return
        
        logger.info(f"Response: {text[:50]}...")
        
        # Notify UI
        if self.on_response_ready:
            self.on_response_ready(text)
        
        # Save to database
        if self.current_session_id:
            self.session_db.add_message(
                self.current_session_id,
                role="assistant",
                content=text,
            )
        
        # Synthesize and play TTS
        asyncio.create_task(self._synthesize_and_play(text))
    
    async def _synthesize_and_play(self, text: str) -> None:
        """Synthesize TTS and play audio.
        
        Args:
            text: Text to synthesize.
        """
        self._set_state(AppState.SPEAKING)
        
        # Mute audio recorder during TTS playback (echo cancellation)
        if self.audio_recorder:
            # Note: AudioRecorder should have a mute/unmute mechanism
            # For now, we check state in _on_speech_detected
            pass
        
        try:
            # Synthesize
            audio_bytes = await self.tts_client.synthesize(text)
            
            logger.debug(f"TTS synthesized: {len(audio_bytes)} bytes")
            
            # Play audio (this would typically use pygame or pydub)
            # For now, just log
            logger.info("TTS playback would happen here")
            
            # TODO: Implement actual audio playback
            # For example:
            # import pygame
            # pygame.mixer.init()
            # sound = pygame.mixer.Sound(buffer=audio_bytes)
            # sound.play()
            # while pygame.mixer.get_busy():
            #     await asyncio.sleep(0.1)
            
        except TTSError as e:
            logger.error(f"TTS error: {e}")
            self._handle_error(f"Text-to-speech failed: {e}")
        
        except Exception as e:
            logger.exception(f"Unexpected error in TTS: {e}")
            self._handle_error(f"Unexpected error: {e}")
        
        finally:
            self._set_state(AppState.IDLE)
    
    def _on_ws_state_change(self, state: ConnectionState) -> None:
        """Handle WebSocket state change.
        
        Args:
            state: New connection state.
        """
        logger.info(f"WebSocket state: {state}")
        
        if state == ConnectionState.DISCONNECTED:
            self._handle_error("Disconnected from server")
    
    def _on_ws_error(self, error: Exception) -> None:
        """Handle WebSocket error.
        
        Args:
            error: Error exception.
        """
        logger.error(f"WebSocket error: {error}")
        self._handle_error(f"Connection error: {error}")
    
    def _set_state(self, new_state: AppState) -> None:
        """Set application state.
        
        Args:
            new_state: New state.
        """
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            
            logger.info(f"State changed: {old_state.value} -> {new_state.value}")
            
            if self.on_state_changed:
                self.on_state_changed(new_state)
    
    def _handle_error(self, error_message: str) -> None:
        """Handle application error.
        
        Args:
            error_message: Error message.
        """
        logger.error(f"Application error: {error_message}")
        
        if self.on_error:
            self.on_error(error_message)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string.
        
        Returns:
            Timestamp string.
        """
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def create_new_session(self, title: Optional[str] = None) -> str:
        """Create a new chat session.
        
        Args:
            title: Optional session title.
        
        Returns:
            New session ID.
        """
        self.current_session_id = self.session_db.create_session(
            title=title or f"Session {self._get_timestamp()}"
        )
        
        logger.info(f"Created new session: {self.current_session_id}")
        
        return self.current_session_id
    
    def get_current_state(self) -> AppState:
        """Get current application state.
        
        Returns:
            Current state.
        """
        return self.state
    
    def is_idle(self) -> bool:
        """Check if application is idle.
        
        Returns:
            True if idle.
        """
        return self.state == AppState.IDLE
    
    def is_listening(self) -> bool:
        """Check if application is listening.
        
        Returns:
            True if listening.
        """
        return self.state == AppState.LISTENING
    
    def is_processing(self) -> bool:
        """Check if application is processing.
        
        Returns:
            True if processing.
        """
        return self.state == AppState.PROCESSING
    
    def is_speaking(self) -> bool:
        """Check if application is speaking (TTS playing).
        
        Returns:
            True if speaking.
        """
        return self.state == AppState.SPEAKING
