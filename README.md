# ZentroMart Customer Support Agent

ZentroMart is an AI-powered customer support assistant developed as a capstone project for an external GenAI course. It explores how large language models (LLMs), Retrieval-Augmented Generation (RAG), and speech technologies can be combined to build a customer support system.

The project uses Google's Gemini API for generating responses, a knowledge base for answering company-related questions, Gnani.ai for speech processing, and Flask for a browser-based interface.

## Repository

**Public GitHub Repository:**  
https://github.com/jinacodes/ZentroMart-Customer-Support-Agent

Clone the repository using the commands below:

```bash
git clone https://github.com/jinacodes/ZentroMart-Customer-Support-Agent.git
cd ZentroMart-Customer-Support-Agent
```

## Features

- **Basic LLM responses:** Answer customer questions using Google's Gemini API.
- **Retrieval-Augmented Generation (RAG):** Retrieve relevant information from knowledge base documents to help answer customer queries.
- **Conversational assistant:** Handle interactive text-based conversations.
- **Order support tools:** Use sample customer and order data for customer-support workflows.
- **Voice interaction:** Convert customer speech into text and generate spoken responses.
- **Audio conversion:** Convert laptop recordings from `.m4a` to WAV format.
- **JSON results:** Save audio transcripts, assistant responses, and retrieved document evidence.
- **Web interface:** Interact with the assistant through a Flask application.

## Technologies Used

- Python
- Google Gemini API (`google-genai`)
- Retrieval-Augmented Generation (RAG)
- Flask
- Gnani.ai speech-to-text (STT) and text-to-speech (TTS)
- FFmpeg through `imageio-ffmpeg`
- CSV and Markdown files

## Project Workflow

The project is organized into several stages:

1. **Step 1 — Basic LLM:** Generate responses using Gemini.
2. **Step 2 — RAG:** Use knowledge base documents to answer customer questions.
3. **Step 3 — Conversation Agent:** Provide an interactive text-based customer-support conversation.
4. **Voice Pipeline:** Transcribe customer audio, generate a response, save a JSON result, and create a spoken reply.
5. **Web Interface:** Provide a browser-based way to interact with the assistant.

## Getting Started

### Prerequisites

- Python installed on your computer.
- API credentials for the services used by the features you want to run.
- Internet access for API requests.

### 1. Clone the repository

```bash
git clone https://github.com/jinacodes/ZentroMart-Customer-Support-Agent.git
cd ZentroMart-Customer-Support-Agent
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

Create a local `.env` file by copying the provided `.env.example` file.

**On Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**On macOS/Linux:**

```bash
cp .env.example .env
```

Open the newly created `.env` file and add your own API credentials:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GNANI_API_KEY=your_gnani_api_key_here
REFERENCE_DATE=2026-10-20
DEFAULT_LANGUAGE=en-IN
```

Replace the placeholder API key values with your actual credentials. Keep your `.env` file private and never upload it to GitHub. The `.env.example` file is provided as a configuration template.

## Running the Project

### Step 1: Basic LLM

```bash
python src/step1_basic_llm.py
```

### Step 2: RAG

```bash
python src/step2_rag.py
```

### Step 3: Interactive conversation

```bash
python src/step3_conversation.py
```

Type a question when prompted. Enter `exit` or `quit` to end the conversation.

### Audio Conversion

Create an `input_audio` folder in the project root if it does not already exist. Place your `.m4a` recordings inside it and run:

```bash
python convert_audio.py
```

Converted WAV files are saved in `input_audio_wav/`.

### Voice Pipeline

Run the pipeline on a folder containing `.wav` or `.mp3` files:

```bash
python run.py input_audio_wav
```

The pipeline saves JSON results in `outputs/results/` and generated voice replies in `outputs/voice_replies/`.

### Web Interface

Run:

```bash
python web_page.py
```

Open the local URL printed in the terminal to use the web interface.

## Project Documentation

- `DATASET_README.md` — Dataset information and instructions.
- `DATA_DICTIONARY.md` — Description of dataset fields.
- `TESTING.md` — Testing notes.
- `CHANGELOG.md` — Project changes.
- `ZIP_SCHEMA.md` — Dataset or archive structure.

## Notes

This project is intended for learning and demonstration. It uses sample customer-support data and depends on external API services for AI and speech functionality. Results may vary depending on API availability and the quality of the input audio.