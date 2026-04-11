# Roadmap: JK AI Desktop Robot

## Phase 0 — Hardware Setup *(Week 1)*
- [ ] Solder and test all components on breadboard
- [ ] Verify SPI display, I2S mic, I2S speaker independently
- [ ] Confirm GPIO map against physical board pinout
- [ ] Flash MicroPython firmware to ESP32-S3
- [ ] Run smoke tests per subsystem

## Phase 1.1 — Brain - Ollama API Connection *(Week 2)*
- [ ] Create `Brain/main.py` - connect to local Ollama
- [ ] Test API endpoints (/api/tags, /api/generate)
- [ ] Verify text prompt → response flow

## Phase 1.2 — Mic - PC Audio Capture *(Week 2)*
- [ ] Create `Mic/main.py` - capture audio from PC microphone
- [ ] Implement VAD (Voice Activity Detection)
- [ ] Buffer audio chunks

**Plans:** 1 plan

- [ ] 01.2-01-PLAN.md — Mic module with audio capture, VAD, and buffering

## Phase 1.3 — Speaker - Audio Playback/TTS *(Week 2)*
- [ ] Create `Speaker/main.py` - play audio through PC speakers
- [ ] Integrate TTS (pyttsx3 or gTTS)
- [ ] Test text → speech conversion

## Phase 1.4 — STT - Speech to Text *(Week 3)*
- [ ] Create `STT/main.py` - convert voice to text
- [ ] Use Ollama Whisper or speech_recognition library
- [ ] Test transcription accuracy

## Phase 1.5 — Integration - Full Loop *(Week 3)*
- [ ] Wire all modules together (Mic → STT → Brain → Speaker)
- [ ] Test complete voice conversation flow
- [ ] Fix bugs and optimize

## Phase 2.1 — Brain - MicroPython Version *(Week 3)*
- [ ] Convert Brain to `Brain/model.py` (MicroPython)
- [ ] Adapt for ESP32 with urequests
- [ ] Test on hardware

## Phase 2.2 — Mic - I2S Mic Code *(Week 3)*
- [ ] Convert Mic to `Mic/model.py` (MicroPython)
- [ ] Use machine.I2S for INMP441
- [ ] Test on hardware

## Phase 2.3 — Speaker - I2S Speaker Code *(Week 4)*
- [ ] Convert Speaker to `Speaker/model.py` (MicroPython)
- [ ] Use machine.I2S for PAM8302
- [ ] Test on hardware

## Phase 2.4 — STT - MicroPython Version *(Week 4)*
- [ ] Convert STT to `STT/model.py` (MicroPython)
- [ ] Stream audio to API
- [ ] Test on hardware

## Phase 2 — Brain Integration *(Week 4)*
- [ ] Implement `Brain/main.py` — WiFi boot, NTP, full conversation loop
- [ ] Wire STT → LLM → TTS pipeline end-to-end
- [ ] Integrate Display states with conversation events
- [ ] Add servo gesture mapping

## Phase 3 — Connectivity *(Week 5)*
- [ ] BLE GATT server for phone commands
- [ ] WiFi web UI (hosted on ESP32) for face/config changes
- [ ] OTA update endpoint

## Phase 4 — Enclosure & Polish *(Week 6)*
- [ ] Fit all components into 6 × 4 × 4 cm body
- [ ] Final cable routing, hot-glue speaker
- [ ] Tune VAD thresholds in real enclosure acoustics
- [ ] Power consumption profiling; optimise sleep modes
- [ ] Record demo video

## Success Criteria

| Phase | Criterion |
|-------|-----------|
| 0 | All hardware components respond to basic tests |
| 1.x | Each module (Brain, Mic, Speaker, STT) works on PC |
| 1.5 | Full conversation loop on PC: voice → STT → Ollama → TTS → speaker |
| 2.x | Each module runs on ESP32 (MicroPython) |
| 2.5 | Full conversation loop on ESP32 |
| 3 | Phone can control JK via BLE and WiFi |
| 4 | Robot is fully assembled and functional |