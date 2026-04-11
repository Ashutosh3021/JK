"""
Mic Module - PC Audio Capture with VAD for JK Robot

Purpose: Capture voice input from PC microphone, detect speech presence,
and buffer audio chunks for downstream STT processing.
"""

import sounddevice as sd
import numpy as np
import threading
import time
from typing import Optional, Callable
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioCapture:
    """Captures audio from PC microphone using sounddevice."""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        device_index: Optional[int] = None,
        channels: int = 1
    ):
        """
        Initialize audio capture.

        Args:
            sample_rate: Sample rate in Hz (default: 16000)
            chunk_size: Number of frames per chunk (default: 1024)
            device_index: Audio device index (None = default device)
            channels: Number of audio channels (default: 1 = mono)
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.device_index = device_index
        self.channels = channels

        self._stream: Optional[sd.InputStream] = None
        self._latest_chunk: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._is_recording = False

    def start(self) -> None:
        """Start continuous audio capture in background."""
        if self._is_recording:
            logger.warning("Audio capture already started")
            return

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            blocksize=self.chunk_size,
            device=self.device_index,
            callback=self._audio_callback
        )
        self._stream.start()
        self._is_recording = True
        logger.info(f"Audio capture started (sample_rate={self.sample_rate})")

    def stop(self) -> None:
        """Stop audio capture."""
        if not self._is_recording:
            return

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self._is_recording = False
        logger.info("Audio capture stopped")

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: object,
        status: object
    ) -> None:
        """Internal callback for audio data."""
        with self._lock:
            self._latest_chunk = indata.copy()

    def get_audio_chunk(self) -> Optional[bytes]:
        """
        Get latest audio chunk as bytes.

        Returns:
            Audio chunk as bytes, or None if no data available
        """
        with self._lock:
            if self._latest_chunk is None:
                return None
            return self._latest_chunk.tobytes()

    def get_audio_chunk_array(self) -> Optional[np.ndarray]:
        """Get latest audio chunk as numpy array."""
        with self._lock:
            return self._latest_chunk.copy() if self._latest_chunk is not None else None

    @property
    def is_recording(self) -> bool:
        """Return True if currently recording."""
        return self._is_recording


class VoiceActivityDetector:
    """Detects voice activity in audio chunks using energy-based VAD."""

    def __init__(
        self,
        sample_rate: int = 16000,
        mode: int = 3,
        energy_threshold: float = 0.01
    ):
        """
        Initialize VAD.

        Args:
            sample_rate: Audio sample rate in Hz
            mode: VAD aggressiveness (0-3, 3 = most aggressive)
            energy_threshold: Energy threshold for speech detection
        """
        self.sample_rate = sample_rate
        self.mode = mode
        self.energy_threshold = energy_threshold

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Check if audio chunk contains speech.

        Args:
            audio_chunk: Audio data as numpy array

        Returns:
            True if voice detected, False otherwise
        """
        if audio_chunk is None or len(audio_chunk) == 0:
            return False

        energy = np.abs(audio_chunk).mean()
        return energy > self.energy_threshold

    def is_speech_bytes(self, audio_bytes: bytes) -> bool:
        """Check if audio bytes contain speech."""
        audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
        return self.is_speech(audio_array)

    def set_mode(self, mode: int) -> None:
        """Change VAD sensitivity (0=least aggressive, 3=most)."""
        if mode < 0 or mode > 3:
            raise ValueError("Mode must be between 0 and 3")
        self.mode = mode


class AudioBuffer:
    """Stores audio chunks for later processing."""

    def __init__(
        self,
        max_size_seconds: float = 10.0,
        sample_rate: int = 16000
    ):
        """
        Initialize audio buffer.

        Args:
            max_size_seconds: Maximum buffer duration in seconds
            sample_rate: Audio sample rate
        """
        self.max_size_seconds = max_size_seconds
        self.sample_rate = sample_rate
        self.max_samples = int(max_size_seconds * sample_rate)

        self._buffer: list[np.ndarray] = []
        self._lock = threading.Lock()

    def add_chunk(self, audio_chunk: np.ndarray) -> None:
        """Add audio chunk to buffer."""
        with self._lock:
            self._buffer.append(audio_chunk.copy())

            total_samples = sum(len(chunk) for chunk in self._buffer)
            while total_samples > self.max_samples and self._buffer:
                removed = self._buffer.pop(0)
                total_samples -= len(removed)

    def get_buffer(self) -> bytes:
        """
        Get all buffered audio as bytes.

        Returns:
            Audio data as bytes
        """
        with self._lock:
            if not self._buffer:
                return b""
            return b"".join(chunk.tobytes() for chunk in self._buffer)

    def get_buffer_array(self) -> np.ndarray:
        """Get all buffered audio as numpy array."""
        with self._lock:
            if not self._buffer:
                return np.array([])
            return np.concatenate(self._buffer)

    def clear(self) -> None:
        """Clear the buffer."""
        with self._lock:
            self._buffer.clear()

    def get_duration(self) -> float:
        """Get current buffer duration in seconds."""
        with self._lock:
            total_samples = sum(len(chunk) for chunk in self._buffer)
            return total_samples / self.sample_rate


class MicController:
    """
    Main orchestrator combining audio capture, VAD, and buffering.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        vad_mode: int = 3,
        energy_threshold: float = 0.01,
        max_buffer_seconds: float = 10.0,
        device_index: Optional[int] = None
    ):
        """
        Initialize MicController.

        Args:
            sample_rate: Audio sample rate (default: 16000)
            chunk_size: Frames per chunk (default: 1024)
            vad_mode: VAD aggressiveness 0-3 (default: 3)
            energy_threshold: Energy threshold for speech detection
            max_buffer_seconds: Max buffer duration
            device_index: Audio device (None = default)
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size

        self._capture = AudioCapture(
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            device_index=device_index
        )

        self._vad = VoiceActivityDetector(
            sample_rate=sample_rate,
            mode=vad_mode,
            energy_threshold=energy_threshold
        )

        self._buffer = AudioBuffer(
            max_size_seconds=max_buffer_seconds,
            sample_rate=sample_rate
        )

        self._is_running = False
        self._processing_thread: Optional[threading.Thread] = None

        self._on_voice_start: Optional[Callable[[], None]] = None
        self._on_voice_end: Optional[Callable[[], None]] = None

    def start(self) -> None:
        """Start capture and VAD processing."""
        if self._is_running:
            logger.warning("MicController already running")
            return

        self._capture.start()
        self._is_running = True

        self._processing_thread = threading.Thread(
            target=self._process_loop,
            daemon=True
        )
        self._processing_thread.start()
        logger.info("MicController started")

    def stop(self) -> None:
        """Stop capture and processing."""
        self._is_running = False

        if self._processing_thread:
            self._processing_thread.join(timeout=2.0)

        self._capture.stop()
        logger.info("MicController stopped")

    def _process_loop(self) -> None:
        """Background thread that monitors audio and manages buffer."""
        was_speaking = False

        while self._is_running:
            chunk = self._capture.get_audio_chunk_array()

            if chunk is not None and len(chunk) > 0:
                is_speaking = self._vad.is_speech(chunk)

                if is_speaking:
                    self._buffer.add_chunk(chunk)

                    if not was_speaking:
                        if self._on_voice_start:
                            self._on_voice_start()
                        logger.debug("Voice started")

                    was_speaking = True
                else:
                    if was_speaking:
                        if self._on_voice_end:
                            self._on_voice_end()
                        logger.debug("Voice ended")

                    was_speaking = False

            time.sleep(0.01)

    def listen(self, timeout: float = 30.0) -> Optional[bytes]:
        """
        Blocking call that waits for voice activity and returns audio when speech ends.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Buffered audio as bytes, or None if timeout
        """
        self._buffer.clear()
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self._buffer.get_duration() > 0.5:
                time.sleep(0.3)
                return self.get_buffer()

            time.sleep(0.05)

        logger.warning("Listen timeout reached")
        return self.get_buffer() if self._buffer.get_duration() > 0 else None

    def get_live_audio(self) -> Optional[np.ndarray]:
        """Get latest audio chunk (non-blocking)."""
        return self._capture.get_audio_chunk_array()

    def get_buffer(self) -> bytes:
        """Get current buffered audio."""
        return self._buffer.get_buffer()

    def get_buffer_array(self) -> np.ndarray:
        """Get current buffered audio as array."""
        return self._buffer.get_buffer_array()

    def clear_buffer(self) -> None:
        """Clear audio buffer."""
        self._buffer.clear()

    @property
    def is_recording(self) -> bool:
        """Return True if currently recording."""
        return self._capture.is_recording

    def set_voice_callbacks(
        self,
        on_start: Optional[Callable[[], None]] = None,
        on_end: Optional[Callable[[], None]] = None
    ) -> None:
        """Set callbacks for voice start/end events."""
        self._on_voice_start = on_start
        self._on_voice_end = on_end


def list_devices() -> None:
    """List available audio input devices."""
    print("\nAvailable audio input devices:")
    print("-" * 50)
    devices = sd.query_devices(kind='input')
    if isinstance(devices, dict):
        print(f"Device {devices['index']}: {devices['name']}")
        print(f"  Sample rate: {devices['default_samplerate']}")
        print(f"  Channels: {devices['max_input_channels']}")
    else:
        for dev in devices:
            if dev['max_input_channels'] > 0:
                print(f"Device {dev['index']}: {dev['name']}")
                print(f"  Sample rate: {dev['default_samplerate']}")
                print(f"  Channels: {dev['max_input_channels']}")
    print("-" * 50)


def main():
    """Main execution when run directly."""
    print("JK Robot - Mic Module")
    print("=" * 40)

    list_devices()

    print("\nInitializing MicController...")
    mic = MicController()

    print("Starting capture... (Press Ctrl+C to stop)")
    print("Audio levels will be printed in real-time.\n")

    mic.start()

    try:
        while True:
            chunk = mic.get_live_audio()
            if chunk is not None and len(chunk) > 0:
                energy = np.abs(chunk).mean()
                bar = "#" * int(energy * 500)
                print(f"Energy: {energy:.4f} {bar}")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        mic.stop()
        print("MicController stopped.")


if __name__ == "__main__":
    main()