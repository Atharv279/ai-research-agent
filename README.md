# AI Research Agent

Automated agent that discovers, analyzes, and reports on new AI/ML repositories on GitHub — daily.

## What It Does

1. **Searches** GitHub for newly created AI repositories (LLMs, agents, deep learning, transformers, etc.)
2. **Analyzes** each repo: README, language breakdown, dependencies, tech stack
3. **Summarizes** using a local Ollama LLM
4. **Clones & tests** repositories — detects test frameworks, runs tests, captures results
5. **Compares** repositories with scoring and LLM-written comparative narratives
6. **Commits** a daily markdown report to `reports/`

## Setup

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/) installed and running
- Git

### Install

```bash
pip install -r requirements.txt
ollama pull llama3.2
```

### Configure

Edit `config/settings.yaml` to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `search.queries` | Broad AI/ML terms | GitHub search keywords |
| `search.min_stars` | 5 | Minimum star count |
| `search.max_repos` | 10 | Max repos per run |
| `ollama.model` | llama3.2 | Ollama model name |
| `advanced.clone_and_test` | true | Clone repos and run tests |
| `advanced.comparative_analysis` | true | Generate comparative reports |

### Run

```bash
# Full pipeline
python main.py

# Without git commit
python main.py --no-commit

# Skip cloning/testing
python main.py --no-clone

# Skip comparative analysis
python main.py --no-compare

# Custom config
python main.py --config path/to/settings.yaml
```

Set `GITHUB_TOKEN` for higher API rate limits:

```bash
export GITHUB_TOKEN=ghp_your_token_here
python main.py
```

## Automation

The included GitHub Actions workflow (`.github/workflows/daily-research.yml`) runs the agent daily at 8 AM UTC. It installs Ollama in the runner, pulls the model, runs the agent, and pushes the report.

You can also trigger it manually from the Actions tab.

## Reports

Reports are saved to `reports/YYYY-MM-DD.md` and include:

- Per-repo analysis with metadata, tech stack, and LLM summary
- Test results (pass/fail counts, duration, framework)
- Comparative rankings with composite scoring
- LLM-written comparative narrative

## Project Structure

```
├── main.py                  # CLI entry point
├── config/settings.yaml     # Configuration
├── src/
│   ├── github_search.py     # GitHub API search
│   ├── repo_analyzer.py     # README, languages, dependencies
│   ├── summarizer.py        # Ollama LLM summaries
│   ├── repo_tester.py       # Clone, detect tests, run tests
│   ├── comparator.py        # Scoring and comparative analysis
│   ├── report_generator.py  # Markdown report generation
│   └── git_ops.py           # Git commit operations
├── reports/                 # Generated daily reports
└── .github/workflows/       # GitHub Actions automation
```
