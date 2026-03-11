import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
from streamlit_agraph import agraph, Node, Edge, Config

# --- Page Configuration ---
st.set_page_config(
    page_title="Content Creator Mapping", #"Controversy Early Warning System",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Configuration ---
DATA_DIR = Path("data")
ANALYZED_CSV_PATH = DATA_DIR / "analyzed_data.csv"
# GRAPH_JSON_PATH = DATA_DIR / "processed/graph/fandom_graph_data_combined.json"
GRAPH_JSON_PATH = DATA_DIR / "yt_api/graph_data.json"
# --- Data Loading Functions ---

# @st.cache_data
# def load_scandal_data(filepath):
#     """Loads Phase 1 Sentiment Data"""
#     if not filepath.exists():
#         return None
#     df = pd.read_csv(filepath)
#     df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], errors='coerce')
#     df.dropna(subset=['timestamp_utc'], inplace=True)
#     return df

@st.cache_data
def load_graph_data(filepath):
    """Loads Phase 2 Graph Data"""
    if not filepath.exists():
        return None
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

# --- Tab 1: Scandal-O-Meter Logic ---
# def render_scandal_dashboard(df):
#     st.subheader("High-Level Summary: Hasan 'Shock Collar' Incident")

#     # KPIs
#     total_comments = len(df)
#     sentiment_counts = df['sentiment_label'].value_counts()
#     total_negative = sentiment_counts.get('Negative', 0)
#     neg_percentage = (total_negative / total_comments) * 100 if total_comments > 0 else 0

#     # Gauge
#     col_gauge, col_stats = st.columns([1, 2])
#     with col_gauge:
#         st.write("### Scandal Score")
#         st.gauge(
#             value=neg_percentage,
#             min_value=0,
#             max_value=100,
#             label="Negative Sentiment %",
#             format_string=f"{neg_percentage:.1f}%"
#         )
#     with col_stats:
#         st.write("### Sentiment Breakdown")
#         c1, c2, c3 = st.columns(3)
#         c1.metric("Negative", f"{total_negative:,}", delta_color="inverse")
#         c2.metric("Positive", f"{sentiment_counts.get('Positive', 0):,}")
#         c3.metric("Neutral", f"{sentiment_counts.get('Neutral', 0):,}")

#     # Keywords
#     st.divider()
#     st.subheader("receipts: Top Negative Keywords")
#     negative_comments = df[df['sentiment_label'] == 'Negative']
#     keyword_counts = negative_comments['keywords'].str.split(', ').explode().value_counts()
#     keyword_counts = keyword_counts[keyword_counts.index != '']
    
#     st.dataframe(
#         keyword_counts.head(15), 
#         column_config={"index": "Keyword", "value": "Count"},
#         use_container_width=True
#     )

# --- Tab 2: Creator Galaxy Logic ---
def render_creator_galaxy(graph_data):
    st.subheader("The Creator Galaxy (Semantic Similarity)")
    
    col_graph, col_details = st.columns([3, 1])

    with col_graph:
        # 1. Convert JSON data to agraph Nodes
        nodes = []
        for n in graph_data['nodes']:
            nodes.append(Node(
                id=n['id'],
                label=n['label'],
                size=800,
                shape="circularImage",
                image=n['image'], # Displays their YouTube Avatar
                # title=f"{n['label']} ({n['subscribers']} subs)", # Hover text
                # We use the calculated MDS coordinates for initial positioning
                x=n.get('x', 0), 
                y=n.get('y', 0)
            ))

        # 2. Convert JSON data to agraph Edges
        edges = []
        for e in graph_data['edges']:
            edges.append(Edge(
                source=e['source'],
                target=e['target'],
                # Thickness based on similarity score
                width=e['weight'] * 2,
                color="#cccccc"
            ))

        # 3. Configure the Graph Physics
        config = Config(
            width="100%",
            height=600,
            directed=False, 
            nodeHighlightBehavior=True, 
            highlightColor="#F7A241", # Orange highlight on hover
            collapsible=False,
            # Physics settings for a "bouncy" but stable graph
            physics={
                "enabled": True,
                "stabilization": {"iterations": 100}
            }
        )

        # 4. Render!
        return_value = agraph(nodes=nodes, edges=edges, config=config)

    # 5. Interactivity: Show details when a node is clicked
    with col_details:
        st.info("👆 Click a node to see details.")
        
        if return_value:
            # Find the clicked node data
            selected_node = next((n for n in graph_data['nodes'] if n['id'] == return_value), None)
            
            if selected_node:
                st.image(selected_node['image'], width=100)
                st.markdown(f"### {selected_node['label']}")
                st.markdown(f"**Subscribers:** {int(selected_node['subscribers']):,}")
                
                # Find connected creators (neighbors)
                st.markdown("#### Closest Connections:")
                neighbors = []
                for e in graph_data['edges']:
                    if e['source'] == selected_node['id']:
                        neighbors.append(e['target'])
                    elif e['target'] == selected_node['id']:
                        neighbors.append(e['source'])
                
                # Match IDs back to Names
                neighbor_names = [n['label'] for n in graph_data['nodes'] if n['id'] in neighbors]
                
                if neighbor_names:
                    for name in neighbor_names:
                        st.caption(f"🔗 {name}")
                else:
                    st.write("No strong connections found.")

# --- Main Application ---
def main():
    st.title("Content Creator Mapping") #"Controversy Early Warning System",)
    
    # Create Tabs
    tab1, tab2 = st.tabs(["🔥 Scandal-O-Meter", "🌌 Creator Galaxy"])

    # --- TAB 1: SCANDAL METER ---
    # with tab1:
    #     df = load_scandal_data(ANALYZED_CSV_PATH)
    #     if df is not None:
    #         render_scandal_dashboard(df)
    #     else:
    #         st.warning("No scandal data found. Run Phase 1 pipeline.")

    # --- TAB 2: CREATOR GALAXY ---
    with tab2:
        graph_data = load_graph_data(GRAPH_JSON_PATH)
        if graph_data is not None:
            render_creator_galaxy(graph_data)
        else:
            st.warning("No graph data found. Run `python run_pipeline.py` to build the graph.")

if __name__ == "__main__":
    main()