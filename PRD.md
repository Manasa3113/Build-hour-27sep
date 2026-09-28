# Product Requirements Document: HDFC Mutual Fund FAQ RAG Chatbot

## 1. Overview

**Product Name:** HDFC MF FAQ Assistant  
**Purpose:** A facts-only RAG chatbot answering mutual fund scheme queries using only official public sources  
**Target Users:** Retail investors comparing schemes, support/content teams handling repetitive MF questions  
**Scope:** HDFC AMC — 5 schemes across categories (Large Cap, Flexi Cap, ELSS, Small Cap, Balanced Advantage)  
**Delivery:** Working prototype (app/notebook) or ≤3-min demo video + source list + README + sample Q&A

---

## 2. Problem Statement

Retail investors and support teams need quick, accurate answers to factual mutual fund questions (expense ratio, exit load, minimum SIP, lock-in, riskometer, benchmark, statement downloads). Current solutions either give generic advice, hallucinate, or lack source citations. This assistant provides **facts-only answers with one clear source link per answer**, refuses opinionated questions, and uses only public AMC/SEBI/AMFI pages.

---

## 3. Goals & Success Criteria

### Primary Goals
- Answer factual queries about 5 HDFC schemes using only 5 specified Groww public pages
- Every answer includes exactly one citation link to the source page
- Refuse opinionated/portfolio questions with polite facts-only message + educational link
- Complete RAG pipeline: Ingestion (Load→Chunk→Embed→Store) → Query (Embed→Retrieve→LLM→Answer)

### Success Metrics
- **Accuracy:** 100% of answers grounded in provided sources (no hallucination)
- **Citation:** 100% of factual answers include one valid source link
- **Refusal:** 100% of opinionated queries refused with standard message
- **Latency:** < 3s end-to-end response time
- **Constraints met:** Public sources only, no PII, no performance claims, ≤3 sentences per answer

---

## 4. User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-01 | As a retail user, I want to ask "What is the expense ratio of HDFC Large Cap Fund?" and get a factual answer with a source link | P0 |
| US-02 | As a user, I want to ask "What is the ELSS lock-in period?" and get the exact lock-in with citation | P0 |
| US-03 | As a user, I want to ask "Should I buy HDFC Small Cap Fund?" and receive a polite refusal with an educational link | P0 |
| US-04 | As a user, I want to see 3 example questions on the welcome screen to understand what I can ask | P0 |
| US-05 | As a user, I want to see "Last updated from sources: [date]" on every answer for transparency | P0 |
| US-06 | As a developer, I want the ingestion pipeline to run once and persist to ChromaDB so restarts are fast | P1 |
| US-07 | As a reviewer, I want a source list (CSV/MD) of the 5 URLs used for verification | P1 |

---

## 5. Functional Requirements

### 5.1 Corpus & Data Sources (Fixed)
| Scheme | Category | URL |
|--------|----------|-----|
| HDFC Large Cap Fund Direct Growth | Large Cap | `https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth` |
| HDFC Equity Fund Direct Growth | Flexi Cap | `https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth` |
| HDFC ELSS Tax Saver Fund Direct Plan Growth | ELSS | `https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth` |
| HDFC Small Cap Fund Direct Growth | Small Cap | `https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth` |
| HDFC Balanced Advantage Fund Direct Growth | Balanced Advantage | `https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth` |

**Allowed source types:** Factsheets, KIM/SID, scheme FAQs, fee/charges pages, riskometer/benchmark notes, statement/tax-doc guides from these pages.

### 5.2 Ingestion Pipeline
- **Load:** Fetch HTML from 5 URLs (respect robots.txt, add delays)
- **Chunk:** Agent decides strategy after inspecting data — must document chunk size, overlap, metadata kept
- **Embed:** `sentence-transformers/all-MiniLM-L6-v2` (384-dim, local, no API key)
- **Store:** ChromaDB persisted to disk (`./chroma_db/`) — ingestion runs once
- **Output:** Save all chunks to readable `.txt` file for inspection

### 5.3 Query Pipeline
- **Embed question:** Same embedding model (all-MiniLM-L6-v2)
- **Retrieve:** Top-k chunks from ChromaDB (k=4 default, tunable)
- **Generate:** Groq LLM (API key in `.env`, never committed)
- **Prompt template enforces:**
  - Answer ONLY from retrieved context
  - ≤3 sentences
  - Exactly one source link (from chunk metadata)
  - Append "Last updated from sources: [date]"
  - If context insufficient → "I don't have this information in the provided sources."
  - If opinionated → Refusal message (see 5.4)

### 5.4 Opinionated Query Refusal
**Trigger:** Questions asking for advice, predictions, comparisons, buy/sell, "should I", "better than", returns, performance
**Response:** 
> "I can only provide factual information from official scheme documents. For investment advice, please consult a SEBI-registered investment advisor. Learn more: [educational link — e.g., AMFI investor education page]"

### 5.5 UI Requirements (Tiny)
- Welcome line: "HDFC Mutual Fund FAQ Assistant — Facts only. No investment advice."
- 3 example questions (clickable or shown):
  1. "What is the expense ratio of HDFC Large Cap Fund?"
  2. "What is the lock-in period for HDFC ELSS Tax Saver Fund?"
  3. "How do I download my capital gains statement?"
- Input box + submit
- Answer display with source link (clickable)
- "Last updated from sources: [date]" below answer

---

## 6. Non-Functional Requirements

| Requirement | Specification |
|-------------|---------------|
| **Sources** | Public only (5 specified Groww pages). No third-party blogs, no backend screenshots |
| **PII** | Never accept/store PAN, Aadhaar, account numbers, OTPs, emails, phones |
| **Performance** | No return calculations/comparisons. Link to official factsheet if asked |
| **Answer length** | ≤3 sentences + citation + "Last updated from sources:" |
| **Latency** | < 3s end-to-end |
| **Persistence** | ChromaDB on disk — ingestion runs once |
| **Security** | Groq API key in `.env` only, `.env` in `.gitignore` |
| **Portability** | Single command to run (`python app.py` or `streamlit run app.py`) |

---

## 7. Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INGESTION (Run Once)                     │
│  5 Groww URLs ──▶ HTML Loader ──▶ Chunker ──▶ Embedder        │
│                                    │                             │
│                                    ▼                             │
│                          ChromaDB (persisted)                    │
│                                    │                             │
│                                    ▼                             │
│                          chunks.txt (inspectable)               │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                          QUERY (Per Request)                    │
│  User Question ──▶ Embedder ──▶ ChromaDB (top-k) ──▶ Groq LLM  │
│       │                                                         │
│       ▼                                                         │
│  Answer (≤3 sentences + 1 source link + timestamp)             │
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack (Fixed)
| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Vector DB | ChromaDB (persistent, local) |
| LLM | Groq (API key in `.env`) |
| Framework | LangChain or LlamaIndex (agent choice) |
| UI | Streamlit (simplest) or Gradio |
| HTML Fetch | `requests` + `BeautifulSoup` or `httpx` + `selectolax` |

---

## 8. Chunking Strategy (Agent Decision Required)

**Before coding, the agent must:**
1. Fetch and inspect the 5 pages
2. Propose chunking strategy with justification
3. Specify: chunk size, overlap, metadata fields per chunk
4. Save chunks to `chunks.txt` for review

**Suggested starting point:**
- Chunk size: 500 tokens (covers full paragraphs/tables)
- Overlap: 50 tokens
- Metadata per chunk: `source_url`, `scheme_name`, `category`, `section_title` (if detectable), `chunk_index`

---

## 9. Prompt Template (Core)

```python
SYSTEM_PROMPT = """You are a facts-only Mutual Fund FAQ assistant for HDFC schemes.
Rules:
1. Answer ONLY from the provided context. Do not use external knowledge.
2. Maximum 3 sentences.
3. Include EXACTLY ONE source link from the context in your answer.
4. End with: "Last updated from sources: {today_date}"
5. If context lacks the answer: "I don't have this information in the provided sources."
6. If question seeks advice/opinion/returns/comparison: Refuse with the standard message.

Standard refusal: "I can only provide factual information from official scheme documents. For investment advice, please consult a SEBI-registered investment advisor. Learn more: https://www.amfiindia.com/investor-education"

Context: {context}
Question: {question}
Answer:"""
```

---

## 10. Deliverables Checklist

| Deliverable | Format | Status |
|-------------|--------|--------|
| Working prototype | App (Streamlit/Gradio) or ≤3-min demo video | ☐ |
| Source list | `sources.md` or `sources.csv` with 5 URLs | ☐ |
| README | Setup steps, scope (AMC + 5 schemes), known limits | ☐ |
| Sample Q&A | `sample_qa.md` — 5–10 queries with answers + links | ☐ |
| Disclaimer snippet | Exact text used in UI | ☐ |
| Chunks file | `chunks.txt` — all chunks for inspection | ☐ |

---

## 11. Sample Queries for Testing

| Query | Expected Behavior |
|-------|-------------------|
| "What is the expense ratio of HDFC Large Cap Fund?" | Factual answer + source link |
| "What is the exit load for HDFC Small Cap Fund?" | Factual answer + source link |
| "What is the minimum SIP amount for HDFC Equity Fund?" | Factual answer + source link |
| "What is the lock-in period for HDFC ELSS Tax Saver Fund?" | Factual answer + source link |
| "What is the riskometer rating for HDFC Balanced Advantage Fund?" | Factual answer + source link |
| "How do I download my capital gains statement?" | Factual answer + source link |
| "Should I invest in HDFC Large Cap Fund?" | Refusal + educational link |
| "Which is better: HDFC Large Cap or HDFC Flexi Cap?" | Refusal + educational link |
| "What returns will HDFC Small Cap give next year?" | Refusal + educational link |
| "Compare expense ratios of all 5 funds" | Refusal (comparison) or individual facts if asked separately |

---

## 12. Known Limits (Document in README)

- Only 5 schemes, 1 AMC, 5 public pages — not comprehensive
- Groww pages may not have all facts (some data only in factsheets/KIM)
- No real-time NAV, no transaction processing, no portfolio tracking
- Groq API dependency (rate limits, availability)
- Chunking may miss tabular data (expense ratio tables)
- No multi-turn conversation memory (stateless per query)

---

## 13. Quick Start

```bash
# 1. Clone & setup
cd grow-bot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Add Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# 3. Run ingestion (once)
python ingest.py

# 4. Run app
streamlit run app.py
# or
python app.py
```

### `requirements.txt`
```
sentence-transformers
chromadb
langchain
langchain-community
langchain-groq
streamlit
requests
beautifulsoup4
python-dotenv
```

---

## 14. File Structure

```
grow-bot/
├── .env                 # GROQ_API_KEY (gitignored)
├── .gitignore
├── requirements.txt
├── ingest.py            # Ingestion pipeline (run once)
├── app.py               # Streamlit/Gradio app
├── chains.py            # RAG chain setup
├── prompts.py           # System prompt template
├── chroma_db/           # Persisted ChromaDB (gitignored)
├── chunks.txt           # Inspectable chunks output
├── sources.md           # 5 URLs list
├── sample_qa.md         # 5-10 sample Q&A
├── README.md            # Setup, scope, limits
└── PRD.md               # This file
```

---

## 15. Acceptance Criteria for Demo

- [ ] Ingestion runs without errors, creates `chroma_db/` and `chunks.txt`
- [ ] App loads, shows welcome line + 3 example questions
- [ ] All 5 factual sample queries return correct answers with valid source links
- [ ] All 3 opinionated sample queries return refusal message with educational link
- [ ] Every answer ≤3 sentences + "Last updated from sources:" timestamp
- [ ] No PII requested, no performance claims made
- [ ] Source list (`sources.md`) matches the 5 specified URLs
- [ ] README has setup steps, scope, known limits
- [ ] Sample Q&A file has 5–10 entries with answers + links