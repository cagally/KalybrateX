# KalybrateX - Claude Code Instructions

## Project Overview

KalybrateX is a rating platform for AI agent skills. We evaluate skills by running A/B comparisons: 
does the skill make Claude's output better than without it?

**Repository:** https://github.com/cagally/KalybrateX

## Key Concepts

- **Skill**: A SKILL.md file that extends Claude's capabilities
- **Quality Win Rate**: Our primary metric - how often does skill beat baseline
- **Security Grade**: Secondary metric - is the skill safe to use
- **Cost**: Secondary metric - token spend in USD per use

## Architecture

```
Discovery → Prompt Generator → Quality Evaluator → Scorer → Website
                                     ↓
                              Security Checker
```

1. **Discovery** (`discovery/`): Scrape SkillsMP for repos, fetch metadata + SKILL.md from GitHub
2. **Evaluator** (`evaluator/`): Generate prompts, run A/B comparisons, check security, score results
3. **Website** (`website/`): Display leaderboard and skill details

## Development Approach

- **Plan first**: Review PRDs, ask clarifying questions before building
- **Write tests first**: TDD - tests define acceptance criteria
- **One component at a time**: Follow the build plan phases
- **Keep it simple**: Avoid over-engineering
- **Verify before moving on**: Run tests, check outputs match expectations

## Important Context

### Claude Code Knowledge
When evaluating skills, the judge (Sonnet) must know that Claude Code features are REAL:
- Hooks (PreToolUse, PostToolUse, Notification, Stop)
- Custom slash commands
- SKILL.md files
- Rules and agents

This context MUST be added to judge prompts to avoid penalizing Claude Code-specific skills.

### Models Used
| Operation | Model | Why |
|-----------|-------|-----|
| Task execution | Haiku | Cost efficient |
| Prompt generation | Sonnet | Needs to understand SKILL.md |
| Judging | Sonnet | Needs nuance |
| Security check | Sonnet | Needs to understand code risks |

## Directory Structure

```
KalybrateX/
├── CLAUDE.md                 # This file
├── README.md                 # Project overview
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore
│
├── docs/                     # PRDs and planning docs
│   ├── 00-index.md
│   ├── 01-vision-and-goals.md
│   ├── 02-mvp-prd.md
│   ├── 03-build-plan.md
│   ├── 04-learnings.md
│   └── components/
│       └── 01-discovery-prd.md
│
├── discovery/
│   ├── __init__.py
│   ├── skillsmp_scraper.py   # Scrape skill list from SkillsMP
│   ├── github_fetcher.py     # Fetch metadata + SKILL.md from GitHub
│   ├── models.py             # Data structures
│   └── main.py               # CLI entry point
│
├── evaluator/
│   ├── __init__.py
│   ├── prompt_generator.py   # Generate comparison prompts from SKILL.md
│   ├── quality_evaluator.py  # Run A/B comparisons
│   ├── security_checker.py   # Analyze SKILL.md for security risks
│   ├── scorer.py             # Calculate win rate, grade, cost
│   ├── data_logger.py        # Save all evidence
│   ├── models.py             # Data structures
│   └── main.py               # CLI entry point
│
├── data/
│   ├── discovered/           # skills.json from discovery
│   ├── skills/               # Individual SKILL.md files
│   ├── evaluations/          # Full evidence per skill
│   └── leaderboard.json      # Aggregated rankings
│
├── tests/
│   ├── __init__.py
│   ├── test_discovery.py
│   ├── test_prompt_generator.py
│   ├── test_quality_evaluator.py
│   ├── test_security_checker.py
│   └── test_scorer.py
│
└── website/                  # Frontend (Phase 8)
```

## File Locations

| Data | Location |
|------|----------|
| Discovered skills | `data/discovered/skills.json` |
| SKILL.md files | `data/skills/{name}/SKILL.md` |
| Skill metadata | `data/skills/{name}/metadata.json` |
| Evaluation results | `data/evaluations/{name}/` |
| Leaderboard | `data/leaderboard.json` |

## Commands (after setup)

```bash
# Discovery
python -m discovery.main --all --limit 20

# Evaluation  
python -m evaluator.main --skill pdf
python -m evaluator.main --all

# Tests
pytest tests/
pytest tests/test_discovery.py -v
```

## Environment Variables

Required in `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...  # Required for evaluation
GITHUB_TOKEN=ghp_...          # Optional, for higher rate limits (5000/hr vs 60/hr)
```

## Metrics

### Primary: Quality Win Rate
```
Win Rate = Skill Wins / (Skill Wins + Baseline Wins)
```

| Win Rate | Grade |
|----------|-------|
| 80%+ | A |
| 60-79% | B |
| 40-59% | C |
| 20-39% | D |
| <20% | F |

### Secondary: Cost
- Tokens per use → $ estimate
- Tracked per evaluation

### Secondary: Security Grade
- Secure / Warning / Fail
- Based on SKILL.md analysis for risky patterns

## Build Phases

| Phase | Component | Status |
|-------|-----------|--------|
| 0 | Repo Setup | Pending |
| 1 | Discovery | Pending |
| 2 | Prompt Generator | Pending |
| 3 | Quality Evaluator | Pending |
| 4 | Security Checker | Pending |
| 5 | Scorer | Pending |
| 6 | Data Logger | Pending |
| 7 | CLI | Pending |
| 8 | Website | Pending |

See `docs/03-build-plan.md` for detailed phase specifications.

## Key Implementation Details

### Judge Context (CRITICAL)
Every judge prompt must include this context so Claude Code skills aren't unfairly penalized:

```
IMPORTANT CONTEXT:
These skills are designed for Claude Code users. Claude Code is Anthropic's 
CLI coding assistant with features including:
- Hooks (PreToolUse, PostToolUse, Notification, Stop, etc.)
- Custom slash commands  
- SKILL.md files for specialized capabilities
- Rules for validation and automation
- Custom agents

A response that provides Claude Code-specific configuration (hooks, rules, 
SKILL.md files) is VALUABLE and REAL, not fictional. Judge based on value 
to Claude Code users.
```

### A/B Comparison Flow
1. Run prompt WITHOUT skill → baseline response
2. Run prompt WITH skill (SKILL.md in system prompt) → skill response
3. Randomize which is shown as A vs B (avoid position bias)
4. Sonnet judges which is better
5. Record verdict + reasoning

### Data Sources
- **SkillsMP**: Only for discovering repo URLs (minimal scrape)
- **GitHub API**: All metadata (stars, description, last_updated, version)
- **GitHub Raw**: SKILL.md content
