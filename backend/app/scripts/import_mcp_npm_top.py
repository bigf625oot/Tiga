import argparse
import json
import re
from typing import Any, Dict, List, Optional

import requests


def slugify(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    t = re.sub(r"-{2,}", "-", t).strip("-")
    return t or "mcp"


def npm_search(text: str, size: int = 250, from_offset: int = 0) -> Dict[str, Any]:
    url = "https://registry.npmjs.org/-/v1/search"
    params = {"text": text, "size": size, "from": from_offset}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        raise RuntimeError("NPM search 返回非对象")
    return data


def api_get_list(api_base: str, path: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    url = f"{api_base.rstrip('/')}/{path.lstrip('/')}"
    r = requests.get(url, params=params or {}, timeout=20)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def api_post(api_base: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{api_base.rstrip('/')}/{path.lstrip('/')}"
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        raise RuntimeError("POST 返回非对象")
    return data


def api_put(api_base: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{api_base.rstrip('/')}/{path.lstrip('/')}"
    r = requests.put(url, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        raise RuntimeError("PUT 返回非对象")
    return data


def build_seed(obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    pkg = obj.get("package") or {}
    if not isinstance(pkg, dict):
        return None

    name = pkg.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    name = name.strip()

    desc = pkg.get("description")
    if not isinstance(desc, str):
        desc = ""
    desc = desc.strip()
    if desc:
        desc = f"{desc}（来源：npm）"
    else:
        desc = "（来源：npm）"

    version = pkg.get("version")
    if not isinstance(version, str) or not version.strip():
        version = "1.0.0"

    publisher = pkg.get("publisher") or {}
    author = "npm"
    if isinstance(publisher, dict) and isinstance(publisher.get("username"), str) and publisher["username"].strip():
        author = publisher["username"].strip()

    is_official = name.startswith("@modelcontextprotocol/")

    return {
        "slug": f"mcp-npm-{slugify(name)}",
        "name": name,
        "description": desc,
        "version": version,
        "transport_type": "stdio",
        "config": {"command": "npx", "args": ["-y", name]},
        "env_vars": {},
        "category": "NPM MCP",
        "author": author,
        "is_official": is_official,
        "downloads": 0,
        "is_active": True,
        "status": "inactive",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", default="http://localhost:5173/api/v1")
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--query", default="mcp-server")
    parser.add_argument("--min-monthly", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--update-existing", action="store_true")
    parser.add_argument("--out", default=None, help="将生成的 seed 列表写入 JSON 文件")
    args = parser.parse_args()

    api_base = args.api_base.rstrip("/")

    existing = api_get_list(api_base, "/mcp/", params={"limit": 10000})
    by_slug = {x.get("slug"): x for x in existing if isinstance(x.get("slug"), str)}
    seen_slugs = set(by_slug.keys())

    data = npm_search(args.query, size=250, from_offset=0)
    objects = data.get("objects") or []
    if not isinstance(objects, list):
        objects = []

    candidates: List[Dict[str, Any]] = []
    for obj in objects:
        if not isinstance(obj, dict):
            continue
        downloads = obj.get("downloads") or {}
        monthly = 0
        if isinstance(downloads, dict) and isinstance(downloads.get("monthly"), int):
            monthly = downloads["monthly"]
        if monthly < max(0, args.min_monthly):
            continue
        seed = build_seed(obj)
        if not seed:
            continue
        if seed["slug"] in seen_slugs:
            continue
        candidates.append({"seed": seed, "monthly": monthly})
        seen_slugs.add(seed["slug"])

    candidates.sort(key=lambda x: x.get("monthly", 0), reverse=True)
    seeds = [x["seed"] for x in candidates[: max(0, args.limit)]]

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(seeds, f, ensure_ascii=False, indent=2)

    created = 0
    updated = 0
    skipped = 0
    failed: List[Dict[str, Any]] = []

    if not args.dry_run:
        existing2 = api_get_list(api_base, "/mcp/", params={"limit": 10000})
        by_slug2 = {x.get("slug"): x for x in existing2 if isinstance(x.get("slug"), str)}
    else:
        by_slug2 = by_slug

    for seed in seeds:
        try:
            exact = by_slug2.get(seed["slug"])
            if exact and args.update_existing:
                if args.dry_run:
                    updated += 1
                else:
                    api_put(api_base, f"/mcp/{exact['id']}", seed)
                    updated += 1
                continue

            if exact:
                skipped += 1
                continue

            if args.dry_run:
                created += 1
                continue

            api_post(api_base, "/mcp/", seed)
            created += 1
        except Exception as e:
            failed.append({"slug": seed.get("slug"), "error": str(e)})

    print(
        json.dumps(
            {
                "api_base": api_base,
                "query": args.query,
                "requested": args.limit,
                "generated": len(seeds),
                "created": created,
                "updated": updated,
                "skipped": skipped,
                "failed": failed,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())

