# Requirements: JK AI Desktop Robot

## MVP (Must Have)

### Hardware
- [ ] ESP32-S3 with MicroPython flashed
- [ ] 2.4" TFT display (ST7789/ILI9341) connected via SPI
- [ ] INMP441 I2S microphone for voice capture
- [ ] PAM8302 amplifier + 1W speaker for audio output
- [ ] LiPo 500 mAh battery with USB-C charging (TP4056)
- [ ] Basic enclosure (6×4×4 cm)

### Core Features
- [ ] Boot animation on TFT display
- [ ] WiFi connection with stored credentials
- [ ] Microphone capture with basic VAD (Voice Activity Detection)
- [ ] STT via Whisper API (cloud)
- [ ] LLM reply via GPT-4o API (cloud)
- [ ] TTS playback via OpenAI TTS or Google TTS
- [ ] Idle / listening / speaking face states on display
- [ ] USB-C charging functional
- [ ] BLE pairing with phone

### Display States
- [ ] Idle face — slow blink animation
- [ ] Listening face — pulsing ring animation
- [ ] Thinking face — spinning dots
- [ ] Speaking face — mouth sync with audio
- [ ] Status bar — WiFi signal, battery %, time

## v1.1 (Should Have)

- [ ] Phone/web UI to change face packs
- [ ] Chat history displayed on screen with scroll
- [ ] Pan/tilt servo gestures linked to emotions
- [ ] WS2812B LED mood lighting
- [ ] RTC clock screensaver
- [ ] OTA firmware update over WiFi
- [ ] Battery % display on status bar

## v2.0 (Nice to Have)

- [ ] On-device wake word detection ("Hey JK")
- [ ] Custom face designer in phone app
- [ ] Multi-robot sync over local MQTT
- [ ] Offline LLM via quantised model
- [ ] PIR / proximity sensor for auto-wake
- [ ] Multi-language TTS/STT