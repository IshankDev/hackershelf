.PHONY: install extract llm resolve cards data clean

# Install dependencies
install:
	pip install -r requirements.txt

# Step 1: Extract candidates from HN data (no API key needed)
extract:
	python pipeline/01_extract_candidates.py

# Step 2: LLM extraction (requires GEMINI_API_KEY)
llm:
	python pipeline/02_llm_extract.py

# Step 3: Resolve via Open Library and filter
resolve:
	python pipeline/03_resolve_and_filter.py

# Step 4: Generate cards and categorize
cards:
	python pipeline/04_generate_cards.py

# Step 5: Prepare site data
site-data:
	python pipeline/05_prepare_site_data.py

# Run all non-LLM steps (useful for testing)
non-llm: extract resolve cards site-data

# Run full pipeline
data: extract llm resolve cards site-data

# Clean intermediate files
clean:
	rm -rf data/raw/ data/*.parquet data/llm_cache/ data/ol_cache/
