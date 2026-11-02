#!/usr/bin/env python3
"""
Prepare final data files for the static site:
- site/data/books.json
- site/data/mentions.json
- site/data/stats.json
- site/download/hackershelf-data.zip
"""

import json
from pathlib import Path
import zipfile
from datetime import datetime

def load_final_books():
    """Load final books with cards."""
    with open("data/final_books.json") as f:
        return json.load(f)

def prepare_site_data():
    """Prepare all site data files."""
    
    print("=== Prepare Site Data ===\n")
    
    books_data = load_final_books()
    
    # Prepare books.json (without full text of mentions)
    books_for_site = []
    all_mentions = []
    
    for work_key, book in books_data.items():
        # Book card
        book_card = {
            "work_key": work_key,
            "title": book["title"],
            "author": book["author"],
            "first_publish_year": book.get("first_publish_year"),
            "cover_id": book.get("cover_id"),
            "summary": book.get("summary", ""),
            "why_hn": book.get("why_hn", ""),
            "level": book.get("level", "intermediate"),
            "kind": book.get("kind", "other"),
            "topics": book.get("topics", []),
            "categories": book.get("categories", []),
            "score": book["score"],
            "recommender_count": book["recommender_count"],
            "mention_count": book["mention_count"],
            "strong_rec_count": book.get("strong_rec_count", 0)
        }
        books_for_site.append(book_card)
        
        # Mentions for this book
        for mention in book.get("mentions", []):
            mention_data = {
                "work_key": work_key,
                "comment_id": mention["comment_id"],
                "by": mention["by"],
                "time": mention["time"],
                "year": mention["year"],
                "month": mention["month"],
                "stance": mention["stance"],
                "why": mention.get("why", ""),
                "quote": mention.get("quote", ""),
                "parent": mention.get("parent")
            }
            all_mentions.append(mention_data)
    
    # Sort books by score
    books_for_site.sort(key=lambda x: x["score"], reverse=True)
    
    # Save books.json
    books_path = Path("site/data/books.json")
    books_path.parent.mkdir(parents=True, exist_ok=True)
    with open(books_path, 'w') as f:
        json.dump(books_for_site, f, indent=2)
    print(f"✓ Saved {len(books_for_site)} books to {books_path}")
    
    # Save mentions.json
    mentions_path = Path("site/data/mentions.json")
    with open(mentions_path, 'w') as f:
        json.dump(all_mentions, f, indent=2)
    print(f"✓ Saved {len(all_mentions)} mentions to {mentions_path}")
    
    # Calculate stats
    all_years = set()
    all_recommenders = set()
    all_categories = set()
    
    for mention in all_mentions:
        all_years.add(mention["year"])
        all_recommenders.add(mention["by"])
    
    for book in books_for_site:
        all_categories.update(book["categories"])
    
    stats = {
        "book_count": len(books_for_site),
        "mention_count": len(all_mentions),
        "recommender_count": len(all_recommenders),
        "year_range": [min(all_years), max(all_years)],
        "category_count": len(all_categories),
        "generated": datetime.now().isoformat()
    }
    
    stats_path = Path("site/data/stats.json")
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"✓ Saved stats to {stats_path}")
    
    # Create downloadable data package
    print("\nCreating data package...")
    
    # Write DATA.md
    data_md_content = f"""# HackerShelf Data

Generated: {datetime.now().strftime('%Y-%m-%d')}

## Overview

This dataset contains books recommended by the Hacker News community, extracted from 
{stats['year_range'][0]}-{stats['year_range'][1]} of HN comments.

- **{stats['book_count']}** books
- **{stats['mention_count']}** mentions
- **{stats['recommender_count']}** unique recommenders

## Methodology

Following the HackerTube approach by Andrej Karpathy:

1. Scanned all HN comments from {stats['year_range'][0]}-{stats['year_range'][1]} 
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
"""
    
    download_dir = Path("site/download")
    download_dir.mkdir(parents=True, exist_ok=True)
    
    data_md_path = download_dir / "DATA.md"
    with open(data_md_path, 'w') as f:
        f.write(data_md_content)
    
    # Create zip
    zip_path = download_dir / "hackershelf-data.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(books_path, "books.json")
        zipf.write(mentions_path, "mentions.json")
        zipf.write(stats_path, "stats.json")
        zipf.write(data_md_path, "DATA.md")
    
    print(f"✓ Created {zip_path}")
    
    print("\n=== Summary ===")
    print(f"Books: {stats['book_count']}")
    print(f"Mentions: {stats['mention_count']}")
    print(f"Recommenders: {stats['recommender_count']}")
    print(f"Years: {stats['year_range'][0]}-{stats['year_range'][1]}")
    print(f"Categories: {stats['category_count']}")

if __name__ == "__main__":
    prepare_site_data()
