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
from chains import check_guardrails

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "hdfc_faq"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 6

QUESTIONS = [
    "What is the expense ratio of HDFC Large Cap Fund?",
    "What is the lock-in period for HDFC ELSS Tax Saver Fund?",
    "What is the minimum SIP amount for HDFC Equity Fund?",
    "What is the exit load for HDFC Small Cap Fund?",
    "How do I download my capital gains statement?",
    "What is the riskometer rating for HDFC Balanced Advantage Fund?",
    "Should I invest in HDFC Large Cap Fund?",
    "Which is better: HDFC Large Cap or HDFC Flexi Cap?",
    "What is the weather like today?",
]


def main():
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )
    print(f"Collection: {collection.count()} chunks\n")

    for q in QUESTIONS:
        print(f"{'=' * 70}")
        print(f"Q: {q}")

        refusal = check_guardrails(q)
        if refusal:
            print(f"  [GUARDRAIL] Refused (opinionated/off-topic)")
            print()

        results = collection.query(query_texts=[q], n_results=TOP_K)
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]

        print(f"  Retrieved {len(docs)} chunks:")
        for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists), 1):
            scheme = meta.get("scheme_name", "N/A")
            print(f"    [{i}] score={dist:.4f} | {scheme}")
            print(f"        {doc[:120]}{'...' if len(doc) > 120 else ''}")
        print()


if __name__ == "__main__":
    main()
