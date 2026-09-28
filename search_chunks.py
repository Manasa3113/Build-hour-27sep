import os
import sys
import ssl

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["HF_HUB_DISABLE_XET"] = "1"
ssl._create_default_https_context = ssl._create_unverified_context

import httpx
_original_client_init = httpx.Client.__init__
def _patched_client_init(self, *args, **kwargs):
    kwargs["verify"] = False
    _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = _patched_client_init

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "hdfc_faq"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def search(query, n=10):
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    col = client.get_collection(name=COLLECTION_NAME, embedding_function=embedding_fn)
    results = col.query(query_texts=[query], n_results=n)
    for i, (doc, meta, dist) in enumerate(zip(results["documents"][0], results["metadatas"][0], results["distances"][0]), 1):
        scheme = meta.get("scheme_name", "N/A")
        print(f"[{i}] score={dist:.4f} | {scheme}")
        print(f"    {doc[:250]}")
        print()


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "expense ratio exit load lock-in SIP minimum"
    search(query)
