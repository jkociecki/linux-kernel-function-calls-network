"""
Linux Kernel Call Graph Dashboard
Interactive explorer for function roles, criticality, and attack simulation
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import networkx as nx

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG & CACHE
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="Linux Kernel Call Graph", layout="wide", initial_sidebar_state="expanded")

DATA = Path("data/out")

@st.cache_data
def load_data():
    """Load metrics, nodes, edges"""
    metrics = pd.read_csv(DATA / "node_metrics.csv")
    nodes = pd.read_csv(DATA / "nodes.csv")
    edges = pd.read_csv(DATA / "edges.csv")
    return metrics, nodes, edges

@st.cache_data
def build_graph(edges):
    """Build networkx directed graph"""
    G = nx.DiGraph()
    for _, row in edges.iterrows():
        G.add_edge(row['source'], row['target'])
    return G

def classify_role(row):
    """Classify node role based on in/out degree"""
    in_deg = row['in_degree']
    out_deg = row['out_degree']
    if in_deg == 0 and out_deg == 0:
        return 'Isolated'
    elif in_deg > 0 and out_deg == 0:
        return 'Executor'
    elif in_deg == 0 and out_deg > 0:
        return 'Dispatcher'
    else:
        return 'Bridge'

def simulate_attack(edges, nodes_to_remove):
    """
    Simulate attack by removing top-N nodes
    Returns: fraction of calls intact
    """
    # Vectorized filtering is much faster than iterating 4.4M edges in Python.
    removed_mask = edges['source'].isin(nodes_to_remove) | edges['target'].isin(nodes_to_remove)
    remaining_edges = (~removed_mask).sum()
    total_edges = len(edges)
    fci = remaining_edges / total_edges if total_edges > 0 else 0
    return fci

@st.cache_data
def coupling_matrix(edges, id_to_subsystem, subsystems=None):
    """Build subsystem coupling matrix from real source->target call edges."""
    if subsystems is None:
        subsystems = sorted(id_to_subsystem['subsystem'].unique().tolist())

    edge_subsys = pd.DataFrame({
        'src_subsystem': edges['source'].map(id_to_subsystem['subsystem']),
        'dst_subsystem': edges['target'].map(id_to_subsystem['subsystem']),
    }).dropna()

    edge_subsys = edge_subsys[
        edge_subsys['src_subsystem'].isin(subsystems) & edge_subsys['dst_subsystem'].isin(subsystems)
    ]

    counts = pd.crosstab(edge_subsys['src_subsystem'], edge_subsys['dst_subsystem'])
    counts = counts.reindex(index=subsystems, columns=subsystems, fill_value=0)

    row_sums = counts.sum(axis=1).replace(0, 1)
    coupling = counts.div(row_sums, axis=0).to_numpy()

    return coupling, subsystems

# ═══════════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════════

metrics, nodes, edges = load_data()
metrics['role'] = metrics.apply(classify_role, axis=1)
id_to_subsystem = metrics[['id', 'subsystem']].drop_duplicates().set_index('id')

st.sidebar.title("🔍 Linux Kernel Call Graph Explorer")
st.sidebar.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: SEARCH FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs(["🔎 Search Function", "⚔️ Attack Simulator", "🕸️ Coupling Matrix", "📊 Statistics"])

with tab1:
    st.header("Search Function")
    st.markdown("Find any function and view its properties, role, and criticality.")
    
    # Search bar
    search_term = st.text_input("Enter function name (partial match supported):", placeholder="e.g., memset, printk, kmalloc")
    
    if search_term:
        matching = metrics[metrics['func_name'].str.contains(search_term, case=False, na=False)]
        
        if len(matching) == 0:
            st.warning(f"No functions found matching '{search_term}'")
        elif len(matching) > 20:
            st.info(f"Found {len(matching)} matches. Showing first 20:")
            matching = matching.head(20)
        
        # Display results
        for idx, row in matching.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([2, 3])
                
                with col1:
                    st.markdown(f"### `{row['func_name']}`")
                    role = row['role']
                    role_colors = {
                        'Dispatcher': '🔵',
                        'Bridge': '🟢',
                        'Executor': '🔴',
                        'Isolated': '⚪'
                    }
                    st.markdown(f"**Role:** {role_colors.get(role, '?')} {role}")
                    st.markdown(f"**Subsystem:** `{row['subsystem']}`")
                
                with col2:
                    metrics_data = {
                        'In-degree': int(row['in_degree']),
                        'Out-degree': int(row['out_degree']),
                        'Total degree': int(row['degree']),
                        'PageRank': f"{row['pagerank']:.2e}",
                        'Module': row['module'],
                    }
                    
                    for key, val in metrics_data.items():
                        st.metric(key, val)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: ATTACK SIMULATOR
# ═══════════════════════════════════════════════════════════════════════════════

with tab2:
    st.header("⚔️ Attack Simulator")
    st.markdown("Simulate the impact of removing top-N functions from the kernel")
    
    col1, col2 = st.columns(2)
    
    with col1:
        strategy = st.selectbox(
            "Attack strategy:",
            ["Top by in-degree", "Top by PageRank", "Top by out-degree", "Random"]
        )
        
        n_remove = st.slider("Number of functions to remove:", 1, 100, 10)
    
    with col2:
        if strategy == "Top by in-degree":
            top_nodes = metrics.nlargest(n_remove, 'in_degree')['id'].tolist()
            st.write(f"Removing {n_remove} functions with highest in-degree")
        elif strategy == "Top by PageRank":
            top_nodes = metrics.nlargest(n_remove, 'pagerank')['id'].tolist()
            st.write(f"Removing {n_remove} functions with highest PageRank")
        elif strategy == "Top by out-degree":
            top_nodes = metrics.nlargest(n_remove, 'out_degree')['id'].tolist()
            st.write(f"Removing {n_remove} functions with highest out-degree")
        else:
            top_nodes = np.random.choice(metrics['id'], n_remove, replace=False).tolist()
            st.write(f"Removing {n_remove} random functions")
    
    if st.button("Run Attack Simulation", type="primary"):
        # Calculate FCI (fraction of calls intact)
        fci = simulate_attack(edges, set(top_nodes))
        calls_lost_pct = (1 - fci) * 100
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Calls Intact", f"{fci*100:.1f}%")
        col2.metric("Calls Lost", f"{calls_lost_pct:.1f}%")
        col3.metric("Functions Removed", f"{n_remove} ({n_remove/len(metrics)*100:.2f}%)")
        
        st.markdown("---")
        
        # Show affected nodes
        st.subheader("Removed Functions")
        removed_data = metrics[metrics['id'].isin(top_nodes)][['func_name', 'subsystem', 'in_degree', 'out_degree', 'role']].sort_values('in_degree', ascending=False)
        st.dataframe(removed_data, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: COUPLING MATRIX
# ═══════════════════════════════════════════════════════════════════════════════

with tab3:
    st.header("🕸️ Subsystem Coupling Matrix")
    st.markdown("Heatmap showing fraction of calls from one subsystem to another")
    
    # Get top subsystems
    top_subsystems = metrics['subsystem'].value_counts().head(12).index.tolist()
    
    with st.spinner("Computing coupling matrix..."):
        coupling, subsys_list = coupling_matrix(edges, id_to_subsystem, top_subsystems)
    
    # Plot heatmap
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(coupling, xticklabels=subsys_list, yticklabels=subsys_list, 
                annot=False, cmap='YlOrRd', cbar_kws={'label': 'Fraction of calls'},
                ax=ax)
    ax.set_title("Subsystem Coupling Matrix (Top 12 by size)")
    ax.set_xlabel("Destination Subsystem")
    ax.set_ylabel("Source Subsystem")
    plt.tight_layout()
    st.pyplot(fig)
    
    # Alerts
    st.subheader("⚠️ Alerts")
    kernel_idx = subsys_list.index('kernel') if 'kernel' in subsys_list else -1
    if kernel_idx >= 0:
        kernel_deps = coupling[:, kernel_idx]
        high_deps = [subsys_list[i] for i in np.where(kernel_deps > 0.3)[0]]
        if high_deps:
            st.warning(f"🔴 High coupling to **kernel**: {', '.join(high_deps)}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: STATISTICS
# ═══════════════════════════════════════════════════════════════════════════════

with tab4:
    st.header("📊 Network Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Functions", f"{len(metrics):,}")
    col2.metric("Total Call Edges", f"{len(edges):,}")
    col3.metric("Avg Degree", f"{(metrics['degree'].mean()):.1f}")
    col4.metric("Subsystems", f"{metrics['subsystem'].nunique()}")
    
    st.markdown("---")
    
    # Role distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Role Distribution")
        role_counts = metrics['role'].value_counts()
        fig, ax = plt.subplots(figsize=(8, 5))
        colors = {'Dispatcher': '#3498db', 'Bridge': '#2ecc71', 'Executor': '#e74c3c', 'Isolated': '#95a5a6'}
        role_counts.plot(kind='bar', ax=ax, color=[colors.get(r, '#999') for r in role_counts.index])
        ax.set_title("Functions by Role")
        ax.set_xlabel("Role")
        ax.set_ylabel("Count")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    
    with col2:
        st.subheader("Top 10 Subsystems")
        subsys_counts = metrics['subsystem'].value_counts().head(10)
        fig, ax = plt.subplots(figsize=(8, 5))
        subsys_counts.plot(kind='barh', ax=ax, color='#3498db')
        ax.set_title("Functions per Subsystem (Top 10)")
        ax.set_xlabel("Count")
        st.pyplot(fig)
    
    st.markdown("---")
    
    # Top hubs
    st.subheader("Top 10 Hub Functions (by in-degree)")
    top_hubs = metrics.nlargest(10, 'in_degree')[['func_name', 'subsystem', 'in_degree', 'role']]
    st.dataframe(top_hubs, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

st.sidebar.markdown("---")
st.sidebar.markdown("""
### About
Linux Kernel Call Graph Explorer — Interactive dashboard for analyzing the network structure of Linux kernel function calls.

**Data:** 466,572 functions | 4,440,158 call edges | Linux 6.x allmodconfig

**Metrics:**
- **Role**: Dispatcher (initiators), Bridge (connectors), Executor (leaves), Isolated
- **FCI**: Fraction of Calls Intact under attack
- **PageRank**: Global influence score
""")
