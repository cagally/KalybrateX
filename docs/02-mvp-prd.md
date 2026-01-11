# KalybrateX - MVP Product Requirements Document

## Overview

KalybrateX is a rating platform for AI agent skills. We answer one question: **Does this skill make Claude better?**

This document defines the minimum viable product scope.

---

## The Problem

- 37,000+ skills on SkillsMP alone
- No way to know which skills work vs which are broken/abandoned
- Model routing systems need reliable capability data
- Users limited to skills in context, need to choose wisely

## Our Solution

- A/B comparison testing (skill vs baseline Claude)
- Auto-generated tests from SKILL.md content
- Full transparency - show the evidence behind every rating
- Clean website showing skill ratings with detailed breakdowns

---

## MVP Scope

### In Scope
- Discover skills from SkillsMP (with marketplace.json filter)
- Fetch metadata + SKILL.md from GitHub
- Auto-generate comparison prompts from SKILL.md
- Run A/B quality comparisons (with/without skill)
- Calculate win rate and assign grades
- Security analysis of SKILL.md
- Track token usage / cost
- Save all evidence
- Public website showing leaderboard
- Skill detail pages with sample comparisons

### Out of Scope (Phase 2+)
- Task completion verification
- Multi-model support (Gemini, GPT, etc.)
- Skill marketplace / transactions
- Skill creation tools
- Real-time monitoring
- User accounts / authentication
- API access
- Badge certification program

---

## Evaluation Methodology

### Primary Metric: Quality Win Rate

**What it measures:** Does the skill make Claude's output better?

**Process:**
1. Generate 10 comparison prompts from SKILL.md (using Sonnet)
2. For each prompt:
   - Run WITHOUT skill → baseline response (Haiku)
   - Run WITH skill in system prompt → skill response (Haiku)
   - Randomize A/B order (avoid position bias)
   - Judge which is better (Sonnet)
3. Calculate win rate: `wins / (wins + losses)`
4. Ties don't count against either side

**Grading:**
| Win Rate | Grade |
|----------|-------|
| 80%+ | A |
| 60-79% | B |
| 40-59% | C |
| 20-39% | D |
| <20% | F |

### Secondary Metric: Security Grade

**What it measures:** Is the skill safe to use?

**Process:**
- Single Sonnet call analyzing SKILL.md
- Check for: data exfiltration, file system abuse, credential theft, code injection, malicious dependencies

**Grading:**
- **Secure:** No issues found
- **Warning:** Potential risks identified
- **Fail:** Clear malicious patterns

### Secondary Metric: Cost

**What it measures:** Token usage per interaction

**Process:**
- Track output tokens for each skill response
- Calculate average tokens per use
- Convert to USD using Haiku pricing

---

## Data Models

### SkillRating
```json
{
  "skill_name": "pdf",
  "grade": "B",
  "win_rate": 70,
  "wins": 7,
  "losses": 3,
  "ties": 0,
  "security_grade": "secure",
  "security_issues": [],
  "avg_tokens": 1500,
  "cost_per_use": "$0.0045",
  "evaluated_at": "2025-01-07T12:00:00Z",
  "repository": "https://github.com/anthropics/skills",
  "stars": 15000,
  "description": "Create and manipulate PDF documents"
}
```

### ComparisonResult
```json
{
  "prompt": "Help me merge 5 PDF contracts into one document",
  "baseline_response": "You can use Adobe Acrobat or...",
  "skill_response": "I'll help you merge those PDFs. Here's Python code using PyPDF2...",
  "verdict": "skill",
  "reasoning": "Skill response provided working code vs just suggesting tools",
  "baseline_tokens": 450,
  "skill_tokens": 1200,
  "position_a": "baseline",
  "position_b": "skill"
}
```

### SecurityResult
```json
{
  "skill_name": "pdf",
  "grade": "secure",
  "issues": [],
  "analysis": "No security concerns found. Skill focuses on PDF manipulation using standard libraries.",
  "analyzed_at": "2025-01-07T12:00:00Z"
}
```

---

## User Interface

### Leaderboard Page
- Ranked list of all rated skills
- Each skill shows: name, grade, win rate, security grade, stars, cost
- Filter by: grade, security, cost range
- Sort by: grade, win rate, stars, name
- Search by name

### Skill Detail Page
- Full rating breakdown
- Sample A/B comparison (one example with both responses)
- Security analysis summary
- GitHub metadata (stars, last updated, description)
- Link to SKILL.md source
- Link to full evidence JSON

### Methodology Page
- Explain A/B testing approach
- Show how prompts are generated
- Explain grading scale
- Link to this PRD for full details

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      KalybrateX Pipeline                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ Discovery │ → │ Prompt   │ → │ Quality  │ → │ Scorer   │    │
│  │           │   │ Generator│   │ Evaluator│   │          │    │
│  └──────────┘   └──────────┘   └────┬─────┘   └──────────┘    │
│                                      │                          │
│                                ┌─────▼─────┐                   │
│                                │ Security  │                   │
│                                │ Checker   │                   │
│                                └───────────┘                   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     Data Logger                           │  │
│  │  (saves all evidence to data/evaluations/)               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                       Website                             │  │
│  │  (reads from data/leaderboard.json)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Model Configuration

| Operation | Model | Why |
|-----------|-------|-----|
| Prompt generation | claude-3-5-sonnet | Needs to understand SKILL.md |
| Task execution (baseline) | claude-3-5-haiku | Cost efficient |
| Task execution (with skill) | claude-3-5-haiku | Must match baseline |
| Quality judging | claude-3-5-sonnet | Needs nuance |
| Security analysis | claude-3-5-sonnet | Needs code understanding |

---

## File Structure

### Evidence Storage
```
data/evaluations/{skill_name}/
├── skill.md                    # Copy of SKILL.md tested
├── prompts.json                # Generated comparison prompts
├── comparisons/
│   ├── 01.json                 # Full comparison data
│   ├── 02.json
│   └── ...
├── security.json               # Security analysis
├── score.json                  # Calculated scores
└── summary.json                # Aggregated results
```

### Leaderboard
```json
{
  "generated_at": "2025-01-07T12:00:00Z",
  "total_skills": 21,
  "ratings": [
    { "skill_name": "pdf", "grade": "A", "win_rate": 90, ... },
    { "skill_name": "xlsx", "grade": "B", "win_rate": 70, ... },
    ...
  ]
}
```

---

## Cost Budget

| Item | Cost |
|------|------|
| Prompt generation (Sonnet × 1/skill) | ~$0.05/skill |
| Comparisons (Haiku × 20/skill) | ~$0.04/skill |
| Judging (Sonnet × 10/skill) | ~$0.08/skill |
| Security (Sonnet × 1/skill) | ~$0.02/skill |
| **Total per skill** | **~$0.19** |
| **Full run (21 skills)** | **~$4.00** |
| **Budget ceiling** | **$20** |

---

## Success Criteria

### MVP Complete When:
- [ ] 20+ skills rated with full evidence
- [ ] Website live at public URL
- [ ] Leaderboard displays all rated skills
- [ ] Can drill down to see comparison examples
- [ ] Methodology page explains approach
- [ ] Any rating can be verified from saved evidence

### Quality Indicators:
- [ ] No skills with 100% or 0% win rate (sanity check)
- [ ] Security checker catches obvious test cases
- [ ] Cost estimates are within 2x of actuals
- [ ] Re-running produces consistent results (±10%)

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| SkillsMP changes structure | Discovery breaks | Monitor, update scraper |
| GitHub rate limits | Slow discovery | Use token, implement backoff |
| Judge bias | Bad ratings | Randomize A/B, review samples |
| Skills produce invalid output | N/A | A/B handles this - invalid = loses |
| Cost overrun | Budget blown | Implement hard limits, monitor |

---

## Out of Scope Decisions

### Why No Task Completion?
Task completion verification is complex and weak:
- Different verification per skill type
- Most skills produce text where "verification" = "did it respond?"
- Source of most bugs in previous attempts
- A/B comparison already captures this - if output is invalid, it loses

### Why No Multi-Model?
- Adds complexity without adding value for MVP
- Skills are designed for Claude
- Can add later if there's demand

### Why SkillsMP Only?
- Already curated by community (stars)
- Has marketplace.json filter for quality
- 37,000+ skills is plenty for MVP
- Can expand sources later
