
# TechRAGBot (RagBot)

A small Retrieval-Augmented-Generation (RAG) demo focused on tech news with speech emotion detection and a Streamlit chat UI (370 lines).

## Overview

- **Purpose:** Collect recent technology articles, embed them, and answer user questions using those retrieved contexts. It also accepts audio input, transcribes it, detects user emotion, and uses that metadata when generating answers.

- **Main interfaces:**
	- A Streamlit front-end (`app.py`) for chat and audio input.
	- A RAG backend (`store.py`) exposing a `/query` endpoint.
	- A speech/emotion FastAPI service (`speechapi.py`) exposing a `/speech` endpoint.

## Quick Start

1. Create a Python 3.10+ virtual environment and activate it.
2. Install dependencies (examples — adapt as needed):

```bash
pip install streamlit requests feedparser beautifulsoup4 fastapi uvicorn sentence-transformers numpy faiss-cpu whisper openai scipy scikit-learn keras nltk tiktoken pydantic
```

3. Set your OpenAI API key environment variable used by `store.py` (If you're not able to provide a key, message owner for a key...):

```bash
# Windows PowerShell
$env:OPEN_API_KEY = "your_api_key_here"
```

4. Start the backend services (examples):

```bash
# RAG API (port 8001)
uvicorn store:app --reload --port 8001

# Speech & emotion API (port 8000)
uvicorn speechapi:app --reload --port 8000

# Streamlit UI
streamlit run app.py
```

Notes: `speechapi.py` uses `textrecog.py` (which relies on `textrecogitems/` model files). `store.py` builds an in-memory FAISS index at startup by scraping feeds.

## File summaries

- [app.py](app.py): Streamlit chat UI. Sends text queries to `/query` and uploads audio to `/speech`. Stores chat history in `st.session_state` and animates assistant responses.

- [feedparsing.py](feedparsing.py): Fetches a list of technology RSS feeds, requests each article page, extracts paragraph text via BeautifulSoup, and returns a list of article dicts.

- [store.py](store.py): Core RAG backend. Uses `feedparsing.fetch_articles()` to gather articles, tokenises and chunks text via `tokenisation.chunk_text()`, embeds chunks using `sentence-transformers` (`all-MiniLM-L6-v2`), stores vectors in a FAISS index, and exposes a FastAPI `/query` endpoint that retrieves relevant chunks and calls the OpenAI Chat Completions API to generate answers. Important env var: `OPEN_API_KEY`.

- [speechapi.py](speechapi.py): FastAPI endpoint to accept uploaded audio files, saves them temporarily, transcribes via `TextRecogApp` in `textrecog.py`, detects emotion, and returns `text`, `emotion`, and `confidence`.

- [textrecog.py](textrecog.py): Handles speech-to-text and emotion recognition. Loads:
	- `textrecogitems/CountVectorizer.pkl` (CountVectorizer)
	- `textrecogitems/encoder.pkl` (label encoder)
	- `textrecogitems/stt_model.h5` (Keras model for emotion probs)
	- Whisper model (`small`) for transcription
	It preprocesses text, predicts emotion labels and confidences, and returns structured results.

- [tokenisation.py](tokenisation.py): Tokeniser and `chunk_text()` helper (using `tiktoken`) to split long article text into overlapping chunks for embedding.

- `textrecogitems/`: Directory containing model artifacts used by `textrecog.py` (CountVectorizer.pkl, encoder.pkl, stt_model.h5). Keep these files in place for speech/emotion features.

- `praveengovi/emotions-dataset-for-nlp/`: Included dataset files used to train emotion models (not required to run inference but useful for retraining).

## Important notes 

- The FAISS index in `store.py` is built at import time by scraping feeds — this may take time and requires network access. Consider persisting the index for quicker restarts.
- The OpenAI model name used in `store.py` is `gpt-4o-mini` in the code; ensure your API key has access or change to a model you can use.
- `whisper`, `sentence-transformers`, and model downloads may require significant disk space and time on first run.
- `faiss` installation differs between platforms; if `faiss-cpu` cannot be installed via pip on Windows, use a compatible build or run on Linux.

## Development tips

- For local iteration, run `store.py` and `speechapi.py` with `uvicorn --reload` so code changes pick up automatically.
- Consider saving the FAISS index and `docs` metadata to disk after building so startup is faster.

TechRAGBot is a lightweight Retrieval-Augmented Generation demo that scrapes tech news feeds, embeds article chunks with SentenceTransformers + FAISS, and answers user queries with context-aware LLM responses. It supports audio input with Whisper transcription and an emotion classifier to provide richer conversational context.

