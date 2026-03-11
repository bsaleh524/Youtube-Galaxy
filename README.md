# Controversy-Early-Warning-System
Data pipeline for the YouTube Galaxy project. Scrapes Fandom wiki data and builds ML-based creator embeddings / star map data.

> **The Streamlit visualization app has moved!**
> See [Youtube-Galaxy-Streamlit-App](../Youtube-Galaxy-Streamlit-App/) for the deployable front-end.

## Pipeline Overview

End-to-end workflow to update the YouTube Galaxy visualization:

1. **Scrape** — `python src/scrapers/fandom/my_combined.py`
   → `data/fandom/youtubers_data_combined.json`

2. **Build star map** — `python src/plots/starmap_builder.py`
   → `data/processed/plotly/starmap_data_big_tsne_trimmed_120_labeled.csv` (numeric cluster IDs)

3. **Label clusters** — Feed the CSV to Gemini Pro to add human-readable `cluster_name` column; save the result as the same labeled CSV.

4. **Export Parquet** — `python src/plots/export_parquet.py`
   → `data/processed/plotly/starmap_data.parquet` (~45% smaller than CSV)
   The script also prints the exact `gh release create` command for the next step.

5. **Upload to GitHub Releases** — Run the printed command (example for a new version):
   ```bash
   gh release create vX.Y \
     data/processed/plotly/starmap_data.parquet \
     --repo bsaleh524/Youtube-Galaxy-Streamlit-App \
     --title "Starmap data vX.Y" \
     --notes "Description of what changed"
   ```
   Then update `PARQUET_URL` in `Youtube-Galaxy-Streamlit-App/streamlit_app.py` to point to the new tag.
    Note: Last used parquet based on starmap_data_big_tsne_trimmed_120_labeled.csv
## Setup
```bash
mamba env create -f env_mac.yml   # or env_windows.yml on Windows
mamba activate contro
```

---

Predict controversies with influencers before they happen, based upon trends of current influencers on the respective platforms

Problems:
- Bias: Going to r/livestreamfails or youtube comments ona  topic that is sensitive already causes HEAVY bias. 


## Things we overcame:
- Balance of Pricing vs time:
    * By using the Gemini pricing, we'd be limited to 60 comments per minute since that's what's allowed. We would need to:
      * Why it's 100% Free: It gives you a permanent free-of-charge tier with a rate limit of 60 queries per minute (QPM).

        The Trade-off: You exactly identified it: "We dont need to worry about time."

            If you have 20,000 comments, it will take 20,000 / 60 = 333 minutes (about 5.5 hours) to process them all.

            Your analyzer.py script will just run in your terminal for 6 hours, politely respecting the 60 QPM limit, and it will cost you $0.00.

        Model Quality: It's fantastic. You can use a model like gemini-1.5-flash and give it a prompt to return both sentiment and the scandal topic in one go, saving you even more time.
    
    * Better option: Use a local model(s). Hugging face
        * What it is: Instead of calling an API, you download a pre-trained, open-source model from Hugging Face and run it on your own computer using the transformers library.

        Pros:

            100% Free, Forever: No API keys, no rate limits.

            FAST: If you have a decent computer (especially with a GPU), this will be much faster than the 6-hour rate-limited Gemini API.

            Impressive Skill: This is a very good skill to show. It's what MLOps engineers do.

        Cons (for this MVP):

            More Complex: The code is more complex than a simple API call.

            "Dumber" Models: You would need two separate models:

                A small, fast sentiment model (easy).

                A separate topic extraction model (much harder).

            This complexity can slow you down, which is exactly what you wanted to avoid.

* Learned along the way
    - Must truncate texts due to token limitations of models

* For embedding models:
    The Problem with "Last 50 Videos"

You suggested grabbing the last 50 video titles and descriptions. While more data is usually better, we hit two technical bottlenecks here:

    The Context Window (Token Limit): The model we are using (all-MiniLM-L6-v2) has a limit (usually 256 or 384 tokens). 50 video titles + descriptions will result in thousands of tokens. The model will simply chop off the last 90% of your text. It won't even "see" videos 6 through 50.

    The Noise Ratio: Video descriptions are often full of "boilerplate" junk: Merch links, social media handles, affiliate codes, and copyright disclaimers. This is "noise" that dilutes the "signal" (the actual topic).

    