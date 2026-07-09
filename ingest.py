"""
ingest.py
Run this once for each PDF (or loop over a folder) to add a book to your
local knowledge base. Zero cost: extraction, chunking, embedding, and
storage all run on your machine.

Usage:
    python ingest.py "/path/to/book.pdf" "Practical Malware Analysis"
"""

import sys
import os
import fitz  # PyMuPDF
import chromadb
from sentence_transformers import SentenceTransformer

# ---- CONFIG ----
DB_PATH = "./chroma_db"          # where the vector DB lives on disk
COLLECTION_NAME = "cybersec_books"
CHUNK_SIZE = 400                 # approx words per chunk
CHUNK_OVERLAP = 60               # words of overlap between chunks
EMBED_MODEL = "BAAI/bge-small-en-v1.5"  # small, free, runs on CPU

# ---- 1. Load embedding model (downloads once, then cached locally) ----
print("Loading embedding model (first run downloads ~130MB, then it's cached)...")
embedder = SentenceTransformer(EMBED_MODEL)

# ---- 2. Set up local vector DB ----
client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(COLLECTION_NAME)


def extract_text_by_page(pdf_path):
    """Return list of (page_number, text) tuples."""
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            pages.append((i + 1, text))
    doc.close()
    return pages


def chunk_text(pages, book_title):
    """
    Turn (page_number, text) list into overlapping word-based chunks,
    each tagged with the book title and page number for citation.
    """
    chunks = []
    for page_num, text in pages:
        words = text.split()
        start = 0
        while start < len(words):
            end = start + CHUNK_SIZE
            chunk_words = words[start:end]
            chunk_str = " ".join(chunk_words)
            if len(chunk_str.strip()) > 20:  # skip near-empty chunks
                chunks.append({
                    "text": chunk_str,
                    "book": book_title,
                    "page": page_num,
                })
            start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def ingest_pdf(pdf_path, book_title):
    print(f"Extracting text from: {pdf_path}")
    pages = extract_text_by_page(pdf_path)
    print(f"  {len(pages)} pages with text found.")

    print("Chunking...")
    chunks = chunk_text(pages, book_title)
    print(f"  {len(chunks)} chunks created.")

    print("Embedding chunks (this is the slow part, runs locally on CPU)...")
    texts = [c["text"] for c in chunks]
    embeddings = embedder.encode(texts, show_progress_bar=True, batch_size=32)

    print("Storing in vector DB...")
    ids = [f"{book_title}_{i}" for i in range(len(chunks))]
    metadatas = [{"book": c["book"], "page": c["page"]} for c in chunks]

    # Chroma has a max batch size per add() call, so we chunk the insert too
    BATCH = 500
    for i in range(0, len(chunks), BATCH):
        collection.add(
            ids=ids[i:i+BATCH],
            embeddings=embeddings[i:i+BATCH].tolist(),
            documents=texts[i:i+BATCH],
            metadatas=metadatas[i:i+BATCH],
        )

    print(f"Done. '{book_title}' is now searchable in the knowledge base.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('Usage: python ingest.py "/path/to/book.pdf" "Book Title"')
        sys.exit(1)

    pdf_path = sys.argv[1]
    book_title = sys.argv[2]

    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    ingest_pdf(pdf_path, book_title)
