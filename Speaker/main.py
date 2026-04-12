"""
Speaker Module - PC Audio Playback with TTS for JK Robot

Purpose: Enable the robot to speak responses through PC speakers
using text-to-speech synthesis.

Windows SAPI fix: pyttsx3's runAndWait() sets an internal 'isBusy' flag that
never resets when reusing the same engine instance across calls. The only
reliable fix on Windows is to spin up a fresh pyttsx3 engine in a NEW thread
for every speak() call. We serialize calls through a threading.Lock so only
one thread runs at a time, and we join() before returning so blocking speak()
truly blocks.
"""

import threading
import logging
from typing import Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TTSEngine:
    """Text-to-Speech engine with multiple backend support."""

    def __init__(
        self,
        engine: str = "pyttsx3",
        voice: Optional[str] = None,
        rate: int = 150,
        volume: float = 1.0
    ):
        """
        Initialize TTS engine.

        Args:
            engine: TTS engine ('pyttsx3' or 'gtts')
            voice: Voice ID (pyttsx3 only)
            rate: Speech rate in WPM
            volume: Volume 0.0 to 1.0
        """
        self.engine_name = engine.lower()
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self._gtts_class = None
        self._is_speaking = False

        # Serialize speak calls — only one thread speaks at a time
        self._lock = threading.Lock()

        self._init_engine()

    def _init_engine(self) -> None:
        """Validate engine choice and pre-import dependencies."""
        if self.engine_name == "pyttsx3":
            self._validate_pyttsx3()
        elif self.engine_name in ("gtts", "google"):
            self._init_gtts()
        else:
            logger.warning(f"Unknown engine '{self.engine_name}', defaulting to pyttsx3")
            self.engine_name = "pyttsx3"
            self._validate_pyttsx3()

    def _validate_pyttsx3(self) -> None:
        """Confirm pyttsx3 is importable. No persistent instance is stored."""
        try:
            import pyttsx3  # noqa: F401
            logger.info("pyttsx3 available — will create per-call instances (Windows SAPI fix)")
        except ImportError as e:
            logger.error(f"pyttsx3 not installed: {e}")

    def _init_gtts(self) -> None:
        """Initialize gTTS engine."""
        try:
            from gtts import gTTS
            self._gtts_class = gTTS
            logger.info("Initialized gTTS TTS engine")
        except Exception as e:
            logger.error(f"Failed to init gTTS: {e}")
            self._gtts_class = None

    # ------------------------------------------------------------------
    # Core speak logic
    # ------------------------------------------------------------------

    def _pyttsx3_worker(self, text: str) -> None:
        """
        Runs in its own thread. Creates a BRAND NEW pyttsx3 engine,
        speaks, then destroys it.

        Why a new thread every call?
        Windows SAPI COM sets an internal 'isBusy' flag inside the
        driver after runAndWait() completes. If you call say()+runAndWait()
        again on the same engine object — even after it finishes — SAPI
        silently skips playback because it thinks the engine is still busy.
        Creating the engine inside a fresh thread gives SAPI a clean COM
        apartment with no leftover state, so every call works identically.
        """
        engine = None
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
            if self.voice:
                engine.setProperty("voice", self.voice)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            logger.error(f"pyttsx3 worker error: {e}")
        finally:
            if engine:
                try:
                    engine.stop()
                except Exception:
                    pass

    def speak(self, text: str) -> None:
        """
        Convert text to speech and play (blocking).

        Args:
            text: Text to speak
        """
        if not text or not text.strip():
            return

        with self._lock:
            self._is_speaking = True
            try:
                if self.engine_name == "pyttsx3":
                    # Fresh thread = fresh COM apartment = no SAPI busy-flag
                    t = threading.Thread(
                        target=self._pyttsx3_worker,
                        args=(text,),
                        daemon=True
                    )
                    t.start()
                    t.join()  # Block here until speech finishes
                elif self.engine_name in ("gtts", "google"):
                    self._speak_gtts(text)
                else:
                    logger.warning("No TTS engine available")
            except Exception as e:
                logger.error(f"TTS speak error: {e}")
            finally:
                self._is_speaking = False

    def speak_async(self, text: str) -> None:
        """
        Non-blocking TTS. Runs speak() in a daemon thread.

        Args:
            text: Text to speak
        """
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()

    def _speak_gtts(self, text: str) -> None:
        """
        Speak using gTTS — saves to temp mp3 and plays via OS player.

        Args:
            text: Text to speak
        """
        try:
            from gtts import gTTS
            import tempfile
            import subprocess

            tts = gTTS(text=text, lang="en")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                temp_file = f.name
            tts.save(temp_file)
            subprocess.run(["start", "", temp_file], shell=True)
        except Exception as e:
            logger.error(f"gTTS playback error: {e}")

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def stop(self) -> None:
        """Stop current playback (best-effort)."""
        self._is_speaking = False

    def set_voice(self, voice_id: str) -> None:
        """Change voice (pyttsx3 only). Takes effect on next speak() call."""
        self.voice = voice_id
        logger.info(f"Voice set to: {voice_id}")

    def set_rate(self, rate: int) -> None:
        """Change speech rate. Takes effect on next speak() call."""
        self.rate = rate
        logger.info(f"Rate set to: {rate}")

    def set_volume(self, volume: float) -> None:
        """Change volume (0.0 to 1.0). Takes effect on next speak() call."""
        self.volume = max(0.0, min(1.0, volume))
        logger.info(f"Volume set to: {self.volume}")

    def list_voices(self) -> List[dict]:
        """
        Return available voices by briefly spinning up a temp engine.
        Safe to call even after multiple speak() calls.
        """
        voices = []
        if self.engine_name != "pyttsx3":
            return voices
        engine = None
        try:
            import pyttsx3
            engine = pyttsx3.init()
            for voice in engine.getProperty("voices"):
                voices.append({
                    "id": voice.id,
                    "name": voice.name,
                    "languages": voice.languages
                })
        except Exception as e:
            logger.error(f"list_voices error: {e}")
        finally:
            if engine:
                try:
                    engine.stop()
                except Exception:
                    pass
        return voices

    @property
    def is_speaking(self) -> bool:
        """Return True if currently speaking."""
        return self._is_speaking


class AudioPlayer:
    """Plays raw audio data or audio files through PC speakers."""

    def __init__(self, device_index: Optional[int] = None):
        """
        Initialize audio player.

        Args:
            device_index: Audio output device index (None = default)
        """
        self.device_index = device_index
        self._is_playing = False

    def play(self, audio_data: bytes, sample_rate: int = 16000) -> None:
        """
        Play raw PCM audio bytes.

        Args:
            audio_data: Raw PCM audio bytes
            sample_rate: Sample rate in Hz
        """
        try:
            import numpy as np
            import sounddevice as sd

            self._is_playing = True
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            sd.play(audio_array, samplerate=sample_rate,
                    device=self.device_index)
            sd.wait()
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
        finally:
            self._is_playing = False

    def play_file(self, filepath: str) -> None:
        """
        Play an audio file (wav, mp3, ogg, flac, etc.).

        Args:
            filepath: Path to audio file
        """
        try:
            import sounddevice as sd
            import soundfile as sf

            self._is_playing = True
            data, samplerate = sf.read(filepath)
            sd.play(data, samplerate=samplerate, device=self.device_index)
            sd.wait()
        except Exception as e:
            logger.error(f"File playback error: {e}")
        finally:
            self._is_playing = False

    def stop(self) -> None:
        """Stop any active playback."""
        try:
            import sounddevice as sd
            sd.stop()
        except Exception as e:
            logger.error(f"AudioPlayer stop error: {e}")
        self._is_playing = False

    @property
    def is_playing(self) -> bool:
        """Return True if currently playing."""
        return self._is_playing


class SpeakerController:
    """Main orchestrator for TTS and audio playback."""

    def __init__(
        self,
        tts_engine: str = "pyttsx3",
        device_index: Optional[int] = None,
        voice: Optional[str] = None,
        rate: int = 150,
        volume: float = 1.0
    ):
        """
        Initialize SpeakerController.

        Args:
            tts_engine: TTS engine name ('pyttsx3' or 'gtts')
            device_index: Audio output device index (None = default)
            voice: Voice ID (pyttsx3 only)
            rate: Speech rate in WPM
            volume: Volume 0.0 to 1.0
        """
        self._tts = TTSEngine(
            engine=tts_engine,
            voice=voice,
            rate=rate,
            volume=volume
        )
        self._player = AudioPlayer(device_index=device_index)

    def speak(self, text: str) -> None:
        """
        Blocking text-to-speech.

        Args:
            text: Text to speak
        """
        logger.info(f"Speaking: {text[:60]}...")
        self._tts.speak(text)

    def speak_async(self, text: str) -> None:
        """
        Non-blocking text-to-speech.

        Args:
            text: Text to speak
        """
        logger.info(f"Speaking async: {text[:60]}...")
        self._tts.speak_async(text)

    def play_sound(self, filepath: str) -> None:
        """
        Play an audio file.

        Args:
            filepath: Path to audio file
        """
        logger.info(f"Playing: {filepath}")
        self._player.play_file(filepath)

    def stop(self) -> None:
        """Stop all audio output."""
        self._tts.stop()
        self._player.stop()
        logger.info("Audio stopped")

    def set_voice(self, voice_id: str) -> None:
        """Change TTS voice."""
        self._tts.set_voice(voice_id)

    def set_rate(self, rate: int) -> None:
        """Change TTS speech rate."""
        self._tts.set_rate(rate)

    def set_volume(self, volume: float) -> None:
        """Change TTS volume (0.0 to 1.0)."""
        self._tts.set_volume(volume)

    def list_voices(self) -> List[dict]:
        """List available TTS voices."""
        return self._tts.list_voices()

    @property
    def is_speaking(self) -> bool:
        """Return True if TTS is currently active."""
        return self._tts.is_speaking

    @property
    def is_playing(self) -> bool:
        """Return True if audio player is currently active."""
        return self._player.is_playing


def list_devices() -> None:
    """List available audio output devices."""
    try:
        import sounddevice as sd
        print("\nAvailable audio output devices:")
        print("-" * 50)
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev["max_output_channels"] > 0:
                print(f"Device {i}: {dev['name']}")
                print(f"  Sample rate : {dev['default_samplerate']}")
                print(f"  Channels    : {dev['max_output_channels']}")
        print("-" * 50)
    except Exception as e:
        print(f"Could not list devices: {e}")


def main():
    """Main execution when run directly."""
    print("JK Robot - Speaker Module")
    print("=" * 40)

    list_devices()

    print("\nInitializing SpeakerController...")
    speaker = SpeakerController()

    print("\nAvailable voices:")
    for voice in speaker.list_voices():
        print(f"  - {voice.get('name', 'Unknown')}  [{voice.get('id', '')}]")

    print("\nInteractive mode — type text to speak, 'quit' to exit")
    print("-" * 40)

    while True:
        try:
            text = input("You: ").strip()
            if text.lower() in ("quit", "exit", "q"):
                break
            if text:
                speaker.speak(text)
        except KeyboardInterrupt:
            print("\n\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")

    speaker.stop()
    print("Speaker stopped.")


if __name__ == "__main__":
    main()