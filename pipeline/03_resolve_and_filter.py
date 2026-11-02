#!/usr/bin/env python3
"""
Resolve books via Open Library and filter by HackerTube criteria:
- ≥3 distinct users
- ≥3 distinct months  
- Recommended (rec/strong_rec) only
"""

import json
import requests
import time
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import duckdb

OPENLIBRARY_SEARCH = "https://openlibrary.org/search.json"
CACHE_DIR = Path("data/ol_cache")

def normalize_title(title):
    """Normalize title for matching."""
    import re
    # Remove subtitle after colon
    title = re.split(r'[:\-–—]', title)[0]
    # Lowercase, remove articles and punctuation
    title = title.lower()
    title = re.sub(r'^(the|a|an)\s+', '', title)
    title = re.sub(r'[^\w\s]', '', title)
    return title.strip()

def normalize_author(author):
    """Normalize author name."""
    import re
    if not author:
        return ""
    author = author.lower().strip()
    # Remove Jr., Sr., etc.
    author = re.sub(r'\b(jr|sr|ii|iii|iv)\b\.?', '', author)
    return author.strip()

def resolve_book(title, author):
    """Resolve book via Open Library API."""
    
    # Check cache first
    CACHE_DIR.mkdir(exist_ok=True, parents=True)
    cache_key = f"{normalize_title(title)}_{normalize_author(author)}"
    cache_file = CACHE_DIR / f"{hash(cache_key) % 100000:05d}.json"
    
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)
    
    # Query Open Library
    params = {
        "title": title,
        "author": author,
        "limit": 1
    }
    
    try:
        response = requests.get(OPENLIBRARY_SEARCH, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("docs"):
            doc = data["docs"][0]
            result = {
                "work_key": doc.get("key", "").replace("/works/", ""),
                "title": doc.get("title", title),
                "author": doc.get("author_name", [author])[0] if doc.get("author_name") else author,
                "first_publish_year": doc.get("first_publish_year"),
                "cover_id": doc.get("cover_i"),
                "subjects": doc.get("subject", [])[:10],  # Keep top 10
            }
        else:
            # No match found
            result = {
                "work_key": None,
                "title": title,
                "author": author,
                "first_publish_year": None,
                "cover_id": None,
                "subjects": []
            }
        
        # Cache result
        with open(cache_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        time.sleep(0.5)  # Rate limit
        return result
        
    except Exception as e:
        print(f"Error resolving '{title}' by {author}: {e}")
        return {
            "work_key": None,
            "title": title,
            "author": author,
            "first_publish_year": None,
            "cover_id": None,
            "subjects": []
        }

def load_data():
    """Load candidates and extracted books."""
    
    # Load candidates
    con = duckdb.connect()
    candidates_df = con.execute("SELECT * FROM read_parquet('data/candidates.parquet')").fetchdf()
    con.close()
    
    candidates = {}
    for _, row in candidates_df.iterrows():
        candidates[row['id']] = {
            'by': row['by'],
            'time': row['time'],
            'text': row['text'],
            'parent': row['parent'],
            'year': row['year'],
            'month': row['month']
        }
    
    # Load extracted books
    with open("data/extracted_books.json") as f:
        extracted = json.load(f)
    
    return candidates, extracted

def resolve_and_filter():
    """Main pipeline: resolve books and apply filters."""
    
    print("=== Resolve & Filter Books ===\n")
    
    candidates, extracted = load_data()
    print(f"Loaded {len(candidates)} candidates")
    print(f"Loaded extractions for {len(extracted)} comments\n")
    
    # Build mentions list
    all_mentions = []
    
    for comment_id_str, extraction in extracted.items():
        comment_id = int(comment_id_str)
        
        if comment_id not in candidates:
            continue
        
        candidate = candidates[comment_id]
        books = extraction.get("books", [])
        
        for book in books:
            stance = book.get("stance", "reference")
            
            # Only keep recommendations
            if stance not in ["rec", "strong_rec"]:
                continue
            
            mention = {
                "comment_id": comment_id,
                "title": book.get("title", ""),
                "author": book.get("author", ""),
                "stance": stance,
                "why": book.get("why", ""),
                "quote": book.get("quote", ""),
                "by": candidate["by"],
                "time": candidate["time"],
                "parent": candidate["parent"],
                "year": candidate["year"],
                "month": candidate["month"],
                "text": candidate["text"]
            }
            all_mentions.append(mention)
    
    print(f"Found {len(all_mentions)} book recommendations (rec/strong_rec only)\n")
    
    # Resolve books via Open Library
    print("Resolving books via Open Library...")
    
    book_to_mentions = defaultdict(list)
    resolved_books = {}
    
    for i, mention in enumerate(all_mentions):
        title = mention["title"]
        author = mention["author"]
        
        # Create a key for grouping
        norm_key = f"{normalize_title(title)}||{normalize_author(author)}"
        
        # Resolve if not already done
        if norm_key not in resolved_books:
            if (i + 1) % 50 == 0:
                print(f"  Resolved {i+1}/{len(all_mentions)}...")
            resolved = resolve_book(title, author)
            resolved_books[norm_key] = resolved
        
        resolved = resolved_books[norm_key]
        work_key = resolved.get("work_key")
        
        if not work_key:
            continue  # Skip unresolved books
        
        # Add mention to this book (convert timestamp to int)
        mention_data = {
            **mention,
            "resolved_title": resolved["title"],
            "resolved_author": resolved["author"]
        }
        # Convert timestamp to unix timestamp if it's not already an int
        if hasattr(mention_data["time"], "timestamp"):
            mention_data["time"] = int(mention_data["time"].timestamp())
        book_to_mentions[work_key].append(mention_data)
    
    print(f"✓ Resolved to {len(book_to_mentions)} unique books\n")
    
    # Apply HackerTube filters: ≥3 users in ≥3 months
    print("Applying filters (≥3 users in ≥3 months)...")
    
    filtered_books = {}
    
    for work_key, mentions in book_to_mentions.items():
        # Count distinct users and months
        users = set(m["by"] for m in mentions)
        months = set((m["year"], m["month"]) for m in mentions)
        
        if len(users) >= 3 and len(months) >= 3:
            # Keep up to 20 mentions, favoring different users
            kept_mentions = []
            seen_users = set()
            
            # First pass: one per user
            for m in mentions:
                if m["by"] not in seen_users:
                    kept_mentions.append(m)
                    seen_users.add(m["by"])
                if len(kept_mentions) >= 20:
                    break
            
            # Second pass: fill remaining slots
            if len(kept_mentions) < 20:
                for m in mentions:
                    if m not in kept_mentions:
                        kept_mentions.append(m)
                    if len(kept_mentions) >= 20:
                        break
            
            # Calculate score: distinct recommenders + 2×strong_rec
            strong_rec_count = sum(1 for m in mentions if m["stance"] == "strong_rec")
            score = len(users) + 2 * strong_rec_count
            
            # Get book metadata
            norm_key = list(resolved_books.keys())[list(resolved_books.values()).index(
                next(v for k, v in resolved_books.items() if v.get("work_key") == work_key)
            )]
            book_info = resolved_books[norm_key]
            
            filtered_books[work_key] = {
                "work_key": work_key,
                "title": book_info["title"],
                "author": book_info["author"],
                "first_publish_year": book_info["first_publish_year"],
                "cover_id": book_info["cover_id"],
                "subjects": book_info["subjects"],
                "score": score,
                "recommender_count": len(users),
                "strong_rec_count": strong_rec_count,
                "mention_count": len(mentions),
                "mentions": kept_mentions
            }
    
    print(f"✓ Kept {len(filtered_books)} books after filtering\n")
    
    # Save results
    output_path = Path("data/filtered_books.json")
    with open(output_path, 'w') as f:
        json.dump(filtered_books, f, indent=2)
    
    print(f"✓ Saved to {output_path}")
    
    # Print summary stats
    print("\n=== Summary ===")
    print(f"Books kept: {len(filtered_books)}")
    print(f"Total mentions: {sum(b['mention_count'] for b in filtered_books.values())}")
    print(f"Total recommenders: {sum(b['recommender_count'] for b in filtered_books.values())}")
    
    # Top 10 by score
    top_books = sorted(filtered_books.values(), key=lambda x: x["score"], reverse=True)[:10]
    print("\nTop 10 books by score:")
    for i, book in enumerate(top_books, 1):
        print(f"  {i}. {book['title']} by {book['author']} (score: {book['score']})")

if __name__ == "__main__":
    resolve_and_filter()
