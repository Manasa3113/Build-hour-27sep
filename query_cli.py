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
from langchain_groq import ChatGroq

from config import GROQ_API_KEY, GROQ_MODEL
from chains import check_guardrails, format_context
from prompts import INSUFFICIENT_CONTEXT_MESSAGE, build_prompt
from memory import ConversationMemory

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "hdfc_faq"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 4


def main():
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set. Add it to .env file.")
        return

    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )
    print(f"Connected to ChromaDB: {collection.count()} chunks available")

    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0,
    )

    print(f"Using model: {GROQ_MODEL}")
    print("Type 'quit' to exit, 'clear' to reset memory\n")

    memory = ConversationMemory(max_messages=10)

    while True:
        question = input("Question: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break
        if question.lower() == "clear":
            memory.clear()
            print("[Memory cleared]\n")
            continue
        if not question:
            continue

        refusal = check_guardrails(question)
        if refusal:
            print(f"\n[GUARDRAIL] Opinionated query detected")
            print(f"Answer: {refusal}\n")
            memory.add_user_message(question)
            memory.add_assistant_message(refusal)
            continue

        # Rewrite follow-up questions using conversation context
        if len(memory.messages) > 0:
            history = memory.format_for_rewrite()
            rewrite_prompt = (
                "Given the following conversation history, rewrite the latest question "
                "to be a standalone question that resolves any pronouns or references. "
                "If the question is already standalone, return it unchanged.\n\n"
                f"History:\n{history}\n\n"
                f"Latest question: {question}\n\n"
                "Standalone question:"
            )
            rewrite_response = llm.invoke(rewrite_prompt)
            rewritten = rewrite_response.content if hasattr(rewrite_response, "content") else str(rewrite_response)
            rewritten = rewritten.strip().strip('"')
            if rewritten and rewritten.lower() != question.lower():
                print(f"[Rewritten] {question} -> {rewritten}")
                question = rewritten

        results = collection.query(
            query_texts=[question],
            n_results=TOP_K,
        )

        docs = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        print(f"\n--- Retrieved {len(docs)} chunks ---")
        for i, (doc, meta, dist) in enumerate(zip(docs, metadatas, distances), 1):
            print(f"\n[Chunk {i}] score={dist:.4f}")
            print(f"  Scheme: {meta.get('scheme_name', 'N/A')}")
            print(f"  Source: {meta.get('source_url', 'N/A')}")
            print(f"  Text: {doc[:200]}{'...' if len(doc) > 200 else ''}")

        if not docs:
            print(f"\nAnswer: {INSUFFICIENT_CONTEXT_MESSAGE}\n")
            continue

        context = format_context_from_results(docs, metadatas)
        from datetime import date
        today = date.today().strftime("%Y-%m-%d")
        prompt = build_prompt(question, context, today)

        print(f"\n--- Sending to Groq LLM ---")
        response = llm.invoke(prompt)
        answer_text = response.content if hasattr(response, "content") else str(response)

        source = metadatas[0].get("source_url", "") if metadatas else ""

        print(f"\n=== Answer ===")
        print(answer_text)
        if source:
            print(f"\nSource: {source}")
        print()

        memory.add_user_message(question)
        memory.add_assistant_message(answer_text)


def format_context_from_results(docs, metadatas):
    parts = []
    for i, (doc, meta) in enumerate(zip(docs, metadatas), 1):
        source = meta.get("source_url", "")
        parts.append(f"[Chunk {i}] Source: {source}\n{doc}")
    return "\n\n".join(parts)


if __name__ == "__main__":
    main()
