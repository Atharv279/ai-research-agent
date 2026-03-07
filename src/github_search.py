import os
import logging
from datetime import datetime, timedelta, timezone

import requests

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


def _headers():
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def search_repos(queries: list[str], min_stars: int = 5,
                 max_repos: int = 10, created_within_days: int = 1) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=created_within_days)).strftime("%Y-%m-%d")
    seen = set()
    results = []

    for query in queries:
        if len(results) >= max_repos:
            break

        q = f"{query} created:>{since} stars:>={min_stars}"
        params = {"q": q, "sort": "stars", "order": "desc", "per_page": min(max_repos, 30)}

        try:
            resp = requests.get(f"{GITHUB_API}/search/repositories",
                                headers=_headers(), params=params, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.warning(f"Search failed for query '{query}': {e}")
            continue

        for item in resp.json().get("items", []):
            full_name = item["full_name"]
            if full_name in seen:
                continue
            seen.add(full_name)

            results.append({
                "full_name": full_name,
                "name": item["name"],
                "owner": item["owner"]["login"],
                "url": item["html_url"],
                "description": item.get("description") or "",
                "language": item.get("language") or "Unknown",
                "stars": item["stargazers_count"],
                "forks": item["forks_count"],
                "topics": item.get("topics", []),
                "created_at": item["created_at"],
                "size_kb": item.get("size", 0),
            })

            if len(results) >= max_repos:
                break

    logger.info(f"Found {len(results)} repositories across {len(queries)} queries")
    return results
