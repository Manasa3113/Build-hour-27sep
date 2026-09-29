import os
import re
import ssl

os.environ["HF_HUB_DISABLE_XET"] = "1"

ssl._create_default_https_context = ssl._create_unverified_context

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHUNKS_FILE = "data/chunks/chunks.txt"
CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "hdfc_faq"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def parse_chunks_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        r"--- Chunk \d+ ---\n"
        r"Scheme: (.+?)\n"
        r"Category: (.+?)\n"
        r"Source: (.+?)\n"
        r"Chunk Index: (\d+)\n"
        r"Char Count: (\d+)\n"
        r"\n(.*?)(?=\n--- Chunk \d+ ---|\Z)",
        re.DOTALL,
    )

    chunks = []
    for m in pattern.finditer(content):
        chunks.append(
            {
                "scheme_name": m.group(1).strip(),
                "category": m.group(2).strip(),
                "source_url": m.group(3).strip(),
                "chunk_index": int(m.group(4)),
                "char_count": int(m.group(5)),
                "text": m.group(6).strip(),
            }
        )
    return chunks


def main():
    chunks = parse_chunks_file(CHUNKS_FILE)
    print(f"Parsed {len(chunks)} chunks from {CHUNKS_FILE}")

    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {
            "source_url": c["source_url"],
            "scheme_name": c["scheme_name"],
            "category": c["category"],
            "chunk_index": c["chunk_index"],
        }
        for c in chunks
    ]

    BATCH = 50
    for start in range(0, len(chunks), BATCH):
        end = start + BATCH
        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"  Embedded + stored chunks {start}-{end - 1}")

    print(f"\nCollection '{COLLECTION_NAME}' count: {collection.count()}")
    print(f"Persisted to: {CHROMA_DIR}/")


if __name__ == "__main__":
    main()
