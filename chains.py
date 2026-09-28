from datetime import date

from prompts import (
    INSUFFICIENT_CONTEXT_MESSAGE,
    REFUSAL_MESSAGE,
    build_prompt,
    is_opinionated,
)

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "hdfc_faq"
TOP_K = 4


def check_guardrails(question: str):
    if is_opinionated(question):
        return REFUSAL_MESSAGE
    return None


def format_context(chunks) -> str:
    parts = []
    for i, doc in enumerate(chunks, start=1):
        source = doc.metadata.get("source_url", "")
        parts.append(f"[Chunk {i}] Source: {source}\n{doc.page_content}")
    return "\n\n".join(parts)


def build_rag_chain(llm, retriever):
    def answer(question: str) -> dict:
        refusal = check_guardrails(question)
        if refusal:
            return {
                "answer": refusal,
                "source": "https://www.amfiindia.com/investor-education",
                "refused": True,
            }

        docs = retriever.invoke(question)
        if not docs:
            return {
                "answer": INSUFFICIENT_CONTEXT_MESSAGE,
                "source": "",
                "refused": False,
            }

        context = format_context(docs)
        today = date.today().strftime("%Y-%m-%d")
        prompt = build_prompt(question, context, today)

        response = llm.invoke(prompt)
        answer_text = response.content if hasattr(response, "content") else str(response)

        source = docs[0].metadata.get("source_url", "") if docs else ""

        return {
            "answer": answer_text,
            "source": source,
            "refused": False,
        }

    return answer
