#!/usr/bin/env python3
"""
Extract book candidate comments from HN data.
Reads from open-index/hacker-news parquet files and extracts comments that:
- Are at least 100 chars of own text
- Contain book links OR book-related keywords near quoted/title-cased text
"""

import duckdb
import re
from pathlib import Path
from datetime import datetime
import html

# Book link patterns
BOOK_LINK_PATTERNS = [
    r'amazon\.[a-z.]+/(dp|gp/product)/',
    r'goodreads\.com/book/show/',
    r'bookshop\.org',
    r'openlibrary\.org/(works|books)/',
    r'oreilly\.com/library/view/',
    r'manning\.com/books/',
    r'pragprog\.com/titles/',
    r'ISBN[- ]?(1[03])?:?\s*[\d-]{10,17}',
]

# Book cue keywords
BOOK_CUES = r'(?i)\b(read|book|author|novel|recommend|reading|wrote|published)\b'

def has_book_link(text):
    """Check if text contains any book-related links."""
    for pattern in BOOK_LINK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False

def has_book_cue(text):
    """
    Check if text has book cues near quoted or Title-Cased spans.
    Loose heuristic - we'll let the LLM filter false positives.
    """
    if not re.search(BOOK_CUES, text):
        return False
    
    # Look for quoted text or Title-Cased words (2+ caps words in a row)
    has_quotes = bool(re.search(r'["""\'\'](.*?)["""\'\'"]', text))
    has_title_case = bool(re.search(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text))
    
    return has_quotes or has_title_case

def unescape_html(text):
    """Unescape HTML entities in HN comment text."""
    if not text:
        return text
    return html.unescape(text)

def get_text_length(text):
    """Get actual text length excluding HTML tags."""
    if not text:
        return 0
    # Remove HTML tags for length calculation
    clean = re.sub(r'<[^>]+>', '', text)
    return len(clean.strip())

def extract_candidates(start_year=2007, end_year=None):
    """Extract candidate comments from HN data."""
    
    if end_year is None:
        end_year = datetime.now().year
    
    print(f"Extracting candidates from {start_year} to {end_year}")
    print(f"This will scan HN comments for book links and book-related keywords...")
    
    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Initialize DuckDB with httpfs
    con = duckdb.connect()
    con.execute("INSTALL httpfs")
    con.execute("LOAD httpfs")
    
    all_candidates = []
    yearly_counts = {}
    
    base_url = "https://huggingface.co/datasets/open-index/hacker-news/resolve/main/data"
    
    for year in range(start_year, end_year + 1):
        year_candidates = 0
        print(f"\nProcessing year {year}...")
        
        for month in range(1, 13):
            month_str = f"{month:02d}"
            parquet_url = f"{base_url}/{year}/{year}-{month_str}.parquet"
            
            try:
                # Read parquet - get all comments with text >= 100 chars
                query = f"""
                    SELECT 
                        id,
                        "by",
                        time,
                        text,
                        parent
                    FROM read_parquet('{parquet_url}')
                    WHERE type = 2 
                        AND deleted = 0
                        AND dead = 0
                        AND text IS NOT NULL
                """
                
                result = con.execute(query).fetchall()
                
                month_candidates = 0
                processed = 0
                for row in result:
                    comment_id, by_user, timestamp, text, parent = row
                    processed += 1
                    
                    # Skip if not enough text
                    if not text or get_text_length(text) < 100:
                        continue
                    
                    # Unescape HTML
                    text = unescape_html(text)
                    
                    # Check for book signals
                    if has_book_link(text) or has_book_cue(text):
                        all_candidates.append({
                            'id': comment_id,
                            'by': by_user,
                            'time': timestamp,
                            'text': text,
                            'parent': parent,
                            'year': year,
                            'month': month
                        })
                        month_candidates += 1
                
                # Show progress even if 0 candidates
                status = f"{month_candidates} candidates" if month_candidates > 0 else f"0 (scanned {processed})"
                print(f"  {year}-{month_str}: {status}", flush=True)
                
                year_candidates += month_candidates
                
            except Exception as e:
                # File might not exist for future months or early years
                if "404" not in str(e) and "HTTP Error" not in str(e):
                    print(f"  {year}-{month_str}: Error - {e}")
        
        yearly_counts[year] = year_candidates
        print(f"Year {year} total: {year_candidates} candidates")
    
    # Save candidates to parquet
    if all_candidates:
        output_path = data_dir / "candidates.parquet"
        
        # Convert to DuckDB table and save
        con.execute("DROP TABLE IF EXISTS candidates")
        con.execute("""
            CREATE TABLE candidates (
                id UINTEGER,
                "by" VARCHAR,
                time TIMESTAMP WITH TIME ZONE,
                text VARCHAR,
                parent UINTEGER,
                year INTEGER,
                month INTEGER
            )
        """)
        
        # Insert in batches
        batch_size = 1000
        for i in range(0, len(all_candidates), batch_size):
            batch = all_candidates[i:i+batch_size]
            con.executemany("""
                INSERT INTO candidates (id, "by", time, text, parent, year, month)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [(c['id'], c['by'], c['time'], c['text'], c['parent'], c['year'], c['month']) 
                  for c in batch])
        
        con.execute(f"COPY candidates TO '{output_path}' (FORMAT PARQUET)")
        print(f"\n✓ Saved {len(all_candidates)} candidates to {output_path}")
        
        # Print summary
        print("\n=== Summary ===")
        print(f"Total candidates: {len(all_candidates)}")
        print("\nBy year:")
        for year, count in sorted(yearly_counts.items()):
            if count > 0:
                print(f"  {year}: {count}")
    else:
        print("\n✗ No candidates found")
    
    con.close()

if __name__ == "__main__":
    import sys
    
    # Can optionally specify year range
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 2007
    end = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    extract_candidates(start, end)
