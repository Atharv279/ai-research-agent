import logging
from datetime import datetime, timezone

import git

logger = logging.getLogger(__name__)


def commit_report(report_path: str, repo_dir: str = ".") -> bool:
    try:
        repo = git.Repo(repo_dir)
    except git.InvalidGitRepositoryError:
        logger.warning(f"{repo_dir} is not a git repository, skipping commit")
        return False

    repo.index.add([report_path])

    if not repo.index.diff("HEAD") and not repo.untracked_files:
        logger.info("No changes to commit")
        return False

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    repo.index.commit(f"research: daily AI report {today}")
    logger.info(f"Committed report: {report_path}")
    return True
