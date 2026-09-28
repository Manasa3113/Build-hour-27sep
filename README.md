# HDFC Mutual Fund FAQ Assistant

A facts-only RAG chatbot that answers mutual fund scheme queries using only official public sources (Groww pages for HDFC AMC schemes).

## Scope

- **AMC:** HDFC Mutual Fund
- **Schemes:** 5 (Large Cap, Flexi Cap, ELSS, Small Cap, Balanced Advantage)
- **Sources:** 5 Groww public pages only
- **Answers:** Facts only, max 3 sentences, one source link per answer

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.10+ |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (local) |
| Vector DB | ChromaDB (persistent, local) |
| LLM | Groq API |
| Framework | LangChain |
| UI | Streamlit |
| HTML Parsing | requests + BeautifulSoup4 |

## Project Structure

```
grow-bot/
├── .env                     # GROQ_API_KEY (gitignored)
├── .gitignore
├── requirements.txt
├── config.py                # Loads env vars via python-dotenv
├── ingest.py                # Fetch + chunk source pages
├── embed_store.py           # Embed chunks + store in ChromaDB
├── chains.py                # Guardrails + RAG chain
├── prompts.py               # System prompt template
├── memory.py                # Conversation memory (last 10 messages)
├── query_cli.py             # CLI for testing queries
├── test_retrieval.py        # Retrieval test script
├── search_chunks.py         # Quick chunk search utility
├── preview_embeddings.py    # Embedding preview generator
├── chroma_db/               # Persisted ChromaDB (gitignored)
├── data/
│   ├── raw/                 # Raw text from each source page
│   └── chunks/
│       └── chunks.txt       # All chunks with metadata
├── docs/
│   ├── PRD.md
│   ├── architecture.md
│   └── implementation.md
└── README.md
```

## Setup

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add Groq API key
copy .env.example .env
# Edit .env and paste your Groq API key

# 4. Run ingestion (once)
py ingest.py
py embed_store.py

# 5. Test retrieval
py test_retrieval.py

# 6. Test with LLM (interactive)
py query_cli.py
```

## Known Limits

- Only 5 schemes, 1 AMC, 5 public pages — not comprehensive
- Groww pages may not have all facts (some data only in factsheets/KIM)
- No real-time NAV, no transaction processing, no portfolio tracking
- Groq API dependency (rate limits, availability)
- Chunking may miss some tabular data
- No multi-turn conversation memory in CLI (stateless per query)

## Sources

1. https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth
2. https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth
3. https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth
4. https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth
5. https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth
