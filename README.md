# CyberSec Advisor — Web UI (local, free)

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

## Notes
- Conversation history resets if you restart the server (kept simple on purpose).
- If you see "GEMINI_API_KEY is not set" in the browser, the key wasn't picked up —
  make sure you set it in the same terminal session before running `python app.py`.
- Everything here (Flask, embeddings, Chroma) runs locally and free. Only the
  final answer generation calls the Gemini API.
