#!/usr/bin/env python3
import argparse
import logging

import yaml

from src.github_search import search_repos
from src.repo_analyzer import analyze_repo
from src.summarizer import summarize_repo
from src.report_generator import generate_report
from src.repo_tester import test_repo
from src.comparator import compare_repos
from src.git_ops import commit_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="AI Research Agent")
    parser.add_argument("--config", default="config/settings.yaml", help="Path to config file")
    parser.add_argument("--no-commit", action="store_true", help="Skip git commit")
    parser.add_argument("--no-clone", action="store_true", help="Skip cloning and testing repos")
    parser.add_argument("--no-compare", action="store_true", help="Skip comparative analysis")
    args = parser.parse_args()

    config = load_config(args.config)
    search_cfg = config["search"]
    ollama_cfg = config["ollama"]
    advanced_cfg = config.get("advanced", {})

    do_clone = advanced_cfg.get("clone_and_test", True) and not args.no_clone
    do_compare = advanced_cfg.get("comparative_analysis", True) and not args.no_compare

    # Step 1: Search
    logger.info("Searching GitHub for new AI repositories...")
    repos = search_repos(
        queries=search_cfg["queries"],
        min_stars=search_cfg.get("min_stars", 5),
        max_repos=search_cfg.get("max_repos", 10),
        created_within_days=search_cfg.get("created_within_days", 1),
    )

    if not repos:
        logger.info("No new repositories found. Exiting.")
        return

    # Step 2: Analyze
    logger.info(f"Analyzing {len(repos)} repositories...")
    analyzed = []
    for repo in repos:
        analysis = analyze_repo(repo)
        analyzed.append(analysis)

    # Step 3: Summarize
    logger.info("Generating summaries...")
    for repo in analyzed:
        summary = summarize_repo(repo, ollama_cfg["endpoint"], ollama_cfg["model"])
        repo["summary"] = summary
        logger.info(f"  Summarized: {repo['full_name']}")

    # Step 4: Clone & Test (Advanced)
    if do_clone:
        logger.info("Cloning and testing repositories...")
        timeout = advanced_cfg.get("test_timeout_seconds", 60)
        for repo in analyzed:
            result = test_repo(repo, timeout=timeout)
            repo["test_results"] = result
            if result:
                logger.info(f"  Tested: {repo['full_name']} - "
                            f"{result.get('passed', 0)} passed, {result.get('failed', 0)} failed")

    # Step 5: Comparative Analysis (Advanced)
    comparative = None
    if do_compare and len(analyzed) >= 2:
        logger.info("Running comparative analysis...")
        comparative = compare_repos(analyzed, ollama_cfg["endpoint"], ollama_cfg["model"])

    # Step 6: Generate Report
    logger.info("Generating report...")
    report_path = generate_report(analyzed, comparative=comparative)
    logger.info(f"Report saved to {report_path}")

    # Step 7: Commit
    if not args.no_commit:
        logger.info("Committing report...")
        committed = commit_report(report_path)
        if committed:
            logger.info("Report committed successfully.")
        else:
            logger.info("No commit made.")

    logger.info("Done.")


if __name__ == "__main__":
    main()
