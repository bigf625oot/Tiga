import argparse
import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests


@dataclass(frozen=True)
class RepoRef:
    owner: str
    repo: str
    ref: str


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


def gh_api_get(url: str, timeout_s: float = 15.0) -> Any:
    r = requests.get(url, timeout=timeout_s, headers={"Accept": "application/vnd.github+json"})
    r.raise_for_status()
    return r.json()


def get_repo_stars(repo_ref: RepoRef) -> Optional[int]:
    url = f"https://api.github.com/repos/{repo_ref.owner}/{repo_ref.repo}"
    try:
        data = gh_api_get(url)
        stars = data.get("stargazers_count")
        if isinstance(stars, int):
            return stars
    except Exception:
        return None
    return None


def list_skill_dirs(repo_ref: RepoRef, skills_path: str) -> List[str]:
    path = skills_path.strip("/")
    url = f"https://api.github.com/repos/{repo_ref.owner}/{repo_ref.repo}/contents/{path}?ref={repo_ref.ref}"
    data = gh_api_get(url)
    dirs = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("type") == "dir" and isinstance(item.get("name"), str):
                dirs.append(item["name"])
    return sorted(dirs)


def fetch_raw_skill_md(repo_ref: RepoRef, skill_dir: str, skills_path: str) -> Tuple[str, str]:
    base_path = "/".join([p for p in [skills_path.strip("/"), skill_dir.strip("/")] if p])
    candidates = [
        f"https://raw.githubusercontent.com/{repo_ref.owner}/{repo_ref.repo}/{repo_ref.ref}/{base_path}/SKILL.md",
        f"https://raw.githubusercontent.com/{repo_ref.owner}/{repo_ref.repo}/{repo_ref.ref}/{base_path}/skill.md",
        f"https://raw.githubusercontent.com/{repo_ref.owner}/{repo_ref.repo}/{repo_ref.ref}/{base_path}/SKILL.mdx",
        f"https://raw.githubusercontent.com/{repo_ref.owner}/{repo_ref.repo}/{repo_ref.ref}/{base_path}/{skill_dir}.md",
    ]
    last_err = None
    for url in candidates:
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200 and r.text.strip():
                return url, r.text
            last_err = f"{r.status_code} {url}"
        except Exception as e:
            last_err = str(e)
    raise RuntimeError(f"无法获取 SKILL.md: {repo_ref.owner}/{repo_ref.repo}/{base_path} ({last_err})")


def slugify(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    t = re.sub(r"-{2,}", "-", t).strip("-")
    return t or "skill"


def api_get_skills(api_base: str, q: str, limit: int = 5) -> List[Dict[str, Any]]:
    url = f"{api_base.rstrip('/')}/skills/"
    r = requests.get(url, params={"q": q, "limit": limit}, timeout=15)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def api_create_skill(api_base: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{api_base.rstrip('/')}/skills/"
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        raise RuntimeError("创建 skill 返回非对象")
    return data


def api_update_skill(api_base: str, skill_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{api_base.rstrip('/')}/skills/{skill_id}"
    r = requests.put(url, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        raise RuntimeError("更新 skill 返回非对象")
    return data


def build_skill_payload(
    repo_ref: RepoRef,
    skills_path: str,
    skill_dir: str,
    raw_url: str,
    markdown: str,
    repo_stars: Optional[int],
    version: str,
) -> Dict[str, Any]:
    fm, _ = parse_frontmatter(markdown)

    name = str(fm.get("name") or skill_dir).strip()
    description = str(fm.get("description") or "").strip()
    if "\n" in description:
        description = description.split("\n", 1)[0].strip()

    slug = slugify(f"{repo_ref.owner}-{repo_ref.repo}-{skill_dir}")

    tree_url = f"https://github.com/{repo_ref.owner}/{repo_ref.repo}/tree/{repo_ref.ref}/{skills_path.strip('/')}/{skill_dir}"
    skills_path_key = skills_path.strip("/").lstrip("./").strip()
    if skills_path_key == "skills":
        skillsmp_segment = "skills"
    elif skills_path_key.endswith("agents/skills") or skills_path_key.endswith("agents-skills") or "agents/skills" in skills_path_key:
        skillsmp_segment = "agents-skills"
    else:
        skillsmp_segment = "skills"
    skillsmp_url = f"https://skillsmp.com/zh/skills/{repo_ref.owner}-{repo_ref.repo}-{skillsmp_segment}-{skill_dir}-skill-md"

    meta_data = {
        "source": {"name": "skillsmp", "sortBy": "stars"},
        "github": {
            "owner": repo_ref.owner,
            "repo": repo_ref.repo,
            "ref": repo_ref.ref,
            "skills_path": skills_path,
            "skill_dir": skill_dir,
            "tree_url": tree_url,
            "raw_skill_md_url": raw_url,
            "stargazers_count": repo_stars,
        },
        "skillsmp": {"url": skillsmp_url},
        "frontmatter": fm,
    }

    return {
        "slug": slug,
        "name": name,
        "description": description,
        "version": version,
        "content": markdown,
        "author_id": "system",
        "is_official": False,
        "downloads": 0,
        "rating": 0,
        "is_active": True,
        "is_public": True,
        "meta_data": meta_data,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-base", default="http://localhost:5173/api/v1", help="例如 http://localhost:5173/api/v1")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--owner", default="openclaw")
    parser.add_argument("--repo", default="openclaw")
    parser.add_argument("--ref", default="main")
    parser.add_argument("--skills-path", default="skills")
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--update-existing", action="store_true")
    args = parser.parse_args()

    api_base = args.api_base.rstrip("/")
    repo_ref = RepoRef(owner=args.owner, repo=args.repo, ref=args.ref)

    repo_stars = get_repo_stars(repo_ref)
    skill_dirs = list_skill_dirs(repo_ref, args.skills_path)
    if not skill_dirs:
        raise RuntimeError("未发现任何 skill 目录")

    selected = skill_dirs[: max(0, args.limit)]

    created = 0
    updated = 0
    skipped = 0
    failed: List[Dict[str, Any]] = []

    for skill_dir in selected:
        try:
            raw_url, markdown = fetch_raw_skill_md(repo_ref, skill_dir, args.skills_path)
            payload = build_skill_payload(
                repo_ref=repo_ref,
                skills_path=args.skills_path,
                skill_dir=skill_dir,
                raw_url=raw_url,
                markdown=markdown,
                repo_stars=repo_stars,
                version=args.version,
            )

            existing = api_get_skills(api_base, payload["slug"], limit=5)
            exact = next((x for x in existing if x.get("slug") == payload["slug"]), None)

            if exact and args.update_existing:
                if args.dry_run:
                    updated += 1
                else:
                    api_update_skill(api_base, str(exact["id"]), payload)
                    updated += 1
                continue

            if exact:
                skipped += 1
                continue

            if args.dry_run:
                created += 1
                continue

            api_create_skill(api_base, payload)
            created += 1
        except Exception as e:
            failed.append({"skill_dir": skill_dir, "error": str(e)})

    print(
        json.dumps(
            {
                "repo": f"{repo_ref.owner}/{repo_ref.repo}@{repo_ref.ref}",
                "skills_path": args.skills_path,
                "requested": args.limit,
                "processed": len(selected),
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
