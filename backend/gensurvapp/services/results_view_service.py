"""Config-driven reader for the compact per-sample results viewer."""

from __future__ import annotations

import csv
import json
import re
from functools import lru_cache
from pathlib import Path


CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "results_view_config.json"


@lru_cache(maxsize=1)
def load_results_view_config() -> list[dict]:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _read_rows(path: Path, delimiter: str, header: bool) -> tuple[list[str], list]:
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        if header:
            reader = csv.DictReader(handle, delimiter=delimiter)
            return list(reader.fieldnames or []), list(reader)
        rows = list(csv.reader(handle, delimiter=delimiter))
        return [], rows


def _species_from_classification(classification: str) -> str:
    match = re.search(r"(?:^|;)s__([^;]+)", classification or "")
    if not match:
        return ""
    # GTDB suffixes species names with values such as _C.
    return re.sub(r"_[A-Z]+$", "", match.group(1).strip())


def _sample_species(root: Path, sample_id: str) -> str:
    path = root / "tools" / "gtdbtk" / f"{sample_id}.tsv"
    if not path.is_file() or path.stat().st_size == 0:
        return ""
    _, rows = _read_rows(path, "\t", True)
    return _species_from_classification(rows[0].get("classification", "")) if rows else ""


def _applies(entry: dict, species: str) -> bool:
    rule = entry.get("applies_to")
    if not rule:
        return True
    genus = species.split(" ", 1)[0] if species else ""
    return species in rule.get("species", []) or genus in rule.get("genera", [])


def _not_run(entry: dict) -> dict:
    return {
        "key": entry["key"], "title": entry["title"], "folder": entry["folder"],
        "status": "not_run", "columns": entry["columns"], "rows": [],
    }


def _read_entry(root: Path, sample_id: str, entry: dict) -> dict:
    filename = entry["file"].replace("{sample}", sample_id)
    path = root / entry["folder"] / filename
    if not path.is_file() or path.stat().st_size == 0:
        return _not_run(entry)

    delimiter = entry.get("delimiter", "\t")
    headers, raw_rows = _read_rows(path, delimiter, entry.get("header", True))
    columns = entry["columns"]

    if entry.get("handler") == "chewbbaca":
        if not raw_rows or "scheme" not in headers:
            return _not_run(entry)
        row = raw_rows[0]
        excluded = {"scheme", "FILE"}
        loci_called = sum(1 for key, value in row.items() if key not in excluded and value != "LNF")
        rows = [[row.get("scheme", ""), str(loci_called)]]
    elif entry.get("header", True):
        required = set(columns)
        filter_rule = entry.get("filter")
        if filter_rule:
            required.add(filter_rule["column"])
        if not required.issubset(headers):
            return _not_run(entry)
        if filter_rule:
            raw_rows = [r for r in raw_rows if r.get(filter_rule["column"]) == filter_rule["equals"]]
        rows = [[row.get(column, "") for column in columns] for row in raw_rows]
    else:
        positions = entry["use_columns"]
        rows = [
            [row[position] if position < len(row) else "" for position in positions]
            for row in raw_rows
        ]

    return {
        "key": entry["key"], "title": entry["title"], "folder": entry["folder"],
        "status": "available", "columns": columns, "rows": rows,
    }


def build_sample_analyses(root: Path, sample_id: str) -> dict:
    species = _sample_species(root, sample_id)
    analyses = [
        _read_entry(root, sample_id, entry)
        for entry in load_results_view_config()
        if _applies(entry, species)
    ]
    return {"sample_id": sample_id, "species": species or None, "analyses": analyses}
