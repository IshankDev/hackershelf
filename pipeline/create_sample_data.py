#!/usr/bin/env python3
"""
Create sample data for testing the site without running LLM extraction.
Pulls a few real comments from candidates and creates mock LLM responses.
"""

import json
import duckdb
from pathlib import Path

# Sample book data with various categories
SAMPLE_BOOKS = [
    ("The Pragmatic Programmer", "Andrew Hunt", "rec", "Essential software craftsmanship principles", "changed how I write code"),
    ("Clean Code", "Robert Martin", "strong_rec", "Code quality and maintainability guide", "uncle Bob's masterpiece on clean coding"),
    ("Designing Data-Intensive Applications", "Martin Kleppmann", "strong_rec", "Comprehensive guide to distributed systems", "best book on distributed systems I've read"),
    ("The Phoenix Project", "Gene Kim", "rec", "DevOps principles in novel form", "eye-opening for understanding IT operations"),
    ("Structure and Interpretation of Computer Programs", "Harold Abelson", "strong_rec", "Classic CS fundamentals", "SICP is a rite of passage for programmers"),
    ("Gödel, Escher, Bach", "Douglas Hofstadter", "strong_rec", "Mind-bending exploration of consciousness", "changed how I think about recursion and mind"),
    ("The Design of Everyday Things", "Don Norman", "rec", "User-centered design principles", "explains why doors confuse us"),
    ("Thinking, Fast and Slow", "Daniel Kahneman", "strong_rec", "Cognitive biases and decision making", "essential for understanding human psychology"),
    ("The Mythical Man-Month", "Frederick Brooks", "rec", "Classic software project management", "still relevant 50 years later"),
    ("Code Complete", "Steve McConnell", "rec", "Practical software construction guide", "comprehensive and practical"),
    ("Domain-Driven Design", "Eric Evans", "rec", "Tackling complexity in software", "the blue book that changed enterprise software"),
    ("Site Reliability Engineering", "Betsy Beyer", "rec", "Google's approach to operations", "how Google runs production systems"),
    ("A Psalm for the Wild-Built", "Becky Chambers", "strong_rec", "Solarpunk hopeful fiction", "warm blanket for the soul"),
    ("Project Hail Mary", "Andy Weir", "strong_rec", "Hard sci-fi problem solving", "The Martian author's best work yet"),
    ("The Three-Body Problem", "Cixin Liu", "rec", "Mind-bending Chinese sci-fi", "unlike any sci-fi I've read before"),
    ("Sapiens", "Yuval Noah Harari", "rec", "History of humankind", "fascinating perspective on human history"),
    ("Atomic Habits", "James Clear", "rec", "Practical habit formation", "actually actionable advice on habits"),
    ("Deep Work", "Cal Newport", "rec", "Focus in a distracted world", "changed my approach to productivity"),
    ("The Mom Test", "Rob Fitzpatrick", "rec", "How to talk to customers", "short and invaluable for founders"),
    ("Zero to One", "Peter Thiel", "rec", "Startup thinking and innovation", "contrarian views on startups"),
    ("The Lean Startup", "Eric Ries", "rec", "Build-measure-learn methodology", "foundational for modern startups"),
    ("Superintelligence", "Nick Bostrom", "reference", "AI safety and existential risk", "important but dense read on AI risk"),
    ("Purely Functional Data Structures", "Chris Okasaki", "rec", "Functional programming fundamentals", "brilliant exploration of FP data structures"),
    ("The Art of Computer Programming", "Donald Knuth", "reference", "Comprehensive algorithms reference", "the definitive work but intimidating"),
    ("Hacker News", "Paul Graham", "joke", "The book doesn't exist", "I wish there was a HN book"),
]

def create_sample_data():
    """Create sample extracted books data."""
    
    print("Creating sample data...")
    
    # Load a sample of candidates to get real comment IDs
    con = duckdb.connect()
    candidates = con.execute("""
        SELECT id, "by", time, text, parent, year, month
        FROM read_parquet('data/candidates.parquet')
        LIMIT 200
    """).fetchall()
    con.close()
    
    # Create mock LLM extractions
    extractions = {}
    
    for i, (title, author, stance, why, quote) in enumerate(SAMPLE_BOOKS):
        if i >= len(candidates):
            break
        
        comment_id, by_user, time, text, parent, year, month = candidates[i]
        
        # Create extraction
        extractions[str(comment_id)] = {
            "books": [{
                "title": title,
                "author": author,
                "stance": stance,
                "why": why,
                "quote": quote
            }]
        }
    
    # Add some comments with multiple books
    if len(candidates) > len(SAMPLE_BOOKS):
        idx = len(SAMPLE_BOOKS)
        extractions[str(candidates[idx][0])] = {
            "books": [
                {
                    "title": "The Pragmatic Programmer",
                    "author": "Andrew Hunt",
                    "stance": "rec",
                    "why": "Great for beginners and experienced devs",
                    "quote": "read this every few years"
                },
                {
                    "title": "Clean Code",
                    "author": "Robert Martin",
                    "stance": "rec",
                    "why": "Companion to Pragmatic Programmer",
                    "quote": "both books together are essential"
                }
            ]
        }
    
    # Save
    output_path = Path("data/extracted_books.json")
    with open(output_path, 'w') as f:
        json.dump(extractions, f, indent=2)
    
    print(f"✓ Created {len(extractions)} sample extractions")
    print(f"  Saved to {output_path}")
    print(f"  Books: {len(SAMPLE_BOOKS)}")
    print("\nNote: This is sample data for testing. Run LLM extraction for real data.")

if __name__ == "__main__":
    create_sample_data()
