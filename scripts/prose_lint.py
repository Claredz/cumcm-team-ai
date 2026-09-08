#!/usr/bin/env python3
"""Advisory academic prose lint plus protected-token diff. Never an AI detector."""
from __future__ import annotations
import argparse
from collections import Counter
import json
import re
from pathlib import Path

RULES = [
    ("filler-zh", r"值得注意的是|毋庸置疑|众所周知|综上所述", "检查是否可删除铺垫，直接写具体结论"),
    ("inflation-zh", r"极大地|具有重大意义|革命性|卓越的|赋能|全方位", "删除无证据的程度词，或给出比较依据"),
    ("vague-source", r"研究表明|专家认为|有学者指出|studies show|experts believe", "给出可核查来源及具体结论"),
    ("filler-en", r"\bit is important to note that\b|\bin conclusion\b|\bin order to\b", "Prefer a direct statement when meaning is unchanged"),
    ("inflation-en", r"\bdelve\b|\bgroundbreaking\b|\brevolutionary\b|\bseamless\b|\bpivotal\b", "Check for unsupported significance or promotional language"),
    ("chat-leftover", r"希望这能帮助|作为一个AI|作为人工智能|as an AI|I hope this helps", "删除聊天残留，但保留正式 AI 使用声明"),
]
MATH = re.compile(r"\$\$.*?\$\$|(?<!\\)\$[^$\n]+\$|\\\[.*?\\\]|\\\(.*?\\\)|\\begin\{(equation\*?|align\*?)\}.*?\\end\{\1\}", re.S)
NUMBER = re.compile(r"(?<![A-Za-z0-9_])[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\s*%?")
CITATION = re.compile(r"\\(?:cite\w*|ref|eqref)\{[^}]+\}|\[(?:\d+(?:\s*[,–-]\s*\d+)*)\]|\]\([^)]+\)")


def mask_code(text):
    return re.sub(r"```.*?```|`[^`\n]+`", lambda m: "".join("\n" if c == "\n" else " " for c in m.group()), text, flags=re.S)


def lint(text):
    cleaned = mask_code(text)
    cleaned = MATH.sub(lambda m: "".join("\n" if c == "\n" else " " for c in m.group()), cleaned)
    findings = []
    for code, pattern, suggestion in RULES:
        for match in re.finditer(pattern, cleaned, re.I):
            findings.append({"rule": code, "line": cleaned.count("\n", 0, match.start())+1,
                             "match": match.group(), "suggestion": suggestion})
    return sorted(findings, key=lambda x: x["line"])


def protected(text):
    return {"numbers": Counter(m.group().strip() for m in NUMBER.finditer(text)),
            "math": Counter(m.group() for m in MATH.finditer(text)),
            "citations": Counter(m.group() for m in CITATION.finditer(text)),
            "negation": Counter(re.findall(r"不显著|未达到|不能|并非|无显著|\bnot\b|\bwithout\b", text, re.I))}


def compare(before, after):
    a, b = protected(before), protected(after)
    return {key: {"removed": list((a[key]-b[key]).elements()),
                  "added": list((b[key]-a[key]).elements())}
            for key in a if a[key] != b[key]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("file", type=Path)
    ap.add_argument("--compare", type=Path, help="candidate revision; do not overwrite original")
    ap.add_argument("--output", type=Path)
    a = ap.parse_args()
    text = a.file.read_text(encoding="utf-8")
    delta = compare(text, a.compare.read_text(encoding="utf-8")) if a.compare else {}
    result = {"findings": lint(text), "protected_changes": delta,
              "note": "Style suggestions only. Empty token diff does not establish semantic equivalence."}
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    raise SystemExit(2 if delta else 0)


if __name__ == "__main__":
    main()
