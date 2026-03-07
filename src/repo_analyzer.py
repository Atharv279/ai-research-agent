import base64
import logging

import requests

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"

DEPENDENCY_FILES = {
    "requirements.txt": "Python (pip)",
    "setup.py": "Python (setuptools)",
    "pyproject.toml": "Python (pyproject)",
    "package.json": "Node.js (npm)",
    "Cargo.toml": "Rust (cargo)",
    "go.mod": "Go (modules)",
    "Gemfile": "Ruby (bundler)",
    "pom.xml": "Java (Maven)",
    "build.gradle": "Java/Kotlin (Gradle)",
}


def _headers():
    import os
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch_readme(owner: str, repo: str) -> str:
    try:
        resp = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/readme",
                            headers=_headers(), timeout=15)
        resp.raise_for_status()
        content = resp.json().get("content", "")
        return base64.b64decode(content).decode("utf-8", errors="replace")
    except requests.RequestException:
        logger.warning(f"Could not fetch README for {owner}/{repo}")
        return ""


def _fetch_languages(owner: str, repo: str) -> dict:
    try:
        resp = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/languages",
                            headers=_headers(), timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException:
        logger.warning(f"Could not fetch languages for {owner}/{repo}")
        return {}


def _detect_dependencies(owner: str, repo: str) -> list[str]:
    detected = []
    try:
        resp = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/contents/",
                            headers=_headers(), timeout=15)
        resp.raise_for_status()
        filenames = {item["name"] for item in resp.json() if item["type"] == "file"}
        for dep_file, label in DEPENDENCY_FILES.items():
            if dep_file in filenames:
                detected.append(label)
    except requests.RequestException:
        logger.warning(f"Could not list root contents for {owner}/{repo}")
    return detected


def analyze_repo(repo: dict) -> dict:
    owner = repo["owner"]
    name = repo["name"]

    readme = _fetch_readme(owner, name)
    languages = _fetch_languages(owner, name)
    dependencies = _detect_dependencies(owner, name)

    total_bytes = sum(languages.values()) or 1
    language_breakdown = {lang: round(b / total_bytes * 100, 1)
                         for lang, b in languages.items()}

    return {
        **repo,
        "readme": readme,
        "languages": language_breakdown,
        "dependencies": dependencies,
    }
