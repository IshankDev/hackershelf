# HackerShelf 📚

> "The books Hacker News keeps telling each other to read"

**Live Site:** https://ishankdev.github.io/hackershelf/

HackerShelf is a curated collection of books recommended by the Hacker News community, extracted from 2024-2026 HN comments (9.4M comments scanned, 11,519 candidates). Inspired by Andrej Karpathy's [HackerTube](https://hackertube.org/).

## Features

- 📚 **Curated Books** — Only books with ≥3 recommenders across ≥3 months
- 🔍 **Smart Search** — Filter by title, author, topics, or categories
- 🎨 **HN Orange Theme** — Authentic HN aesthetic with light/dark mode
- 💬 **Real HN Comments** — See what actual HN users said about each book
- 📖 **Reading List** — Save books to read later (localStorage)
- 📊 **Rich Metadata** — Scores, summaries, categories, levels, and topics
- 🌐 **Static Site** — Fast, no backend, works everywhere

## Quick Start

Visit the live site: **https://ishankdev.github.io/hackershelf/**

Or run locally:

```bash
git clone https://github.com/IshankDev/hackershelf.git
cd hackershelf/site
python3 -m http.server 8000
# Open http://localhost:8000
```

## Data Pipeline

The pipeline extracts book recommendations from HN comments following the HackerTube methodology:

### Prerequisites

- Python 3.9+
- DuckDB, requests, python-dotenv
- Gemini API key (get from [aistudio.google.com](https://aistudio.google.com))
- Raw HN parquet files from [open-index/hacker-news](https://huggingface.co/datasets/open-index/hacker-news)

### Setup

```bash
pip install -r requirements.txt

# Set your Gemini API key
export GEMINI_API_KEY=your_key_here
```

### Run the Pipeline

Full pipeline (all stages):

```bash
make data
```

Or run stages individually:

```bash
# Stage 1: Extract candidates from HN (no API key needed)
make extract      # ~30-60 min for full history, outputs data/candidates.parquet

# Stage 2: LLM extraction (requires GEMINI_API_KEY)
make llm          # ~1-2 hours, $1-5 cost, outputs data/extracted_books.json

# Stage 3: Resolve via Open Library and filter (no API key needed)
make resolve      # ~10-30 min, outputs data/filtered_books.json

# Stage 4: Generate cards (requires GEMINI_API_KEY)
make cards        # ~5-15 min, $0.10-1 cost, outputs data/final_books.json

# Stage 5: Prepare site data (no API key needed)
make site-data    # <1 min, outputs site/data/*.json and .zip
```

### Pipeline Details

See [PIPELINE_README.md](./PIPELINE_README.md) for complete documentation.

**Current Status:**
- ✅ Prefilter complete: 11,519 strong candidates from 9.4M comments (2024-01 to 2026-08)
- ✅ LLM extraction complete: Gemini 3.5 Flash Lite processed all candidates
- ✅ Resolve & filter complete: 151 books (≥3 users, ≥3 months)
- ✅ Card generation complete: Summaries and metadata for all books
- ✅ Site data prepared: Full dataset deployed

**Full Dataset:** The site now contains the complete dataset with 151 books from real LLM extraction.

## Methodology

Following [HackerTube](https://hackertube.org/)'s approach:

1. **Prefilter** 9.4M HN comments (2024-01 to 2026-08) for strong book signals
2. **Extract** 11,519 candidates with book links or strong recommendation phrases
3. **LLM Extract** book titles, authors, and stance via Gemini 3.5 Flash Lite
4. **Resolve** books via Open Library API and dedupe by work ID
5. **Filter** — keep books with ≥3 distinct recommenders in ≥3 months
6. **Enrich** — generate summaries, categories, topics via LLM
7. **Score** — `Score = (distinct recommenders) + 2 × (strong recommendations)`

## Tech Stack

**Pipeline:**
- Python 3 + DuckDB (data extraction from 9.4M comments)
- Gemini 3.5 Flash Lite (LLM extraction/cards)
- Open Library API (book metadata)

**Site:**
- Plain HTML/CSS/JS (no framework)
- Client-side routing (hash-based)
- LocalStorage (want-to-read list, theme)
- GitHub Pages (deployment)

## Data & Credits

**Source Data:** [open-index/hacker-news](https://huggingface.co/datasets/open-index/hacker-news) (ODC-By 1.0)  
**Book Metadata:** [Open Library](https://openlibrary.org/)  
**Inspiration:** [HackerTube](https://hackertube.org/) by Andrej Karpathy  
**License:** ODC-By 1.0 (HN comments remain work of their authors)

## Statistics

- **151** books
- **723** mentions
- **601** unique recommenders
- **2024-2026** time span (Jan 2024 - Aug 2026)
- **9** categories

## Download Data

[hackershelf-data.zip](https://ishankdev.github.io/hackershelf/download/hackershelf-data.zip) (includes books.json, mentions.json, stats.json, and DATA.md)

## Deploy

The site deploys automatically to GitHub Pages via GitHub Actions on push to `main`.

**Manual deployment:**

```bash
git push origin main
# Visit https://github.com/IshankDev/hackershelf/actions to monitor
# Live at https://ishankdev.github.io/hackershelf/ after ~1 min
```

**Enabling GitHub Pages:**

If Pages deployment fails, enable it in repo settings:
1. Go to Settings → Pages
2. Source: "GitHub Actions"
3. Save

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run local dev server
cd site
python3 -m http.server 8000
```

Edit files in `site/`:
- `index.html` — Main HTML structure
- `css/style.css` — All styles (HN orange theme)
- `js/app.js` — Router, pages, logic
- `data/` — JSON data files

## Project Structure

```
hackershelf/
├── .github/workflows/
│   └── deploy.yml           # GitHub Actions → Pages
├── data/
│   ├── candidates.parquet   # 392k HN comments (201 MB)
│   ├── extracted_books.json # LLM extractions
│   ├── filtered_books.json  # Post-filter
│   └── final_books.json     # With cards
├── pipeline/
│   ├── 01_extract_candidates.py
│   ├── 02_llm_extract.py
│   ├── 03_resolve_and_filter.py
│   ├── 04_generate_cards.py
│   └── 05_prepare_site_data.py
├── site/
│   ├── index.html           # Main page
│   ├── css/style.css        # All styles
│   ├── js/app.js            # App logic
│   ├── data/                # Site JSON files
│   └── download/            # Data package
├── Makefile                 # Pipeline commands
├── requirements.txt         # Python deps
├── TIMELOG.md              # Build timeline
└── README.md               # This file
```

## Contributing

This is a personal project and not currently accepting contributions. However, feel free to fork and adapt the approach for other communities!

## License

- **Code:** MIT License
- **Data:** ODC-By 1.0 (derivative of open-index/hacker-news)
- **HN Comments:** Remain work of their respective authors

## Acknowledgments

- **Andrej Karpathy** for pioneering this approach with [HackerTube](https://hackertube.org/)
- **open-index** for curating the [hacker-news dataset](https://huggingface.co/datasets/open-index/hacker-news)
- **Open Library** for book metadata
- **Hacker News community** for the recommendations

---

Built with 🧡 for the HN community
