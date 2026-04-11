# Project: JK AI Desktop Robot

> **Hardware:** ESP32-S3 · 6 × 4 × 4 cm ABS body · 2.4" TFT · INMP441 mic · PAM8302 + 1W speaker · 2× MG90S servo · LiPo 500 mAh · USB-C charging
> **Connectivity:** WiFi 802.11 b/g/n · Bluetooth 5 BLE
> **Stack:** MicroPython (on-device) · Python 3 (tools/tests) · HTML/CSS/JS (UI prototyping)

## Overview

JK is a compact AI-powered desktop robot that can:
- Chat — converse via voice or text using an LLM API (GPT-4o / Gemini / local Ollama)
- Listen — pick up speech via an I2S MEMS microphone and run STT (speech-to-text)
- Speak — synthesise replies via TTS and play them through a built-in 1W speaker
- Express — display animated faces, emotions, chat messages, and clock on a colour TFT
- Connect — pair with a phone or PC over WiFi / BLE to change face styles, trigger prompts, and read chat history
- Charge — topped up via USB-C; runs untethered on a LiPo battery

## Folder Structure

```
JK/
├── Brain/main.py         # Core logic: WiFi, LLM, STT/TTS orchestration
├── Display/main.py       # TFT driver: face animations, text, UI frames
├── Mic/main.py           # I2S microphone capture & VAD (voice activity)
├── Speaker/main.py       # I2S audio playback & TTS pipeline
├── TEST/Draft_1/         # Prototype / scratch tests
└── PLAN.md               # Main project documentation
```

## Hardware Bill of Materials

| # | Component | Spec | Purpose |
|---|-----------|------|---------|
| 1 | ESP32-S3 Dev Board | Xtensa LX7 240 MHz, 512 KB RAM, 8 MB flash | Main MCU · WiFi · BT5 BLE |
| 2 | TFT Display | 2.4" ST7789 / ILI9341 · 240 × 320 · SPI | Face animations · chat UI · clock |
| 3 | INMP441 Mic | I2S MEMS · 3.3 V · −26 dBFS sensitivity | Voice input · STT |
| 4 | PAM8302 Amp | Class-D · 1.5 W · 5 V | Drives speaker |
| 5 | Speaker | 8 Ω · 1 W · 40 mm | TTS speech · alerts |
| 6 | MG90S Servo × 2 | 180° · 5 V · 2.5 kg·cm | Pan (yaw) · Tilt (nod) |
| 7 | LiPo Battery | 3.7 V · 500 mAh · 1S | Portable power |
| 8 | TP4056 + USB-C | CC/CV charger · 5 V input | Charging IC |
| 9 | DS3231 RTC | I2C · CR2032 backup | Accurate timekeeping |
| 10 | WS2812B RGB LED | 5 V · single-wire data | Mood / status indicator |
| 11 | Logic Level Shifter | 3.3 V ↔ 5 V · 4-ch | Protect ESP32 GPIOs from 5 V |
| 12 | ABS / PLA Enclosure | 6 × 4 × 4 cm · red body | Housing |

## GPIO Map

| GPIO | Signal | Connected To | Protocol |
|------|--------|-------------|----------|
| 5 | TFT CS | Display CS | SPI |
| 18 | TFT SCK | Display CLK | SPI |
| 19 | TFT MISO | Display MISO | SPI |
| 23 | TFT MOSI | Display MOSI | SPI |
| 25 | I2S DATA | INMP441 SD · PAM8302 IN | I2S |
| 26 | I2S WS | Mic WS · Amp WS | I2S |
| 27 | I2S SCK | Mic SCK · Amp BCLK | I2S |
| 12 | PWM | Servo 1 (Pan) signal | PWM |
| 13 | PWM | Servo 2 (Tilt) signal | PWM |
| 21 | SDA | DS3231 SDA | I2C |
| 22 | SCL | DS3231 SCL | I2C |
| 4 | LED DATA | WS2812B DIN | One-wire |

## Power Design

| State | Est. Current | Notes |
|-------|-------------|-------|
| Deep sleep | ~20 µA | ESP32-S3 ULP running |
| Idle (display on) | ~80 mA | Backlight 50 % |
| Active conversation | ~200 mA | WiFi + I2S + servos |
| Servos at stall | +500 mA peak | From 5 V rail via shifter |
| **Avg active** | ~180 mA | Mixed use |

Battery life: 500 mAh ÷ 180 mA ≈ **~2.7 hours** active · **~25 h** deep sleep