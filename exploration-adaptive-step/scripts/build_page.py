"""Assemble the page text from summary_head.txt and data/tables.md (written as summary_page.txt; save as summary.md)."""

import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
tables = (root / "data" / "tables.md").read_text()
sections = {m.group(1): m.group(2).strip() for m in re.finditer(r"^## (\w+)[^\n]*\n\n(.*?)(?=^## |\Z)", tables, re.S | re.M)}
# accuracy appears twice (dt 0.2 and 0.6); keep the first
first = {}
for m in re.finditer(r"^## (\w+)[^\n]*\n\n(.*?)(?=^## |\Z)", tables, re.S | re.M):
    first.setdefault(m.group(1), m.group(2).strip())
text = (root / "scripts" / "summary_head.txt").read_text()
for k, v in first.items():
    text = text.replace("{{" + k + "}}", v)
(root / "summary_page.txt").write_text(text)
print(len(text), re.findall(r"\{\{\w+\}\}", text))
