"""
export_parquet.py — Convert the labeled starmap CSV to Parquet for GitHub Releases hosting.

Pipeline step 3:
  1. python src/plots/starmap_builder.py   -> CSV with numeric cluster IDs
  2. Feed CSV to Gemini Pro               -> adds cluster_name column, saves labeled CSV
  3. python src/plots/export_parquet.py   -> starmap_data.parquet  (this script)
  4. Run printed gh release create command -> uploads to Streamlit app repo
"""

import os
import pandas as pd
from pathlib import Path

INPUT_CSV = Path("data/processed/plotly/starmap_data_big_tsne_trimmed_120_labeled.csv")
OUTPUT_PARQUET = Path("data/processed/plotly/starmap_data.parquet")

STREAMLIT_REPO = "bsaleh524/Youtube-Galaxy-Streamlit-App"

def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")

    csv_size_mb = INPUT_CSV.stat().st_size / 1_048_576
    print(f"Reading {INPUT_CSV} ({csv_size_mb:.1f} MB) ...")

    df = pd.read_csv(INPUT_CSV)
    print(f"  Rows: {len(df):,}  Columns: {list(df.columns)}")

    df.to_parquet(OUTPUT_PARQUET, index=False, engine="pyarrow", compression="snappy")

    parquet_size_mb = OUTPUT_PARQUET.stat().st_size / 1_048_576
    print(f"Written {OUTPUT_PARQUET} ({parquet_size_mb:.1f} MB)")
    print(f"  Size reduction: {csv_size_mb:.1f} MB -> {parquet_size_mb:.1f} MB "
          f"({100 * (1 - parquet_size_mb / csv_size_mb):.0f}% smaller)")

    print("\n--- Next step: upload to GitHub Releases ---")
    print("Run the following command from the Controversy-Early-Warning-System directory:\n")
    print(
        f"gh release create v1.0 \\\n"
        f"  {OUTPUT_PARQUET} \\\n"
        f"  --repo {STREAMLIT_REPO} \\\n"
        f'  --title "Starmap data v1.0" \\\n'
        f'  --notes "Initial star map data release (Parquet format)"'
    )
    print(
        "\nThe asset will be available at:\n"
        f"  https://github.com/{STREAMLIT_REPO}/releases/download/v1.0/starmap_data.parquet"
    )

if __name__ == "__main__":
    main()
