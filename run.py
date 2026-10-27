import os
import sys
import json
import argparse
from pathlib import Path

from dotenv import load_dotenv
from gnani.stt import GnaniSTTClient
from gnani.tts import GnaniTTSClient

# Find the project root and load the API key.
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

# Allow run.py to import our Step 3 agent.
sys.path.insert(0, str(ROOT / "src"))
from step3_conversation import ZentroMartAgent

# Check that the Gnani API key exists.
if not os.getenv("GNANI_API_KEY"):
    raise SystemExit("Gnani API key is missing. Check your .env file.")


def main():
    parser = argparse.ArgumentParser(
        description="Run the ZentroMart voice support agent."
    )
    parser.add_argument(
        "audio_folder",
        help="Folder containing customer audio files."
    )
    args = parser.parse_args()

    input_folder = Path(args.audio_folder)

    if not input_folder.is_dir():
        raise SystemExit(f"Audio folder not found: {input_folder}")

    audio_files = sorted(
        path for path in input_folder.iterdir()
        if path.is_file() and path.suffix.lower() in {".wav", ".mp3"}
    )

    if not audio_files:
        raise SystemExit("No WAV or MP3 files found in that folder.")

    stt_client = GnaniSTTClient()
    agent = ZentroMartAgent()
    tts_client = GnaniTTSClient()

    for audio_file in audio_files:
        print(f"\nProcessing: {audio_file.name}")

        try:
            transcript = transcribe_audio(audio_file, stt_client)
            print("Customer said:", transcript)

            answer = agent.reply(transcript)
            print("ZentroMart:", answer)

            results_folder = ROOT / "outputs" / "results"
            results_folder.mkdir(parents=True, exist_ok=True)

            result_file = results_folder / f"{audio_file.stem}_result.json"

            result_data = {
                "audio_file": audio_file.name,
                "transcript": transcript,
                "response": answer,
                "document_evidence": agent.last_sources,
            }

            with open(result_file, "w", encoding="utf-8") as file:
                json.dump(result_data, file, indent=2, ensure_ascii=False)

            print("Results saved:", result_file)

            output_folder = ROOT / "outputs" / "voice_replies"
            output_folder.mkdir(parents=True, exist_ok=True)

            audio_output = output_folder / f"{audio_file.stem}_reply.wav"

            tts_client.synthesize(
                text=answer,
                voice="Pranav",
                model="timbre-v2.5",
                language="en-IN",
                output_file=str(audio_output),
            )

            print("Voice reply saved:", audio_output)

        except Exception as error:
            print(f"Failed to transcribe {audio_file.name}: {error}")



def transcribe_audio(audio_path, stt_client):
    """Convert one customer audio file into text."""
    result = stt_client.transcribe(
        str(audio_path),
        language_code="en-IN"
    )

    if not result.get("success"):
        raise RuntimeError(f"STT failed for {audio_path.name}: {result}")

    transcript = result.get("transcript", "").strip()

    if not transcript:
        raise RuntimeError(f"No speech recognized in {audio_path.name}")

    return transcript


if __name__ == "__main__":
    main()
