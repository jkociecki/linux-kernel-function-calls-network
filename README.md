# Linux Kernel Function-Call Network

Analysis of the Linux kernel as a complex directed graph — built from GCC RTL compilation dumps.

![Poster](poster.png)

## Quick start

```bash
bash compile_linux.sh
python src/build_callgraph.py --linux-dir data/linux --output-dir data/out
python src/analyze_graph.py --nodes data/out/nodes.csv --edges data/out/edges.csv --out-dir data/out
```
