"""Append one line per raw file pulled: what, from where, when, and the data vintage if the source reports one."""
import csv
from datetime import datetime, timezone

from config import PROVENANCE_LOG, ROOT


def log_download(path, source, vintage="", note=""):
    PROVENANCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    new = not PROVENANCE_LOG.exists()
    with open(PROVENANCE_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["file", "source", "pulled_utc", "source_vintage", "note"])
        w.writerow([
            path.relative_to(ROOT).as_posix(),
            source,
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            vintage,
            note,
        ])
