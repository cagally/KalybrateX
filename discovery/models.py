# Discovery Models
"""
Pydantic models for the Discovery phase of KalybrateX.
These models represent skills discovered from various sources.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SkillSource(str, Enum):
    """Source where a skill was discovered."""
    ANTHROPIC_OFFICIAL = "anthropic_official"
    AWESOME_LIST = "awesome_list"
    GITHUB_SEARCH = "github_search"
    SKILLSMP = "skillsmp"
    SKILLSMP_TOP = "skillsmp_top"  # Top starred skills without marketplace filter


class GitHubMetadata(BaseModel):
    """Metadata fetched from GitHub API for a repository."""
    stars: int = Field(description="Number of stargazers")
    description: Optional[str] = Field(default=None, description="Repository description")
    default_branch: str = Field(description="Default branch name (main/master)")
    pushed_at: datetime = Field(description="Last push timestamp")
    created_at: datetime = Field(description="Repository creation timestamp")
    language: Optional[str] = Field(default=None, description="Primary programming language")
    license: Optional[str] = Field(default=None, description="SPDX license identifier")
    open_issues: int = Field(default=0, description="Number of open issues")
    forks: int = Field(default=0, description="Number of forks")


class SkillMdInfo(BaseModel):
    """Information about the SKILL.md file for a skill."""
    found: bool = Field(description="Whether SKILL.md was found")
    path: Optional[str] = Field(default=None, description="Path where SKILL.md was found")
    branch: Optional[str] = Field(default=None, description="Branch where SKILL.md was found")
    content: Optional[str] = Field(default=None, description="Content of SKILL.md")


class DiscoveredSkill(BaseModel):
    """A skill discovered from a source."""
    name: str = Field(description="Human-readable skill name")
    slug: str = Field(description="URL-safe identifier for the skill")
    source: SkillSource = Field(description="Where the skill was discovered")
    owner: str = Field(description="GitHub repository owner")
    repo_name: str = Field(description="GitHub repository name")
    repository_url: str = Field(description="Full URL to the repository")
    skill_path: Optional[str] = Field(default=None, description="Path to skill within monorepo")
    github_metadata: GitHubMetadata = Field(description="Repository metadata from GitHub")
    skill_md: SkillMdInfo = Field(description="SKILL.md file information")
    discovered_at: datetime = Field(description="When this skill was discovered")
    fetch_error: Optional[str] = Field(default=None, description="Error message if fetch failed")


class DiscoveryResult(BaseModel):
    """Result of a discovery run."""
    discovered_at: datetime = Field(description="When discovery was run")
    sources_checked: list[str] = Field(description="List of sources that were checked")
    total_skills: int = Field(description="Total number of skills discovered")
    total_with_skill_md: int = Field(description="Number of skills with SKILL.md found")
    skills: list[DiscoveredSkill] = Field(description="List of discovered skills")
