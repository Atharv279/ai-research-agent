# Contributing to ai-research-agent

Thanks for your interest in contributing\!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/ai-research-agent.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Install dependencies: `pip install -r requirements.txt -r dev-requirements.txt`
5. Make your changes
6. Run linting: `ruff check src/ main.py`
7. Submit a pull request

## What You Can Contribute

- **New search queries** — Add AI/ML topics to `config/settings.yaml`
- **Better prompts** — Improve the Ollama summarization prompts in `src/summarizer.py`
- **Report formatting** — Enhance markdown report templates in `src/report_generator.py`
- **Test frameworks** — Add detection for more test runners in `src/repo_tester.py`
- **Bug fixes** — Check the Issues tab for open bugs

## Code Style

- Follow PEP 8 (enforced by `ruff`)
- Keep functions focused and well-named
- Add docstrings for public functions

## Reporting Issues

Use the [bug report template](https://github.com/Atharv279/ai-research-agent/issues/new?template=bug_report.md) for bugs and the [feature request template](https://github.com/Atharv279/ai-research-agent/issues/new?template=feature_request.md) for ideas.
