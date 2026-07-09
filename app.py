"""
app.py — CyberSec Advisor web UI (local, free, runs on modest hardware)

Setup:
    pip install flask pymupdf sentence-transformers chromadb google-generativeai
    export GEMINI_API_KEY="your-key-here"

Run:
    python app.py
Then open http://127.0.0.1:5000 in your browser.

You still use ingest.py separately to add books to the knowledge base
(chroma_db). This app just serves the chat interface on top of it.
"""

import os
import threading
import webbrowser
from flask import Flask, request, jsonify, render_template
import chromadb
import google.generativeai as genai
from sentence_transformers import SentenceTransformer

DB_PATH = "./chroma_db"
COLLECTION_NAME = "cybersec_books"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
TOP_K = 6

SYSTEM_PROMPT = """You are CyberSec Advisor, an expert-level cybersecurity assistant for security
professionals, researchers, students, and engineers. Your knowledge spans offensive
security (pentesting, red teaming, exploit development, malware analysis), defensive
security (blue team, SOC operations, incident response, threat hunting),
architecture (network security, cloud security, zero trust, cryptography),
governance (risk, compliance, frameworks like NIST/ISO 27001/CIS), and secure
software development (SAST/DAST, secure coding, threat modeling).

Behavior:
- Answer technical questions directly and in depth. Assume the user is a competent
  professional working in an authorized context (their own systems, a lab, a CTF,
  or an engagement they're contracted for) unless they say otherwise.
- Explain mechanisms, not just definitions.
- Use concrete examples: commands, code, config snippets.
- Compare tradeoffs when multiple approaches exist.
- Cite the book/chapter/page provided in the context below when you use it.
- If the retrieved context doesn't cover the question, say so plainly and answer
  from general knowledge instead, noting that it isn't from the book corpus.
- Do not help with attacks against a named real-world target, system, or
  organization when there's no indication of authorization.

Below is retrieved context from the user's book library relevant to their question.
Use it as your primary source when relevant.
"""

app = Flask(__name__)

# ---- Load models / DB once at startup ----
print("Loading embedding model...")
embedder = SentenceTransformer(EMBED_MODEL)

print("Connecting to local knowledge base...")
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(COLLECTION_NAME)

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY not set. Set it before asking questions.")
else:
    genai.configure(api_key=api_key)

from google.generativeai.types import HarmCategory, HarmBlockThreshold

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

model = genai.GenerativeModel(
    "gemini-3.1-flash-lite",
    safety_settings=safety_settings,
) if api_key else None

# Keep simple in-memory conversation history (resets on server restart)
conversation_history = []


def retrieve(question, k=TOP_K):
    query_embedding = embedder.encode([question]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=k)

    chunks = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    for doc, meta in zip(docs, metas):
        chunks.append({
            "text": doc,
            "book": meta.get("book"),
            "page": meta.get("page"),
        })
    return chunks


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/ask", methods=["POST"])
def ask():
    if model is None:
        return jsonify({"error": "GEMINI_API_KEY is not set on the server."}), 500

    data = request.get_json()
    question = (data or {}).get("question", "").strip()
    if not question:
        return jsonify({"error": "Empty question."}), 400

    chunks = retrieve(question)
    context_str = "\n\n---\n\n".join(
        f"[{c['book']}, p.{c['page']}]\n{c['text']}" for c in chunks
    ) if chunks else "(no relevant chunks found in knowledge base)"

    full_prompt = f"{SYSTEM_PROMPT}\n\n=== RETRIEVED CONTEXT ===\n{context_str}\n\n=== QUESTION ===\n{question}"

    try:
        response = model.generate_content(full_prompt)
        answer = response.text
    except Exception as e:
        return jsonify({"error": f"Gemini API error: {str(e)}"}), 500

    sources = [{"book": c["book"], "page": c["page"]} for c in chunks]

    return jsonify({"answer": answer, "sources": sources})


def open_browser_window():
    """Open the UI in its own browser window (not just a new tab)."""
    url = "http://127.0.0.1:5000"
    try:
        # Try to force a dedicated app-style window in Chrome/Edge/Brave.
        chrome_path = None
        for candidate in [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe %s",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe %s",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome %s",
            "/usr/bin/google-chrome %s",
        ]:
            if "%s" in candidate:
                exe = candidate.split(" %s")[0]
                if os.path.exists(exe):
                    chrome_path = candidate
                    break
        if chrome_path:
            webbrowser.get(chrome_path).open(f"--new-window {url}")
        else:
            webbrowser.open_new(url)
    except Exception:
        webbrowser.open_new(url)


if __name__ == "__main__":
    # Give the server a moment to start before opening the browser.
    threading.Timer(1.0, open_browser_window).start()
    app.run(debug=False, port=5000, use_reloader=False)
