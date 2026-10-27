from pathlib import Path
import subprocess
import imageio_ffmpeg

# Folder containing your laptop recordings
INPUT_FOLDER = Path("input_audio")

# Store converted WAV files separately
OUTPUT_FOLDER = Path("input_audio_wav")
OUTPUT_FOLDER.mkdir(exist_ok=True)

ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

audio_files = list(INPUT_FOLDER.glob("*.m4a"))

if not audio_files:
    print("No .m4a files found in input_audio.")
else:
    for audio_file in audio_files:
        output_file = OUTPUT_FOLDER / f"{audio_file.stem}.wav"

        command = [
            ffmpeg,
            "-y",
            "-i", str(audio_file),
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "pcm_s16le",
            str(output_file),
        ]

        try:
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
            print(f"Converted: {audio_file.name} -> {output_file.name}")
        except subprocess.CalledProcessError as error:
            print(f"Failed: {audio_file.name}")
            print(error.stderr[-1000:])
