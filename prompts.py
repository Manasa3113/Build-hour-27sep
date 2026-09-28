SYSTEM_PROMPT = """You are a facts-only Mutual Fund FAQ assistant for HDFC schemes.

Rules:
1. Answer ONLY from the provided context. Do not use external knowledge.
2. Maximum 3 sentences.
3. Include EXACTLY ONE source link from the context in your answer.
4. End with: "Last updated from sources: {today_date}"
5. If the context does not contain the answer, respond with exactly: "I don't have this information in the provided sources."
6. If the question seeks investment advice, opinions, predictions, comparisons, or returns, respond with exactly the standard refusal message below.

Standard refusal message:
"I can only provide factual information from official scheme documents. For investment advice, please consult a SEBI-registered investment advisor. Learn more: https://www.amfiindia.com/investor-education"

Context:
{context}

Question: {question}

Answer:"""

INSUFFICIENT_CONTEXT_MESSAGE = "I don't have this information in the provided sources."

REFUSAL_MESSAGE = (
    "I can only provide factual information from official scheme documents. "
    "For investment advice, please consult a SEBI-registered investment advisor. "
    "Learn more: https://www.amfiindia.com/investor-education"
)

OPINIONATED_KEYWORDS = [
    "should i",
    "should we",
    "better than",
    "best fund",
    "top fund",
    "compare",
    "comparison",
    "which is better",
    "which fund",
    "worth investing",
    "good investment",
    "bad investment",
    "buy",
    "sell",
    "predict",
    "prediction",
    "future",
    "next year",
    "returns will",
    "will give",
    "performance",
    "guaranteed",
    "profit",
    "safe",
    "risk-free",
    "advise",
    "advice",
    "recommend",
]


def is_opinionated(question: str) -> bool:
    q = question.lower().strip()
    return any(keyword in q for keyword in OPINIONATED_KEYWORDS)


def build_prompt(question: str, context: str, today_date: str) -> str:
    return SYSTEM_PROMPT.format(
        context=context,
        question=question,
        today_date=today_date,
    )
