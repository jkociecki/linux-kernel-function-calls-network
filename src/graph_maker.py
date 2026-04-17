import clang.cindex
import csv
from tqdm import tqdm
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class Node:
    id: str
    func_name: str
    num_params: int
    module: str
    lines_of_code: int


edges: set[tuple[str, str]] = set()
nodes: dict[str, Node] = {}


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


def find_calls(cursor, caller_usr="global"):
    if cursor.kind == clang.cindex.CursorKind.FUNCTION_DECL:
        if cursor.is_definition():
            usr = cursor.get_usr()
            if usr:
                caller_usr = usr
                if usr not in nodes:
                    nodes[usr] = get_function_features(cursor, usr)

    elif cursor.kind == clang.cindex.CursorKind.CALL_EXPR:
        callee = cursor.referenced
        if callee and callee.kind == clang.cindex.CursorKind.FUNCTION_DECL:
            callee_usr = callee.get_usr()

            if callee_usr and caller_usr != "global":
                if caller_usr != callee_usr:
                    if callee_usr not in nodes:
                        nodes[callee_usr] = Node(
                            id=callee_usr,
                            func_name=callee.spelling,
                            num_params=len(list(callee.get_arguments())),
                            module="external/unknown",
                            lines_of_code=0,
                        )

                    edges.add((caller_usr, callee_usr))

    for child in cursor.get_children():
        find_calls(child, caller_usr)


if __name__ == "__main__":
    data = Path(__file__).resolve().parent.parent / "data"
    linux_dir = data / "linux"
    target_dir = linux_dir

    files = find_source_files(target_dir, {".c"})

    clang_args = [
        "-D__KERNEL__",
        f"-I{linux_dir}/include",
        f"-I{linux_dir}/arch/x86/include",
        "-nostdinc",
    ]

    index = clang.cindex.Index.create()

    for file in tqdm(files, desc="Processing files"):
        tu = index.parse(str(file), args=clang_args)
        find_calls(tu.cursor)

    base_dir = Path(__file__).resolve().parent

    nodes_csv = base_dir / "nodes.csv"
    with open(nodes_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "func_name", "num_params", "module", "lines_of_code"]
        )
        writer.writeheader()
        for node in nodes.values():
            writer.writerow(asdict(node))

    edges_csv = base_dir / "edges.csv"
    with open(edges_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "target"])
        for caller, callee in edges:
            writer.writerow([caller, callee])
