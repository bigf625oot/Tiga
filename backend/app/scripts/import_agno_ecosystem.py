import argparse
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests


@dataclass(frozen=True)
class RepoSource:
    owner: str
    repo: str
    ref: str
    skills_path: str


def _strip_quotes(value: str) -> str:
    v = value.strip()
    if len(v) >= 2 and ((v[0] == v[-1] == '"') or (v[0] == v[-1] == "'")):
        return v[1:-1].strip()
    return v


def parse_frontmatter(markdown: str) -> Tuple[Dict[str, Any], str]:
    if not markdown.startswith("---"):
        return {}, markdown
    parts = markdown.split("\n")
    if len(parts) < 3 or parts[0].strip() != "---":
        return {}, markdown

    fm_lines: List[str] = []
    body_start = None
    for i in range(1, len(parts)):
        if parts[i].strip() == "---":
            body_start = i + 1
            break
        fm_lines.append(parts[i])

    if body_start is None:
        return {}, markdown

    frontmatter: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_list: Optional[List[str]] = None

    for raw in fm_lines:
        line = raw.rstrip("\n")
        if not line.strip():
            continue

        if current_key and current_list is not None:
            m_list = re.match(r"^\s*-\s*(.+?)\s*$", line)
            if m_list:
                current_list.append(_strip_quotes(m_list.group(1)))
                continue
            frontmatter[current_key] = current_list
            current_key = None
            current_list = None

        m_kv = re.match(r"^\s*([A-Za-z0-9_.-]+)\s*:\s*(.*?)\s*$", line)
        if not m_kv:
            continue

        key = m_kv.group(1)
        value = m_kv.group(2)

        if value == "":
            current_key = key
            current_list = []
            continue

        if value == "|" or value == ">":
            frontmatter[key] = ""
            continue

        frontmatter[key] = _strip_quotes(value)

    if current_key and current_list is not None:
        frontmatter[current_key] = current_list

    body = "\n".join(parts[body_start:])
    return frontmatter, body


def slugify(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    t = re.sub(r"-{2,}", "-", t).strip("-")
    return t or "skill"


def gh_api_get(url: str, timeout_s: float = 20.0) -> Any:
    r = requests.get(url, timeout=timeout_s, headers={"Accept": "application/vnd.github+json"})
    r.raise_for_status()
    return r.json()


def list_dirs(owner: str, repo: str, ref: str, path: str) -> List[str]:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path.strip('/')}?ref={ref}"
    data = gh_api_get(url)
    dirs: List[str] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("type") == "dir" and isinstance(item.get("name"), str):
                dirs.append(item["name"])
    return sorted(dirs)


def fetch_raw(owner: str, repo: str, ref: str, path: str) -> str:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path.lstrip('/')}"
    r = requests.get(url, timeout=30)
    if r.status_code != 200 or not r.text.strip():
        raise RuntimeError(f"无法获取文件: {url} ({r.status_code})")
    return r.text


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


def parse_repo_source(value: str) -> RepoSource:
    if ":" not in value:
        raise ValueError("skills source 格式应为 owner/repo@ref:path")
    left, skills_path = value.split(":", 1)
    if "@" in left:
        repo_full, ref = left.split("@", 1)
    else:
        repo_full, ref = left, "main"
    if "/" not in repo_full:
        raise ValueError("skills source repo 格式应为 owner/repo")
    owner, repo = repo_full.split("/", 1)
    return RepoSource(owner=owner.strip(), repo=repo.strip(), ref=ref.strip() or "main", skills_path=skills_path.strip())


def build_skill_payload(source: RepoSource, skill_dir: str, markdown: str) -> Dict[str, Any]:
    fm, _ = parse_frontmatter(markdown)
    name = str(fm.get("name") or skill_dir).strip()
    description = str(fm.get("description") or "").strip()
    if "\n" in description:
        description = description.split("\n", 1)[0].strip()

    slug = slugify(f"agno-{source.owner}-{source.repo}-{skill_dir}")
    return {
        "slug": slug,
        "name": name,
        "description": description,
        "version": "1.0.0",
        "content": markdown,
        "author_id": "system",
        "is_official": True,
        "downloads": 0,
        "rating": 0,
        "is_active": True,
        "is_public": True,
        "meta_data": {
            "source": {"name": "agno", "type": "skills"},
            "github": {
                "owner": source.owner,
                "repo": source.repo,
                "ref": source.ref,
                "skills_path": source.skills_path,
                "skill_dir": skill_dir,
                "raw_skill_md_url": f"https://raw.githubusercontent.com/{source.owner}/{source.repo}/{source.ref}/{source.skills_path.strip('/')}/{skill_dir}/SKILL.md",
            },
            "frontmatter": fm,
        },
    }


def import_skills(api_base: str, sources: List[RepoSource], limit: int, update_existing: bool, dry_run: bool) -> Dict[str, Any]:
    created = 0
    updated = 0
    skipped = 0
    failed: List[Dict[str, Any]] = []

    for source in sources:
        skill_dirs = list_dirs(source.owner, source.repo, source.ref, source.skills_path)
        selected = skill_dirs[: max(0, limit)]
        for skill_dir in selected:
            try:
                md_path = f"{source.skills_path.strip('/')}/{skill_dir}/SKILL.md"
                markdown = fetch_raw(source.owner, source.repo, source.ref, md_path)
                payload = build_skill_payload(source, skill_dir, markdown)

                existing = api_get_list(api_base, "/skills/", params={"q": payload["slug"], "limit": 10})
                exact = next((x for x in existing if x.get("slug") == payload["slug"]), None)

                if exact and update_existing:
                    if dry_run:
                        updated += 1
                    else:
                        api_put(api_base, f"/skills/{exact['id']}", payload)
                        updated += 1
                    continue

                if exact:
                    skipped += 1
                    continue

                if dry_run:
                    created += 1
                    continue

                api_post(api_base, "/skills/", payload)
                created += 1
            except Exception as e:
                failed.append({"source": f"{source.owner}/{source.repo}@{source.ref}:{source.skills_path}", "skill_dir": skill_dir, "error": str(e)})

    return {"created": created, "updated": updated, "skipped": skipped, "failed": failed}


def default_agno_mcp_seeds() -> List[Dict[str, Any]]:
    return [
        {
            "slug": "agno-mcp-git",
            "name": "MCP Git (Agno 示例)",
            "description": "Agno MCP 示例：通过 stdio 运行 mcp-server-git（uvx）。",
            "version": "1.0.0",
            "transport_type": "stdio",
            "config": {"command": "uvx", "args": ["mcp-server-git"]},
            "env_vars": {},
            "category": "Agno / MCP",
            "author": "Agno",
            "is_official": True,
            "downloads": 0,
            "is_active": True,
            "status": "inactive",
        },
        {
            "slug": "agno-mcp-airbnb",
            "name": "MCP Airbnb (Agno 示例)",
            "description": "Agno MCP 示例：通过 stdio 运行 @openbnb/mcp-server-airbnb。",
            "version": "1.0.0",
            "transport_type": "stdio",
            "config": {"command": "npx", "args": ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"]},
            "env_vars": {},
            "category": "Agno / MCP",
            "author": "Agno",
            "is_official": False,
            "downloads": 0,
            "is_active": True,
            "status": "inactive",
        },
        {
            "slug": "agno-mcp-brave-search",
            "name": "MCP Brave Search (Agno 示例)",
            "description": "Agno MCP 示例：通过 stdio 运行 @modelcontextprotocol/server-brave-search（需要 BRAVE_API_KEY）。",
            "version": "1.0.0",
            "transport_type": "stdio",
            "config": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-brave-search"]},
            "env_vars": {},
            "category": "Agno / MCP",
            "author": "Agno",
            "is_official": False,
            "downloads": 0,
            "is_active": True,
            "status": "inactive",
        },
    ]


def import_mcp(api_base: str, seeds: List[Dict[str, Any]], update_existing: bool, dry_run: bool) -> Dict[str, Any]:
    created = 0
    updated = 0
    skipped = 0
    failed: List[Dict[str, Any]] = []

    existing = api_get_list(api_base, "/mcp/", params={"limit": 1000})
    by_slug = {x.get("slug"): x for x in existing if isinstance(x.get("slug"), str)}

    for seed in seeds:
        slug = seed.get("slug")
        if not isinstance(slug, str) or not slug:
            failed.append({"seed": seed, "error": "缺少 slug"})
            continue

        try:
            exact = by_slug.get(slug)
            if exact and update_existing:
                if dry_run:
                    updated += 1
                else:
                    api_put(api_base, f"/mcp/{exact['id']}", seed)
                    updated += 1
                continue

            if exact:
                skipped += 1
                continue

            if dry_run:
                created += 1
                continue

            api_post(api_base, "/mcp/", seed)
            created += 1
        except Exception as e:
            failed.append({"slug": slug, "error": str(e)})

    return {"created": created, "updated": updated, "skipped": skipped, "failed": failed}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", default="http://localhost:5173/api/v1")
    parser.add_argument("--skills-source", action="append", default=[])
    parser.add_argument("--skills-limit", type=int, default=50)
    parser.add_argument("--enable-skills", action="store_true")
    parser.add_argument("--enable-mcp", action="store_true")
    parser.add_argument("--mcp-seed-file", default=None, help="JSON 文件：内容为 MCP seed 列表（数组）")
    parser.add_argument("--update-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    api_base = args.api_base.rstrip("/")

    skills_sources: List[RepoSource] = []
    if args.skills_source:
        skills_sources = [parse_repo_source(x) for x in args.skills_source]
    else:
        skills_sources = [parse_repo_source("agno-agi/agno-skills@main:plugins/agno/skills")]

    results: Dict[str, Any] = {"api_base": api_base, "dry_run": bool(args.dry_run), "update_existing": bool(args.update_existing)}

    if args.enable_skills or (not args.enable_skills and not args.enable_mcp):
        results["skills"] = import_skills(
            api_base=api_base,
            sources=skills_sources,
            limit=args.skills_limit,
            update_existing=bool(args.update_existing),
            dry_run=bool(args.dry_run),
        )

    if args.enable_mcp or (not args.enable_skills and not args.enable_mcp):
        mcp_seeds = default_agno_mcp_seeds()
        if args.mcp_seed_file:
            with open(args.mcp_seed_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if not isinstance(loaded, list):
                raise RuntimeError("--mcp-seed-file 内容必须是 JSON 数组")
            mcp_seeds = [x for x in loaded if isinstance(x, dict)]
        results["mcp"] = import_mcp(
            api_base=api_base,
            seeds=mcp_seeds,
            update_existing=bool(args.update_existing),
            dry_run=bool(args.dry_run),
        )

    print(json.dumps(results, ensure_ascii=False, indent=2))
    failed = []
    if isinstance(results.get("skills"), dict):
        failed += results["skills"].get("failed", [])
    if isinstance(results.get("mcp"), dict):
        failed += results["mcp"].get("failed", [])
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
