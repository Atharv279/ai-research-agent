import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def generate_report(summaries: list[dict], comparative: str | None = None,
                    output_dir: str = "reports") -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"{today}.md")

    lines = [
        f"# AI Research Report - {today}",
        "",
        f"*Automated scan found **{len(summaries)}** new repositories.*",
        "",
        "## Table of Contents",
        "",
    ]

    for i, entry in enumerate(summaries, 1):
        anchor = entry["full_name"].replace("/", "").replace(".", "").lower()
        lines.append(f"{i}. [{entry['full_name']}](#{anchor})")

    if comparative:
        lines.append(f"{len(summaries) + 1}. [Comparative Analysis](#comparative-analysis)")

    lines.append("")
    lines.append("---")
    lines.append("")

    for entry in summaries:
        repo = entry
        lines.extend([
            f"## {repo['full_name']}",
            "",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| **URL** | [{repo['url']}]({repo['url']}) |",
            f"| **Stars** | {repo.get('stars', 'N/A')} |",
            f"| **Language** | {repo.get('language', 'Unknown')} |",
            f"| **Created** | {repo.get('created_at', 'Unknown')[:10]} |",
            "",
        ])

        if repo.get("languages"):
            lines.append("**Language Breakdown:**")
            for lang, pct in repo["languages"].items():
                lines.append(f"- {lang}: {pct}%")
            lines.append("")

        if repo.get("dependencies"):
            lines.append("**Dependencies:** " + ", ".join(repo["dependencies"]))
            lines.append("")

        if repo.get("test_results"):
            tr = repo["test_results"]
            lines.extend([
                "**Test Results:**",
                f"- Framework: {tr.get('framework', 'Unknown')}",
                f"- Passed: {tr.get('passed', 'N/A')}",
                f"- Failed: {tr.get('failed', 'N/A')}",
                f"- Duration: {tr.get('duration_seconds', 'N/A')}s",
                "",
            ])

        lines.append("### Summary")
        lines.append("")
        lines.append(repo.get("summary", "*No summary available.*"))
        lines.append("")
        lines.append("---")
        lines.append("")

    if comparative:
        lines.extend([
            "## Comparative Analysis",
            "",
            comparative,
            "",
        ])

    content = "\n".join(lines)

    with open(filepath, "w") as f:
        f.write(content)

    logger.info(f"Report written to {filepath}")
    return filepath
