from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _flatten_keys(value: Any, prefix: str = "") -> set[str]:
    keys: set[str] = set()

    if isinstance(value, dict):
        for key, child in value.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            if isinstance(child, dict):
                keys |= _flatten_keys(child, new_prefix)
            else:
                keys.add(new_prefix)
    return keys


def validate_translation_files(base_dir: Path) -> list[str]:
    """Ensure all language files keep the same keys as strings.json."""
    errors: list[str] = []
    strings_path = base_dir / "strings.json"
    if not strings_path.exists():
        return [f"Missing base file: {strings_path}"]

    base_data = _load_json(strings_path)
    base_keys = _flatten_keys(base_data)

    translations_dir = base_dir / "translations"
    if not translations_dir.exists():
        return [f"Missing translations directory: {translations_dir}"]

    for file_path in sorted(translations_dir.glob("*.json")):
        try:
            lang_data = _load_json(file_path)
        except json.JSONDecodeError as exc:
            errors.append(f"{file_path.name}: invalid JSON ({exc})")
            continue

        lang_keys = _flatten_keys(lang_data)
        missing = sorted(base_keys - lang_keys)
        extra = sorted(lang_keys - base_keys)

        if missing:
            errors.append(f"{file_path.name}: missing keys: {', '.join(missing)}")
        if extra:
            errors.append(f"{file_path.name}: extra keys: {', '.join(extra)}")

    return errors


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
    results = validate_translation_files(target)
    if results:
        for item in results:
            print(item)
        raise SystemExit(1)
    print("All translation files match strings.json")
