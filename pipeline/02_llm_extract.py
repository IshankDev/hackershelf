#!/usr/bin/env python3
"""
LLM extraction: extract book mentions with title, author, stance from candidates.
Uses Gemini API with caching to minimize cost.
Processes comments in batches of 20.
"""

import os
import json
import duckdb
from pathlib import Path
from datetime import datetime
import time
from dotenv import load_dotenv

load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BATCH_SIZE = 20
CACHE_DIR = Path("data/llm_cache")
COST_FILE = Path("pipeline/cost.json")

EXTRACTION_PROMPT = """You are analyzing Hacker News comments to extract book recommendations.

For each comment, identify any specific books mentioned and the commenter's stance toward each book.

Return a JSON object with this structure:
{
  "comment_id": {
    "books": [
      {
        "title": "Book Title",
        "author": "Author Name", 
        "stance": "strong_rec|rec|reference|critical|joke",
        "why": "Brief reason in ≤20 words",
        "quote": "Verbatim quote from comment ≤25 words"
      }
    ]
  }
}

Stances:
- strong_rec: enthusiastic recommendation ("must read", "changed my life", "best book on X")
- rec: positive recommendation ("good book", "worth reading", "I enjoyed")
- reference: neutral mention (citing a book, listing it)
- critical: negative opinion
- joke: humorous/sarcastic mention

Return empty books array if no specific book is named.
Only include books explicitly mentioned with enough context to identify them.

Here are the comments:
"""

def setup_gemini():
    """Initialize Gemini API client."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment")
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        # Use Gemini 2.0 Flash for cost efficiency
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        return model
    except ImportError:
        raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")

def load_candidates():
    """Load candidates from parquet file."""
    candidates_path = Path("data/candidates.parquet")
    if not candidates_path.exists():
        raise FileNotFoundError(f"{candidates_path} not found. Run 01_extract_candidates.py first.")
    
    con = duckdb.connect()
    df = con.execute("SELECT * FROM read_parquet('data/candidates.parquet')").fetchdf()
    con.close()
    return df

def load_cache():
    """Load existing cache."""
    CACHE_DIR.mkdir(exist_ok=True, parents=True)
    cache = {}
    for cache_file in CACHE_DIR.glob("*.json"):
        try:
            with open(cache_file) as f:
                cache.update(json.load(f))
        except:
            pass
    return cache

def save_cache_batch(batch_data, batch_num):
    """Save a batch of cached results."""
    cache_file = CACHE_DIR / f"batch_{batch_num:06d}.json"
    with open(cache_file, 'w') as f:
        json.dump(batch_data, f, indent=2)

def extract_books_batch(model, comments_batch, cache):
    """Extract books from a batch of comments using Gemini."""
    
    # Filter out already cached
    uncached = [(cid, text) for cid, text in comments_batch if str(cid) not in cache]
    
    if not uncached:
        return {}, 0, 0
    
    # Build prompt with comment batch
    prompt_parts = [EXTRACTION_PROMPT]
    for comment_id, text in uncached:
        # Truncate very long comments
        text_preview = text[:2000] if len(text) > 2000 else text
        prompt_parts.append(f"\n### Comment ID: {comment_id}\n{text_preview}\n")
    
    full_prompt = "\n".join(prompt_parts)
    
    try:
        # Call Gemini
        response = model.generate_content(
            full_prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.1,
            }
        )
        
        # Parse response
        result = json.loads(response.text)
        
        # Count tokens (approximate)
        input_tokens = len(full_prompt.split()) * 1.3  # rough estimate
        output_tokens = len(response.text.split()) * 1.3
        
        return result, input_tokens, output_tokens
        
    except Exception as e:
        print(f"Error processing batch: {e}")
        return {}, 0, 0

def run_extraction():
    """Run the full extraction pipeline."""
    
    print("=== LLM Book Extraction ===\n")
    
    # Setup
    model = setup_gemini()
    candidates = load_candidates()
    cache = load_cache()
    
    print(f"Total candidates: {len(candidates)}")
    print(f"Already cached: {len(cache)}")
    print(f"To process: {len(candidates) - len(cache)}\n")
    
    # Track costs
    total_input_tokens = 0
    total_output_tokens = 0
    
    # Process in batches
    all_results = {**cache}  # Start with cached results
    batch_num = 0
    
    comments_list = [(row['id'], row['text']) for _, row in candidates.iterrows()]
    
    for i in range(0, len(comments_list), BATCH_SIZE):
        batch = comments_list[i:i+BATCH_SIZE]
        batch_num += 1
        
        print(f"Processing batch {batch_num} ({i+1}-{min(i+BATCH_SIZE, len(comments_list))} of {len(comments_list)})...")
        
        results, in_tokens, out_tokens = extract_books_batch(model, batch, all_results)
        
        if results:
            all_results.update(results)
            save_cache_batch(results, batch_num)
            total_input_tokens += in_tokens
            total_output_tokens += out_tokens
            
            # Rate limit
            time.sleep(1)
    
    # Save final results
    output_path = Path("data/extracted_books.json")
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n✓ Saved extractions to {output_path}")
    
    # Calculate cost (Gemini Flash rates as of 2026: ~$0.10/1M input, ~$0.30/1M output)
    cost_per_input_m = 0.10
    cost_per_output_m = 0.30
    estimated_cost = (total_input_tokens / 1_000_000 * cost_per_input_m + 
                     total_output_tokens / 1_000_000 * cost_per_output_m)
    
    # Save cost info
    cost_data = {
        "model": "gemini-2.0-flash-exp",
        "total_input_tokens": int(total_input_tokens),
        "total_output_tokens": int(total_output_tokens),
        "estimated_cost_usd": round(estimated_cost, 4),
        "timestamp": datetime.now().isoformat()
    }
    
    with open(COST_FILE, 'w') as f:
        json.dump(cost_data, f, indent=2)
    
    print(f"\n=== Cost Summary ===")
    print(f"Input tokens: {int(total_input_tokens):,}")
    print(f"Output tokens: {int(total_output_tokens):,}")
    print(f"Estimated cost: ${estimated_cost:.4f}")
    print(f"Saved to {COST_FILE}")

if __name__ == "__main__":
    run_extraction()
