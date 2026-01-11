# KalybrateX Documentation Index

## Quick Reference

**What:** Rating platform for AI agent skills
**Core Metric:** Quality Win Rate (does skill beat baseline Claude?)
**MVP Goal:** 20+ rated skills on public leaderboard

---

## Document Stack

| # | Document | Purpose | Status |
|---|----------|---------|--------|
| 1 | [Vision & Goals](./01-vision-and-goals.md) | Why we exist, business model, success metrics | ✅ Done |
| 2 | [MVP PRD](./02-mvp-prd.md) | What we're building, scope, data models | ✅ Done |
| 3 | [Build Plan](./03-build-plan.md) | Phases, dependencies, repo setup | ✅ Done |
| 4 | [Learnings](./04-learnings.md) | What we learned from previous attempts | ✅ Done |
| 5 | [CLAUDE.md](../CLAUDE.md) | Instructions for Claude Code (in repo root) | ✅ Done |
| 6 | Component PRDs | Detailed specs for each phase | 🔄 In Progress |

---

## Component PRDs

| Phase | Component | File | Status |
|-------|-----------|------|--------|
| 0 | Repo Setup | (In build-plan.md) | ⏳ Pending |
| 1 | Discovery | [01-discovery-prd.md](./components/01-discovery-prd.md) | ⏳ Pending |
| 2 | Prompt Generator | `02-prompt-generator-prd.md` | ⏳ Pending |
| 3 | Quality Evaluator | `03-quality-evaluator-prd.md` | ⏳ Pending |
| 4 | Security Checker | `04-security-checker-prd.md` | ⏳ Pending |
| 5 | Scorer | `05-scorer-prd.md` | ⏳ Pending |
| 6 | Data Logger | `06-data-logger-prd.md` | ⏳ Pending |
| 7 | CLI | `07-cli-prd.md` | ⏳ Pending |
| 8 | Website | `08-website-prd.md` | ⏳ Pending |

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary metric | Quality Win Rate | Simple, defensible, answers "does it help?" |
| Task completion | Dropped | Too complex, weak verification for most skills |
| Model for execution | Haiku | Cost efficient |
| Model for judging | Sonnet | Needs nuance |
| Security check | Added | Cheap, adds credibility, differentiator |
| Discovery source | SkillsMP | Already curated, has stars ranking |
| Marketplace.json filter | Yes | Higher quality skills (~30% of total) |

---

## Metrics Summary

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
- Informational only

### Secondary: Security Grade
- Secure / Warning / Fail
- Based on SKILL.md analysis

---

## Cost Budget

| Item | Cost |
|------|------|
| Per skill | ~$0.19 |
| Full run (21 skills) | ~$4.00 |
| Budget ceiling | $20 |

---

## Current Status

**Phase:** Starting Fresh - Phase 0 (Repo Setup)

**Next Action:** Set up clean repo structure, then build Discovery

**Blockers:** None

---

## File Structure (Target)

```
KalybrateX/
├── CLAUDE.md
├── docs/
│   ├── 00-index.md
│   ├── 01-vision-and-goals.md
│   ├── 02-mvp-prd.md
│   ├── 03-build-plan.md
│   ├── 04-learnings.md
│   └── components/
│       └── 01-discovery-prd.md
├── discovery/
├── evaluator/
├── data/
├── tests/
└── website/
```

---

## How to Use These Docs

### For Claude Code
1. Read `CLAUDE.md` in repo root first (project overview)
2. Read `docs/04-learnings.md` (avoid past mistakes)
3. Read `docs/03-build-plan.md` for current phase
4. Read relevant Component PRD for detailed spec
5. Ask clarifying questions before building
6. Use TDD - write tests first

### For Context Recovery
If context is lost:
1. Start with this Index
2. Read MVP PRD for full scope
3. Check Build Plan for current phase
4. Read Learnings to avoid past mistakes
