import os
import time
import requests
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter

SOURCES = [
    {
        "scheme_name": "HDFC Large Cap Fund Direct Growth",
        "category": "Large Cap",
        "url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
    },
    {
        "scheme_name": "HDFC Equity Fund Direct Growth",
        "category": "Flexi Cap",
        "url": "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    },
    {
        "scheme_name": "HDFC ELSS Tax Saver Fund Direct Plan Growth",
        "category": "ELSS",
        "url": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    },
    {
        "scheme_name": "HDFC Small Cap Fund Direct Growth",
        "category": "Small Cap",
        "url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    },
    {
        "scheme_name": "HDFC Balanced Advantage Fund Direct Growth",
        "category": "Balanced Advantage",
        "url": "https://groww.in/mutual-funds/hdfc-balanced-advantage-fund-direct-growth",
    },
]

CHUNK_SIZE = 300
CHUNK_OVERLAP = 30

RAW_DIR = "data/raw"
CHUNKS_FILE = "data/chunks/chunks.txt"


def fetch_html(url):
    headers = {"User-Agent": "Mozilla/5.0 (compatible; GrowBot/1.0)"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    main = soup.find("main") or soup.find("body") or soup

    parts = []

    for table in main.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if cells:
                rows.append(" | ".join(cells))
        if rows:
            parts.append("\n".join(rows))
        table.decompose()

    text = main.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    kv_labels = {
        "Expense ratio", "Min. for SIP", "Min. for Lumpsum", "Fund size (AUM)",
        "Rating", "Exit load", "Lock-in", "Minimum SIP", "Minimum Lumpsum",
        "NAV", "Category", "Risk", "Benchmark", "Inception Date",
    }

    structured_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line in kv_labels and i + 1 < len(lines):
            structured_lines.append(f"{line}: {lines[i + 1]}")
            i += 2
        else:
            structured_lines.append(line)
            i += 1

    parts.append("\n".join(structured_lines))

    return "\n".join(parts)


def sanitize_filename(name):
    return name.lower().replace(" ", "_").replace("/", "_")


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(CHUNKS_FILE), exist_ok=True)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    all_chunks = []

    for source in SOURCES:
        print(f"Fetching: {source['url']}")
        html = fetch_html(source["url"])
        text = extract_text(html)

        raw_path = os.path.join(RAW_DIR, sanitize_filename(source["scheme_name"]) + ".txt")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  Raw text saved: {raw_path} ({len(text)} chars)")

        chunks = splitter.split_text(text)
        for i, chunk_text in enumerate(chunks):
            all_chunks.append(
                {
                    "text": chunk_text,
                    "source_url": source["url"],
                    "scheme_name": source["scheme_name"],
                    "category": source["category"],
                    "chunk_index": i,
                    "char_count": len(chunk_text),
                }
            )
        print(f"  Chunks created: {len(chunks)}")

        time.sleep(1)

    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        for idx, chunk in enumerate(all_chunks, start=1):
            f.write(f"--- Chunk {idx} ---\n")
            f.write(f"Scheme: {chunk['scheme_name']}\n")
            f.write(f"Category: {chunk['category']}\n")
            f.write(f"Source: {chunk['source_url']}\n")
            f.write(f"Chunk Index: {chunk['chunk_index']}\n")
            f.write(f"Char Count: {chunk['char_count']}\n")
            f.write(f"\n{chunk['text']}\n\n")

    print(f"\nTotal chunks: {len(all_chunks)}")
    print(f"Chunks saved to: {CHUNKS_FILE}")


if __name__ == "__main__":
    main()
