# CyberSec Advisor

A local-first, retrieval-augmented chatbot for cybersecurity research and study.

CyberSec Advisor ingests your own library of security books (pentesting,
malware analysis, network defense, cryptography, governance) into a local
vector database, then answers technical questions grounded in that material
— with citations back to the specific book and page.

The entire pipeline — PDF extraction, chunking, embedding, and storage —
runs locally on modest hardware. Only the final answer-generation step
calls an external LLM API (free tier), keeping the whole project at zero
infrastructure cost.

## Features
- 📚 Ingests PDF technical references into a searchable knowledge base
- 🔍 Retrieval-augmented answers with book/page citations
- 💻 Runs locally — no paid infrastructure required
- 🌐 Clean browser-based chat interface
- 🧠 Local embeddings (no per-query embedding cost)


<img width="1920" height="1078" alt="cybersec-advisor - Google Chrome 7_31_2026 9_27_27 AM" src="https://github.com/user-attachments/assets/5e4499f8-2420-472f-8eb5-68cc23f59efd" />
<img width="1920" height="1078" alt="cybersec-advisor - Google Chrome 7_31_2026 9_28_18 AM" src="https://github.com/user-attachments/assets/894b58af-98ae-4245-8c9c-085d20f850b8" />

## Tech stack
PyMuPDF · Sentence-Transformers · ChromaDB · Flask · Gemini API

## One-time setup

```
pip install flask pymupdf sentence-transformers chromadb google-generativeai
```

Get a free Gemini API key at https://aistudio.google.com/ and set it:

Mac/Linux:
```
export GEMINI_API_KEY="paste-your-key-here"
```

Windows (Command Prompt, then reopen terminal):
```
setx GEMINI_API_KEY "paste-your-key-here"
```

## Add books to the knowledge base

Run once per PDF (same as before):
```
python ingest.py "/path/to/book.pdf" "Book Title"
```

This creates/updates a `chroma_db` folder in this same directory.

## Run the web chat UI

```
python app.py
```

Then open **http://127.0.0.1:5000** in your browser. That's your chat window —
type questions, get answers grounded in your book library with page citations
shown under each response.

## Integrated frontend setup (React + Flask)

The `CyberSec-Advisor` React app is now integrated with this Flask backend:

- Production/runtime: Flask serves `CyberSec-Advisor/dist` automatically when built.
- Fallback: if no React build exists yet, Flask still serves the legacy `templates/index.html` UI.

Build the React frontend once (or whenever UI changes):

```
cd CyberSec-Advisor
npm install
npm run build
```

Optional frontend dev mode:

```
cd CyberSec-Advisor
npm run dev
```

Vite proxies `/api/*` calls to `http://127.0.0.1:5000`, so keep `python app.py` running while developing.

## Notes
- Conversation history resets if you restart the server (kept simple on purpose).
- If you see "GEMINI_API_KEY is not set" in the browser, the key wasn't picked up —
  make sure you set it in the same terminal session before running `python app.py`.
- Everything here (Flask, embeddings, Chroma) runs locally and free. Only the
  final answer generation calls the Gemini API.
