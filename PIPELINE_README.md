# HackerShelf Data Pipeline

This pipeline extracts book recommendations from Hacker News comments and prepares data for the static site.

## Prerequisites

- Python 3.9+
- Gemini API key (get free tier at aistudio.google.com)

## Installation

```bash
pip install -r requirements.txt
```

## Run the Pipeline

### Full Pipeline (with LLM steps)

**IMPORTANT:** You need a `GEMINI_API_KEY` environment variable for steps 2 and 4.

```bash
# Set your API key
export GEMINI_API_KEY=your_key_here

# Or create a .env file:
echo "GEMINI_API_KEY=your_key_here" > .env

# Run all steps
make data
```

### Run Individual Steps

The pipeline has 5 steps:

#### 1. Extract Candidates (no API key needed)

```bash
make extract
```

Scans HN comments from 2007-present and extracts candidates with book links or book keywords.

- **Input**: Remote parquet files from `open-index/hacker-news`
- **Output**: `data/candidates.parquet`
- **Duration**: ~30-60 minutes for full history

To run a subset (e.g., 2015-2026 only):

```bash
python pipeline/01_extract_candidates.py 2015 2026
```

#### 2. LLM Extraction (**requires GEMINI_API_KEY**)

```bash
make llm
```

Uses Gemini API to extract book titles, authors, stance from candidates.

- **Input**: `data/candidates.parquet`
- **Output**: `data/extracted_books.json`, `pipeline/cost.json`
- **Duration**: Varies by candidate count (~1-2 hours for thousands)
- **Cost**: ~$0.50-5.00 depending on volume (cached, so reruns are free)

**Skip this step if running without API key.** A sample extraction will be provided.

#### 3. Resolve & Filter (no API key needed)

```bash
make resolve
```

Resolves books via Open Library and filters by HackerTube criteria (≥3 users, ≥3 months).

- **Input**: `data/candidates.parquet`, `data/extracted_books.json`
- **Output**: `data/filtered_books.json`
- **Duration**: ~10-30 minutes depending on book count

#### 4. Generate Cards (**requires GEMINI_API_KEY**)

```bash
make cards
```

Generates summaries, why_hn, level, kind, topics for each book.

- **Input**: `data/filtered_books.json`
- **Output**: `data/final_books.json`
- **Duration**: ~5-15 minutes
- **Cost**: ~$0.10-1.00

**Skip this step if running without API key.** Sample cards will be provided.

#### 5. Prepare Site Data (no API key needed)

```bash
make site-data
```

Prepares final JSON files for the static site and creates downloadable data package.

- **Input**: `data/final_books.json`
- **Output**: 
  - `site/data/books.json`
  - `site/data/mentions.json`
  - `site/data/stats.json`
  - `site/download/hackershelf-data.zip`
- **Duration**: <1 minute

### Running Without LLM API Key

If you don't have an API key, you can run non-LLM steps and use sample data:

```bash
# Extract candidates
make extract

# Use sample LLM outputs (provided)
# Then run remaining steps
make resolve cards site-data
```

The sample data includes ~20-50 books for development.

## Data Files

### Pipeline Intermediate Files

- `data/candidates.parquet` - Extracted candidate comments (~1-10 MB)
- `data/extracted_books.json` - LLM extractions with book titles/authors/stance
- `data/filtered_books.json` - Resolved and filtered books (≥3 users, ≥3 months)
- `data/final_books.json` - Books with generated cards

### Site Data Files

- `site/data/books.json` - Final book list for the site
- `site/data/mentions.json` - HN comment mentions
- `site/data/stats.json` - Summary statistics
- `site/download/hackershelf-data.zip` - Downloadable data package

## Caching

The pipeline caches API responses to minimize cost:

- LLM extractions: `data/llm_cache/`
- Open Library lookups: `data/ol_cache/`

Caches are keyed by input, so re-running is free if inputs haven't changed.

## Configuration

### Environment Variables

- `GEMINI_API_KEY` - Gemini API key (required for steps 2 and 4)

### Adjusting Time Range

Edit `pipeline/01_extract_candidates.py` or pass arguments:

```bash
python pipeline/01_extract_candidates.py 2020 2026
```

### Adjusting Filters

Edit filter criteria in `pipeline/03_resolve_and_filter.py`:

```python
# Change these lines:
if len(users) >= 3 and len(months) >= 3:  # Minimum thresholds
```

## Cost Estimation

For full HN history (2007-2026):

- Candidate extraction: **FREE** (uses public data)
- LLM extraction: **~$1-5** (batched, cached)
- Open Library: **FREE** (no API key required)
- Card generation: **~$0.10-1** (one call per book)

**Total: ~$1-6** for full dataset.

Subsequent runs with cache: **~$0**.

## Troubleshooting

### "GEMINI_API_KEY not found"

Set the environment variable:

```bash
export GEMINI_API_KEY=your_key_here
```

Or create a `.env` file in the project root.

### "candidates.parquet not found"

Run step 1 first:

```bash
make extract
```

### Rate limit errors

The scripts include delays (0.5-1s) between API calls. If you hit limits, increase the delays in the scripts.

### Memory issues

If extracting candidates uses too much memory, process year-by-year:

```bash
for year in {2015..2026}; do
  python pipeline/01_extract_candidates.py $year $year
done
```

Then merge the parquet files manually.

## License

Pipeline code: MIT  
Data: ODC-By 1.0 (derivative of open-index/hacker-news)
