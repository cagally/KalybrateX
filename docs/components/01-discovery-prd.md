# Component PRD: Discovery (Phase 1)

## Overview

Discovery finds skills from SkillsMP, then fetches metadata and SKILL.md content from GitHub.

**Input:** SkillsMP homepage, GitHub API
**Output:** `data/discovered/skills.json` + individual SKILL.md files

---

## Requirements

### D1: Scrape SkillsMP for Skill Repos
- Scrape https://skillsmp.com homepage
- Extract repository URLs for each skill
- Handle JS-rendered content (requires Playwright)
- Respect rate limits

### D2: Filter by marketplace.json
- Only include skills that have a `marketplace.json` file in their repo
- This filters to ~30% of skills but much higher quality

### D3: Fetch GitHub Metadata
- For each repo, fetch via GitHub API:
  - `stars` (stargazers_count)
  - `description`
  - `default_branch`
  - `last_updated` (pushed_at)
  - `created_at`
  - `language`
  - `license`
  - `open_issues`
  - `forks`
- Handle rate limiting (60/hr without token, 5000/hr with)

### D4: Fetch Latest Release/Version
- Check GitHub releases API
- If no releases, use latest commit SHA
- Store as `latest_version`

### D5: Fetch SKILL.md Content
- Try multiple paths in order:
  1. `SKILL.md`
  2. `skill.md`
  3. `src/SKILL.md`
  4. `.claude/SKILL.md`
  5. `claude/SKILL.md`
- Try both `main` and `master` branches
- Use raw.githubusercontent.com for content

### D6: Save Discovered Skills
- Save aggregate list to `data/discovered/skills.json`
- Save individual SKILL.md to `data/skills/{name}/SKILL.md`
- Save metadata to `data/skills/{name}/metadata.json`

### D7: Handle Errors Gracefully
- Log failures, don't crash
- Mark skills with missing SKILL.md
- Continue processing remaining skills

### D8: Support Re-runs
- Check if skill already exists before fetching
- `--force` flag to override and refetch
- Don't duplicate entries

### D9: Support Limits
- `--limit N` to only process first N skills
- Useful for testing

### D10: Track Fetch Status
- Record `last_fetched_at` timestamp
- Record `skill_md_fetched` boolean
- Record `fetch_error` if failed

---

## Data Models

### DiscoveredSkill
```python
class DiscoveredSkill(BaseModel):
    name: str                          # Skill name (derived from repo)
    repository: str                    # Full repo URL
    owner: str                         # GitHub owner
    repo_name: str                     # GitHub repo name
    
    # GitHub metadata
    stars: int
    description: str | None
    default_branch: str
    last_updated: datetime
    created_at: datetime
    language: str | None
    license: str | None
    open_issues: int
    forks: int
    latest_version: str | None
    
    # Fetch status
    has_marketplace_json: bool
    skill_md_path: str | None          # Local path if fetched
    skill_md_fetched: bool
    fetch_error: str | None
    last_fetched_at: datetime
```

### SkillsDiscoveryResult
```python
class SkillsDiscoveryResult(BaseModel):
    skills: list[DiscoveredSkill]
    total_found: int
    total_with_marketplace: int
    total_with_skillmd: int
    discovered_at: datetime
```

---

## File Structure

```
discovery/
├── __init__.py
├── models.py             # DiscoveredSkill, SkillsDiscoveryResult
├── skillsmp_scraper.py   # Scrape SkillsMP for repo URLs
├── github_fetcher.py     # Fetch metadata + SKILL.md from GitHub
└── main.py               # CLI orchestration

data/
├── discovered/
│   └── skills.json       # SkillsDiscoveryResult
└── skills/
    └── {skill-name}/
        ├── SKILL.md      # Raw skill content
        └── metadata.json # GitHub metadata
```

---

## CLI Interface

```bash
# Discover all skills
python -m discovery.main --all

# Discover with limit
python -m discovery.main --all --limit 20

# Force refetch
python -m discovery.main --all --force

# Check status
python -m discovery.main --status
```

---

## Tests

### Unit Tests

```python
# test_discovery.py

def test_parse_repo_url():
    """Extract owner/repo from various URL formats"""
    
def test_construct_raw_url():
    """Build raw.githubusercontent.com URL correctly"""
    
def test_skill_md_path_variations():
    """Try all path variations"""
    
def test_filter_marketplace_json():
    """Only include skills with marketplace.json"""
    
def test_parse_github_metadata():
    """Extract all fields from API response"""
```

### Integration Tests

```python
def test_fetch_single_skill_metadata():
    """Fetch metadata for known skill repo"""
    
def test_fetch_skillmd_content():
    """Fetch SKILL.md from known repo"""
    
def test_handle_missing_skillmd():
    """Gracefully handle repo without SKILL.md"""
    
def test_handle_rate_limit():
    """Back off when rate limited"""
```

### End-to-End Test

```python
def test_full_discovery_pipeline():
    """Run discovery with limit=5, verify all data present"""
```

---

## Implementation Notes

### SkillsMP Scraping
```python
from playwright.sync_api import sync_playwright

def scrape_skillsmp() -> list[str]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://skillsmp.com")
        page.wait_for_load_state("networkidle")
        
        # Extract repo URLs from skill cards
        # ... implementation depends on actual page structure
        
        browser.close()
    return repo_urls
```

### GitHub API
```python
import httpx

def fetch_repo_metadata(owner: str, repo: str, token: str | None = None) -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    
    response = httpx.get(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers=headers
    )
    response.raise_for_status()
    return response.json()
```

### SKILL.md Fetching
```python
SKILL_PATHS = [
    "SKILL.md",
    "skill.md", 
    "src/SKILL.md",
    ".claude/SKILL.md",
    "claude/SKILL.md"
]

BRANCHES = ["main", "master"]

def fetch_skillmd(owner: str, repo: str) -> str | None:
    for branch in BRANCHES:
        for path in SKILL_PATHS:
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
            response = httpx.get(url)
            if response.status_code == 200:
                return response.text
    return None
```

---

## Acceptance Criteria

- [ ] Discovers 15+ skills with marketplace.json
- [ ] GitHub metadata complete for all discovered skills
- [ ] 80%+ SKILL.md fetch success rate
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Re-running doesn't duplicate entries
- [ ] `--limit` flag works
- [ ] `--force` flag works
- [ ] Errors logged but don't crash pipeline

---

## Edge Cases to Handle

1. **Repo not found** - Owner deleted repo, log and skip
2. **Rate limited** - Back off exponentially, retry
3. **No SKILL.md** - Mark as `skill_md_fetched: false`, continue
4. **Private repo** - Will 404, log and skip
5. **Malformed URL** - Log and skip
6. **Empty SKILL.md** - Still save it, evaluation will handle
7. **Binary file at SKILL.md path** - Check content type, skip if not text

---

## Success Metrics

After running `python -m discovery.main --all`:

1. `data/discovered/skills.json` exists and is valid JSON
2. Contains 15+ skills with `has_marketplace_json: true`
3. Each skill has stars, description, default_branch
4. 80%+ have `skill_md_fetched: true`
5. Individual SKILL.md files exist in `data/skills/`
