import os
import json
import pandas as pd
import numpy as np
import torch # Required for hardware detection
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
from umap import UMAP

# --- Configuration ---
DATA_DIR = "data"
INPUT_FILE = os.path.join(DATA_DIR, "fandom", "youtubers_data_combined.json")

def get_best_device():
    """
    Automatically detects the best available hardware accelerator.
    Prioritizes: NVIDIA (CUDA) > Mac (MPS) > CPU
    """
    if torch.cuda.is_available():
        return "cuda"
    elif torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"

def build_starmap(reduction_method="tsne"):
    """
    1. Loads scraped data.
    2. Generates embeddings using GTE-Large (Hardware Accelerated).
    3. Clusters data into 'Genres' (K-Means).
    4. Projects to 2D (t-SNE or UMAP).
    5. Saves as a lightweight CSV for the App.
    """
    print("--- Starting Star Map Builder ---")

    # 1. Load Data
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        creators = json.load(f)
    
    print(f"Loaded {len(creators)} creators.")
    if len(creators) < 5:
        print("Not enough data to build a map. Need at least 5 creators.")
        return

    # 2. Generate Embeddings
    target_device = get_best_device()
    print(f"🚀 Hardware Accelerator Detected: {target_device.upper()}")

    print("Loading 'Alibaba-NLP/gte-large-en-v1.5'...")
    # This model is significantly larger and smarter than the previous ones.
    # trust_remote_code=True is REQUIRED for GTE models.
    try:
        model = SentenceTransformer(
            'Alibaba-NLP/gte-large-en-v1.5', 
            trust_remote_code=True,
            device=target_device
        )
    except Exception as e:
        print("\n❌ Error loading model. You might need to install `einops`.")
        print("Try running: pip install einops")
        print(f"Original Error: {e}")
        return

    print("Generating embeddings (this will take longer due to model size)...")
    
    text_corpus = []
    for c in creators:
        # GTE Large has an 8192 token limit (approx 32,000 characters).
        # We increase the slice here to utilize that massive context window.
        cleaned_description = c['description'].replace('\n', ' ')[:32000]
        text_corpus.append(f"{c['title']} - {cleaned_description}")

    # encode() handles batching automatically
    embeddings = model.encode(text_corpus, show_progress_bar=True, batch_size=4)

    # 3. Clustering (The "Genre" Detector)
    print("Clustering creators into genres...")
    num_clusters = 120 
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    clusters = kmeans.fit_predict(embeddings)

    if reduction_method == "tsne":
        print("Projecting to 3D space with TSNE...")
        n_samples = len(embeddings)
        perplexity_val = min(30, max(2, n_samples - 1))
        tsne = TSNE(
            n_components=3, 
            perplexity=perplexity_val, 
            random_state=42, 
            init='pca', 
            learning_rate='auto'
        )
        coords = tsne.fit_transform(embeddings)
    elif reduction_method == "umap":
        print("Projecting to 3D space with UMAP...")
        reducer = UMAP(
            n_components=3,
            n_neighbors=30,
            min_dist=0.1,
            metric='cosine',
            random_state=42
        )
        coords = reducer.fit_transform(embeddings)

    # 5. Build DataFrame & Save
    print("Saving Star Map data...")
    
    df = pd.DataFrame({
        'id': [c['id'] for c in creators],
        'title': [c['title'] for c in creators],
        'description': [c['description'] + "..." for c in creators],
        'thumbnail': [c.get('thumbnail', '') for c in creators],
        'youtube_url': [c.get('youtube_url', '') for c in creators],
        'cluster_id': clusters,
        'x': coords[:, 0],
        'y': coords[:, 1],
        'z': coords[:, 2],
    })

    df.sort_values('cluster_id', inplace=True)
    output_file = os.path.join(DATA_DIR, "processed", "plotly", f"starmap_data_big_{reduction_method}_{num_clusters}.csv")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    df.to_csv(output_file, index=False)
    print(f"Done! Saved {len(df)} nodes to {output_file}")

if __name__ == "__main__":
    build_starmap(reduction_method="umap")