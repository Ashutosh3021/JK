# Mic Module - PC Audio Capture for JK Robot

## Overview

This module captures audio from the PC microphone, detects voice activity using VAD (Voice Activity Detection), and buffers audio chunks for downstream STT processing.

## Installation

```bash
cd Mic
pip install -r requirements.txt
```

**Note:** If you get PortAudio errors:
- **Windows:** `pip install portaudio` (or use conda)
- **macOS:** `brew install portaudio`
- **Linux:** `sudo apt-get install portaudio19-dev`

## Classes

### AudioCapture

Captures audio from PC microphone using sounddevice.

```python
from Mic.main import AudioCapture

capture = AudioCapture(
    sample_rate=16000,
    chunk_size=1024,
    device_index=None  # None = default device
)

capture.start()
audio_chunk = capture.get_audio_chunk()
capture.stop()
```

**Parameters:**
- `sample_rate`: Sample rate in Hz (default: 16000)
- `chunk_size`: Frames per chunk (default: 1024)
- `device_index`: Audio device index (None = default)
- `channels`: Number of channels (default: 1 = mono)

### VoiceActivityDetector

Detects voice activity in audio chunks using energy-based VAD.

```python
from Mic.main import VoiceActivityDetector

vad = VoiceActivityDetector(
    sample_rate=16000,
    mode=3,
    energy_threshold=0.01
)

is_speech = vad.is_speech(audio_chunk)
```

**Parameters:**
- `sample_rate`: Audio sample rate
- `mode`: VAD aggressiveness 0-3 (3 = most aggressive)
- `energy_threshold`: Energy threshold for speech detection

### AudioBuffer

Stores audio chunks for later processing.

```python
from Mic.main import AudioBuffer

buffer = AudioBuffer(
    max_size_seconds=10.0,
    sample_rate=16000
)

buffer.add_chunk(audio_chunk)
audio_data = buffer.get_buffer()
duration = buffer.get_duration()
buffer.clear()
```

**Parameters:**
- `max_size_seconds`: Maximum buffer duration
- `sample_rate`: Audio sample rate

### MicController

Main orchestrator combining all components.

```python
from Mic.main import MicController

mic = MicController()

mic.start()
audio_data = mic.listen()  # Blocking - waits for speech
mic.stop()
```

**Parameters:**
- `sample_rate`: Audio sample rate (default: 16000)
- `chunk_size`: Frames per chunk (default: 1024)
- `vad_mode`: VAD aggressiveness 0-3 (default: 3)
- `energy_threshold`: Energy threshold (default: 0.01)
- `max_buffer_seconds`: Max buffer duration (default: 10.0)
- `device_index`: Audio device (None = default)

## Usage Examples

### Basic Usage

```python
from Mic.main import MicController

mic = MicController()
mic.start()

# Blocking listen - waits for voice
audio_data = mic.listen(timeout=30.0)

if audio_data:
    print(f"Captured {len(audio_data)} bytes of audio")
    # Send to STT...

mic.stop()
```

### With Callbacks

```python
def on_voice_start():
    print("Voice started!")

def on_voice_end():
    print("Voice ended!")
    audio = mic.get_buffer()
    # Process audio...

mic = MicController()
mic.set_voice_callbacks(on_start=on_voice_start, on_end=on_voice_end)
mic.start()
```

### Non-blocking Mode

```python
mic = MicController()
mic.start()

while True:
    chunk = mic.get_live_audio()
    if chunk is not None:
        # Process live audio...
    time.sleep(0.1)
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| sample_rate | 16000 | Audio sample rate (Hz) |
| chunk_size | 1024 | Frames per audio chunk |
| vad_mode | 3 | VAD aggressiveness (0-3) |
| energy_threshold | 0.01 | Energy threshold for speech |
| max_buffer_seconds | 10.0 | Max buffer duration |

## Running Tests

```bash
# List devices
python -c "from Mic.main import list_devices; list_devices()"

# Run test
python Mic/test_capture.py
```

## Troubleshooting

### PortAudio not found
Install PortAudio library for your OS (see Installation section).

### No audio device found
Check that your microphone is connected and enabled in system settings.

### VAD too sensitive / not sensitive enough
Adjust `energy_threshold` (lower = more sensitive) or `vad_mode` (0 = least aggressive, 3 = most).

## Future Development (ESP32)

In Phase 2.2, this module will be converted to MicroPython for ESP32:
- Use `machine.I2S` instead of sounddevice
- Connect INMP441 I2S microphone
- Implement VAD with limited memory