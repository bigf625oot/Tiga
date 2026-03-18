import re
from typing import Dict, Optional


def to_markdown(text: str, meta: Optional[Dict] = None) -> str:
    if not text:
        return ""
    s = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = s.split("\n")
    out = []
    i = 0
    title = None
    if isinstance(meta, dict):
        title = meta.get("title")
    while i < len(lines):
        line = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        m_setext_eq = re.fullmatch(r"\s*[=]+\s*", nxt or "")
        m_setext_dash = re.fullmatch(r"\s*[-]+\s*", nxt or "")
        if line.strip() and (m_setext_eq or m_setext_dash):
            lvl = "#" if m_setext_eq else "##"
            out.append(f"{lvl} {line.strip()}")
            i += 2
            continue
        i += 1
        out.append(line)
    norm = []
    prev_blank = False
    for line in out:
        cleaned = re.sub(r"<[^>]+>", "", line)
        cleaned = re.sub(
            r"^\s*#{1,6}\s*(.+)\s*$",
            lambda m: "#" * min(6, m.group(0).lstrip().count("#")) + " " + m.group(1).strip(),
            cleaned,
        )
        cleaned = re.sub(r"^\s*[•▪·–]\s+", "- ", cleaned)
        cleaned = re.sub(r"^\s*[\-\*]\s+", "- ", cleaned)
        cleaned = re.sub(r"^\s*(\d+)[\.\、\)．]\s+", lambda m: f"{m.group(1)}. ", cleaned)
        cleaned = re.sub(r"^\s*[（(]?(\d+)[）)]\s+", lambda m: f"{m.group(1)}. ", cleaned)
        cleaned = re.sub(r"^\s*([一二三四五六七八九十百千]+[、\.．])\s*", "## ", cleaned)
        cleaned = re.sub(r"^\s*[第]?\s*([一二三四五六七八九十百千0-9]+)\s*[章节节]\s*", "## ", cleaned)
        if re.fullmatch(r"\s*[-_*]{3,}\s*", cleaned):
            cleaned = "---"
        cleaned = re.sub(r"\*{3,}", "**", cleaned)
        cleaned = re.sub(r"_{3,}", "__", cleaned)
        cleaned = re.sub(r"\s+$", "", cleaned)
        if not cleaned.strip():
            if prev_blank:
                continue
            prev_blank = True
            norm.append("")
        else:
            prev_blank = False
            norm.append(cleaned)
    has_atx = any(re.match(r"^\s*#{1,6}\s+\S", ln) for ln in norm[:5])
    if title and not has_atx:
        norm = [f"# {title}", ""] + norm
    return "\n".join(norm).strip()
