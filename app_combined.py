import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import requests  # Added for image fetching
from io import BytesIO  # Added for image processing
from pathlib import Path

# --- Page Configuration ---
st.set_page_config(
    page_title="Youtube Galaxy",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Configuration ---
DATA_DIR = Path("data")
# Keeping your specific path
STARMAP_CSV_PATH = DATA_DIR / "processed/plotly/starmap_data_big_tsne_trimmed_120_labeled.csv"

# --- Helper Function for Images ---
@st.cache_data(show_spinner=False)
def get_image_from_url(url):
    """
    Fetches image bytes from a URL to bypass hotlink protection.
    Returns the image data or None if it fails.
    """
    try:
        response = requests.get(url, timeout=3)
        # Check if the request was successful
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception:
        return None

# --- Data Loading ---
@st.cache_data
def load_starmap_data(filepath):
    if not filepath.exists(): return None
    df = pd.read_csv(filepath)
    if 'youtube_url' not in df.columns:
        df['youtube_url'] = ""
    df['youtube_url'] = df['youtube_url'].fillna("")
    return df

# --- Components ---

def render_starmap(df):
    """Tab 2: The Creator Galaxy (3D)"""
    st.subheader("The Creator Galaxy (3D Star Map)")
    
    # Create a copy so we don't mutate the cached dataframe
    df = df.copy()
    
    # --- PRE-CHECK: Neighbor Click Logic ---
    # This block detects if a neighbor was clicked in the PREVIOUS run.
    # It updates the 'search_box' session state BEFORE the search widget renders.
    if 'active_neighbor_grid_key' in st.session_state:
        grid_key = st.session_state['active_neighbor_grid_key']
        
        # Check if this specific grid has a selection in session state
        if grid_key in st.session_state:
            selection_state = st.session_state[grid_key]
            
            # Check if rows are selected (Standard Streamlit 1.35+ selection structure)
            if selection_state and selection_state.get('selection') and selection_state['selection'].get('rows'):
                # Get the index of the selected row
                row_idx = selection_state['selection']['rows'][0]
                
                # Retrieve the list of neighbors associated with this specific grid
                if 'active_neighbor_list' in st.session_state:
                    neighbor_list = st.session_state['active_neighbor_list']
                    
                    # Safety check to ensure index is valid
                    if 0 <= row_idx < len(neighbor_list):
                        new_creator = neighbor_list[row_idx]
                        
                        # Update the search box state (only if changed)
                        if st.session_state.get('search_box') != new_creator:
                            st.session_state['search_box'] = new_creator

    col_map, col_info = st.columns([3, 1])
    
    # Placeholder for logic sharing
    list_selected_creator_title = None

    with col_map:
        # --- Filters ---
        c1, c2 = st.columns([1, 1])
        with c1:
            # Key="search_box" binds this widget to st.session_state['search_box']
            search_query = st.text_input("🔍 Find a Creator", "", key="search_box")
        with c2:
            # Handle potential column name variations
            cluster_col = 'cluster_name' if 'cluster_name' in df.columns else 'cluster_id'
            
            # Get unique clusters for the dropdown
            if cluster_col in df.columns:
                clusters = sorted(df[cluster_col].astype(str).unique())
                cluster_options = ["All"] + list(clusters)
            else:
                cluster_options = ["All"]
            selected_cluster = st.selectbox("🎨 Highlight Group", cluster_options)

    # --- LIST SELECTION LOGIC (Sidebar) ---
    with col_info:
        if selected_cluster != "All":
            st.markdown(f"**Members of '{selected_cluster}'**")
            st.caption("Select one to highlight")
            
            # Filter for the list
            cluster_df = df[df[cluster_col].astype(str) == selected_cluster].sort_values('title')
            
            # Show list with selection enabled
            selection = st.dataframe(
                cluster_df[['title']], 
                hide_index=True, 
                width='stretch', 
                on_select="rerun",
                selection_mode="single-row",
                key=f"list_{selected_cluster}" # Resets selection if you change category
            )
            
            # Capture the selection
            if selection and selection.selection.rows:
                idx = selection.selection.rows[0]
                list_selected_creator_title = cluster_df.iloc[idx]['title']

    # --- MAP LOGIC ---
    with col_map:
        # 1. Base State
        df['color_group'] = df[cluster_col].astype(str)
        df['size'] = 3 # Default size
        
        # 2. Colors
        palette = px.colors.qualitative.Dark24 + px.colors.qualitative.Light24
        unique_clusters = df[cluster_col].unique() if not df.empty else []
        cluster_color_map = {str(c): palette[i % len(palette)] for i, c in enumerate(unique_clusters)}
        cluster_color_map['Match'] = '#FF0000'     # Bright Red for Search/Selection
        cluster_color_map['Background'] = '#222222' # Dark Gray for Dimmed items

        if selected_cluster != "All":
            # Identify rows that do NOT match the selection
            mask_unselected = df[cluster_col].astype(str) != selected_cluster
            
            # "Turn small" and gray out the unselected
            df.loc[mask_unselected, 'size'] = 1
            df.loc[mask_unselected, 'color_group'] = 'Background'
            
            # Highlight selected cluster
            mask_selected = df[cluster_col].astype(str) == selected_cluster
            df.loc[mask_selected, 'size'] = 15

        # 3. Apply Search OR List Selection Highlight (Overrides Cluster logic)
        mask_search = pd.Series(False, index=df.index)
        mask_list = pd.Series(False, index=df.index)

        # Check Search
        if search_query:
            mask_search = df['title'].str.contains(search_query, case=False, na=False)
        
        # Check List Selection
        if list_selected_creator_title:
            mask_list = df['title'] == list_selected_creator_title

        # Combine Matches
        final_match_mask = mask_search | mask_list

        if final_match_mask.any():
            df.loc[final_match_mask, 'color_group'] = 'Match' 
            df.loc[final_match_mask, 'size'] = 20 # Super big
            
            if search_query:
                st.success(f"Found {mask_search.sum()} matches!")
        
        # 4. Render Chart
        # Setup hover data safely
        hover_data = {'x': False, 'y': False, 'z': False, 'color_group': False, 'size': False}
        if cluster_col in df.columns: hover_data[cluster_col] = False
        
        custom_data_cols = ['title']
        for col in ['thumbnail', 'description', 'youtube_url']:
            if col in df.columns: custom_data_cols.append(col)

        fig = px.scatter_3d(
            df, 
            x='x', 
            y='y', 
            z='z',
            color='color_group',
            hover_name='title',
            hover_data=hover_data,
            custom_data=custom_data_cols,
            size='size',
            size_max=14,
            opacity=0.7,
            color_discrete_map=cluster_color_map,
            title="Creator Semantic Clusters (3D)"
        )
        
        fig.update_layout(
            height=800, 
            scene=dict(
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                zaxis=dict(visible=False),
                bgcolor='#0e1117'
            ),
            paper_bgcolor='#0e1117',
            font=dict(color="white"),
            showlegend=True,
            legend=dict(itemsizing='constant'),
            margin=dict(l=0, r=0, t=30, b=0),
            clickmode='event+select'
        )
        
        selected_points = st.plotly_chart(fig, width='stretch', on_select="rerun")

    # --- INFO PANEL (DETAILS) ---
    with col_info:
        st.markdown("---") 
        
        target_row = None
        
        # Priority Logic:
        # 1. List Selection (Specific drill-down)
        if list_selected_creator_title:
            matches = df[df['title'] == list_selected_creator_title]
            if not matches.empty: target_row = matches.iloc[0]
        
        # 2. Map Click (Visual exploration)
        elif selected_points and selected_points['selection']['points']:
            point_index = selected_points['selection']['points'][0]['point_index']
            target_row = df.iloc[point_index]

        # 3. Search Query (Text search)
        elif search_query and mask_search.any():
            target_row = df[mask_search].iloc[0]

        if target_row is not None:
            # --- 1. Basic Details ---
            # CHANGED: Use the helper function to fetch image bytes
            if 'thumbnail' in target_row and pd.notna(target_row['thumbnail']) and str(target_row['thumbnail']).startswith('http'):
                image_data = get_image_from_url(target_row['thumbnail'])
                if image_data:
                    st.image(image_data, width=150)
                else:
                    # Optional: Fallback text or icon if image fails
                    st.warning("Image unavailable")
            
            st.markdown(f"### {target_row['title']}")
            
            if 'youtube_url' in target_row:
                yt_url = str(target_row['youtube_url']).strip()
                if yt_url and yt_url.startswith('http'):
                    st.markdown(f"**[📺 Visit YouTube Channel]({yt_url})**")
            
            st.caption(f"Cluster Group: {target_row[cluster_col]}")
            st.markdown("---")
            
            # --- 2. Truncated Description ---
            st.markdown("**Bio Preview:**")
            if 'description' in target_row:
                desc = str(target_row['description'])
                if len(desc) > 600:
                    desc = desc[:600] + "..."
                st.write(desc)
            
            st.markdown("---")
            
            # --- 3. Nearest Neighbors Logic ---
            st.markdown("#### 🔭 Closest Creators")
            
            tx, ty, tz = target_row['x'], target_row['y'], target_row['z']
            
            # Calculate Distance
            distances = np.sqrt(
                (df['x'] - tx)**2 + 
                (df['y'] - ty)**2 + 
                (df['z'] - tz)**2
            )
            
            df_neighbors = df.copy()
            df_neighbors['distance'] = distances
            
            # Filter self and get top 5
            closest_df = df_neighbors[df_neighbors['distance'] > 0.0001].nsmallest(5, 'distance')
            
            # The 'key' ensures the selection resets when the main target changes
            unique_key_suffix = target_row['id'] if 'id' in target_row else target_row['title']
            
            # We construct a dynamic key for this specific neighbor grid
            current_grid_key = f"neighbors_of_{unique_key_suffix}"
            
            # CHANGED: Store the context (Key and Data) in session state for the PRE-CHECK in the next run
            st.session_state['active_neighbor_grid_key'] = current_grid_key
            st.session_state['active_neighbor_list'] = closest_df['title'].tolist()

            neighbor_selection = st.dataframe(
                closest_df[['title', cluster_col]],
                column_config={
                    "title": "Creator",
                    cluster_col: "Group",
                },
                hide_index=True,
                width='stretch', # Fixed: replaced 'width="stretch"' which is deprecated/invalid
                on_select="rerun",
                selection_mode="single-row",
                key=current_grid_key 
            )

        else:
             if selected_cluster == "All":
                 st.info("Search for a creator or select category to find a creator")

# --- Main ---
def main():
    st.title("🌌 Youtube Galaxy")
    st.markdown("""
    Explore the vast universe of YouTube creators clustered by content similarity.
    Use the search box or highlight specific groups to discover creators and their connections.
    Created by SpookyPharaoh
    """)
    
    # Corrected tab unpacking
    tabs = st.tabs(["Galaxy"])
    
    with tabs[0]:
        df_map = load_starmap_data(STARMAP_CSV_PATH)
        if df_map is not None: 
            if 'z' not in df_map.columns:
                st.error("⚠️ Data is 2D. Please run `python src/starmap_builder.py` to regenerate 3D data.")
            else:
                render_starmap(df_map)
        else: 
            st.warning(f"No star map data found at {STARMAP_CSV_PATH}. Run 'src/starmap_builder.py'.")

if __name__ == "__main__":
    main()