import asyncio
import json
from datetime import datetime
from pathlib import Path

from app.crud.crud_task_mode import task_mode
from app.db.session import AsyncSessionLocal


async def run(output_path: str, task_id: str | None = None, include_logs: bool = True):
    async with AsyncSessionLocal() as db:
        tasks, versions, qas, logs = await task_mode.export_backup(db, task_id=task_id, include_logs=include_logs)

    payload = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "tasks": tasks,
        "versions": versions,
        "qas": qas,
        "logs": logs,
    }
    path = Path(output_path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--include-logs", action="store_true")
    args = parser.parse_args()

    asyncio.run(run(args.out, task_id=args.task_id, include_logs=args.include_logs))

