import json
import logging

import requests

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are an AI research analyst. Analyze the following GitHub repository and provide a concise summary.

Repository: {name}
URL: {url}
Description: {description}
Primary Language: {language}
Stars: {stars}
Tech Stack: {tech_stack}

README (excerpt):
{readme_excerpt}

Provide your analysis in this format:
1. **What it does**: One-paragraph summary of the project's purpose and functionality.
2. **Key innovations**: What makes this project notable or different from existing solutions.
3. **Tech stack**: Languages, frameworks, and key dependencies used.
4. **Potential impact**: How this could affect the AI/ML ecosystem.
"""


def summarize_repo(repo_analysis: dict, ollama_endpoint: str, model: str) -> str:
    readme = repo_analysis.get("readme", "")
    readme_excerpt = readme[:2000] if readme else "No README available."

    tech_stack = ", ".join(repo_analysis.get("dependencies", [])) or "Not detected"
    if repo_analysis.get("languages"):
        lang_str = ", ".join(f"{k} ({v}%)" for k, v in repo_analysis["languages"].items())
        tech_stack = f"{lang_str}; {tech_stack}"

    prompt = PROMPT_TEMPLATE.format(
        name=repo_analysis["full_name"],
        url=repo_analysis["url"],
        description=repo_analysis.get("description", "No description"),
        language=repo_analysis.get("language", "Unknown"),
        stars=repo_analysis.get("stars", 0),
        tech_stack=tech_stack,
        readme_excerpt=readme_excerpt,
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
        logger.warning(f"Ollama summarization failed for {repo_analysis['full_name']}: {e}")
        return _fallback_summary(repo_analysis, readme_excerpt, tech_stack)


def _fallback_summary(repo: dict, readme_excerpt: str, tech_stack: str) -> str:
    return (
        f"**{repo['full_name']}** - {repo.get('description', 'No description')}\n\n"
        f"**Tech Stack:** {tech_stack}\n\n"
        f"**README excerpt:** {readme_excerpt[:500]}...\n\n"
        f"*Note: LLM summary unavailable. This is a raw analysis.*"
    )
