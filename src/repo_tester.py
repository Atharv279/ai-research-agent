import os
import shutil
import subprocess
import tempfile
import time
import logging

logger = logging.getLogger(__name__)

TEST_FRAMEWORKS = {
    "Python": {
        "detect": ["pytest.ini", "setup.cfg", "pyproject.toml", "tests/", "test/"],
        "install": "pip install -q -r requirements.txt 2>/dev/null; pip install -q pytest 2>/dev/null",
        "command": "python -m pytest --tb=short -q",
    },
    "JavaScript": {
        "detect": ["package.json", "jest.config.js", "jest.config.ts", ".mocharc.yml"],
        "install": "npm install --silent 2>/dev/null",
        "command": "npx jest --silent 2>/dev/null || npx mocha --exit 2>/dev/null",
    },
    "TypeScript": {
        "detect": ["package.json", "jest.config.ts", "tsconfig.json"],
        "install": "npm install --silent 2>/dev/null",
        "command": "npx jest --silent 2>/dev/null",
    },
    "Rust": {
        "detect": ["Cargo.toml"],
        "install": "",
        "command": "cargo test 2>&1",
    },
    "Go": {
        "detect": ["go.mod"],
        "install": "",
        "command": "go test ./... 2>&1",
    },
}


def _detect_framework(repo_dir: str, language: str) -> dict | None:
    contents = set()
    for item in os.listdir(repo_dir):
        contents.add(item)

    # Try the primary language first, then others
    ordered = [language] + [k for k in TEST_FRAMEWORKS if k != language]

    for lang in ordered:
        fw = TEST_FRAMEWORKS.get(lang)
        if not fw:
            continue
        for marker in fw["detect"]:
            check_path = os.path.join(repo_dir, marker.rstrip("/"))
            if os.path.exists(check_path):
                return fw

    return None


def _parse_test_output(output: str, framework_cmd: str) -> dict:
    passed = 0
    failed = 0

    for line in output.splitlines():
        line_lower = line.lower().strip()
        # pytest style: "5 passed, 2 failed"
        if "passed" in line_lower:
            for part in line_lower.split(","):
                part = part.strip()
                if "passed" in part:
                    try:
                        passed = int(part.split()[0])
                    except (ValueError, IndexError):
                        pass
                if "failed" in part:
                    try:
                        failed = int(part.split()[0])
                    except (ValueError, IndexError):
                        pass
        # jest style: "Tests: X passed, Y failed"
        if "tests:" in line_lower:
            parts = line_lower.split(",")
            for part in parts:
                part = part.strip()
                if "passed" in part:
                    try:
                        passed = int(part.split()[0])
                    except (ValueError, IndexError):
                        pass
                if "failed" in part:
                    try:
                        failed = int(part.split()[0])
                    except (ValueError, IndexError):
                        pass

    return {"passed": passed, "failed": failed}


def test_repo(repo: dict, timeout: int = 60) -> dict | None:
    size_mb = repo.get("size_kb", 0) / 1024
    if size_mb > 500:
        logger.warning(f"Skipping {repo['full_name']}: too large ({size_mb:.0f}MB)")
        return None

    tmpdir = tempfile.mkdtemp(prefix="ai-research-")

    try:
        logger.info(f"Cloning {repo['full_name']}...")
        clone_result = subprocess.run(
            ["git", "clone", "--depth=1", repo["url"], tmpdir + "/repo"],
            capture_output=True, text=True, timeout=60,
        )
        if clone_result.returncode != 0:
            logger.warning(f"Clone failed for {repo['full_name']}: {clone_result.stderr[:200]}")
            return None

        repo_dir = os.path.join(tmpdir, "repo")
        framework = _detect_framework(repo_dir, repo.get("language", ""))

        if not framework:
            logger.info(f"No test framework detected for {repo['full_name']}")
            return {"framework": "none", "passed": 0, "failed": 0,
                    "duration_seconds": 0, "error": "No test framework detected"}

        # Install dependencies
        if framework["install"]:
            subprocess.run(
                framework["install"], shell=True, cwd=repo_dir,
                capture_output=True, timeout=120,
            )

        # Run tests
        start = time.time()
        try:
            result = subprocess.run(
                framework["command"], shell=True, cwd=repo_dir,
                capture_output=True, text=True, timeout=timeout,
            )
            duration = round(time.time() - start, 2)
            output = result.stdout + "\n" + result.stderr
        except subprocess.TimeoutExpired:
            duration = timeout
            output = ""
            logger.warning(f"Tests timed out for {repo['full_name']}")
            return {"framework": framework["command"].split()[0],
                    "passed": 0, "failed": 0, "duration_seconds": duration,
                    "error": "Timeout"}

        counts = _parse_test_output(output, framework["command"])

        return {
            "framework": framework["command"].split()[0],
            "passed": counts["passed"],
            "failed": counts["failed"],
            "duration_seconds": duration,
            "output_excerpt": output[:500],
        }

    except Exception as e:
        logger.error(f"Error testing {repo['full_name']}: {e}")
        return None
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
