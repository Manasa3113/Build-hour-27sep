import os
import ssl

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
PREVIEW_FILE = "data/embeddings_preview.txt"


def main():
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )

    count = collection.count()
    print(f"Collection count: {count}")

    results = collection.get(
        include=["embeddings", "documents", "metadatas"],
        limit=5,
    )

    with open(PREVIEW_FILE, "w", encoding="utf-8") as f:
        f.write(f"Embeddings Preview - First 5 vectors (first 10 dimensions each)\n")
        f.write(f"Model: {EMBED_MODEL}\n")
        f.write(f"Total vectors in collection: {count}\n")
        f.write(f"Dimensions per vector: {len(results['embeddings'][0])}\n")
        f.write("=" * 80 + "\n\n")

        for i in range(len(results["ids"])):
            vec = results["embeddings"][i]
            doc = results["documents"][i]
            meta = results["metadatas"][i]
            first_10 = vec[:10]

            f.write(f"Vector {i + 1} (id: {results['ids'][i]})\n")
            f.write(f"  Scheme: {meta.get('scheme_name', 'N/A')}\n")
            f.write(f"  Source: {meta.get('source_url', 'N/A')}\n")
            f.write(f"  First 10 dims: {first_10}\n")
            f.write(f"  Text preview: {doc[:150]}{'...' if len(doc) > 150 else ''}\n")
            f.write("\n")

    print(f"Preview saved to: {PREVIEW_FILE}")


if __name__ == "__main__":
    main()
