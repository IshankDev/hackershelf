#!/usr/bin/env python3
"""
Create rich sample data with multiple users and months for each book.
This ensures books pass the ≥3 users, ≥3 months filter.
"""

import json
import duckdb
from pathlib import Path
from collections import defaultdict

# Popular books that should appear in sample
POPULAR_BOOKS = [
    ("The Pragmatic Programmer", "Andrew Hunt"),
    ("Clean Code", "Robert Martin"),
    ("Designing Data-Intensive Applications", "Martin Kleppmann"),
    ("The Phoenix Project", "Gene Kim"),
    ("Gödel, Escher, Bach", "Douglas Hofstadter"),
    ("The Design of Everyday Things", "Don Norman"),
    ("Thinking, Fast and Slow", "Daniel Kahneman"),
    ("The Mythical Man-Month", "Frederick Brooks"),
    ("Site Reliability Engineering", "Betsy Beyer"),
    ("A Psalm for the Wild-Built", "Becky Chambers"),
    ("Project Hail Mary", "Andy Weir"),
    ("Sapiens", "Yuval Noah Harari"),
    ("Atomic Habits", "James Clear"),
    ("Deep Work", "Cal Newport"),
    ("Zero to One", "Peter Thiel"),
]

STANCES = ["rec", "strong_rec"]
WHYS = [
    "Essential reading for software engineers",
    "Changed my perspective on the topic",
    "Highly practical and actionable",
    "A classic that stands the test of time",
    "Best book on this subject",
    "Everyone should read this",
    "Thought-provoking and insightful",
    "Incredibly well-written",
]

QUOTES = [
    "couldn't put it down",
    "re-read this every year",
    "wish I'd read this earlier",
    "the best book on the subject",
    "highly recommended",
    "a must-read",
    "changed how I think about things",
    "still relevant today",
]

def create_rich_sample():
    """Create sample with multiple mentions per book."""
    
    print("Creating rich sample data...")
    
    # Load candidates from different months/years
    con = duckdb.connect()
    # Sample across different time periods
    candidates = con.execute("""
        WITH sampled AS (
            SELECT id, "by", time, text, parent, year, month,
                   ROW_NUMBER() OVER (PARTITION BY year, month ORDER BY id) as rn
            FROM read_parquet('data/candidates.parquet')
        )
        SELECT id, "by", time, text, parent, year, month
        FROM sampled
        WHERE rn <= 10  -- Get 10 from each month
        ORDER BY year, month, id
        LIMIT 300
    """).fetchall()
    con.close()
    
    print(f"Loaded {len(candidates)} candidates")
    
    extractions = {}
    
    # Group candidates by month for better distribution
    by_month = defaultdict(list)
    for cand in candidates:
        comment_id, by_user, time, text, parent, year, month = cand
        by_month[(year, month)].append(cand)
    
    months = sorted(by_month.keys())
    print(f"Candidates span {len(months)} months: {months[0]} to {months[-1]}")
    
    # For each book, create 5+ mentions from different users/months
    for book_idx, (book_title, book_author) in enumerate(POPULAR_BOOKS):
        mentions_needed = 5  # Ensure we have enough diversity
        
        for mention_idx in range(mentions_needed):
            # Pick from different months cyclically
            month_key = months[mention_idx % len(months)]
            month_candidates = by_month[month_key]
            
            if not month_candidates:
                continue
            
            # Pick a candidate from this month
            cand = month_candidates.pop(0)
            comment_id, by_user, time, text, parent, year, month = cand
            
            # Alternate stance
            stance = STANCES[mention_idx % 2]
            why = WHYS[(book_idx + mention_idx) % len(WHYS)]
            quote = QUOTES[(book_idx + mention_idx) % len(QUOTES)]
            
            extractions[str(comment_id)] = {
                "books": [{
                    "title": book_title,
                    "author": book_author,
                    "stance": stance,
                    "why": why,
                    "quote": quote
                }]
            }
    
    # Add a few with multiple books mentioned
    remaining = [c for month_list in by_month.values() for c in month_list if month_list]
    if len(remaining) > 0:
        cand = remaining[0]
        extractions[str(cand[0])] = {
            "books": [
                {
                    "title": "The Pragmatic Programmer",
                    "author": "Andrew Hunt",
                    "stance": "rec",
                    "why": "Great companion to Clean Code",
                    "quote": "both books complement each other well"
                },
                {
                    "title": "Clean Code",
                    "author": "Robert Martin",
                    "stance": "rec",
                    "why": "Essential for code quality",
                    "quote": "uncle Bob knows his stuff"
                }
            ]
        }
    
    # Save
    output_path = Path("data/extracted_books.json")
    with open(output_path, 'w') as f:
        json.dump(extractions, f, indent=2)
    
    # Count books
    book_counts = defaultdict(int)
    for extraction in extractions.values():
        for book in extraction.get("books", []):
            if book.get("stance") in ["rec", "strong_rec"]:
                key = f"{book['title']} by {book['author']}"
                book_counts[key] += 1
    
    print(f"\n✓ Created {len(extractions)} extractions")
    print(f"  Total comment mentions: {len(extractions)}")
    print(f"  Unique books (rec/strong_rec): {len(book_counts)}")
    print(f"\nBook mention counts:")
    for book, count in sorted(book_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {book}: {count} mentions")
    
    print(f"\n✓ Saved to {output_path}")
    print("\nNote: This is enriched sample data. Each popular book has 5+ mentions.")

if __name__ == "__main__":
    create_rich_sample()
