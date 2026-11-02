# LLM Stage Instructions

## Overview

The pipeline has 5 stages. Stages 2 and 4 require a Gemini API key (or other LLM).

**Completed stages (no API key needed):**
- ✅ Stage 1: Candidate extraction
- ✅ Stage 3: Resolve & filter (uses Open Library API, no key needed)
- ✅ Stage 5: Prepare site data

**Pending stages (require GEMINI_API_KEY):**
- ⏳ Stage 2: LLM extraction
- ⏳ Stage 4: Generate cards

## Running the LLM Stage Locally

### Prerequisites

1. Get a free Gemini API key at https://aistudio.google.com
2. Set environment variable:

```bash
export GEMINI_API_KEY=your_key_here
```

Or create a `.env` file:

```bash
echo "GEMINI_API_KEY=your_key_here" > .env
```

### Stage 2: LLM Extraction

Extract book titles, authors, and stance from candidates:

```bash
python3 pipeline/02_llm_extract.py
```

**Input:** `data/candidates.parquet` (392,831 comments)  
**Output:** `data/extracted_books.json` + `pipeline/cost.json`  
**Duration:** ~1-2 hours (batched, cached)  
**Cost:** ~$1-5 (Gemini 2.0 Flash)

The script:
- Processes 20 comments per API call
- Caches all responses in `data/llm_cache/`
- Tracks token usage and estimated cost
- Returns JSON: `{comment_id: {books: [{title, author, stance, why, quote}]}}`

### Stage 4: Generate Cards

Create summaries and metadata for each book:

```bash
python3 pipeline/04_generate_cards.py
```

**Input:** `data/filtered_books.json`  
**Output:** `data/final_books.json`  
**Duration:** ~5-15 minutes  
**Cost:** ~$0.10-1.00

The script:
- One API call per book
- Generates: summary (2 sentences), why_hn (1 sentence), level, kind, topics
- Assigns categories based on topics

## Sample Data

For development, a sample of 4 books has been created in:
- `data/sample_extracted_books.json` (LLM extraction sample)

To use the sample data and run the rest of the pipeline:

```bash
# Copy sample to main file
cp data/sample_extracted_books.json data/extracted_books.json

# Run stages 3-5
python3 pipeline/03_resolve_and_filter.py
python3 pipeline/04_generate_cards.py  # Skip if no API key
python3 pipeline/05_prepare_site_data.py
```

## Full Pipeline Command

With API key:

```bash
make data
```

Without API key (using samples):

```bash
make extract  # Already done
cp data/sample_extracted_books.json data/extracted_books.json
make resolve site-data
```

## Expected File Sizes

- `data/candidates.parquet`: 201 MB (392k comments)
- `data/extracted_books.json`: ~50-100 MB (depends on how many books found)
- `data/filtered_books.json`: ~5-10 MB (after filtering)
- `data/final_books.json`: ~8-15 MB (with cards)
- `site/data/books.json`: ~1-2 MB (optimized for web)

## Caching

Both LLM scripts cache responses to minimize cost:
- Stage 2: `data/llm_cache/batch_*.json`
- Stage 4: Cached within `data/final_books.json`

Re-running with the same input is nearly free.

## Notes

- The candidate file (201 MB) is kept in the repo since it's under 300 MB
- LLM cache files are gitignored
- Real LLM outputs will be committed once generated
