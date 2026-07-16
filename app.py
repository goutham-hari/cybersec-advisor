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
import re
import threading
import webbrowser
from flask import Flask, request, jsonify, render_template
import chromadb
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

DB_PATH = "./chroma_db"
COLLECTION_NAME = "cybersec_books"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
TOP_K = 6              # final number of chunks sent to the LLM
CANDIDATES_PER_METHOD = 20  # how many each of vector/BM25 contribute before fusion
RRF_K = 60              # standard Reciprocal Rank Fusion constant


def tokenize(text):
    """Simple lowercase word tokenizer for BM25 (good enough for technical text)."""
    return re.findall(r"[a-z0-9][a-z0-9\-_.]*", text.lower())

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

# ---- Build BM25 keyword index from everything currently in Chroma ----
# Rebuilt fresh each time the app starts, so it always matches the vector
# store without needing a separate persistence step.
print("Building BM25 keyword index...")
_bm25_ids = []
_bm25_docs = []
_bm25_metas = []
_bm25 = None

_all = collection.get(include=["documents", "metadatas"])
if _all and _all.get("ids"):
    _bm25_ids = _all["ids"]
    _bm25_docs = _all["documents"]
    _bm25_metas = _all["metadatas"]
    tokenized_corpus = [tokenize(d) for d in _bm25_docs]
    _bm25 = BM25Okapi(tokenized_corpus)
    print(f"BM25 index built over {len(_bm25_docs)} chunks.")
else:
    print("Knowledge base is empty — ingest some books first.")

_id_to_pos = {cid: i for i, cid in enumerate(_bm25_ids)}

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY not set. Set it before asking questions.")
else:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel(
    "gemini-3.1-flash-lite",
    system_instruction=SYSTEM_PROMPT,
) if api_key else None

# ---- Conversation memory ----
# A single ongoing chat session, kept in memory only (resets when the server
# restarts, or when the user clicks "New conversation" in the UI). This lets
# follow-up questions like "explain more about that" work, since Gemini's
# chat session automatically carries prior turns as context.
chat_session = None


def get_chat_session():
    global chat_session
    if chat_session is None:
        chat_session = model.start_chat(history=[])
    return chat_session


def retrieve_vector(question, k):
    """Semantic (embedding-based) retrieval. Good for meaning/paraphrase matches."""
    query_embedding = embedder.encode([question]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=k)
    ids = results.get("ids", [[]])[0]
    return ids  # ranked list of chunk ids, best first


def retrieve_bm25(question, k):
    """Keyword (BM25) retrieval. Good for exact strings: CVE IDs, flags, function names."""
    if _bm25 is None:
        return []
    scores = _bm25.get_scores(tokenize(question))
    ranked_positions = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    top_positions = [i for i in ranked_positions[:k] if scores[i] > 0]
    return [_bm25_ids[i] for i in top_positions]  # ranked list of chunk ids, best first


def reciprocal_rank_fusion(rank_lists, k=RRF_K):
    """
    Merge multiple ranked lists of chunk ids into one combined ranking.
    Each list contributes 1/(k + rank) to every id it contains; ids that
    appear in both lists accumulate score from each, naturally boosting
    chunks both retrieval methods agree on.
    """
    scores = {}
    for rank_list in rank_lists:
        for rank, chunk_id in enumerate(rank_list):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)


def retrieve(question, k=TOP_K):
    """
    Hybrid retrieval: run vector search and BM25 keyword search in parallel,
    then merge with Reciprocal Rank Fusion. This catches both semantic
    matches (vector) and exact technical strings like CVE IDs or command
    flags (BM25) that embeddings alone can miss.
    """
    vector_ids = retrieve_vector(question, CANDIDATES_PER_METHOD)
    bm25_ids = retrieve_bm25(question, CANDIDATES_PER_METHOD)

    fused_ids = reciprocal_rank_fusion([vector_ids, bm25_ids])[:k]

    chunks = []
    for chunk_id in fused_ids:
        pos = _id_to_pos.get(chunk_id)
        if pos is None:
            continue
        meta = _bm25_metas[pos]
        chunks.append({
            "text": _bm25_docs[pos],
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

    # The system prompt is already attached to the model via system_instruction,
    # so each turn only needs the retrieved context + the new question. Prior
    # turns are carried automatically by the chat session.
    turn_message = f"=== RETRIEVED CONTEXT ===\n{context_str}\n\n=== QUESTION ===\n{question}"

    try:
        chat = get_chat_session()
        response = chat.send_message(turn_message)
        answer = response.text
    except Exception as e:
        return jsonify({"error": f"Gemini API error: {str(e)}"}), 500

    sources = [{"book": c["book"], "page": c["page"]} for c in chunks]

    return jsonify({"answer": answer, "sources": sources})


@app.route("/api/reset", methods=["POST"])
def reset():
    """Start a fresh conversation, discarding prior turns' memory."""
    global chat_session
    chat_session = None
    return jsonify({"status": "reset"})


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
