from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


def logs_dir() -> Path:
    backend_dir = Path(__file__).resolve().parents[5]
    d = backend_dir / "data" / "logs" / "pathway"
    d.mkdir(parents=True, exist_ok=True)
    return d


def allocate_log_file(job_id: int, job_name: str) -> str:
    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in (job_name or "job"))
    filename = f"{job_id}-{safe_name}.log"
    return str(logs_dir() / filename)


def allocate_monitoring_port() -> int:
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    _, port = s.getsockname()
    s.close()
    return int(port)


def parse_log_line(line: str) -> Tuple[str, str, str]:
    parts = [p.strip() for p in (line or "").split(" - ", 3)]
    if len(parts) >= 4:
        ts, _, level, msg = parts[0], parts[1], parts[2], parts[3]
        return ts, level.upper(), msg
    now = datetime.now(timezone.utc).isoformat()
    return now, "INFO", line


def tail_log_entries(log_file: str, limit: int = 200) -> List[Dict[str, Any]]:
    path = Path(log_file)
    if not path.exists() or not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    lines = lines[-max(1, min(int(limit), 2000)) :]
    entries: List[Dict[str, Any]] = []
    for ln in lines:
        ts, level, msg = parse_log_line(ln)
        if level not in {"INFO", "WARN", "ERROR", "DEBUG"}:
            level = "INFO"
        entries.append({"timestamp": ts, "level": level, "message": msg})
    return entries

