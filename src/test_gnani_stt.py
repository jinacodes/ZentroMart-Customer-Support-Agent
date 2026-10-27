import os
from pathlib import Path
from dotenv import load_dotenv
from gnani.stt import GnaniSTTClient

project_folder = Path(__file__).resolve().parent.parent
load_dotenv(project_folder / ".env")

audio_path = project_folder / "speech4.wav"

if not os.getenv("GNANI_API_KEY"):
    print("Gnani API key is missing.")
    raise SystemExit

if not audio_path.exists():
    print("Audio file not found:", audio_path)
    raise SystemExit

try:
    client = GnaniSTTClient()
    result = client.transcribe(
        str(audio_path),
        language_code="en-IN"
    )

    print("Transcription result:")
    print(result)

except Exception as e:
    print("Error type:", type(e).__name__)
    print("Error details:", str(e))
