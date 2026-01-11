# Tests for Discovery Phase
"""
Unit tests for the Discovery module.
Tests written first using TDD approach.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
import json


# =============================================================================
# Test: Models
# =============================================================================

class TestSkillSourceEnum:
    """Test SkillSource enum values."""

    def test_has_anthropic_official(self):
        from discovery.models import SkillSource
        assert SkillSource.ANTHROPIC_OFFICIAL == "anthropic_official"

    def test_has_awesome_list(self):
        from discovery.models import SkillSource
        assert SkillSource.AWESOME_LIST == "awesome_list"


class TestGitHubMetadata:
    """Test GitHubMetadata model."""

    def test_create_with_required_fields(self):
        from discovery.models import GitHubMetadata

        metadata = GitHubMetadata(
            stars=100,
            description="A test skill",
            default_branch="main",
            pushed_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

        assert metadata.stars == 100
        assert metadata.description == "A test skill"
        assert metadata.default_branch == "main"

    def test_optional_fields_default_to_none(self):
        from discovery.models import GitHubMetadata

        metadata = GitHubMetadata(
            stars=50,
            description=None,
            default_branch="main",
            pushed_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )

        assert metadata.language is None
        assert metadata.license is None

    def test_all_fields(self):
        from discovery.models import GitHubMetadata

        metadata = GitHubMetadata(
            stars=200,
            description="Full metadata skill",
            default_branch="main",
            pushed_at=datetime(2024, 3, 1, tzinfo=timezone.utc),
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            language="Python",
            license="MIT",
            open_issues=5,
            forks=10,
        )

        assert metadata.language == "Python"
        assert metadata.license == "MIT"
        assert metadata.open_issues == 5
        assert metadata.forks == 10


class TestSkillMdInfo:
    """Test SkillMdInfo model."""

    def test_found_skill_md(self):
        from discovery.models import SkillMdInfo

        info = SkillMdInfo(
            found=True,
            path="SKILL.md",
            branch="main",
            content="# My Skill\n\nThis is a skill."
        )

        assert info.found is True
        assert info.path == "SKILL.md"
        assert info.branch == "main"
        assert "My Skill" in info.content

    def test_not_found_skill_md(self):
        from discovery.models import SkillMdInfo

        info = SkillMdInfo(
            found=False,
            path=None,
            branch=None,
            content=None
        )

        assert info.found is False
        assert info.path is None
        assert info.content is None


class TestDiscoveredSkill:
    """Test DiscoveredSkill model."""

    def test_create_discovered_skill(self):
        from discovery.models import DiscoveredSkill, SkillSource, GitHubMetadata, SkillMdInfo

        skill = DiscoveredSkill(
            name="pdf-skill",
            slug="pdf-skill",
            source=SkillSource.ANTHROPIC_OFFICIAL,
            owner="anthropics",
            repo_name="skill-pdf",
            repository_url="https://github.com/anthropics/skill-pdf",
            skill_path="skills/pdf",
            github_metadata=GitHubMetadata(
                stars=100,
                description="PDF skill",
                default_branch="main",
                pushed_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
            skill_md=SkillMdInfo(
                found=True,
                path="SKILL.md",
                branch="main",
                content="# PDF Skill"
            ),
            discovered_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )

        assert skill.name == "pdf-skill"
        assert skill.source == SkillSource.ANTHROPIC_OFFICIAL
        assert skill.owner == "anthropics"
        assert skill.github_metadata.stars == 100
        assert skill.skill_md.found is True

    def test_skill_without_skill_md(self):
        from discovery.models import DiscoveredSkill, SkillSource, GitHubMetadata, SkillMdInfo

        skill = DiscoveredSkill(
            name="incomplete-skill",
            slug="incomplete-skill",
            source=SkillSource.AWESOME_LIST,
            owner="someuser",
            repo_name="my-skill",
            repository_url="https://github.com/someuser/my-skill",
            skill_path=None,
            github_metadata=GitHubMetadata(
                stars=10,
                description="Incomplete",
                default_branch="master",
                pushed_at=datetime(2024, 2, 1, tzinfo=timezone.utc),
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
            skill_md=SkillMdInfo(
                found=False,
                path=None,
                branch=None,
                content=None
            ),
            discovered_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )

        assert skill.skill_md.found is False
        assert skill.skill_path is None


class TestDiscoveryResult:
    """Test DiscoveryResult model."""

    def test_discovery_result(self):
        from discovery.models import (
            DiscoveryResult, DiscoveredSkill, SkillSource,
            GitHubMetadata, SkillMdInfo
        )

        skill = DiscoveredSkill(
            name="test-skill",
            slug="test-skill",
            source=SkillSource.ANTHROPIC_OFFICIAL,
            owner="anthropics",
            repo_name="skills",
            repository_url="https://github.com/anthropics/skills",
            skill_path="skills/test",
            github_metadata=GitHubMetadata(
                stars=50,
                description="Test",
                default_branch="main",
                pushed_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
            skill_md=SkillMdInfo(found=True, path="SKILL.md", branch="main", content="# Test"),
            discovered_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )

        result = DiscoveryResult(
            discovered_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
            sources_checked=["anthropic_official", "awesome_list"],
            total_skills=1,
            total_with_skill_md=1,
            skills=[skill],
        )

        assert result.total_skills == 1
        assert result.total_with_skill_md == 1
        assert len(result.skills) == 1
        assert "anthropic_official" in result.sources_checked


# =============================================================================
# Test: URL Parsing Utilities
# =============================================================================

class TestParseRepoUrl:
    """Test parse_repo_url function."""

    def test_parse_https_url(self):
        from discovery.github_fetcher import parse_repo_url

        owner, repo = parse_repo_url("https://github.com/anthropics/skill-pdf")
        assert owner == "anthropics"
        assert repo == "skill-pdf"

    def test_parse_https_url_with_trailing_slash(self):
        from discovery.github_fetcher import parse_repo_url

        owner, repo = parse_repo_url("https://github.com/anthropics/skill-pdf/")
        assert owner == "anthropics"
        assert repo == "skill-pdf"

    def test_parse_https_url_with_git_suffix(self):
        from discovery.github_fetcher import parse_repo_url

        owner, repo = parse_repo_url("https://github.com/anthropics/skill-pdf.git")
        assert owner == "anthropics"
        assert repo == "skill-pdf"

    def test_parse_ssh_url(self):
        from discovery.github_fetcher import parse_repo_url

        owner, repo = parse_repo_url("git@github.com:anthropics/skill-pdf.git")
        assert owner == "anthropics"
        assert repo == "skill-pdf"

    def test_parse_url_with_subpath(self):
        from discovery.github_fetcher import parse_repo_url

        owner, repo = parse_repo_url("https://github.com/anthropics/skills/tree/main/skills/pdf")
        assert owner == "anthropics"
        assert repo == "skills"

    def test_parse_invalid_url_returns_none(self):
        from discovery.github_fetcher import parse_repo_url

        result = parse_repo_url("not-a-valid-url")
        assert result is None

    def test_parse_non_github_url_returns_none(self):
        from discovery.github_fetcher import parse_repo_url

        result = parse_repo_url("https://gitlab.com/user/repo")
        assert result is None


class TestConstructRawUrl:
    """Test construct_raw_url function."""

    def test_construct_basic_raw_url(self):
        from discovery.github_fetcher import construct_raw_url

        url = construct_raw_url("anthropics", "skill-pdf", "main", "SKILL.md")
        assert url == "https://raw.githubusercontent.com/anthropics/skill-pdf/main/SKILL.md"

    def test_construct_raw_url_with_subpath(self):
        from discovery.github_fetcher import construct_raw_url

        url = construct_raw_url("anthropics", "skills", "main", "skills/pdf/SKILL.md")
        assert url == "https://raw.githubusercontent.com/anthropics/skills/main/skills/pdf/SKILL.md"

    def test_construct_raw_url_master_branch(self):
        from discovery.github_fetcher import construct_raw_url

        url = construct_raw_url("user", "repo", "master", "src/SKILL.md")
        assert url == "https://raw.githubusercontent.com/user/repo/master/src/SKILL.md"


# =============================================================================
# Test: Skill Name Extraction
# =============================================================================

class TestExtractSkillName:
    """Test extract_skill_name function."""

    def test_extract_from_skill_prefixed_repo(self):
        from discovery.github_fetcher import extract_skill_name

        name = extract_skill_name("anthropics", "skill-pdf", None)
        assert name == "pdf"

    def test_extract_from_repo_without_prefix(self):
        from discovery.github_fetcher import extract_skill_name

        name = extract_skill_name("someuser", "my-awesome-skill", None)
        assert name == "my-awesome-skill"

    def test_extract_from_skill_path_in_monorepo(self):
        from discovery.github_fetcher import extract_skill_name

        name = extract_skill_name("anthropics", "skills", "skills/pdf")
        assert name == "pdf"

    def test_extract_from_skill_path_nested(self):
        from discovery.github_fetcher import extract_skill_name

        name = extract_skill_name("anthropics", "skills", "community/skills/my-tool")
        assert name == "my-tool"

    def test_extract_handles_claude_suffix(self):
        from discovery.github_fetcher import extract_skill_name

        name = extract_skill_name("user", "pdf-claude", None)
        assert name == "pdf"


# =============================================================================
# Test: GitHub API Response Parsing
# =============================================================================

class TestParseGitHubApiResponse:
    """Test parse_github_api_response function."""

    def test_parse_full_response(self):
        from discovery.github_fetcher import parse_github_api_response
        from discovery.models import GitHubMetadata

        api_response = {
            "stargazers_count": 150,
            "description": "A great skill",
            "default_branch": "main",
            "pushed_at": "2024-03-15T10:30:00Z",
            "created_at": "2024-01-01T00:00:00Z",
            "language": "Python",
            "license": {"spdx_id": "MIT"},
            "open_issues_count": 3,
            "forks_count": 7,
        }

        metadata = parse_github_api_response(api_response)

        assert isinstance(metadata, GitHubMetadata)
        assert metadata.stars == 150
        assert metadata.description == "A great skill"
        assert metadata.default_branch == "main"
        assert metadata.language == "Python"
        assert metadata.license == "MIT"
        assert metadata.open_issues == 3
        assert metadata.forks == 7

    def test_parse_response_with_null_description(self):
        from discovery.github_fetcher import parse_github_api_response

        api_response = {
            "stargazers_count": 10,
            "description": None,
            "default_branch": "master",
            "pushed_at": "2024-02-01T00:00:00Z",
            "created_at": "2024-01-01T00:00:00Z",
            "language": None,
            "license": None,
            "open_issues_count": 0,
            "forks_count": 0,
        }

        metadata = parse_github_api_response(api_response)

        assert metadata.description is None
        assert metadata.language is None
        assert metadata.license is None

    def test_parse_response_with_license_object(self):
        from discovery.github_fetcher import parse_github_api_response

        api_response = {
            "stargazers_count": 50,
            "description": "Test",
            "default_branch": "main",
            "pushed_at": "2024-01-15T00:00:00Z",
            "created_at": "2024-01-01T00:00:00Z",
            "language": "TypeScript",
            "license": {"spdx_id": "Apache-2.0", "name": "Apache License 2.0"},
            "open_issues_count": 1,
            "forks_count": 2,
        }

        metadata = parse_github_api_response(api_response)
        assert metadata.license == "Apache-2.0"


# =============================================================================
# Test: Model Serialization
# =============================================================================

class TestModelSerialization:
    """Test that models serialize to JSON correctly."""

    def test_discovered_skill_to_json(self):
        from discovery.models import (
            DiscoveredSkill, SkillSource, GitHubMetadata, SkillMdInfo
        )

        skill = DiscoveredSkill(
            name="test-skill",
            slug="test-skill",
            source=SkillSource.ANTHROPIC_OFFICIAL,
            owner="anthropics",
            repo_name="skills",
            repository_url="https://github.com/anthropics/skills",
            skill_path="skills/test",
            github_metadata=GitHubMetadata(
                stars=50,
                description="Test",
                default_branch="main",
                pushed_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
            skill_md=SkillMdInfo(found=True, path="SKILL.md", branch="main", content="# Test"),
            discovered_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )

        # Should serialize without errors
        json_str = skill.model_dump_json()
        data = json.loads(json_str)

        assert data["name"] == "test-skill"
        assert data["source"] == "anthropic_official"
        assert data["github_metadata"]["stars"] == 50

    def test_discovery_result_to_json(self):
        from discovery.models import (
            DiscoveryResult, DiscoveredSkill, SkillSource,
            GitHubMetadata, SkillMdInfo
        )

        skill = DiscoveredSkill(
            name="test-skill",
            slug="test-skill",
            source=SkillSource.ANTHROPIC_OFFICIAL,
            owner="anthropics",
            repo_name="skills",
            repository_url="https://github.com/anthropics/skills",
            skill_path=None,
            github_metadata=GitHubMetadata(
                stars=50,
                description="Test",
                default_branch="main",
                pushed_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            ),
            skill_md=SkillMdInfo(found=False, path=None, branch=None, content=None),
            discovered_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )

        result = DiscoveryResult(
            discovered_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
            sources_checked=["anthropic_official"],
            total_skills=1,
            total_with_skill_md=0,
            skills=[skill],
        )

        json_str = result.model_dump_json()
        data = json.loads(json_str)

        assert data["total_skills"] == 1
        assert len(data["skills"]) == 1


# =============================================================================
# Test: GitHubFetcher Class
# =============================================================================

class TestGitHubFetcherInit:
    """Test GitHubFetcher initialization."""

    def test_init_without_token(self):
        from discovery.github_fetcher import GitHubFetcher

        fetcher = GitHubFetcher(token=None)
        assert fetcher.token is None

    def test_init_with_token(self):
        from discovery.github_fetcher import GitHubFetcher

        fetcher = GitHubFetcher(token="ghp_test_token")
        assert fetcher.token == "ghp_test_token"


class TestGitHubFetcherRateLimit:
    """Test rate limit tracking."""

    def test_rate_limit_from_headers(self):
        from discovery.github_fetcher import GitHubFetcher

        fetcher = GitHubFetcher(token=None)

        # Simulate headers from GitHub API response
        headers = {
            "x-ratelimit-limit": "60",
            "x-ratelimit-remaining": "55",
            "x-ratelimit-reset": "1704067200",  # Unix timestamp
        }

        fetcher.update_rate_limit(headers)

        assert fetcher.rate_limit_remaining == 55
        assert fetcher.rate_limit_limit == 60


# =============================================================================
# Test: SKILL.md Path Discovery
# =============================================================================

class TestSkillMdPaths:
    """Test the paths tried when looking for SKILL.md."""

    def test_default_paths(self):
        from discovery.github_fetcher import SKILL_MD_PATHS

        expected_paths = [
            "SKILL.md",
            "skill.md",
            "src/SKILL.md",
            ".claude/SKILL.md",
            "claude/SKILL.md",
        ]

        assert SKILL_MD_PATHS == expected_paths

    def test_default_branches(self):
        from discovery.github_fetcher import BRANCHES

        expected_branches = ["main", "master"]
        assert BRANCHES == expected_branches


# =============================================================================
# Test: Slug Generation
# =============================================================================

class TestGenerateSlug:
    """Test slug generation for skills."""

    def test_generate_slug_simple(self):
        from discovery.github_fetcher import generate_slug

        slug = generate_slug("PDF Skill")
        assert slug == "pdf-skill"

    def test_generate_slug_with_special_chars(self):
        from discovery.github_fetcher import generate_slug

        slug = generate_slug("My_Awesome.Skill!")
        assert slug == "my-awesome-skill"

    def test_generate_slug_already_clean(self):
        from discovery.github_fetcher import generate_slug

        slug = generate_slug("pdf")
        assert slug == "pdf"
