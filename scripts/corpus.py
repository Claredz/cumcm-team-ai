#!/usr/bin/env python3
"""Local authorized-paper corpus with provenance, content deduplication and QA."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path


def metrics(text, pages):
    return {"pages": pages, "characters": len(text.strip()),
            "chinese_characters": len(re.findall(r"[\u4e00-\u9fff]", text)),
            "figure_mentions_unique": len(set(re.findall(r"(?:图|Figure)\s*(\d+(?:\.\d+)?)", text, re.I))),
            "table_mentions_unique": len(set(re.findall(r"(?:表|Table)\s*(\d+(?:\.\d+)?)", text, re.I)))}


def ingest(directory: Path, manifest: dict):
    import pymupdf
    source_map = {item["filename"]: item for item in manifest.get("papers", [])}
    records, seen = [], {}
    for path in sorted(directory.rglob("*.pdf")):
        name = str(path.relative_to(directory))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        source = source_map.get(name, {})
        rec = {"filename": name, "sha256": digest, "source": source, "qa": [], "metrics": None}
        if digest in seen:
            rec.update(status="duplicate", duplicate_of=seen[digest])
        else:
            seen[digest] = name
            try:
                with pymupdf.open(path) as doc:
                    text = "\n".join(p.get_text(sort=True) for p in doc)
                    rec["metrics"] = metrics(text, len(doc))
                if len(text.strip()) < 200:
                    rec["qa"].append("image-only-or-short")
                if "\ufffd" in text:
                    rec["qa"].append("replacement-character")
                if not source.get("url") or not source.get("usage_basis"):
                    rec["qa"].append("missing-provenance")
                rec["status"] = "excluded" if rec["qa"] else "accepted"
            except Exception as exc:
                rec.update(status="error", error=str(exc))
        records.append(rec)
    return {"schema_version": 1, "root": str(directory.resolve()), "records": records,
            "scope": "Local descriptive analysis; raw PDFs are not published by this tool"}


def quantile(values, q):
    values = sorted(values)
    pos = (len(values)-1)*q
    lo = int(pos)
    hi = min(lo+1, len(values)-1)
    return values[lo] + (values[hi]-values[lo])*(pos-lo)


def stats(index):
    good = [r for r in index["records"] if r["status"] == "accepted"]
    groups = {"all": good}
    for r in good:
        s = r["source"]
        for key in [f"year:{s.get('year', 'unknown')}", f"topic:{s.get('topic', 'unknown')}"]:
            groups.setdefault(key, []).append(r)
    result = {}
    for key, records in groups.items():
        dimensions = {}
        if records:
            for field in records[0]["metrics"]:
                values = [r["metrics"][field] for r in records]
                dimensions[field] = {"p25": quantile(values, .25), "p50": quantile(values, .5),
                                     "p75": quantile(values, .75)}
        result[key] = {"n": len(records), "dimensions": dimensions}
    return {"total_files": len(index["records"]), "accepted": len(good), "groups": result,
            "limitations": "Extractable authorized subset only; mention counts are heuristics, not quality thresholds or award predictions"}


def discover(url, year):
    """Metadata only: read one official exhibition index; never download page images."""
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urlparse
    from urllib.request import urlopen, Request
    if urlparse(url).hostname != "dxs.moe.gov.cn":
        raise ValueError("Discovery is restricted to the official dxs.moe.gov.cn source index")
    class Links(HTMLParser):
        def __init__(self):
            super().__init__(); self.href = None; self.label = []; self.items = []
        def handle_starttag(self, tag, attrs):
            if tag == "a":
                self.href = dict(attrs).get("href"); self.label = []
        def handle_data(self, data):
            if self.href:
                self.label.append(data)
        def handle_endtag(self, tag):
            if tag == "a" and self.href:
                title = "".join(self.label).strip()
                match = re.search(r"[（(]([A-F]\d+)[）)]", title)
                if match:
                    self.items.append({"id": f"{year}-{match[1]}", "year": year,
                                       "topic": match[1][0], "title": title,
                                       "url": urljoin(url, self.href), "source_index": url,
                                       "usage_basis": "metadata-only; full-text redistribution not granted"})
                self.href = None
    with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=40) as response:
        text = response.read().decode("utf-8", errors="replace")
    parser = Links(); parser.feed(text)
    return list({item["id"]: item for item in parser.items}.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["ingest", "stats", "discover"])
    ap.add_argument("--papers-dir", type=Path)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--index", type=Path)
    ap.add_argument("--url")
    ap.add_argument("--year", type=int)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    if a.command == "ingest":
        if not a.papers_dir or not a.manifest:
            ap.error("ingest needs --papers-dir and --manifest")
        result = ingest(a.papers_dir, json.loads(a.manifest.read_text(encoding="utf-8")))
    elif a.command == "stats":
        if not a.index:
            ap.error("stats needs --index")
        result = stats(json.loads(a.index.read_text(encoding="utf-8")))
    else:
        if not a.url or not a.year:
            ap.error("discover needs --url and --year")
        result = {"papers": discover(a.url, a.year), "kind": "official-exhibition-metadata"}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(a.output)


if __name__ == "__main__":
    main()
