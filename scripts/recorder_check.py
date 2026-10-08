from __future__ import annotations

import ast
from pathlib import Path


def _unrecorded_names(class_node: ast.ClassDef) -> set[str]:

    names: set[str] = set()
    for node in class_node.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(t, ast.Name) and t.id == "_unrecorded_attributes" for t in node.targets
        ):
            continue
        for literal in ast.walk(node.value):
            if isinstance(literal, ast.Constant) and isinstance(literal.value, str):
                names.add(literal.value)
    return names


def _growing_attributes(class_node: ast.ClassDef) -> set[str]:

    keys: set[str] = set()
    for node in class_node.body:
        if not isinstance(node, ast.FunctionDef) or node.name != "extra_state_attributes":
            continue
        for dict_node in ast.walk(node):
            if not isinstance(dict_node, ast.Dict):
                continue
            for key, value in zip(dict_node.keys, dict_node.values):
                if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                    continue
                is_comprehension = isinstance(value, (ast.ListComp, ast.List))
                is_snapshot_list = (
                    isinstance(value, ast.Call)
                    and isinstance(value.func, ast.Name)
                    and value.func.id == "_snap_list"
                )
                if is_comprehension or is_snapshot_list:
                    keys.add(key.value)
    return keys


def validate_recorder_attributes(sensor_path: Path) -> list[str]:

    if not sensor_path.exists():
        return [f"Missing file: {sensor_path}"]

    tree = ast.parse(sensor_path.read_text(encoding="utf-8"))
    errors: list[str] = []

    for class_node in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
        growing = _growing_attributes(class_node)
        if not growing:
            continue
        missing = sorted(growing - _unrecorded_names(class_node))
        if missing:
            errors.append(
                f"{class_node.name}: list attributes not in _unrecorded_attributes: "
                f"{', '.join(missing)}"
            )

    return errors


if __name__ == "__main__":
    import sys

    default = Path(__file__).resolve().parents[1] / "custom_components" / "battery_monitor" / "sensor.py"
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else default
    results = validate_recorder_attributes(target)
    if results:
        for item in results:
            print(item)
        raise SystemExit(1)
    print("All list attributes are excluded from the recorder")
