import re
import csv
import os
import logging
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict, fields
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict
from tqdm import tqdm


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


@dataclass
class Node:
    id: str
    func_name: str
    module: str
    subsystem: str
    file_path: str
    is_static: bool
    is_definition: bool


@dataclass
class Edge:
    source: str
    target: str


SKIP_DIRS = {"tools", "scripts", "Documentation"}


def find_rtl_dumps(linux_dir: Path) -> list[Path]:

    results = []
    for path in linux_dir.rglob("*.expand"):
        if not SKIP_DIRS.intersection(path.parts):
            results.append(path)
    log.info("Znaleziono %d plików *.expand", len(results))
    return sorted(results)


def find_source_files(linux_dir: Path) -> list[Path]:
    results = []
    for path in linux_dir.rglob("*.c"):
        if not SKIP_DIRS.intersection(path.parts):
            results.append(path)
    return sorted(results)


_TOPLEVEL_SUBSYSTEMS = {
    "arch",
    "block",
    "certs",
    "crypto",
    "drivers",
    "fs",
    "include",
    "init",
    "ipc",
    "kernel",
    "lib",
    "mm",
    "net",
    "security",
    "sound",
    "virt",
    "usr",
}


def extract_subsystem(file_path: Path, linux_dir: Path) -> str:
    try:
        rel = file_path.resolve().relative_to(linux_dir.resolve())
        parts = rel.parts
        if not parts:
            return "unknown"
        top = parts[0]
        if top not in _TOPLEVEL_SUBSYSTEMS:
            return top
        if top in ("drivers", "arch") and len(parts) > 1:
            return f"{top}/{parts[1]}"
        return top
    except ValueError:
        return "unknown"


_FUNC_HEADER = re.compile(r"^;;\s+Function\s+(\S+)\s+\((\S+)(?:,|\))")
_CALL_SYMBOL = re.compile(r'symbol_ref[^"]*"([a-zA-Z_][a-zA-Z0-9_]*)"')
_STATIC_MARKER = re.compile(r"\bstatic\b")


def parse_rtl_dump(dump_path: Path, linux_dir: Path) -> tuple[dict, set]:

    nodes: dict[str, Node] = {}
    edges: set[tuple[str, str]] = set()

    source_path = (
        Path(str(dump_path).split(".c.")[0] + ".c")
        if ".c." in str(dump_path)
        else dump_path
    )
    module_name = source_path.name
    subsystem = extract_subsystem(source_path, linux_dir)
    file_path_str = str(source_path)

    try:
        content = dump_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return nodes, edges

    current_func: str | None = None

    for line in content.splitlines():
        m = _FUNC_HEADER.match(line)
        if m:
            current_func = m.group(1)
            if current_func not in nodes:
                nodes[current_func] = Node(
                    id=current_func,
                    func_name=current_func,
                    module=module_name,
                    subsystem=subsystem,
                    file_path=file_path_str,
                    is_static=False,  # RTL nie mówi wprost, uzupełni enrich_metrics
                    is_definition=True,
                )
            continue

        if current_func is None:
            continue

        for callee in _CALL_SYMBOL.findall(line):
            if callee != current_func and callee:
                edges.add((current_func, callee))
                if callee not in nodes:
                    nodes[callee] = Node(
                        id=callee,
                        func_name=callee,
                        module="external",
                        subsystem="external",
                        file_path="",
                        is_static=False,
                        is_definition=False,
                    )

    return nodes, edges


def process_dump(dump_path: Path, linux_dir: Path) -> tuple[dict, set, str | None]:
    try:
        nodes, edges = parse_rtl_dump(dump_path, linux_dir)
        return nodes, edges, None
    except Exception as exc:
        return {}, set(), f"{dump_path.name}: {exc}"


def merge_nodes(global_nodes: dict, local_nodes: dict) -> None:
    for name, node in local_nodes.items():
        existing = global_nodes.get(name)
        if existing is None:
            global_nodes[name] = node
        elif node.is_definition and not existing.is_definition:
            global_nodes[name] = node


def save_nodes_csv(path: Path, nodes: dict) -> None:
    node_fields = [f.name for f in fields(Node)]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=node_fields)
        writer.writeheader()
        for node in nodes.values():
            writer.writerow(asdict(node))
    log.info("Zapisano %d węzłów → %s", len(nodes), path)


def save_edges_csv(path: Path, edges: set) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target"])
        for src, dst in sorted(edges):
            writer.writerow([src, dst])
    log.info("Zapisano %d krawędzi → %s", len(edges), path)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Buduje graf wywołań z dumpów RTL gcc -fdump-rtl-expand"
    )
    p.add_argument("--linux-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, default=None)
    p.add_argument("--workers", type=int, default=max(1, os.cpu_count() - 1))
    return p.parse_args()


def main() -> None:
    args = parse_args()
    linux_dir = args.linux_dir.resolve()
    output_dir = (args.output_dir or Path(__file__).resolve().parent).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    dumps = find_rtl_dumps(linux_dir)
    if not dumps:
        log.error(
            "Nie znaleziono plików *.expand w %s\n"
            "Uruchom build z flagą: make -j$(nproc) KCFLAGS='-fdump-rtl-expand'",
            linux_dir,
        )
        raise SystemExit(1)

    global_nodes: dict[str, Node] = {}
    global_edges: set[tuple[str, str]] = set()
    errors: list[str] = []

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_dump, d, linux_dir): d for d in dumps}
        for future in tqdm(
            as_completed(futures), total=len(dumps), desc="Parsowanie RTL"
        ):
            local_nodes, local_edges, err = future.result()
            merge_nodes(global_nodes, local_nodes)
            global_edges.update(local_edges)
            if err:
                errors.append(err)

    log.info("Graf: węzły=%d, krawędzie=%d", len(global_nodes), len(global_edges))
    if errors:
        log.warning("Błędy: %d plików", len(errors))

    save_nodes_csv(output_dir / "nodes.csv", global_nodes)
    save_edges_csv(output_dir / "edges.csv", global_edges)


if __name__ == "__main__":
    main()
