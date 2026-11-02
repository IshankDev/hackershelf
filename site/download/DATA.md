# HackerShelf Data

Generated: 2026-11-02

## Overview

This dataset contains books recommended by the Hacker News community, extracted from 
2024-2026 of HN comments.

- **151** books
- **723** mentions
- **601** unique recommenders

## Methodology

Following the HackerTube approach by Andrej Karpathy:

1. Scanned all HN comments from 2024-2026 
2. Extracted candidate comments (≥100 chars) with book links or book-related keywords
3. Used LLM (Gemini 2.0 Flash) to extract book titles, authors, and stance
4. Resolved books via Open Library API
5. Filtered: kept books with ≥3 recommenders in ≥3 different months
6. Generated summaries and categorization via LLM
7. Built taxonomy and assigned categories

## Filters Applied

- Only "rec" (recommendation) and "strong_rec" (strong recommendation) stances included
- Minimum 3 distinct users recommending
- Minimum 3 distinct months
- Maximum 20 mentions kept per book (favoring diversity of recommenders)

## Scoring

Score = (distinct recommenders) + 2 × (strong recommendations)

## Files

- `books.json` - Book metadata and cards
- `mentions.json` - HN comment mentions with stance and quotes
- `stats.json` - Summary statistics

## License & Attribution

### Data Source

Source data: **open-index/hacker-news** dataset  
https://huggingface.co/datasets/open-index/hacker-news  
License: ODC-By 1.0

This dataset is a derivative work and is released under **ODC-By 1.0**.

### Attribution Required

When using this data, please attribute:
- Original HN comments remain the work of their respective authors
- Compiled dataset: HackerShelf (https://ishankdev.github.io/hackershelf/)
- Source corpus: open-index/hacker-news

### Inspiration

Methodology inspired by Andrej Karpathy's **HackerTube**  
https://hackertube.org/

## Book Metadata

Book metadata (titles, authors, cover images, subjects) provided by **Open Library**  
https://openlibrary.org/
