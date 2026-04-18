import clang.cindex
import csv
import os
from tqdm import tqdm
from pathlib import Path
from dataclasses import dataclass, asdict
from concurrent.futures import ProcessPoolExecutor, as_completed

@dataclass
class Node:
    id: str
    func_name: str
    num_params: int
    module: str
    lines_of_code: int

def find_source_files(directory: Path, extensions: set[str]) -> list[Path]:
    source_files = []
    for ext in extensions:
        source_files.extend(directory.rglob(f"*{ext}"))
    return source_files

def get_function_features(cursor, usr_id: str) -> Node:
    file_name = cursor.location.file.name if cursor.location.file else "unknown"
    module_name = Path(file_name).name

    start_line = cursor.extent.start.line
    end_line = cursor.extent.end.line
    loc = (end_line - start_line + 1) if (start_line and end_line) else 0

    params_count = len(list(cursor.get_arguments()))

    return Node(
        id=usr_id,
        func_name=cursor.spelling,
        num_params=params_count,
        module=module_name,
        lines_of_code=loc,
    )

def process_single_file(file_path: Path, clang_args: list) -> tuple[dict, set]:
    """Ta funkcja działa w odizolowanym procesie dla jednego pliku."""
    local_nodes = {}
    local_edges = set()
    
    index = clang.cindex.Index.create()
    tu = index.parse(str(file_path), args=clang_args)

    def find_calls_local(cursor, caller_usr="global"):
        if cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            if cursor.is_definition():
                usr = cursor.get_usr()
                if usr:
                    caller_usr = usr
                    if usr not in local_nodes:
                        local_nodes[usr] = get_function_features(cursor, usr)

        elif cursor.kind == clang.cindex.CursorKind.CALL_EXPR:
            callee = cursor.referenced
            if callee and callee.kind == clang.cindex.CursorKind.FUNCTION_DECL:
                callee_usr = callee.get_usr()

                if callee_usr and caller_usr != "global":
                    if caller_usr != callee_usr:
                        if callee_usr not in local_nodes:
                            local_nodes[callee_usr] = Node(
                                id=callee_usr,
                                func_name=callee.spelling,
                                num_params=len(list(callee.get_arguments())),
                                module="external/unknown",
                                lines_of_code=0,
                            )
                        local_edges.add((caller_usr, callee_usr))

        for child in cursor.get_children():
            find_calls_local(child, caller_usr)

    find_calls_local(tu.cursor)
    return local_nodes, local_edges


if __name__ == "__main__":
    data = Path(__file__).resolve().parent.parent / "data"
    linux_dir = data / "linux"
    target_dir = linux_dir

    files = find_source_files(target_dir, {".c"})
    
    files = [f for f in files if "tools" not in f.parts]

    clang_args = [
        "-D__KERNEL__",
        f"-I{linux_dir}/include",
        f"-I{linux_dir}/arch/x86/include",
        "-nostdinc",
    ]

    global_nodes = {}
    global_edges = set()

    max_workers = max(1, os.cpu_count() - 1)
    print(f"Znaleziono {len(files)} plików. Uruchamiam analizę na {max_workers} rdzeniach...")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_single_file, f, clang_args) for f in files]
        
        for future in tqdm(as_completed(futures), total=len(files), desc="Przetwarzanie"):
            try:
                local_nodes, local_edges = future.result()
                global_nodes.update(local_nodes)
                global_edges.update(local_edges)
            except Exception as e:
                pass 

    base_dir = Path(__file__).resolve().parent

    nodes_csv = base_dir / "nodes.csv"
    with open(nodes_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "func_name", "num_params", "module", "lines_of_code"]
        )
        writer.writeheader()
        for node in global_nodes.values():
            writer.writerow(asdict(node))

    edges_csv = base_dir / "edges.csv"
    with open(edges_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target"])
        for caller, callee in global_edges:
            writer.writerow([caller, callee])
            
