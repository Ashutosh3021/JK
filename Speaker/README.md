# Speaker Module - PC Audio Playback with TTS for JK Robot

## Overview

This module handles text-to-speech synthesis and audio playback for the JK robot through PC speakers.

## Installation

```bash
cd Speaker
pip install -r requirements.txt
```

**Notes:**
- **pyttsx3**: Uses system TTS (Windows SAPI, macOS NSSpeechSynthesizer, Linux espeak/festival)
- **gTTS**: Requires internet for Google TTS
- **simpleaudio**: For playing audio files

## Classes

### TTSEngine

Text-to-speech engine with multiple backend support.

```python
from Speaker.main import TTSEngine

tts = TTSEngine(engine='pyttsx3', rate=150, volume=1.0)
tts.speak("Hello world")
```

**Parameters:**
- `engine`: 'pyttsx3' (offline) or 'gtts' (Google online)
- `voice`: Voice ID (pyttsx3 only)
- `rate`: Speech rate in WPM (default: 150)
- `volume`: Volume 0.0-1.0 (default: 1.0)

### AudioPlayer

Plays raw audio data through PC speakers.

```python
from Speaker.main import AudioPlayer

player = AudioPlayer()
player.play_file("sound.wav")
```

### SpeakerController

Main orchestrator combining TTS and audio playback.

```python
from Speaker.main import SpeakerController

speaker = SpeakerController()
speaker.speak("Hello, I am JK!")
```

## Usage Examples

### Basic Usage

```python
from Speaker.main import SpeakerController

speaker = SpeakerController()
speaker.speak("Hello, I am JK!")
```

### Non-blocking Speech

```python
speaker = SpeakerController()
speaker.speak_async("I will keep talking while you do other things...")
```

### Change Voice

```python
speaker = SpeakerController()

# List available voices
for voice in speaker.list_voices():
    print(voice['name'])

# Set voice
speaker.set_voice(voice_id)
speaker.speak("Hello with new voice!")
```

### Control Rate and Volume

```python
speaker = SpeakerController()
speaker.set_rate(200)  # Faster
speaker.set_volume(0.5)  # Quieter
speaker.speak("Speaking faster and quieter.")
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| tts_engine | pyttsx3 | TTS engine (pyttsx3, gtts) |
| rate | 150 | Speech rate in WPM |
| volume | 1.0 | Volume 0.0-1.0 |
| voice | None | Voice ID |

## Running Tests

```bash
# Install dependencies
pip install -r Speaker/requirements.txt

# Run test
python Speaker/test_speaker.py

# Interactive mode
python Speaker/main.py
```

## TTS Engine Comparison

| Engine | Pros | Cons |
|--------|------|------|
| pyttsx3 | Fast, offline, no internet | Limited voices, platform-specific |
| gTTS | High quality, many languages | Requires internet |

## Troubleshooting

### No audio output
- Check system volume
- Verify default audio device in OS settings

### pyttsx3 not working on Linux
- Install espeak: `sudo apt-get install espeak`
- Install festival: `sudo apt-get install festival`

### gTTS not playing
- Install simpleaudio: `pip install simpleaudio`

## Future Development (ESP32)

In Phase 2.3, this module will be converted to MicroPython for ESP32:
- Use `machine.I2S` instead of sounddevice
- Connect PAM8302 amplifier + speaker
- TTS via HTTP to external service