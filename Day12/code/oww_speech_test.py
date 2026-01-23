import sys
import os
import queue
import json
import numpy as np
import sounddevice as sd
from openwakeword.model import Model as OWWModel
from vosk import Model as VoskModel, KaldiRecognizer

# =========================
# CONFIGURATION
# =========================
WAKE_WORD = "hey"          # trigger phrase (must match an available openwakeword model name)
VOSK_PATH = "vosk_model"   # path to your unzipped Vosk model folder (e.g., "vosk-model-small-en-us-0.15")

# =========================
# GLOBAL STATE
# =========================
q = queue.Queue()
is_command_mode = False  # False = listening for wake word, True = listening for command


# =========================
# AUDIO CALLBACK
# =========================
def callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))


# =========================
# COMMAND PARSER (SPEECH TEST MODE)
# =========================
def execute_command(text: str):
    if not text:
        return

    t = (text or "").strip().lower()
    print(f" >> COMMAND RECOGNIZED: '{t}'")

    if "take off" in t or "takeoff" in t:
        print("Heard: 'Take Off'")

    elif "land" in t:
        print("Heard: 'Land'")

    elif "up" in t:
        print("Heard: 'Up'")

    elif "down" in t:
        print("Heard: 'Down'")

    elif "left" in t:
        print("Heard: 'Left'")

    elif "right" in t:
        print("Heard: 'Right'")

    elif "forward" in t:
        print("Heard: 'Forward'")

    elif "back" in t or "backward" in t:
        print("Heard: 'Back'")

    elif "stop" in t or "hover" in t:
        print("Heard: 'Stop/Hover'")

    elif "flip" in t:
        print("Heard: 'Flip'")

    else:
        print("Heard: (no matching command)")


# =========================
# MAIN
# =========================
def main():
    global is_command_mode

    # 1) Load models
    print(f"[INIT] Loading OpenWakeWord model: '{WAKE_WORD}' ...")
    oww = OWWModel(wakeword_models=[WAKE_WORD])

    print(f"[INIT] Loading Vosk model from: '{VOSK_PATH}' ...")
    if not os.path.exists(VOSK_PATH):
        print(f"[ERROR] Vosk model folder '{VOSK_PATH}' not found!")
        print("        Put the unzipped model folder here, or set VOSK_PATH to the correct path.")
        return

    v_model = VoskModel(VOSK_PATH)
    v_rec = KaldiRecognizer(v_model, 16000)

    # 2) Start mic stream
    print("\n" + "=" * 60)
    print(f"SYSTEM READY (speech test only)")
    print(f"1) Say wake word: '{WAKE_WORD}'")
    print("2) Then say a command: take off / land / up / down / left / right / forward / back / stop / flip")
    print("=" * 60 + "\n")

    # OpenWakeWord expects 16-bit PCM at 16kHz
    with sd.RawInputStream(
        samplerate=16000,
        blocksize=1280,
        dtype="int16",
        channels=1,
        callback=callback
    ):
        while True:
            data = q.get()

            if not is_command_mode:
                # --- WAKE WORD DETECTION ---
                audio_np = np.frombuffer(data, dtype=np.int16)
                prediction = oww.predict(audio_np)

                if prediction.get(WAKE_WORD, 0.0) > 0.5:
                    print("\n[!] WAKE WORD DETECTED! Speak your command now...")
                    is_command_mode = True
                    v_rec.Reset()  # clear previous buffer

            else:
                # --- COMMAND RECOGNITION (VOSK) ---
                if v_rec.AcceptWaveform(data):
                    result = json.loads(v_rec.Result())
                    cmd_text = result.get("text", "").strip()

                    if cmd_text:
                        execute_command(cmd_text)
                        print("[INFO] Returning to Wake Word mode...\n")
                        is_command_mode = False
                        oww.reset()  # reset wakeword buffer
                else:
                    # optional: partial = json.loads(v_rec.PartialResult()).get("partial","")
                    pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping...")