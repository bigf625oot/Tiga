from __future__ import annotations

import argparse
from pathlib import Path

REWRITE_MAP = {
    "from app.services.openclaw.exceptions import": (
        "from app.services.openclaw.common.errors import"
    ),
    "import app.services.openclaw.exceptions": (
        "import app.services.openclaw.common.errors"
    ),
    "from app.services.openclaw.metrics import": (
        "from app.services.openclaw.observability.dispatch_metrics import"
    ),
    "import app.services.openclaw.metrics": (
        "import app.services.openclaw.observability.dispatch_metrics"
    ),
}

TARGET_GLOBS = ("**/*.py", "**/*.md", "**/*.yml", "**/*.yaml")


def rewrite_file(file_path: Path, dry_run: bool) -> bool:
    original = file_path.read_text(encoding="utf-8")
    updated = original
    for old, new in REWRITE_MAP.items():
        updated = updated.replace(old, new)
    if updated == original:
        return False
    if not dry_run:
        file_path.write_text(updated, encoding="utf-8")
    return True


def run(root: Path, dry_run: bool) -> tuple[int, int]:
    scanned = 0
    changed = 0
    for pattern in TARGET_GLOBS:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            scanned += 1
            if rewrite_file(path, dry_run=dry_run):
                changed += 1
    return scanned, changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="project root path")
    parser.add_argument("--apply", action="store_true", help="apply rewrite")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    scanned, changed = run(root=root, dry_run=not args.apply)
    mode = "apply" if args.apply else "dry-run"
    print(f"mode={mode} scanned={scanned} changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
