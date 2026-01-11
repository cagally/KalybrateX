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
        Discover skills from the awesome-claude-skills curated list.

        Args:
            limit: Maximum number of skills to return

        Returns:
            List of discovered skills
        """
        skills = []

        # Fetch the awesome-claude-skills README
        awesome_repos = [
            ("anthropics", "awesome-claude-skills"),
            ("wong2", "awesome-claude-code"),  # Alternative list
        ]

        readme_content = None
        for owner, repo in awesome_repos:
            url = construct_raw_url(owner, repo, "main", "README.md")

            try:
                with httpx.Client() as client:
                    response = client.get(url, timeout=30.0)
                    if response.status_code == 200:
                        readme_content = response.text
                        logger.info(f"Found awesome list: {owner}/{repo}")
                        break
            except httpx.HTTPError:
                continue

        if not readme_content:
            logger.warning("Could not fetch any awesome-claude-skills list")
            return skills

        # Parse GitHub repo URLs from the README
        # Look for patterns like: [name](https://github.com/owner/repo)
        url_pattern = r"\[([^\]]+)\]\((https://github\.com/[^/]+/[^/)]+)\)"
        matches = re.findall(url_pattern, readme_content)

        # Apply limit
        if limit:
            matches = matches[:limit]

        # Process each repo
        for name, repo_url in matches:
            parsed = parse_repo_url(repo_url)
            if not parsed:
                continue

            owner, repo = parsed

            # Skip the skills monorepo (handled separately)
            if owner == "anthropics" and repo == "skills":
                continue

            # Fetch metadata
            metadata = self.get_repo_metadata(owner, repo)
            if not metadata:
                logger.warning(f"Skipping {owner}/{repo} - failed to fetch metadata")
                continue

            # Fetch SKILL.md
            skill_md = self.fetch_skill_md(owner, repo)

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

            logger.info(f"Discovered awesome-list skill: {skill_name}")

        return skills

    def run_discovery(
        self,
        sources: Optional[list[str]] = None,
        limit: Optional[int] = None
    ) -> DiscoveryResult:
        """
        Run full discovery from all sources.

        Args:
            sources: List of sources to check (defaults to all)
            limit: Maximum skills per source

        Returns:
            DiscoveryResult with all discovered skills
        """
        all_skills = []
        sources_checked = []

        if sources is None:
            sources = ["anthropic_official", "awesome_list"]

        # Discover from each source
        if "anthropic_official" in sources:
            sources_checked.append("anthropic_official")
            official_skills = self.discover_official_skills(limit=limit)
            all_skills.extend(official_skills)

        if "awesome_list" in sources:
            sources_checked.append("awesome_list")
            awesome_skills = self.discover_awesome_list_skills(limit=limit)
            all_skills.extend(awesome_skills)

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
