import json 
import re
import numpy as np

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

from chatbot_rag.config import (
    CHUNK_OVERLAP, CHUNK_SIZE, CHUNKS_FILE, DATA_DIR,
    EMBEDDING_MODEL_NAME, EMBEDDINGS_FILE
)

def load_pdf(path) -> list[dict]: 
    reader = PdfReader(path)
    pages = []

    for i, page in enumerate(reader.pages, start = 1):
        text = page.extract_text() or ""
        text = re.sub(r"\s+", " ", text).strip()

        if text:
            pages.append({"text": text, "page": i, "source": path.name})

    return pages

def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:

    chunks = []
    start = 0

    while start < len(text):

        end = min(start + size, len(text))

        if end < len(text):
            last_space = text.rfind(" ", start, end)
            if last_space > start:
                end = last_space

        chunks.append(text[start:end].strip())

        if end == len(text):
            break

        start = max(end - overlap,  start + 1)

    return [c for c in chunks if c]

def build_index() -> None : 
    pdfs = sorted(DATA_DIR.glob("*.pdf"))

    if not pdfs:
        raise SystemExit(f"Nenhum PDF encontrado em {DATA_DIR}")

    chunks: list[dict] = []
    for pdf in pdfs:
        for page in load_pdf(pdf):
            for piece in chunk_text(page["text"]):
                chunks.append({
                    "text": piece,
                    "page": page["page"],
                    "source": page["source"]
                })

    print(f"{len(pdfs)} PDF(s) -> {len(chunks)} chunks")

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    textos = [c["text"] for c in chunks]

    embeddings = model.encode( 
        textos,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    np.save(EMBEDDINGS_FILE, embeddings.astype(np.float32))

    CHUNKS_FILE.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2), 
        encoding="utf-8"
    )

    print(f"Índice salvo em {DATA_DIR}")

if __name__ == "__main__":
    build_index()
