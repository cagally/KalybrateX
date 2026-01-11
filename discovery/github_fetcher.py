# GitHub Fetcher
"""
Fetches skill metadata and SKILL.md content from GitHub.
Supports both individual repos and the official anthropics/skills monorepo.
"""

import re
import logging
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

import httpx

from .models import (
    SkillSource, GitHubMetadata, SkillMdInfo, DiscoveredSkill, DiscoveryResult
)

# Re-export GitHubMetadata for use in discover_github_search_skills
__all__ = [
    "GitHubFetcher",
    "parse_repo_url",
    "construct_raw_url",
    "extract_skill_name",
    "generate_slug",
    "parse_github_api_response",
    "SKILL_MD_PATHS",
    "BRANCHES",
]


# Configure logging
logger = logging.getLogger(__name__)


# Constants
SKILL_MD_PATHS = [
    "SKILL.md",
    "skill.md",
    "src/SKILL.md",
    ".claude/SKILL.md",
    "claude/SKILL.md",
]

BRANCHES = ["main", "master"]

GITHUB_API_BASE = "https://api.github.com"
RAW_GITHUB_BASE = "https://raw.githubusercontent.com"


def parse_repo_url(url: str) -> Optional[tuple[str, str]]:
    """
    Extract owner and repo name from a GitHub URL.

    Handles formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/tree/main/path
    - git@github.com:owner/repo.git

    Returns:
        tuple of (owner, repo) or None if invalid
    """
    if not url:
        return None

    # Handle SSH format: git@github.com:owner/repo.git
    ssh_match = re.match(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", url)
    if ssh_match:
        return ssh_match.group(1), ssh_match.group(2)

    # Handle HTTPS format
    # Remove .git suffix if present
    url = re.sub(r"\.git$", "", url)

    # Match GitHub URLs
    https_match = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)(?:/.*)?$",
        url
    )
    if https_match:
        owner = https_match.group(1)
        repo = https_match.group(2)
        # Remove trailing slash if present
        repo = repo.rstrip("/")
        return owner, repo

    return None


def construct_raw_url(owner: str, repo: str, branch: str, path: str) -> str:
    """
    Construct a raw.githubusercontent.com URL for fetching file content.

    Args:
        owner: Repository owner
        repo: Repository name
        branch: Branch name
        path: Path to file within repo

    Returns:
        Full URL to raw file content
    """
    return f"{RAW_GITHUB_BASE}/{owner}/{repo}/{branch}/{path}"


def extract_skill_name(owner: str, repo: str, skill_path: Optional[str]) -> str:
    """
    Extract a clean skill name from repository info.

    Priority:
    1. Last component of skill_path (for monorepos)
    2. Repo name with prefixes/suffixes removed

    Args:
        owner: Repository owner
        repo: Repository name
        skill_path: Path to skill within repo (for monorepos)

    Returns:
        Clean skill name
    """
    if skill_path:
        # For monorepos, use the last path component
        path_parts = skill_path.strip("/").split("/")
        return path_parts[-1]

    # Remove common prefixes
    name = repo
    prefix_stripped = False
    prefixes = ["skill-", "claude-", "claude_"]
    for prefix in prefixes:
        if name.lower().startswith(prefix):
            name = name[len(prefix):]
            prefix_stripped = True
            break

    # Remove common suffixes (only -claude and _claude are always stripped)
    # -skill and _skill are only stripped if they appear alone (not as part of meaningful name)
    suffixes_always = ["-claude", "_claude"]
    for suffix in suffixes_always:
        if name.lower().endswith(suffix):
            name = name[:-len(suffix)]
            break

    return name


def generate_slug(name: str) -> str:
    """
    Generate a URL-safe slug from a skill name.

    Args:
        name: Skill name

    Returns:
        URL-safe slug (lowercase, hyphens for spaces/special chars)
    """
    # Convert to lowercase
    slug = name.lower()
    # Replace spaces, underscores, and dots with hyphens
    slug = re.sub(r"[\s_.]", "-", slug)
    # Remove any character that's not alphanumeric or hyphen
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    # Replace multiple hyphens with single hyphen
    slug = re.sub(r"-+", "-", slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    return slug


def parse_github_api_response(response: dict) -> GitHubMetadata:
    """
    Parse GitHub API response into GitHubMetadata model.

    Args:
        response: JSON response from GitHub repos API

    Returns:
        GitHubMetadata instance
    """
    # Extract license (can be None or an object)
    license_info = response.get("license")
    license_id = None
    if license_info and isinstance(license_info, dict):
        license_id = license_info.get("spdx_id")

    # Parse timestamps
    pushed_at = datetime.fromisoformat(
        response["pushed_at"].replace("Z", "+00:00")
    )
    created_at = datetime.fromisoformat(
        response["created_at"].replace("Z", "+00:00")
    )

    return GitHubMetadata(
        stars=response.get("stargazers_count", 0),
        description=response.get("description"),
        default_branch=response.get("default_branch", "main"),
        pushed_at=pushed_at,
        created_at=created_at,
        language=response.get("language"),
        license=license_id,
        open_issues=response.get("open_issues_count", 0),
        forks=response.get("forks_count", 0),
    )


class GitHubFetcher:
    """
    Fetches skill information from GitHub.

    Supports:
    - Rate limit tracking
    - Token authentication for higher limits
    - Fetching repo metadata
    - Fetching SKILL.md content
    - Discovering skills from official sources
    """

    def __init__(self, token: Optional[str] = None):
        """
        Initialize the fetcher.

        Args:
            token: Optional GitHub personal access token for higher rate limits
        """
        self.token = token
        self.rate_limit_limit = 60  # Default for unauthenticated
        self.rate_limit_remaining = 60
        self.rate_limit_reset = None

        # Build headers
        self._headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "KalybrateX-Discovery/1.0",
        }
        if token:
            self._headers["Authorization"] = f"token {token}"
            self.rate_limit_limit = 5000  # Authenticated limit
            self.rate_limit_remaining = 5000

    def update_rate_limit(self, headers: dict) -> None:
        """
        Update rate limit tracking from response headers.

        Args:
            headers: Response headers dict
        """
        if "x-ratelimit-limit" in headers:
            self.rate_limit_limit = int(headers["x-ratelimit-limit"])
        if "x-ratelimit-remaining" in headers:
            self.rate_limit_remaining = int(headers["x-ratelimit-remaining"])
        if "x-ratelimit-reset" in headers:
            self.rate_limit_reset = int(headers["x-ratelimit-reset"])

    def get_repo_metadata(self, owner: str, repo: str) -> Optional[GitHubMetadata]:
        """
        Fetch repository metadata from GitHub API.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            GitHubMetadata or None if fetch failed
        """
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"

        try:
            with httpx.Client() as client:
                response = client.get(url, headers=self._headers, timeout=30.0)
                self.update_rate_limit(dict(response.headers))

                if response.status_code == 404:
                    logger.warning(f"Repository not found: {owner}/{repo}")
                    return None

                if response.status_code == 403:
                    logger.warning(f"Rate limited or forbidden: {owner}/{repo}")
                    return None

                response.raise_for_status()
                return parse_github_api_response(response.json())

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {owner}/{repo}: {e}")
            return None

    def fetch_skill_md(
        self,
        owner: str,
        repo: str,
        skill_path: Optional[str] = None
    ) -> SkillMdInfo:
        """
        Fetch SKILL.md content, trying multiple paths and branches.

        Args:
            owner: Repository owner
            repo: Repository name
            skill_path: Optional path prefix for monorepos

        Returns:
            SkillMdInfo with found status and content
        """
        with httpx.Client() as client:
            for branch in BRANCHES:
                for skill_md_path in SKILL_MD_PATHS:
                    # Build full path
                    if skill_path:
                        full_path = f"{skill_path.strip('/')}/{skill_md_path}"
                    else:
                        full_path = skill_md_path

                    url = construct_raw_url(owner, repo, branch, full_path)

                    try:
                        response = client.get(url, timeout=30.0)

                        if response.status_code == 200:
                            # Check if content looks like markdown (not binary)
                            content = response.text
                            if content and not content.startswith("\x00"):
                                logger.info(
                                    f"Found SKILL.md at {owner}/{repo}/{branch}/{full_path}"
                                )
                                return SkillMdInfo(
                                    found=True,
                                    path=full_path,
                                    branch=branch,
                                    content=content
                                )
                    except httpx.HTTPError as e:
                        logger.debug(f"Failed to fetch {url}: {e}")
                        continue

        # Not found in any location
        logger.warning(f"SKILL.md not found for {owner}/{repo}")
        return SkillMdInfo(found=False, path=None, branch=None, content=None)

    def discover_official_skills(self, limit: Optional[int] = None) -> list[DiscoveredSkill]:
        """
        Discover skills from the official anthropics/skills repository.

        Args:
            limit: Maximum number of skills to return

        Returns:
            List of discovered skills
        """
        skills = []
        owner = "anthropics"
        repo = "skills"

        # First, get the repo metadata
        metadata = self.get_repo_metadata(owner, repo)
        if not metadata:
            logger.error("Failed to fetch anthropics/skills repo metadata")
            return skills

        # Get the contents of the skills directory
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/skills"

        try:
            with httpx.Client() as client:
                response = client.get(url, headers=self._headers, timeout=30.0)
                self.update_rate_limit(dict(response.headers))

                if response.status_code != 200:
                    logger.error(f"Failed to list skills directory: {response.status_code}")
                    return skills

                items = response.json()

                # Filter to directories only
                skill_dirs = [
                    item for item in items
                    if item.get("type") == "dir"
                ]

                # Apply limit
                if limit:
                    skill_dirs = skill_dirs[:limit]

                # Process each skill
                for item in skill_dirs:
                    skill_name = item["name"]
                    skill_path = f"skills/{skill_name}"

                    # Fetch SKILL.md for this skill
                    skill_md = self.fetch_skill_md(owner, repo, skill_path)

                    skill = DiscoveredSkill(
                        name=skill_name,
                        slug=generate_slug(skill_name),
                        source=SkillSource.ANTHROPIC_OFFICIAL,
                        owner=owner,
                        repo_name=repo,
                        repository_url=f"https://github.com/{owner}/{repo}",
                        skill_path=skill_path,
                        github_metadata=metadata,
                        skill_md=skill_md,
                        discovered_at=datetime.now(timezone.utc),
                    )
                    skills.append(skill)

                    logger.info(f"Discovered official skill: {skill_name}")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error discovering official skills: {e}")

        return skills

    def discover_awesome_list_skills(
        self,
        limit: Optional[int] = None
    ) -> list[DiscoveredSkill]:
        """
        Discover skills from the awesome-claude-skills curated lists.

        Args:
            limit: Maximum number of skills to return

        Returns:
            List of discovered skills
        """
        skills = []
        seen_repos = set()  # Avoid duplicates

        # Fetch from multiple awesome lists (correct URLs)
        awesome_repos = [
            ("travisvn", "awesome-claude-skills"),
            ("ComposioHQ", "awesome-claude-skills"),
        ]

        for list_owner, list_repo in awesome_repos:
            url = construct_raw_url(list_owner, list_repo, "main", "README.md")

            try:
                with httpx.Client() as client:
                    response = client.get(url, timeout=30.0)
                    if response.status_code != 200:
                        logger.warning(f"Could not fetch {list_owner}/{list_repo}: {response.status_code}")
                        continue

                    readme_content = response.text
                    logger.info(f"Found awesome list: {list_owner}/{list_repo}")

                    # Parse GitHub repo URLs from the README
                    # Look for patterns like: [name](https://github.com/owner/repo)
                    url_pattern = r"\[([^\]]+)\]\((https://github\.com/[^/]+/[^/)#\s]+)"
                    matches = re.findall(url_pattern, readme_content)

                    for name, repo_url in matches:
                        # Clean up the URL
                        repo_url = repo_url.rstrip(")")

                        parsed = parse_repo_url(repo_url)
                        if not parsed:
                            continue

                        owner, repo = parsed
                        repo_key = f"{owner}/{repo}".lower()

                        # Skip already seen repos
                        if repo_key in seen_repos:
                            continue
                        seen_repos.add(repo_key)

                        # Skip the skills monorepo (handled separately)
                        if owner == "anthropics" and repo == "skills":
                            continue

                        # Skip awesome lists themselves
                        if "awesome" in repo.lower():
                            continue

                        # Fetch metadata
                        metadata = self.get_repo_metadata(owner, repo)
                        if not metadata:
                            logger.warning(f"Skipping {owner}/{repo} - failed to fetch metadata")
                            continue

                        # Fetch SKILL.md
                        skill_md = self.fetch_skill_md(owner, repo)

                        # Only include if it has SKILL.md
                        if not skill_md.found:
                            logger.debug(f"Skipping {owner}/{repo} - no SKILL.md found")
                            continue

                        # Extract skill name
                        skill_name = extract_skill_name(owner, repo, None)

                        skill = DiscoveredSkill(
                            name=skill_name,
                            slug=generate_slug(skill_name),
                            source=SkillSource.AWESOME_LIST,
                            owner=owner,
                            repo_name=repo,
                            repository_url=repo_url,
                            skill_path=None,
                            github_metadata=metadata,
                            skill_md=skill_md,
                            discovered_at=datetime.now(timezone.utc),
                        )
                        skills.append(skill)
                        logger.info(f"Discovered awesome-list skill: {skill_name} ({metadata.stars} stars)")

                        # Check limit
                        if limit and len(skills) >= limit:
                            return skills

            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching {list_owner}/{list_repo}: {e}")
                continue

        return skills

    def discover_github_search_skills(
        self,
        limit: Optional[int] = None,
        min_stars: int = 100
    ) -> list[DiscoveredSkill]:
        """
        Discover skills by searching GitHub for repos with 'claude skill' in name/description.
        Sorted by stars descending.

        Args:
            limit: Maximum number of skills to return
            min_stars: Minimum stars required (default 100)

        Returns:
            List of discovered skills (sorted by stars)
        """
        skills = []
        seen_repos = set()

        # Search GitHub for claude skill repos
        search_url = f"{GITHUB_API_BASE}/search/repositories"
        params = {
            "q": "claude skill in:name,description",
            "sort": "stars",
            "order": "desc",
            "per_page": 100,  # Max per page
        }

        try:
            with httpx.Client() as client:
                response = client.get(
                    search_url,
                    params=params,
                    headers=self._headers,
                    timeout=30.0
                )
                self.update_rate_limit(dict(response.headers))

                if response.status_code != 200:
                    logger.error(f"GitHub search failed: {response.status_code}")
                    return skills

                data = response.json()
                logger.info(f"GitHub search found {data.get('total_count', 0)} repos")

                for item in data.get("items", []):
                    owner = item["owner"]["login"]
                    repo = item["name"]
                    stars = item["stargazers_count"]
                    repo_key = f"{owner}/{repo}".lower()

                    # Skip if below min stars
                    if stars < min_stars:
                        continue

                    # Skip already seen
                    if repo_key in seen_repos:
                        continue
                    seen_repos.add(repo_key)

                    # Skip awesome lists and official skills repo
                    if "awesome" in repo.lower():
                        continue
                    if owner == "anthropics" and repo == "skills":
                        continue

                    # Try to fetch SKILL.md
                    skill_md = self.fetch_skill_md(owner, repo)
                    if not skill_md.found:
                        logger.debug(f"Skipping {owner}/{repo} - no SKILL.md")
                        continue

                    # Parse metadata from search result
                    metadata = GitHubMetadata(
                        stars=stars,
                        description=item.get("description"),
                        default_branch=item.get("default_branch", "main"),
                        pushed_at=datetime.fromisoformat(item["pushed_at"].replace("Z", "+00:00")),
                        created_at=datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")),
                        language=item.get("language"),
                        license=item.get("license", {}).get("spdx_id") if item.get("license") else None,
                        open_issues=item.get("open_issues_count", 0),
                        forks=item.get("forks_count", 0),
                    )

                    skill_name = extract_skill_name(owner, repo, None)

                    skill = DiscoveredSkill(
                        name=skill_name,
                        slug=generate_slug(skill_name),
                        source=SkillSource.GITHUB_SEARCH,
                        owner=owner,
                        repo_name=repo,
                        repository_url=f"https://github.com/{owner}/{repo}",
                        skill_path=None,
                        github_metadata=metadata,
                        skill_md=skill_md,
                        discovered_at=datetime.now(timezone.utc),
                    )
                    skills.append(skill)
                    logger.info(f"Discovered via GitHub search: {skill_name} ({stars} stars)")

                    if limit and len(skills) >= limit:
                        break

        except httpx.HTTPError as e:
            logger.error(f"HTTP error in GitHub search: {e}")

        return skills

    def run_discovery(
        self,
        sources: Optional[list[str]] = None,
        limit: Optional[int] = None,
        top_n: Optional[int] = None,
        min_stars: int = 50
    ) -> DiscoveryResult:
        """
        Run full discovery from all sources.

        Args:
            sources: List of sources to check (defaults to all)
            limit: Maximum skills per source (before deduplication)
            top_n: Return only the top N skills by stars (after combining all sources)
            min_stars: Minimum stars for github_search source (default 50)

        Returns:
            DiscoveryResult with all discovered skills (sorted by stars)
        """
        all_skills = []
        sources_checked = []
        seen_repos = set()  # Track repos to avoid duplicates across sources

        if sources is None:
            sources = ["anthropic_official", "awesome_list", "github_search"]

        # Discover from each source
        if "anthropic_official" in sources:
            sources_checked.append("anthropic_official")
            official_skills = self.discover_official_skills(limit=limit)
            for skill in official_skills:
                repo_key = f"{skill.owner}/{skill.repo_name}:{skill.skill_path}".lower()
                if repo_key not in seen_repos:
                    seen_repos.add(repo_key)
                    all_skills.append(skill)

        if "awesome_list" in sources:
            sources_checked.append("awesome_list")
            awesome_skills = self.discover_awesome_list_skills(limit=limit)
            for skill in awesome_skills:
                repo_key = f"{skill.owner}/{skill.repo_name}".lower()
                if repo_key not in seen_repos:
                    seen_repos.add(repo_key)
                    all_skills.append(skill)

        if "github_search" in sources:
            sources_checked.append("github_search")
            search_skills = self.discover_github_search_skills(limit=limit, min_stars=min_stars)
            for skill in search_skills:
                repo_key = f"{skill.owner}/{skill.repo_name}".lower()
                if repo_key not in seen_repos:
                    seen_repos.add(repo_key)
                    all_skills.append(skill)

        # Sort all skills by stars (descending)
        all_skills.sort(key=lambda s: s.github_metadata.stars, reverse=True)

        # Apply top_n filter if specified
        if top_n and len(all_skills) > top_n:
            all_skills = all_skills[:top_n]

        # Calculate totals
        total_with_skill_md = sum(
            1 for skill in all_skills if skill.skill_md.found
        )

        return DiscoveryResult(
            discovered_at=datetime.now(timezone.utc),
            sources_checked=sources_checked,
            total_skills=len(all_skills),
            total_with_skill_md=total_with_skill_md,
            skills=all_skills,
        )
