import asyncio
import json
from pathlib import Path

from app.crud.crud_task_mode import task_mode
from app.db.session import AsyncSessionLocal


async def run(input_path: str, overwrite: bool = False):
    payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
    async with AsyncSessionLocal() as db:
        result = await task_mode.import_backup(db, payload=payload, overwrite=overwrite)
    print(result)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="inp", required=True)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    asyncio.run(run(args.inp, overwrite=args.overwrite))

