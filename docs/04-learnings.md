# KalybrateX - Learnings from Previous Attempts

## Overview

We've tried building this 3 times before (Kalybrate, Kalybrate2, Kalybrate3). Each attempt taught us something. This document captures those learnings so we don't repeat mistakes.

---

## Critical Learning #1: The Judge Doesn't Know Claude Code Exists

### The Problem
When Sonnet judged responses, it penalized skills that produced Claude Code-specific outputs (hooks, rules, SKILL.md files) because **Sonnet's training cutoff predates Claude Code's public features**.

We tested this directly:
```
Q: "What are Claude Code hooks?"
A: "I don't have any features called 'Claude Code hooks' - these aren't real features"
```

Skills that produced valid Claude Code configurations were marked as "fictional" or "hallucinated."

### The Fix
**Every judge prompt MUST include context explaining Claude Code features:**

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

**This is non-negotiable. Without it, evaluation results are garbage.**

---

## Critical Learning #2: Task Completion Was a Waste of Time

### The Problem
We built elaborate verification for different skill types:
- File skills: Check file exists, opens, has content
- Python: Compile syntax
- TypeScript: Run tsc
- Text output: Check response exists

**Reality:**
- File verification had bugs (nested paths, wrong libraries)
- Most skills produce text/code where "verification" = "did it respond?"
- The signal-to-noise ratio was terrible
- 60% of our bugs were in verification code

### The Fix
**Drop task completion entirely. Focus only on Quality Win Rate.**

One metric that answers the real question: "Does this skill make Claude better?"

If a skill produces invalid output, it will lose the A/B comparison anyway. We don't need separate verification.

---

## Critical Learning #3: Fake Metrics Are Worse Than No Metrics

### Metrics We Dropped

| Metric | Why It Was Fake |
|--------|-----------------|
| Activation Rate | We put skill in prompt and ask relevant questions - of course it "activates" |
| Selectivity | Claude won't use a PDF skill when asked about weather - trivial sanity check |
| Response Relevance | Just checked if code > 50 chars - already covered by other checks |
| Code Extracted | Binary yes/no - doesn't tell you if the code is good |

### The Learning
If you can't explain what the metric tells you that you didn't already know, delete it.

**Keep:** Quality Win Rate (does skill beat baseline?)
**Keep:** Security Grade (is it safe?)
**Keep:** Cost (how expensive?)
**Delete:** Everything else

---

## Critical Learning #4: Cost Tracking Was Broken

### The Problem
Our cost estimates said $0.50 when we expected $6-8. Investigation showed:
- Token counts weren't being captured correctly
- Some API calls weren't being tracked
- The formula was wrong

### The Fix
Track tokens at the source:
```python
response = client.messages.create(...)
input_tokens = response.usage.input_tokens
output_tokens = response.usage.output_tokens
```

Calculate cost immediately and store with each call. Don't try to reconstruct later.

---

## Critical Learning #5: SkillsMP Requires Playwright

### The Problem
SkillsMP is JS-rendered. Simple HTTP requests get empty HTML.

### The Fix
Use Playwright:
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://skillsmp.com")
    page.wait_for_selector(".skill-card")  # Wait for JS to render
    content = page.content()
```

Don't forget to install browsers: `playwright install chromium`

---

## Critical Learning #6: GitHub is Source of Truth

### The Problem
We tried to get everything from SkillsMP. But SkillsMP data is:
- Incomplete (missing fields)
- Stale (not always updated)
- Limited (no version info)

### The Fix
Use SkillsMP only as an index to find repos. Get all metadata from GitHub API:
- Stars, description, default_branch
- Last updated, created at
- Language, license
- Latest release/version

GitHub API gives you 60 requests/hour unauthenticated, 5000/hour with a token.

---

## Critical Learning #7: SKILL.md Paths Vary

### The Problem
Not all skills put SKILL.md in the repo root. We missed skills because we only checked one path.

### The Fix
Try multiple paths in order:
1. `SKILL.md`
2. `skill.md`
3. `src/SKILL.md`
4. `.claude/SKILL.md`
5. `claude/SKILL.md`

Also try both `main` and `master` branches.

---

## Critical Learning #8: Filter by marketplace.json

### The Problem
37,000+ skills on SkillsMP. Many are:
- Broken/abandoned
- Low quality
- Test uploads

### The Fix
Filter for skills with `marketplace.json` file. These are skills the creator explicitly published to the marketplace. Reduces to ~30% of skills, but much higher quality.

---

## Critical Learning #9: Save Everything

### The Problem
When debugging weird scores, we couldn't figure out what went wrong because we only saved summaries.

### The Fix
Save FULL responses, not truncated. Save:
- The exact prompt sent
- The full response received
- Token counts
- Timestamps
- Model used
- Judge reasoning (full text)

Disk is cheap. Debugging without evidence is expensive.

---

## Critical Learning #10: One Component at a Time

### The Problem
We tried to build everything at once. When something broke, we couldn't tell which component was at fault.

### The Fix
Build sequentially:
1. Discovery - verify skills.json looks right
2. Prompt Generator - verify prompts are good
3. Quality Evaluator - verify comparisons work
4. Scorer - verify math is correct
5. CLI - wire it together
6. Website - display results

Test each phase before moving to the next. Don't skip verification.

---

## Summary: What We're Doing Differently

| Before | Now |
|--------|-----|
| Multiple metrics | One metric (Quality Win Rate) |
| Complex verification | No verification (A/B tells us everything) |
| Judge without context | Judge with Claude Code context |
| SkillsMP for everything | SkillsMP for discovery, GitHub for data |
| Single SKILL.md path | Multiple paths + branches |
| All skills | Filter by marketplace.json |
| Summary data only | Full evidence saved |
| Build all at once | One phase at a time |

---

## Red Flags to Watch For

If you see any of these, stop and investigate:

1. **Win rates all 50%** - Probably position bias (not randomizing A/B)
2. **Win rates all 0%** - Probably judge context missing
3. **Cost way off** - Token tracking broken
4. **Empty SKILL.md** - Path detection not working
5. **0 skills discovered** - SkillsMP scraping broken (JS render issue)
6. **Tests pass but results wrong** - Tests aren't testing the right thing

---

## Questions to Ask Before Each Phase

1. What exactly does this phase output?
2. How do we verify the output is correct?
3. What could go wrong?
4. What do we do if it fails?
5. Does this need the Claude Code context fix?
