# KalybrateX - Build Plan

## Overview

9 phases, built sequentially. Each phase has clear inputs, outputs, and acceptance criteria.

---

## Phase 0: Repository Setup

### Goal
Clean repo structure with all scaffolding in place.

### Tasks
1. Create directory structure (discovery/, evaluator/, data/, tests/, docs/, website/)
2. Create `requirements.txt` with dependencies
3. Create `.env.example` with required variables
4. Create `.gitignore`
5. Create empty `__init__.py` files
6. Create `README.md` with project overview
7. Copy docs into `docs/` folder

### Dependencies
```
# requirements.txt
anthropic>=0.18.0
httpx>=0.27.0
playwright>=1.40.0
pydantic>=2.0.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

### Acceptance Criteria
- [ ] All directories exist
- [ ] `pip install -r requirements.txt` succeeds
- [ ] `pytest` runs (even with no tests)
- [ ] `.env.example` documents all required vars

---

## Phase 1: Discovery

### Goal
Discover skills from SkillsMP, fetch metadata and SKILL.md from GitHub.

### Files
- `discovery/models.py` - Data structures
- `discovery/skillsmp_scraper.py` - Scrape repo URLs from SkillsMP
- `discovery/github_fetcher.py` - Fetch metadata + SKILL.md
- `discovery/main.py` - CLI orchestration
- `tests/test_discovery.py` - Unit + integration tests

### Input
- SkillsMP homepage (https://skillsmp.com)
- GitHub API

### Output
- `data/discovered/skills.json` - List of discovered skills with metadata
- `data/skills/{name}/SKILL.md` - Individual skill files
- `data/skills/{name}/metadata.json` - GitHub metadata per skill

### Key Implementation Notes
- SkillsMP is JS-rendered, use Playwright
- Filter for skills with `marketplace.json` (higher quality)
- GitHub API for metadata (stars, description, last_updated)
- GitHub Raw for SKILL.md content
- Try multiple branch names (main, master)
- Try multiple SKILL.md paths (root, src/, .claude/)

### Acceptance Criteria
- [ ] 15+ skills discovered with marketplace.json
- [ ] GitHub metadata complete (stars, description, default_branch, last_updated)
- [ ] 80%+ SKILL.md fetch success rate
- [ ] All tests pass
- [ ] Re-running doesn't duplicate entries

---

## Phase 2: Prompt Generator

### Goal
Auto-generate comparison prompts from SKILL.md content.

### Files
- `evaluator/prompt_generator.py`
- `tests/test_prompt_generator.py`

### Input
- SKILL.md content

### Output
- 10 comparison prompts per skill
- Cached in `data/skills/{name}/prompts.json`

### Key Implementation Notes
- Sonnet reads SKILL.md, extracts capabilities
- Generates realistic user prompts (not "use the X skill")
- Mix of difficulty levels
- Prompts should naturally require skill's capabilities

### Acceptance Criteria
- [ ] Generates 10 prompts per skill
- [ ] Prompts are realistic user requests
- [ ] No mention of skill name in prompts
- [ ] Caches results (doesn't regenerate if exists)

---

## Phase 3: Quality Evaluator

### Goal
Run A/B comparisons to determine if skill beats baseline.

### Files
- `evaluator/quality_evaluator.py`
- `tests/test_quality_evaluator.py`

### Input
- SKILL.md content
- Generated prompts

### Output
- Per-comparison results (both responses, verdict, reasoning)
- Saved to `data/evaluations/{name}/comparisons/`

### A/B Flow
1. Run prompt WITHOUT skill → baseline response (Haiku)
2. Run prompt WITH skill in system prompt → skill response (Haiku)
3. Randomize A/B order
4. Sonnet judges which is better
5. Record verdict + reasoning + tokens

### CRITICAL: Judge Context
Every judge prompt MUST include Claude Code context:
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
SKILL.md files) is VALUABLE and REAL, not fictional.
```

### Acceptance Criteria
- [ ] Runs 10 comparisons per skill
- [ ] Both responses captured in full
- [ ] Position randomized (avoid bias)
- [ ] Judge reasoning captured
- [ ] Token counts tracked
- [ ] Judge context included in every prompt

---

## Phase 4: Security Checker

### Goal
Analyze SKILL.md for security risks.

### Files
- `evaluator/security_checker.py`
- `tests/test_security_checker.py`

### Input
- SKILL.md content

### Output
- Security grade: Secure / Warning / Fail
- List of identified issues
- Saved to `data/evaluations/{name}/security.json`

### Risk Categories
- Data exfiltration (external URLs, webhooks)
- File system abuse (arbitrary paths, deletion)
- Credential theft (env vars, API keys)
- Code injection (eval, exec patterns)
- Malicious dependencies

### Acceptance Criteria
- [ ] Returns grade + issues list
- [ ] Catches obvious red flags
- [ ] Doesn't false-positive on legitimate patterns
- [ ] Single Sonnet call per skill (~$0.02)

---

## Phase 5: Scorer

### Goal
Calculate final scores and grades.

### Files
- `evaluator/scorer.py`
- `tests/test_scorer.py`

### Input
- Comparison results
- Security results
- Token usage

### Output
- Win rate percentage
- Letter grade
- Cost per use estimate
- Saved to `data/evaluations/{name}/score.json`

### Scoring Formula
```
Win Rate = Skill Wins / (Skill Wins + Baseline Wins)
# Ties don't count against either side

Grade:
- A: 80%+
- B: 60-79%
- C: 40-59%
- D: 20-39%
- F: <20%
```

### Cost Calculation
```python
avg_tokens = sum(all_output_tokens) / num_comparisons
cost_per_use = avg_tokens * haiku_price_per_token
```

### Acceptance Criteria
- [ ] Correct win rate calculation
- [ ] Correct grade assignment
- [ ] Cost estimate in USD
- [ ] Handles edge cases (all wins, all losses, all ties)

---

## Phase 6: Data Logger

### Goal
Save all evaluation evidence for transparency.

### Files
- `evaluator/data_logger.py`
- `tests/test_data_logger.py`

### Output Structure
```
data/evaluations/{skill_name}/
├── skill.md                    # Copy of SKILL.md tested
├── prompts.json                # Generated prompts
├── comparisons/
│   └── {n}.json                # Both responses, verdict, reasoning
├── security.json               # Security analysis
├── score.json                  # Final score
└── summary.json                # Aggregated results
```

### Acceptance Criteria
- [ ] All evidence saved (not truncated)
- [ ] Full responses captured
- [ ] Can reconstruct any rating from saved data
- [ ] Timestamps on all files

---

## Phase 7: CLI

### Goal
Single entry point to run evaluations.

### Files
- `evaluator/main.py`

### Commands
```bash
# List discovered skills
python -m evaluator.main --list

# Evaluate one skill
python -m evaluator.main --skill pdf

# Evaluate all skills
python -m evaluator.main --all

# Force re-evaluation
python -m evaluator.main --skill pdf --force

# Skip security check
python -m evaluator.main --skill pdf --skip-security
```

### Output
- Updates `data/leaderboard.json` after each evaluation
- Prints summary to console

### Acceptance Criteria
- [ ] All commands work
- [ ] Progress displayed during evaluation
- [ ] Errors handled gracefully
- [ ] Leaderboard updated atomically

---

## Phase 8: Website

### Goal
Public leaderboard showing skill ratings.

### Stack
- React or Next.js
- Static site (can host on Vercel/Netlify)
- Reads from `data/leaderboard.json`

### Pages
1. **Leaderboard** - Ranked list of skills with grades
2. **Skill Detail** - Full breakdown for one skill
3. **Methodology** - How we rate skills

### Skill Card Shows
- Skill name + description
- Grade (A/B/C/D/F)
- Win rate percentage
- Security grade
- Cost per use
- GitHub stars
- Link to repo

### Skill Detail Shows
- Everything on card
- Sample comparison (one A/B example)
- Security issues (if any)
- Link to full evidence (JSON)

### Acceptance Criteria
- [ ] Leaderboard displays all rated skills
- [ ] Can filter/sort by grade, stars, cost
- [ ] Skill detail page works
- [ ] Methodology page explains A/B testing
- [ ] Mobile responsive
- [ ] Deploys to public URL

---

## Phase Dependencies

```
Phase 0 (Setup)
    ↓
Phase 1 (Discovery)
    ↓
Phase 2 (Prompt Generator)
    ↓
Phase 3 (Quality Evaluator) ←→ Phase 4 (Security Checker)
    ↓                              ↓
    └──────────→ Phase 5 (Scorer) ←┘
                      ↓
               Phase 6 (Data Logger)
                      ↓
               Phase 7 (CLI)
                      ↓
               Phase 8 (Website)
```

Phases 3 and 4 can run in parallel.

---

## Cost Estimates

| Phase | API Calls | Est. Cost |
|-------|-----------|-----------|
| 1 - Discovery | 0 (just HTTP) | $0 |
| 2 - Prompt Gen | 1 Sonnet/skill | ~$0.05/skill |
| 3 - Quality Eval | 20 Haiku + 10 Sonnet/skill | ~$0.12/skill |
| 4 - Security | 1 Sonnet/skill | ~$0.02/skill |
| **Total per skill** | | **~$0.19** |
| **Full run (21 skills)** | | **~$4.00** |

---

## Definition of Done (MVP)

- [ ] 20+ skills rated
- [ ] All ratings have full evidence saved
- [ ] Website live at public URL
- [ ] Can explain any rating by showing evidence
- [ ] Re-run produces consistent results
