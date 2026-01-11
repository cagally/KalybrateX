# Discovery module - scrapes SkillsMP and fetches from GitHub
"""
Discovery phase of KalybrateX.
Discovers skills from official sources and curated lists.
"""

from .models import (
    SkillSource,
    GitHubMetadata,
    SkillMdInfo,
    DiscoveredSkill,
    DiscoveryResult,
)
from .github_fetcher import (
    GitHubFetcher,
    parse_repo_url,
    construct_raw_url,
    extract_skill_name,
    generate_slug,
    parse_github_api_response,
    SKILL_MD_PATHS,
    BRANCHES,
)
from .main import run_discovery, save_results, main

__all__ = [
    # Models
    "SkillSource",
    "GitHubMetadata",
    "SkillMdInfo",
    "DiscoveredSkill",
    "DiscoveryResult",
    # Fetcher
    "GitHubFetcher",
    "parse_repo_url",
    "construct_raw_url",
    "extract_skill_name",
    "generate_slug",
    "parse_github_api_response",
    "SKILL_MD_PATHS",
    "BRANCHES",
    # Main
    "run_discovery",
    "save_results",
    "main",
]
