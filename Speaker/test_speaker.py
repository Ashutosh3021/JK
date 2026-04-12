"""
Test script for Speaker module - verify TTS and audio playback
"""

import sys
import time

sys.path.insert(0, "..")
from Speaker.main import SpeakerController, list_devices


def main():
    print("JK Robot - Speaker Module Test")
    print("=" * 40)

    print("\n[1] Listing available audio devices:")
    list_devices()

    print("\n[2] Initializing SpeakerController with pyttsx3...")
    speaker = SpeakerController(tts_engine="pyttsx3")

    print("\n[3] Available voices:")
    voices = speaker.list_voices()
    for i, voice in enumerate(voices[:5]):
        print(f"  {i}: {voice.get('name', 'Unknown')}")

    print("\n[4] Testing pyttsx3 speak...")
    print("   Saying: 'Hello, I am JK. Your desktop robot assistant.'")
    speaker.speak("Hello, I am JK. Your desktop robot assistant.")
    print("   Done!")

    print("\n[5] Testing async speak...")
    print("   Saying: 'This is non-blocking speech'")
    speaker.speak_async("This is non-blocking speech")
    print("   (returned immediately while speaking)")

    time.sleep(2)

    print("\n[6] Testing stop...")
    speaker.speak_async("This should be stopped")
    time.sleep(0.5)
    speaker.stop()
    print("   Stopped!")

    print("\n[7] Testing rate and volume...")
    speaker.set_rate(200)
    speaker.set_volume(0.8)
    speaker.speak("Speaking faster and quieter.")
    speaker.set_rate(150)
    speaker.set_volume(1.0)

    print("\n✅ Test complete!")
    print("\nTry the interactive mode:")
    print("  python Speaker/main.py")


if __name__ == "__main__":
    main()