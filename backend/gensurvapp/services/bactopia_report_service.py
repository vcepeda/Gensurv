"""
Reads Bactopia's own `bactopia summary` report (rank/reason per sample).
Shared by the per-submission results dashboard, the per-user dashboard's
QC column, and the global statistics QC card, so all three agree on what
counts as passed vs failed and share one cache.
"""

import csv
from pathlib import Path

from django.conf import settings

_report_cache = {"mtime": None, "rows": {}}


def load_bactopia_report() -> dict:
    """
    Returns {sample_id: {"rank": ..., "reason": ...}}, re-parsed whenever the
    file's mtime changes. Returns {} if the file isn't there (e.g. summary
    was never run) rather than erroring.
    """
    path = Path(getattr(settings, "BACTOPIA_REPORT_PATH", ""))
    if not path.exists():
        return {}

    mtime = path.stat().st_mtime
    if _report_cache["mtime"] == mtime:
        return _report_cache["rows"]

    rows = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            sample = (row.get("sample") or "").strip()
            if sample:
                rows[sample] = {
                    "rank": (row.get("rank") or "").strip(),
                    "reason": (row.get("reason") or "").strip(),
                    "species": (row.get("species") or "").strip(),
                }

    _report_cache["mtime"] = mtime
    _report_cache["rows"] = rows
    return rows


def classify_rank(rank: str | None) -> str:
    """Maps a raw Bactopia rank to succeeded/failed/pending."""
    if rank is None:
        return "pending"
    return "failed" if rank == "exclude" else "succeeded"
