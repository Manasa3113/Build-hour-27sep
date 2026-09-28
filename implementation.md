# Implementation Plan: HDFC Mutual Fund FAQ RAG Chatbot

Six phases, each with a clear verification gate before moving to the next.

---

## Phase 1: Project Setup

**Files to create:**
- `.gitignore`
- `requirements.txt`
- `.env` (template only — user fills in their key)

**What this does:**
Creates the project skeleton. `.gitignore` ensures `.env` and `chroma_db/` are never committed. `requirements.txt` pins all dependencies. `.env` holds the Groq API key locally.

**How to verify:**
- Run `pip install -r requirements.txt` — all packages install without errors.
- Confirm `.env` exists and contains `GROQ_API_KEY=your_key_here`.
- Confirm `.env` and `chroma_db/` appear in `.gitignore`.

---

## Phase 2: Loading & Chunking

**Files to create:**
- `ingest.py` (loader + chunker portion)
- `sources.md` (auto-generated or manual list of 5 URLs)

**What this does:**
Fetches HTML from the 5 Groww scheme pages using `requests` + `BeautifulSoup`. Extracts main text content (strips nav, footer, scripts). Splits text into ~500-token chunks with 50-token overlap using LangChain's `RecursiveCharacterTextSplitter`. Attaches metadata to each chunk: `source_url`, `scheme_name`, `category`, `section_title`, `chunk_index`. Writes all chunks to `chunks.txt` for human inspection.

**How to verify:**
- Run `python ingest.py` (or the loader/chunker portion).
- Open `chunks.txt` — confirm:
  - Chunks are readable, not garbled HTML.
  - Each chunk has correct metadata (right scheme name, right URL).
  - Chunk count is reasonable (expect ~30–80 chunks total across 5 pages).
  - No chunk is empty or just whitespace.
- Spot-check that key facts (expense ratio, exit load, SIP amount) appear in at least one chunk.

---

## Phase 3: Embedding & Vector Store

**Files to create:**
- `ingest.py` (embed + store portion — same file, extended)

**What this does:**
Loads `sentence-transformers/all-MiniLM-L6-v2` (downloads on first run, ~80MB). Converts each chunk's text into a 384-dim vector. Stores vectors + text + metadata in a ChromaDB persistent collection at `./chroma_db/`. Ingestion runs once; subsequent runs skip if data already exists (or can be forced to re-ingest).

**How to verify:**
- Run `python ingest.py` end-to-end.
- Confirm `./chroma_db/` directory is created with files inside.
- Run a quick Python snippet:
  ```python
  import chromadb
  client = chromadb.PersistentClient(path="./chroma_db")
  col = client.get_collection("hdfc_faq")
  print(col.count())  # should match chunk count from Phase 2
  ```
- Confirm the count matches the number of chunks in `chunks.txt`.

---

## Phase 4: Guardrails

**Files to create:**
- `prompts.py`
- `chains.py` (guardrail/routing portion)

**What this does:**
Defines the system prompt template enforcing: answer only from context, max 3 sentences, exactly one source link, "Last updated from sources: [date]" footer, insufficient-context message, and opinionated-query refusal. Implements a pre-LLM classifier that detects opinionated queries (keywords: "should I", "better than", "compare", "returns", "predict", "buy", "sell") and routes them directly to the refusal message without calling Groq.

**How to verify:**
- Unit-test the opinionated-query detector with the 3 opinionated samples from the PRD:
  - "Should I invest in HDFC Large Cap Fund?" → detected
  - "Which is better: HDFC Large Cap or HDFC Flexi Cap?" → detected
  - "What returns will HDFC Small Cap give next year?" → detected
- Confirm factual queries are NOT flagged:
  - "What is the expense ratio of HDFC Large Cap Fund?" → passes through
- Print the rendered system prompt with dummy context — confirm all 6 rules appear.

---

## Phase 5: Retrieval + LLM Answer

**Files to create:**
- `chains.py` (RAG chain assembly — retriever + LLM + prompt)

**What this does:**
Embeds the user's question with the same MiniLM model. Queries ChromaDB for top-4 most similar chunks. Concatenated chunk text becomes the context. Sends context + question + system prompt to Groq LLM. Returns the generated answer. Handles three outcomes: factual answer with citation, insufficient-context message, or refusal (from Phase 4 guardrail).

**How to verify:**
- Run each of the 6 factual sample queries from the PRD:
  - "What is the expense ratio of HDFC Large Cap Fund?"
  - "What is the exit load for HDFC Small Cap Fund?"
  - "What is the minimum SIP amount for HDFC Equity Fund?"
  - "What is the lock-in period for HDFC ELSS Tax Saver Fund?"
  - "What is the riskometer rating for HDFC Balanced Advantage Fund?"
  - "How do I download my capital gains statement?"
- For each answer, confirm:
  - It is ≤3 sentences.
  - It contains exactly one valid source link.
  - It ends with "Last updated from sources: [date]".
  - The fact is correct (cross-check against the Groww page).
- Run the 3 opinionated queries — confirm refusal message + AMFI link, no Groq call made.
- Time each query — confirm <3s end-to-end.

---

## Phase 6: UI

**Files to create:**
- `app.py`

**What this does:**
Streamlit app with: welcome line ("HDFC Mutual Fund FAQ Assistant — Facts only. No investment advice."), 3 clickable example questions, text input box, submit button, answer display with clickable source link, and "Last updated from sources: [date]" below each answer. Calls the RAG chain from Phase 5 on submit.

**How to verify:**
- Run `streamlit run app.py`.
- Confirm the page loads with the welcome line and 3 example questions visible.
- Click each example question — confirm it populates the input and returns a correct answer.
- Type a custom factual question — confirm answer + citation + timestamp.
- Type an opinionated question — confirm refusal message appears.
- Confirm the source link is clickable and opens the correct Groww page.
- Confirm no PII is requested or stored anywhere in the UI.

---

## Dependency Graph

```
Phase 1 ──▶ Phase 2 ──▶ Phase 3 ──▶ Phase 4 ──▶ Phase 5 ──▶ Phase 6
Setup      Load+Chunk  Embed+Store  Guardrails  RAG Chain   Streamlit UI
```

Each phase depends on the previous. Do not skip verification gates — a broken chunking strategy is cheaper to fix before embedding than after.
