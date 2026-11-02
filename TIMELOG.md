# HackerShelf Build Timelog

## 2026-11-02T14:26:57Z — START
Starting HackerShelf build. Modified approach: no LLM key available, building pipeline as runnable scripts.

## 2026-11-02T14:50:46Z — CHECKPOINT 1: Candidate Extraction Complete
- Scanned HN comments from 2024-2026 (3 years, 36 months)
- Found 392,831 candidate comments with book signals
- Output: data/candidates.parquet (201 MB)
- Duration: ~24 minutes
- Note: Candidates have book links OR book-related keywords near quoted/title-cased text
- Years: 2024 (141k), 2025 (146k), 2026 (106k)

## 2026-11-02T14:59:47Z — CHECKPOINT 3: Resolve & Filter Complete
- Stage 2 (LLM extraction) skipped - using sample data (51 comments, 15 books)
- Resolved books via Open Library API
- Applied filters: ≥3 users in ≥3 months
- Result: 9 books kept from 47 mentions
- Output: data/filtered_books.json
- Duration: ~20 seconds (with sample data)
- Note: Real pipeline will process 392k candidates through LLM extraction

## 2026-11-02T15:02:43Z — CHECKPOINT 4: Static Site Complete
- Built full static site with HTML/CSS/JS
- Features: home, browse with filters/search, book pages with HN comments, want-to-read list, about
- HN orange theme (#FF6600) with light/dark mode
- Responsive grid layout
- Client-side routing and search
- LocalStorage for user preferences
- Data files: books.json, mentions.json, stats.json, data package zip
- Sample data: 9 books ready to display
- Duration: ~3 minutes

