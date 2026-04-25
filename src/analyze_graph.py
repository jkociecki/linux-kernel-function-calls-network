import argparse
import csv
from pathlib import Path

import networkx as nx


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analyze Linux callgraph as a network")
    p.add_argument("--nodes", type=Path, required=True, help="Path to nodes.csv")
    p.add_argument("--edges", type=Path, required=True, help="Path to edges.csv")
    p.add_argument("--out-dir", type=Path, required=True, help="Output directory")
    p.add_argument("--top-k", type=int, default=50, help="Top hubs to export")
    return p.parse_args()


def read_nodes(nodes_path: Path) -> dict[str, dict]:
    result: dict[str, dict] = {}
    with nodes_path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            node_id = row["id"]
            result[node_id] = row
    return result


def read_edges(edges_path: Path) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    with edges_path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            src = row["source"]
            dst = row["target"]
            if src and dst and src != dst:
                result.append((src, dst))
    return result


def build_graph(nodes: dict[str, dict], edges: list[tuple[str, str]]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for node_id, attrs in nodes.items():
        graph.add_node(node_id, **attrs)
    graph.add_edges_from(edges)
    return graph


def compute_metrics(graph: nx.DiGraph) -> dict[str, dict[str, float]]:
    in_deg = dict(graph.in_degree())
    out_deg = dict(graph.out_degree())
    total_deg = dict(graph.degree())

    # Pagerank is a stable global-importance baseline for directed graphs.
    pagerank = nx.pagerank(graph, alpha=0.85, max_iter=100)

    metrics: dict[str, dict[str, float]] = {}
    for node_id in graph.nodes():
        metrics[node_id] = {
            "in_degree": float(in_deg.get(node_id, 0)),
            "out_degree": float(out_deg.get(node_id, 0)),
            "degree": float(total_deg.get(node_id, 0)),
            "pagerank": float(pagerank.get(node_id, 0.0)),
        }
    return metrics


def write_node_metrics_csv(
    out_path: Path, graph: nx.DiGraph, metrics: dict[str, dict[str, float]]
) -> None:
    fieldnames = [
        "id",
        "func_name",
        "module",
        "subsystem",
        "file_path",
        "is_static",
        "is_definition",
        "in_degree",
        "out_degree",
        "degree",
        "pagerank",
    ]

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for node_id, attrs in graph.nodes(data=True):
            row = {
                "id": node_id,
                "func_name": attrs.get("func_name", node_id),
                "module": attrs.get("module", ""),
                "subsystem": attrs.get("subsystem", ""),
                "file_path": attrs.get("file_path", ""),
                "is_static": attrs.get("is_static", ""),
                "is_definition": attrs.get("is_definition", ""),
                **metrics[node_id],
            }
            writer.writerow(row)


def write_top_hubs_csv(
    out_path: Path, graph: nx.DiGraph, metrics: dict[str, dict[str, float]], top_k: int
) -> None:
    ranked = sorted(
        graph.nodes(),
        key=lambda node_id: (
            metrics[node_id]["pagerank"],
            metrics[node_id]["in_degree"],
            metrics[node_id]["degree"],
        ),
        reverse=True,
    )

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "id", "subsystem", "in_degree", "out_degree", "pagerank"])
        for idx, node_id in enumerate(ranked[:top_k], start=1):
            attrs = graph.nodes[node_id]
            m = metrics[node_id]
            writer.writerow(
                [
                    idx,
                    node_id,
                    attrs.get("subsystem", ""),
                    int(m["in_degree"]),
                    int(m["out_degree"]),
                    m["pagerank"],
                ]
            )


def write_subsystem_stats_csv(out_path: Path, graph: nx.DiGraph) -> None:
    node_count: dict[str, int] = {}
    edge_internal: dict[str, int] = {}
    edge_outgoing: dict[str, int] = {}
    edge_incoming: dict[str, int] = {}

    for _, attrs in graph.nodes(data=True):
        subsystem = str(attrs.get("subsystem", "unknown") or "unknown")
        node_count[subsystem] = node_count.get(subsystem, 0) + 1

    for src, dst in graph.edges():
        src_sub = str(graph.nodes[src].get("subsystem", "unknown") or "unknown")
        dst_sub = str(graph.nodes[dst].get("subsystem", "unknown") or "unknown")
        if src_sub == dst_sub:
            edge_internal[src_sub] = edge_internal.get(src_sub, 0) + 1
        else:
            edge_outgoing[src_sub] = edge_outgoing.get(src_sub, 0) + 1
            edge_incoming[dst_sub] = edge_incoming.get(dst_sub, 0) + 1

    subsystems = sorted(set(node_count) | set(edge_internal) | set(edge_outgoing) | set(edge_incoming))

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["subsystem", "nodes", "internal_edges", "outgoing_cross_edges", "incoming_cross_edges"])
        for subsystem in subsystems:
            writer.writerow(
                [
                    subsystem,
                    node_count.get(subsystem, 0),
                    edge_internal.get(subsystem, 0),
                    edge_outgoing.get(subsystem, 0),
                    edge_incoming.get(subsystem, 0),
                ]
            )


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    nodes = read_nodes(args.nodes)
    edges = read_edges(args.edges)
    graph = build_graph(nodes, edges)
    metrics = compute_metrics(graph)

    write_node_metrics_csv(args.out_dir / "node_metrics.csv", graph, metrics)
    write_top_hubs_csv(args.out_dir / "top_hubs.csv", graph, metrics, args.top_k)
    write_subsystem_stats_csv(args.out_dir / "subsystem_stats.csv", graph)

    # GraphML can be loaded directly in Gephi or Cytoscape.
    nx.write_graphml(graph, args.out_dir / "callgraph.graphml")

    print(f"nodes={graph.number_of_nodes()} edges={graph.number_of_edges()}")
    print(f"wrote: {args.out_dir / 'node_metrics.csv'}")
    print(f"wrote: {args.out_dir / 'top_hubs.csv'}")
    print(f"wrote: {args.out_dir / 'subsystem_stats.csv'}")
    print(f"wrote: {args.out_dir / 'callgraph.graphml'}")


if __name__ == "__main__":
    main()