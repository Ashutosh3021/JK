# JK — AI Desktop Robot `v1.0`

A tiny AI-powered desktop companion. It listens, thinks, speaks, and expresses itself — all from a 6 × 4 × 4 cm box on your desk.

---

## What it does

- 🎤 Listens to your voice via a built-in MEMS microphone
- 🧠 Sends your speech to an LLM (GPT-4o) and gets a reply
- 🔊 Speaks the reply out loud through a 1W speaker
- 📺 Shows animated face expressions on a colour TFT display
- 📱 Connects to your phone or PC over WiFi / Bluetooth
- 🔋 Runs on a LiPo battery, charges via USB-C

---

## Hardware

| Component | Details |
|-----------|---------|
| ESP32-S3 | Main MCU · WiFi · BT5 BLE |
| 2.4″ TFT Display | ST7789 / ILI9341 · 240×320 · SPI |
| INMP441 Mic | I2S MEMS microphone |
| PAM8302 + Speaker | 1.5W amp · 8Ω 1W speaker |
| MG90S Servo × 2 | Pan + tilt head movement |
| LiPo 500 mAh | 3.7V rechargeable battery |
| TP4056 + USB-C | Charging IC |
| DS3231 RTC | Real-time clock · I2C |
| WS2812B LED | RGB status indicator |

---

## Project Structure

```
JK/
 ┣ Brain/
 ┃ ┗ main.py       # WiFi, LLM API, conversation loop
 ┣ Display/
 ┃ ┗ main.py       # TFT face animations & UI
 ┣ Mic/
 ┃ ┗ main.py       # I2S mic capture & voice detection
 ┣ Speaker/
 ┃ ┗ main.py       # I2S audio playback & TTS
 ┣ TEST/
 ┃ ┗ Draft_1/      # Prototypes & circuit diagrams
 ┣ .gitignore
 ┣ PLAN.md
 ┗ README.md
```

---

## Getting Started

### 1. Flash MicroPython onto the ESP32-S3

```bash
esptool.py --chip esp32s3 erase_flash
esptool.py --chip esp32s3 write_flash -z 0x0 micropython-esp32s3.bin
```

### 2. Set your credentials

Open `Brain/main.py` and fill in:

```python
WIFI_SSID     = "your_wifi_name"
WIFI_PASSWORD = "your_wifi_password"
OPENAI_API_KEY = "sk-..."
```

### 3. Upload the project files

```bash
mpremote connect /dev/ttyUSB0 cp -r Brain Display Mic Speaker :
```

### 4. Run

```bash
mpremote connect /dev/ttyUSB0 run Brain/main.py
```

JK will boot, connect to WiFi, and start listening.

---

## GPIO Reference

| GPIO | Connected To |
|------|-------------|
| 5, 18, 19, 23 | TFT Display (SPI) |
| 25, 26, 27 | Mic + Speaker (I2S) |
| 12, 13 | Servo Pan, Servo Tilt (PWM) |
| 21, 22 | RTC DS3231 (I2C) |
| 4 | WS2812B RGB LED |

---

## V1 Limitations

This is a first version — it works but it's rough in places.

- Requires a WiFi connection for STT and LLM (no offline mode yet)
- No wake word — press the boot button to start listening
- Face expressions are static sprites, not animated
- No phone app yet — WiFi credentials must be set manually in code
- Battery life not optimised (~2–3 hours active)

See [`PLAN.md`](./PLAN.md) for the full roadmap and what's coming next.

---

## License

MIT