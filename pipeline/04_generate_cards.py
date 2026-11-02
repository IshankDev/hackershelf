#!/usr/bin/env python3
"""
Generate book cards with LLM: summary, why_hn, level, kind, topics.
Then categorize books into a taxonomy.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
import time

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

CARD_PROMPT_TEMPLATE = """Analyze these Hacker News mentions of the book "{title}" by {author} and create a book card.

Mentions:
{mentions}

Return a JSON object with:
{{
  "summary": "2-sentence summary of the book",
  "why_hn": "1 sentence explaining why HN readers recommend it",
  "level": "intro|intermediate|advanced",
  "kind": "technical|business|science|fiction|history|philosophy|other",
  "topics": ["topic1", "topic2", "topic3"]
}}

Be specific and use the actual HN comments to inform your response.
"""

TAXONOMY = {
    "Programming": ["Programming Languages", "Software Engineering", "Algorithms & Data Structures", "Web Development"],
    "Computer Science": ["Theory", "Systems", "AI & Machine Learning", "Databases"],
    "Technology & Society": ["Tech Industry", "Internet Culture", "Privacy & Security", "Future of Tech"],
    "Business": ["Startups", "Management", "Economics", "Product Development"],
    "Science": ["Physics", "Biology", "Mathematics", "Psychology"],
    "History": ["Tech History", "World History", "Biography"],
    "Philosophy": ["Philosophy of Mind", "Ethics", "Critical Thinking"],
    "Fiction": ["Science Fiction", "Classic Literature"],
    "Self-Improvement": ["Productivity", "Learning", "Career"]
}

def setup_gemini():
    """Initialize Gemini API."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found")
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        return model
    except ImportError:
        raise ImportError("google-generativeai not installed")

def load_filtered_books():
    """Load filtered books."""
    with open("data/filtered_books.json") as f:
        return json.load(f)

def generate_card(model, book):
    """Generate a card for one book."""
    
    # Format mentions for prompt
    mentions_text = []
    for m in book["mentions"][:10]:  # Use up to 10 mentions
        stance_emoji = "🔥" if m["stance"] == "strong_rec" else "👍"
        mentions_text.append(f"{stance_emoji} {m['by']}: {m['why']} | \"{m['quote']}\"")
    
    prompt = CARD_PROMPT_TEMPLATE.format(
        title=book["title"],
        author=book["author"],
        mentions="\n".join(mentions_text)
    )
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.3,
            }
        )
        
        card_data = json.loads(response.text)
        return card_data
        
    except Exception as e:
        print(f"Error generating card for {book['title']}: {e}")
        # Return default
        return {
            "summary": f"A book about {', '.join(book.get('subjects', [])[:3])}.",
            "why_hn": "Recommended by the Hacker News community.",
            "level": "intermediate",
            "kind": "other",
            "topics": book.get("subjects", [])[:3]
        }

def assign_categories(book):
    """Assign 1-3 categories to a book based on its topics and kind."""
    topics = book.get("topics", [])
    kind = book.get("kind", "other")
    subjects = book.get("subjects", [])
    
    categories = set()
    
    # Map kind to category
    kind_map = {
        "technical": ["Programming", "Computer Science"],
        "business": ["Business"],
        "science": ["Science"],
        "fiction": ["Fiction"],
        "history": ["History"],
        "philosophy": ["Philosophy"],
    }
    
    if kind in kind_map:
        categories.update(kind_map[kind])
    
    # Map topics to categories (simple keyword matching)
    all_topics = topics + subjects
    for topic in all_topics:
        topic_lower = topic.lower()
        
        if any(kw in topic_lower for kw in ["program", "code", "python", "java", "software", "development"]):
            categories.add("Programming")
        elif any(kw in topic_lower for kw in ["algorithm", "computer science", "systems", "network"]):
            categories.add("Computer Science")
        elif any(kw in topic_lower for kw in ["machine learning", "ai", "artificial intelligence", "neural"]):
            categories.add("AI & Machine Learning")
        elif any(kw in topic_lower for kw in ["startup", "business", "entrepreneur", "management"]):
            categories.add("Business")
        elif any(kw in topic_lower for kw in ["physics", "biology", "chemistry", "math"]):
            categories.add("Science")
        elif any(kw in topic_lower for kw in ["history", "historical"]):
            categories.add("History")
        elif any(kw in topic_lower for kw in ["philosophy", "ethics", "thinking"]):
            categories.add("Philosophy")
        elif any(kw in topic_lower for kw in ["fiction", "novel", "story"]):
            categories.add("Fiction")
    
    # Return up to 3 categories
    return list(categories)[:3] if categories else ["Other"]

def generate_all_cards():
    """Generate cards for all filtered books."""
    
    print("=== Generate Book Cards ===\n")
    
    model = setup_gemini()
    books = load_filtered_books()
    
    print(f"Generating cards for {len(books)} books...\n")
    
    final_books = {}
    
    for i, (work_key, book) in enumerate(books.items(), 1):
        print(f"[{i}/{len(books)}] {book['title']} by {book['author']}")
        
        # Generate card
        card = generate_card(model, book)
        
        # Assign categories
        categories = assign_categories({**book, **card})
        
        # Combine data
        final_book = {
            **book,
            **card,
            "categories": categories
        }
        
        final_books[work_key] = final_book
        
        time.sleep(1)  # Rate limit
    
    # Save final books
    output_path = Path("data/final_books.json")
    with open(output_path, 'w') as f:
        json.dump(final_books, f, indent=2)
    
    print(f"\n✓ Saved {len(final_books)} books with cards to {output_path}")
    
    # Print category distribution
    category_counts = {}
    for book in final_books.values():
        for cat in book["categories"]:
            category_counts[cat] = category_counts.get(cat, 0) + 1
    
    print("\n=== Category Distribution ===")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

if __name__ == "__main__":
    generate_all_cards()
