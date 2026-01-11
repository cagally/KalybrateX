# KalybrateX

**The rating platform for AI agent skills.**

We answer one question: **Does this skill make Claude better?**

## What is KalybrateX?

There are 37,000+ skills on SkillsMP alone. No one knows which ones actually work. KalybrateX rates skills by running A/B comparisons - same prompt, with and without the skill - and measuring which produces better results.

## Core Metric: Quality Win Rate

```
Win Rate = Skill Wins / (Skill Wins + Baseline Wins)
```

| Grade | Win Rate |
|-------|----------|
| A | 80%+ |
| B | 60-79% |
| C | 40-59% |
| D | 20-39% |
| F | <20% |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run discovery
python -m discovery.main --all --limit 20

# Run evaluation
python -m evaluator.main --skill pdf

# Run tests
pytest tests/
```

## Architecture

```
Discovery → Prompt Generator → Quality Evaluator → Scorer → Website
                                     ↓
                              Security Checker
```

## Documentation

- [Vision & Goals](docs/01-vision-and-goals.md)
- [MVP PRD](docs/02-mvp-prd.md)
- [Build Plan](docs/03-build-plan.md)
- [Learnings](docs/04-learnings.md)

## License

MIT
