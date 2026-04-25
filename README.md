# Linux Kernel Function Calls Network

This project builds a directed function-call network from Linux kernel compilation dumps.

## What this project is for

- Compile Linux with GCC RTL dumps enabled (`-fdump-rtl-expand`).
- Parse dumps into:
  - `nodes.csv` (functions),
  - `edges.csv` (caller -> callee).
- Build a complex-network model and analyze centrality, hubs, and subsystem structure.

This is useful in advanced networking/complex-systems classes where you model code as a graph and study topology.

## Quick start

1. Compile Linux and generate RTL dumps:

```bash
bash compile_linux.sh
```

Alternative profiles:

```bash
# fast/default profile
bash compile_linux.sh --config defconfig

# much larger dataset (all as modules)
bash compile_linux.sh --config allmodconfig

# use existing data/linux/.config without regenerating profile
bash compile_linux.sh --config existing
```

2. Build call graph CSV files:

```bash
python src/build_callgraph.py \
  --linux-dir data/linux \
  --output-dir data/out
```

3. Build graph metrics and GraphML for visualization:

```bash
python src/analyze_graph.py \
  --nodes data/out/nodes.csv \
  --edges data/out/edges.csv \
  --out-dir data/out
```

## Command input/output map

1. `bash compile_linux.sh`
- Reads:
  - `data/linux/**` (kernel sources)
  - `data/linux/.config` (creates it when missing)
- Writes:
  - `data/linux/**/*.expand` (GCC RTL dumps)

`compile_linux.sh` options:

- `--config defconfig|allmodconfig|allyesconfig|existing`
- `--jobs N`

2. `python src/build_callgraph.py --linux-dir data/linux --output-dir data/out`
- Reads:
  - `data/linux/**/*.expand`
- Writes:
  - `data/out/nodes.csv`
  - `data/out/edges.csv`

3. `python src/analyze_graph.py --nodes data/out/nodes.csv --edges data/out/edges.csv --out-dir data/out`
- Reads:
  - `data/out/nodes.csv`
  - `data/out/edges.csv`
- Writes:
  - `data/out/node_metrics.csv`
  - `data/out/top_hubs.csv`
  - `data/out/subsystem_stats.csv`
  - `data/out/callgraph.graphml`

Generated analysis files:

- `data/out/node_metrics.csv`
- `data/out/top_hubs.csv`
- `data/out/subsystem_stats.csv`
- `data/out/callgraph.graphml`

## Typical reason for "too few files" after compilation

- Missing `.config` (kernel was not configured before build).
- Build errors hidden by stderr redirection.
- Incremental build recompiles only a small subset of files.
- Old and new dumps mixed together from previous runs.

`compile_linux.sh` addresses these by creating/updating config, removing old dumps, and keeping build errors visible.

## Ideas for visualization and findings

- Directed graph colored by `subsystem`.
- Node size by `in_degree` or `pagerank`.
- Community detection over undirected projection.
- Cross-subsystem matrix (who calls whom most often).
- Compare `drivers/*` vs `net` centrality profile.
- Plot heavy-tail degree distribution (log-log).

Useful questions:

- Which 20 functions are most central globally?
- Is `net` mostly self-contained or strongly coupled to other subsystems?
- Which subsystem has highest incoming dependency pressure?
- Where are potential single points of failure (hub-like nodes)?