import os
import sys
import uuid
from pathlib import Path
import subprocess
import imageio_ffmpeg

from flask import Flask, jsonify, render_template, request, send_from_directory
from dotenv import load_dotenv
from gnani.tts import GnaniTTSClient
from gnani.stt import GnaniSTTClient

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT / "src"))

from step3_conversation import ZentroMartAgent

if not os.getenv("GNANI_API_KEY"):
    raise RuntimeError("GNANI_API_KEY is missing. Check your .env file.")

app = Flask(__name__, template_folder="templates")

agent = ZentroMartAgent()
tts_client = GnaniTTSClient()
stt_client = GnaniSTTClient()

AUDIO_FOLDER = ROOT / "outputs" / "web_replies"
AUDIO_FOLDER.mkdir(parents=True, exist_ok=True)

VOICE_FOLDER = ROOT / "outputs" / "web_recordings"
VOICE_FOLDER.mkdir(parents=True, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/reset", methods=["POST"])
def reset_chat():
    global agent
    agent = ZentroMartAgent()
    return jsonify({"message": "Conversation reset."})


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Please enter a question."}), 400

    try:
        answer = agent.reply(message)

        if not answer or not answer.strip():
            answer = "I'm sorry, I couldn't generate a response. Please try asking in a different way."

        filename = f"{uuid.uuid4().hex}_reply.wav"
        audio_path = AUDIO_FOLDER / filename

        tts_client.synthesize(
            text=answer,
            voice="Pranav",
            model="timbre-v2.5",
            language="en-IN",
            output_file=str(audio_path),
        )

        return jsonify({
            "transcript": message,
            "reply": answer,
            "audio_url": f"/audio/{filename}",
            "sources": agent.last_sources,
        })

    except Exception:
        app.logger.exception("Chat request failed")
        return jsonify({
            "error": "Sorry, something went wrong while processing your question."
        }), 500


@app.route("/api/transcribe", methods=["POST"])
def transcribe_voice():
    uploaded_audio = request.files.get("audio")

    if not uploaded_audio or not uploaded_audio.filename:
        return jsonify({"error": "No recording was received."}), 400

    recording_id = uuid.uuid4().hex
    content_type = uploaded_audio.mimetype or ""

    if "ogg" in content_type:
        extension = ".ogg"
    elif "mp4" in content_type:
        extension = ".mp4"
    elif "wav" in content_type:
        extension = ".wav"
    else:
        extension = ".webm"

    input_path = VOICE_FOLDER / f"{recording_id}{extension}"
    wav_path = VOICE_FOLDER / f"{recording_id}.wav"

    try:
        uploaded_audio.save(input_path)

        if input_path.suffix.lower() != ".wav":
            subprocess.run(
                [
                    imageio_ffmpeg.get_ffmpeg_exe(),
                    "-y",
                    "-i", str(input_path),
                    "-ac", "1",
                    "-ar", "16000",
                    "-c:a", "pcm_s16le",
                    str(wav_path),
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
        else:
            wav_path = input_path

        result = stt_client.transcribe(
            str(wav_path),
            language_code="en-IN",
        )

        if not result.get("success"):
            return jsonify({
                "error": "I couldn't understand the recording. Please try again."
            }), 422

        transcript = result.get("transcript", "").strip()

        if not transcript:
            return jsonify({
                "error": "No speech was detected. Please try again."
            }), 422

        # Return the transcript only. Do not generate an AI answer yet.
        return jsonify({"transcript": transcript})

    except subprocess.TimeoutExpired:
        app.logger.exception("Audio conversion timed out")
        return jsonify({"error": "Audio processing took too long."}), 500

    except Exception:
        app.logger.exception("Transcription failed")
        return jsonify({
            "error": "Couldn't transcribe your recording. Please try again."
        }), 500

    finally:
        for path in {input_path, wav_path}:
            if path.exists() and path.parent == VOICE_FOLDER:
                try:
                    path.unlink()
                except OSError:
                    app.logger.warning(
                        "Could not remove temporary recording: %s", path
                    )


@app.route("/api/voice", methods=["POST"])
def voice():
    uploaded_audio = request.files.get("audio")

    if not uploaded_audio or not uploaded_audio.filename:
        return jsonify({"error": "No voice recording was received."}), 400

    recording_id = uuid.uuid4().hex
    content_type = uploaded_audio.mimetype or ""

    if "ogg" in content_type:
        input_ext = ".ogg"
    elif "mp4" in content_type:
        input_ext = ".mp4"
    elif "wav" in content_type:
        input_ext = ".wav"
    else:
        input_ext = ".webm"

    input_path = VOICE_FOLDER / f"{recording_id}{input_ext}"
    wav_path = VOICE_FOLDER / f"{recording_id}.wav"

    try:
        uploaded_audio.save(input_path)

        # Convert the browser recording to mono, 16 kHz WAV.
        if input_path.suffix.lower() != ".wav":
            subprocess.run(
                [
                    imageio_ffmpeg.get_ffmpeg_exe(),
                    "-y",
                    "-i", str(input_path),
                    "-ac", "1",
                    "-ar", "16000",
                    "-c:a", "pcm_s16le",
                    str(wav_path),
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=60,
            )
        else:
            wav_path = input_path

        # Convert the customer's speech into text.
        result = stt_client.transcribe(
            str(wav_path),
            language_code="en-IN",
        )

        if not result.get("success"):
            return jsonify({
                "error": "Sorry, I couldn't understand that recording. Please try again."
            }), 422

        transcript = result.get("transcript", "").strip()

        if not transcript:
            return jsonify({
                "error": "I couldn't detect any speech. Please try again."
            }), 422

        # Send the transcript to the existing customer support agent.
        answer = agent.reply(transcript)

        # Generate spoken audio for the answer.
        reply_filename = f"{uuid.uuid4().hex}_reply.wav"
        reply_path = AUDIO_FOLDER / reply_filename

        tts_client.synthesize(
            text=answer,
            voice="Pranav",
            model="timbre-v2.5",
            language="en-IN",
            output_file=str(reply_path),
        )

        return jsonify({
            "transcript": transcript,
            "reply": answer,
            "audio_url": f"/audio/{reply_filename}",
            "sources": agent.last_sources,
        })

    except subprocess.TimeoutExpired:
        app.logger.exception("Voice conversion timed out")
        return jsonify({
            "error": "The recording took too long to process. Please try again."
        }), 500

    except Exception:
        app.logger.exception("Voice request failed")
        return jsonify({
            "error": "Sorry, something went wrong while processing your voice message."
        }), 500

    finally:
        # Remove the uploaded recording and converted temporary WAV.
        for path in {input_path, wav_path}:
            if path.exists() and path.parent == VOICE_FOLDER:
                try:
                    path.unlink()
                except OSError:
                    app.logger.warning("Could not remove temporary voice file: %s", path)


@app.route("/audio/<path:filename>")
def play_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)


if __name__ == "__main__":
    app.run(debug=True)
