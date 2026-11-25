from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"

EMBEDDINGS_FILE = DATA_DIR / "embeddings.npy"
CHUNKS_FILE = DATA_DIR / "chunks.json"

EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
TOP_K = 4 

CLAUDE_MODEL = "claude-haiku-5-5"