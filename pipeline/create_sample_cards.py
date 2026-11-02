#!/usr/bin/env python3
"""
Create sample book cards without LLM.
Uses heuristics and book subjects to create reasonable cards.
"""

import json
from pathlib import Path

# Card templates based on book type
CARD_TEMPLATES = {
    "programming": {
        "level": "intermediate",
        "kind": "technical",
        "topics": ["Software Engineering", "Best Practices", "Programming"],
        "categories": ["Programming", "Software Engineering"]
    },
    "systems": {
        "level": "advanced",
        "kind": "technical",
        "topics": ["Distributed Systems", "Architecture", "Scalability"],
        "categories": ["Computer Science", "Systems"]
    },
    "management": {
        "level": "intermediate",
        "kind": "business",
        "topics": ["Project Management", "Teams", "Leadership"],
        "categories": ["Business", "Management"]
    },
    "psychology": {
        "level": "intro",
        "kind": "science",
        "topics": ["Psychology", "Decision Making", "Cognitive Science"],
        "categories": ["Science", "Psychology"]
    },
    "fiction": {
        "level": "intro",
        "kind": "fiction",
        "topics": ["Science Fiction", "Literature"],
        "categories": ["Fiction"]
    },
    "history": {
        "level": "intermediate",
        "kind": "history",
        "topics": ["History", "Civilization", "Culture"],
        "categories": ["History"]
    },
}

# Book-specific data
BOOK_INFO = {
    "The Pragmatic Programmer": {
        "summary": "A practical guide to software craftsmanship and best practices for professional programmers. Covers topics from code organization to career development.",
        "why_hn": "HN readers appreciate its timeless advice on writing maintainable code and thinking like a pragmatic developer.",
        "template": "programming"
    },
    "Clean Code": {
        "summary": "Uncle Bob's principles for writing readable, maintainable code that other developers can understand. Focuses on naming, functions, and code organization.",
        "why_hn": "Widely recommended for learning how to write code that doesn't just work, but is clean and maintainable.",
        "template": "programming"
    },
    "Designing Data-Intensive Applications": {
        "summary": "Comprehensive guide to the architecture and principles behind modern distributed data systems. Covers databases, streaming, and batch processing.",
        "why_hn": "The go-to reference for engineers building scalable systems and working with distributed data.",
        "template": "systems"
    },
    "The Phoenix Project": {
        "summary": "A novel about IT transformation, DevOps principles, and improving flow in software organizations. Follows a struggling IT department's turnaround.",
        "why_hn": "Makes complex DevOps and organizational principles accessible through an engaging story.",
        "template": "management"
    },
    "Gödel, Escher, Bach": {
        "summary": "An exploration of consciousness, self-reference, and formal systems through the work of Gödel, Escher, and Bach. A playful journey through recursion and meaning.",
        "why_hn": "A cult classic that resonates with programmers interested in the deep connections between math, art, and computation.",
        "template": "psychology",
        "kind": "philosophy",
        "topics": ["Philosophy", "Mathematics", "Cognitive Science"],
        "categories": ["Philosophy", "Science"]
    },
    "Thinking, Fast and Slow": {
        "summary": "Nobel laureate Daniel Kahneman's exploration of the two systems that drive human thinking: fast intuition and slow deliberation. Reveals cognitive biases.",
        "why_hn": "Essential for understanding decision-making, cognitive biases, and how we think about thinking.",
        "template": "psychology"
    },
    "The Mythical Man-Month": {
        "summary": "Fred Brooks' classic on software project management, arguing that adding people to a late project makes it later. Full of timeless insights.",
        "why_hn": "50 years old but still the most accurate description of software project realities.",
        "template": "management"
    },
    "Site Reliability Engineering": {
        "summary": "Google's approach to building and running large-scale production systems. Covers SLIs, SLOs, incident response, and operational best practices.",
        "why_hn": "The definitive guide to how Google runs its systems, written by actual Google SREs.",
        "template": "systems",
        "topics": ["SRE", "DevOps", "Operations"],
        "categories": ["Computer Science", "DevOps"]
    },
    "A Psalm for the Wild-Built": {
        "summary": "A hopeful solarpunk novella about a tea monk who meets a robot in a world where humans and nature have found balance. Gentle and contemplative.",
        "why_hn": "A refreshing dose of optimistic fiction that imagines a better future without being naive.",
        "template": "fiction",
        "kind": "fiction",
        "topics": ["Solarpunk", "Hope", "Nature"],
        "categories": ["Fiction", "Science Fiction"]
    },
}

def create_cards():
    """Add cards to filtered books."""
    
    print("Creating sample book cards...")
    
    # Load filtered books
    with open("data/filtered_books.json") as f:
        books = json.load(f)
    
    print(f"Loaded {len(books)} filtered books")
    
    # Add cards
    for work_key, book in books.items():
        title = book["title"]
        
        # Get book-specific info or use defaults
        if title in BOOK_INFO:
            info = BOOK_INFO[title]
            template_name = info["template"]
            template = CARD_TEMPLATES[template_name]
            
            book["summary"] = info["summary"]
            book["why_hn"] = info["why_hn"]
            book["level"] = info.get("level", template["level"])
            book["kind"] = info.get("kind", template["kind"])
            book["topics"] = info.get("topics", template["topics"])
            book["categories"] = info.get("categories", template["categories"])
        else:
            # Default template
            template = CARD_TEMPLATES["programming"]
            book["summary"] = f"A book about {', '.join(book.get('subjects', ['software development'])[:3])}."
            book["why_hn"] = "Recommended by the Hacker News community."
            book["level"] = template["level"]
            book["kind"] = template["kind"]
            book["topics"] = book.get("subjects", [])[:3] or template["topics"]
            book["categories"] = ["Other"]
        
        print(f"  ✓ {title}")
    
    # Save as final_books.json
    output_path = Path("data/final_books.json")
    with open(output_path, 'w') as f:
        json.dump(books, f, indent=2)
    
    print(f"\n✓ Saved {len(books)} books with cards to {output_path}")
    
    # Print category distribution
    from collections import defaultdict
    category_counts = defaultdict(int)
    for book in books.values():
        for cat in book.get("categories", []):
            category_counts[cat] += 1
    
    print("\n=== Category Distribution ===")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

if __name__ == "__main__":
    create_cards()
