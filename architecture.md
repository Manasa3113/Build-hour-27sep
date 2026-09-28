# Architecture: HDFC Mutual Fund FAQ RAG Chatbot

## 1. Components

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| **HTML Loader** | Fetches raw HTML from 5 Groww scheme pages | `requests` + `BeautifulSoup` |
| **Chunker** | Splits page content into overlapping text chunks with metadata | LangChain `RecursiveCharacterTextSplitter` |
| **Embedder** | Converts text chunks/questions into 384-dim vectors | `sentence-transformers/all-MiniLM-L6-v2` (local) |
| **Vector Store** | Persists embeddings + metadata to disk for fast similarity search | ChromaDB (`./chroma_db/`) |
| **Retriever** | Finds top-k most relevant chunks for a query | ChromaDB `similarity_search` (k=4) |
| **LLM** | Generates grounded answers from retrieved context | Groq API (`llama-3.1-8b-instant` or similar) |
| **Prompt Template** | Enforces facts-only, ≤3 sentences, 1 citation, refusal rules | Python f-string / LangChain `ChatPromptTemplate` |
| **UI** | Welcome screen, example questions, input box, answer display | Streamlit |

---

## 2. Data Flow

### 2.1 Ingestion Pipeline (Run Once)

```
5 Groww URLs
    │
    ▼
┌──────────────┐
│  LOAD        │  requests.get() → BeautifulSoup parse → extract text
│  (HTML → Text)│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  CHUNK       │  RecursiveCharacterTextSplitter
│              │  chunk_size=500, overlap=50
│              │  metadata: source_url, scheme_name, category,
│              │           section_title, chunk_index
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  EMBED       │  all-MiniLM-L6-v2 → 384-dim vectors
│              │  (local, no API key)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  STORE       │  ChromaDB persistent collection
│              │  → ./chroma_db/
│              │  + chunks.txt (human-readable dump)
└──────────────┘
```

### 2.2 Query Pipeline (Per Request)

```
User Question
    │
    ▼
┌──────────────┐
│  EMBED       │  Same model: all-MiniLM-L6-v2
│  (Question)  │  → 384-dim query vector
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  RETRIEVE    │  ChromaDB similarity search
│  (Top-k)     │  k=4 chunks + metadata
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  GENERATE    │  Groq LLM + system prompt
│  (Answer)    │  → ≤3 sentences + 1 source link
│              │  → "Last updated from sources: [date]"
│              │  → Refusal if opinionated/insufficient context
└──────┬───────┘
       │
       ▼
   Answer + Citation
```

---

## 3. Tech Stack

| Layer | Choice | Justification |
|-------|--------|---------------|
| Language | Python 3.10+ | Ecosystem fit for RAG/ML |
| Embedding Model | `sentence-transformers/all-MiniLM-L6-v2` | 384-dim, runs locally, no API key, fast |
| Vector DB | ChromaDB | Lightweight, persistent to disk, Python-native |
| LLM | Groq API | Free tier, low latency (<1s), OpenAI-compatible |
| Orchestration | LangChain | Standard RAG abstractions (loaders, splitters, chains) |
| UI | Streamlit | Simplest path to a working chat interface |
| HTML Parsing | `requests` + `BeautifulSoup4` | Simple, well-known |
| Config | `python-dotenv` | Loads `GROQ_API_KEY` from `.env` |

---

## 4. Folder Structure

```
grow-bot/
├── .env                     # GROQ_API_KEY (gitignored, never committed)
├── .gitignore               # .env, chroma_db/, __pycache__/
├── requirements.txt         # All Python dependencies
│
├── ingest.py                # Ingestion pipeline entry point (run once)
├── app.py                   # Streamlit UI entry point
├── chains.py                # RAG chain assembly (retriever + LLM + prompt)
├── prompts.py               # System prompt template (facts-only rules)
│
├── chroma_db/               # Persisted ChromaDB (auto-created, gitignored)
│   ├── <collection_uuid>/
│   │   ├── data_level0.bin
│   │   ├── header.bin
│   │   ├── length.bin
│   │   └── link_lists.bin
│   └── chroma.sqlite3
│
├── chunks.txt               # Human-readable dump of all chunks + metadata
├── sources.md               # 5 source URLs with scheme names
├── sample_qa.md             # 5–10 sample queries with expected answers
│
├── docs/
│   ├── PRD.md               # Product requirements
│   └── architecture.md      # This file
│
└── README.md                # Setup, scope, known limits
```

---

## 5. Query Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         QUERY FLOW (Per Request)                        │
│                                                                         │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐     │
│   │  User     │    │ Embed    │    │ Retrieve │    │  Generate    │     │
│   │  Question │───▶│ Question │───▶│ Top-4    │───▶│  Answer via  │     │
│   │          │    │ (MiniLM) │    │ Chunks   │    │  Groq LLM    │     │
│   └──────────┘    └──────────┘    └────┬─────┘    └──────┬───────┘     │
│                                        │                  │             │
│                                   ┌────▼─────┐    ┌──────▼───────┐     │
│                                   │ ChromaDB │    │ ≤3 sentences  │     │
│                                   │ (local   │    │ + 1 source    │     │
│                                   │  disk)   │    │   link        │     │
│                                   └──────────┘    │ + "Last       │     │
│                                                   │   updated..." │     │
│                                                   └──────┬───────┘     │
│                                                          │             │
│                                                   ┌──────▼───────┐     │
│                                                   │  Opinionated?│     │
│                                                   │  ──Yes──▶ Refusal   │
│                                                   │  ──No───▶ Answer    │
│                                                   └──────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Local embeddings (MiniLM)** | No API key, no cost, runs offline, 384-dim is sufficient for 5 pages |
| **ChromaDB on disk** | Ingestion runs once; restarts are fast; no external DB server needed |
| **Groq for LLM** | Free tier, sub-second latency, OpenAI-compatible SDK |
| **k=4 retrieved chunks** | Balances context coverage vs. token cost; tunable |
| **500-token chunks + 50 overlap** | Preserves paragraph/table boundaries; overlap prevents mid-sentence cuts |
| **Stateless (no chat history)** | Simpler, avoids PII accumulation, matches PRD scope |
| **Refusal before LLM** | Opinionated queries can be detected pre-generation to save tokens |
