"""
Test script for Mic module - verify audio capture and VAD
"""

import sounddevice as sd
import numpy as np
import time
import sys

sys.path.insert(0, "..")
from Mic.main import MicController, list_devices


def main():
    print("JK Robot - Mic Module Test")
    print("=" * 40)

    print("\n[1] Listing available audio devices:")
    list_devices()

    print("\n[2] Initializing MicController...")
    mic = MicController(
        sample_rate=16000,
        chunk_size=1024,
        vad_mode=3,
        energy_threshold=0.01
    )

    print("\n[3] Starting audio capture...")
    mic.start()

    print("\n[4] Running for 10 seconds...")
    print("Speak or make noise to trigger VAD!\n")

    start_time = time.time()
    voice_events = 0

    while time.time() - start_time < 10:
        chunk = mic.get_live_audio()

        if chunk is not None and len(chunk) > 0:
            energy = np.abs(chunk).mean()
            bar = "#" * min(int(energy * 500), 50)

            buffer_duration = mic._buffer.get_duration()
            if buffer_duration > 0.1:
                voice_events += 1
                print(f"🎤 Voice detected! Energy: {energy:.4f} Duration: {buffer_duration:.2f}s {bar}")
                time.sleep(0.5)
            else:
                print(f"  Energy: {energy:.4f} {bar}")

        time.sleep(0.1)

    print("\n[5] Stopping capture...")
    mic.stop()

    print("\n[6] Final buffer check:")
    final_buffer = mic.get_buffer()
    print(f"   Buffer size: {len(final_buffer)} bytes")
    print(f"   Duration: {mic._buffer.get_duration():.2f} seconds")
    print(f"   Voice events: {voice_events}")

    print("\n✅ Test complete!")


if __name__ == "__main__":
    main()