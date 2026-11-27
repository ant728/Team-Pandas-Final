"""Check the raw inputs before anything is computed (self-audit finding C). Runs after the downloads (steps 0-2).

1. Every file in data/raw/ is hashed (sha256) and listed in outputs/input_hashes.csv, so each run records
   exactly which inputs built its outputs. (inputs/ is versioned by git, so it isn't listed here.)
2. The pinned inputs in config.PINNED_INPUTS (CRSP, NIC, the NY Fed link, KRE) must exist and match their hash.
   On a mismatch the run stops: the outputs in the repo were built from different files.

Unpinned files, such as the FDIC API downloads, can change when the source revises its data; compare this
run's manifest with the committed one (git diff outputs/input_hashes.csv) to see which input changed.
"""
import csv
import hashlib

from config import INPUT_MANIFEST, PINNED_INPUTS, RAW, ROOT


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    missing = [p for p in PINNED_INPUTS if not (ROOT / p).exists()]
    assert not missing, (f"pinned inputs missing: {missing}. CRSP and NIC files are placed by hand "
                         "(README, How to run); the others are recreated by steps 0 and 2.")

    rows, mismatched = [], []
    for path in sorted(p for p in RAW.rglob("*") if p.is_file()):
        rel = path.relative_to(ROOT).as_posix()
        digest = sha256(path)
        pinned = PINNED_INPUTS.get(rel)
        status = "unpinned" if pinned is None else ("match" if digest == pinned else "MISMATCH")
        if status == "MISMATCH":
            mismatched.append(f"{rel} (expected {pinned[:12]}..., got {digest[:12]}...)")
        rows.append({"file": rel, "bytes": path.stat().st_size, "sha256": digest, "status": status})

    INPUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(INPUT_MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file", "bytes", "sha256", "status"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    n_match = sum(r["status"] == "match" for r in rows)
    print(f"{len(rows)} raw input files hashed -> {INPUT_MANIFEST.relative_to(ROOT).as_posix()}; "
          f"{n_match} of {len(PINNED_INPUTS)} pinned inputs match")
    assert not mismatched, ("pinned inputs changed: " + "; ".join(mismatched) + ". The committed outputs were built "
                            "from other files. Restore the originals, or update PINNED_INPUTS in config.py on purpose "
                            "and log why in specs_tried.md.")


if __name__ == "__main__":
    main()
