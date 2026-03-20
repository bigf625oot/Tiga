import argparse
import json
import re
from typing import Any, Dict, List, Optional, Tuple

import requests


def slugify(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    t = re.sub(r"-{2,}", "-", t).strip("-")
    return t or "mcp"


def registry_list_servers(limit: int = 100, cursor: Optional[str] = None, search: Optional[str] = None) -> Dict[str, Any]:
    url = "https://registry.modelcontextprotocol.io/v0/servers"
    params: Dict[str, Any] = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    if search:
        params["search"] = search
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        raise RuntimeError("Registry 返回非对象")
    return data


def pick_npm_stdio_package(server: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    packages = server.get("packages") or []
    if not isinstance(packages, list):
        return None
    for pkg in packages:
        if not isinstance(pkg, dict):
            continue
        if pkg.get("registryType") != "npm":
            continue
        transport = pkg.get("transport") or {}
        if isinstance(transport, dict) and transport.get("type") == "stdio":
            identifier = pkg.get("identifier")
            if isinstance(identifier, str) and identifier.strip():
                return pkg
    return None


def build_seed(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    server = item.get("server") or {}
    if not isinstance(server, dict):
        return None

    pkg = pick_npm_stdio_package(server)
    if not pkg:
        return None

    identifier = pkg["identifier"].strip()
    name = server.get("name")
    if not isinstance(name, str) or not name.strip():
        return None
    name = name.strip()

    description = server.get("description")
    if not isinstance(description, str):
        description = ""
    description = description.strip()
    if description:
        description = f"{description}（来源：MCP Registry）"
    else:
        description = "（来源：MCP Registry）"

    version = server.get("version")
    if not isinstance(version, str) or not version.strip():
        version = "1.0.0"

    official_meta = (item.get("_meta") or {}).get("io.modelcontextprotocol.registry/official")
    is_official = bool(official_meta)

    return {
        "slug": f"mcp-registry-{slugify(name)}",
        "name": name,
        "description": description,
        "version": version,
        "transport_type": "stdio",
        "config": {"command": "npx", "args": ["-y", identifier]},
        "env_vars": {},
        "category": "MCP Registry",
        "author": "MCP Registry",
        "is_official": is_official,
        "downloads": 0,
        "is_active": True,
        "status": "inactive",
    }


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", default="http://localhost:5173/api/v1")
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--update-existing", action="store_true")
    parser.add_argument("--only-official", action="store_true", default=True)
    parser.add_argument("--out", default=None, help="将生成的 seed 列表写入 JSON 文件")
    args = parser.parse_args()

    api_base = args.api_base.rstrip("/")

    existing = api_get_list(api_base, "/mcp/", params={"limit": 2000})
    by_slug = {x.get("slug"): x for x in existing if isinstance(x.get("slug"), str)}

    seeds: List[Dict[str, Any]] = []
    seen_slugs = set(by_slug.keys())
    cursor: Optional[str] = None
    fetched = 0

    while len(seeds) < max(0, args.limit):
        data = registry_list_servers(limit=max(1, args.page_size), cursor=cursor)
        items = data.get("servers") or []
        if not isinstance(items, list):
            break

        for item in items:
            if not isinstance(item, dict):
                continue

            if args.only_official:
                meta = (item.get("_meta") or {}).get("io.modelcontextprotocol.registry/official")
                if not meta:
                    continue

            seed = build_seed(item)
            if not seed:
                continue

            if seed["slug"] in seen_slugs:
                continue

            seeds.append(seed)
            seen_slugs.add(seed["slug"])
            if len(seeds) >= max(0, args.limit):
                break

        fetched += len(items)
        cursor = (data.get("metadata") or {}).get("nextCursor")
        if not cursor:
            break

        if fetched > 5000 and len(seeds) < max(0, args.limit):
            break

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(seeds, f, ensure_ascii=False, indent=2)

    created = 0
    updated = 0
    skipped = 0
    failed: List[Dict[str, Any]] = []

    if not args.dry_run:
        existing2 = api_get_list(api_base, "/mcp/", params={"limit": 5000})
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
