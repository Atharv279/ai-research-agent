import logging
from collections import defaultdict

import requests

logger = logging.getLogger(__name__)


def _group_repos(repos: list[dict]) -> dict[str, list[dict]]:
    groups = defaultdict(list)
    for repo in repos:
        lang = repo.get("language", "Unknown")
        groups[lang].append(repo)
    return dict(groups)


def _score_repo(repo: dict) -> float:
    score = 0.0
    score += min(repo.get("stars", 0) / 100, 5.0)

    readme_len = len(repo.get("readme", ""))
    if readme_len > 1000:
        score += 2.0
    elif readme_len > 300:
        score += 1.0

    if repo.get("test_results"):
        tr = repo["test_results"]
        if tr.get("passed", 0) > 0:
            score += 3.0
        if tr.get("failed", 0) == 0 and tr.get("passed", 0) > 0:
            score += 1.0

    if repo.get("dependencies"):
        score += min(len(repo["dependencies"]) * 0.5, 2.0)

    return round(score, 2)


def _build_comparison_table(repos: list[dict]) -> str:
    scored = [(repo, _score_repo(repo)) for repo in repos]
    scored.sort(key=lambda x: x[1], reverse=True)

    lines = [
        "### Rankings",
        "",
        "| Rank | Repository | Stars | Language | Tests | Score |",
        "|------|-----------|-------|----------|-------|-------|",
    ]

    for i, (repo, score) in enumerate(scored, 1):
        test_status = "N/A"
        if repo.get("test_results"):
            tr = repo["test_results"]
            if tr.get("error"):
                test_status = tr["error"]
            else:
                test_status = f"{tr['passed']}P/{tr['failed']}F"

        lines.append(
            f"| {i} | [{repo['full_name']}]({repo['url']}) "
            f"| {repo.get('stars', 0)} | {repo.get('language', '?')} "
            f"| {test_status} | {score} |"
        )

    return "\n".join(lines)


def _llm_comparison(repos: list[dict], ollama_endpoint: str, model: str) -> str:
    summaries_text = ""
    for repo in repos:
        summaries_text += (
            f"- {repo['full_name']} ({repo.get('language', '?')}, "
            f"{repo.get('stars', 0)} stars): {repo.get('summary', repo.get('description', ''))[:200]}\n"
        )

    prompt = (
        "You are an AI research analyst. Compare these repositories found today "
        "and write a brief comparative narrative (3-5 paragraphs). Highlight which "
        "projects are most innovative, which have the best engineering practices, "
        "and what trends you observe.\n\n"
        f"Repositories:\n{summaries_text}"
    )

    try:
        resp = requests.post(
            f"{ollama_endpoint}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except requests.RequestException as e:
        logger.warning(f"LLM comparison failed: {e}")
        return ""


def compare_repos(repos: list[dict], ollama_endpoint: str, model: str) -> str:
    if len(repos) < 2:
        return ""

    sections = []

    # Group-level analysis
    groups = _group_repos(repos)
    if len(groups) > 1:
        sections.append("### Breakdown by Language")
        sections.append("")
        for lang, group in sorted(groups.items(), key=lambda x: -len(x[1])):
            names = ", ".join(r["full_name"] for r in group)
            sections.append(f"- **{lang}** ({len(group)}): {names}")
        sections.append("")

    # Rankings table
    sections.append(_build_comparison_table(repos))
    sections.append("")

    # LLM narrative
    narrative = _llm_comparison(repos, ollama_endpoint, model)
    if narrative:
        sections.append("### Analysis")
        sections.append("")
        sections.append(narrative)

    return "\n".join(sections)
