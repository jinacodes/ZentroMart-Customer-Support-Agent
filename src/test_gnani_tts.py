
import os
from pathlib import Path
from dotenv import load_dotenv
from gnani.tts import GnaniTTSClient

# Find the project folder and load its private API key.
project_folder = Path(__file__).resolve().parent.parent
load_dotenv(project_folder / ".env")

if not os.getenv("GNANI_API_KEY"):
    print("Gnani API key is missing.")
    raise SystemExit(1)

# Save the generated speech in the project's outputs folder.
output_folder = project_folder / "outputs" / "tts_test"
output_folder.mkdir(parents=True, exist_ok=True)
audio_path = output_folder / "test_reply.wav"

try:
    client = GnaniTTSClient()

    result = client.synthesize(
        text="Hello! Welcome to ZentroMart customer support. How can I help you today?",
        voice="Pranav",
        model="timbre-v2.5",
        language="en-IN",
        output_file=audio_path,
    )

    print("TTS synthesis successful!")
    print("Audio saved to:", audio_path)
    print("File exists:", audio_path.exists())
    print("Returned audio bytes:", len(result))

except Exception as error:
    print("TTS test failed.")
    print(type(error).__name__ + ":", error)
