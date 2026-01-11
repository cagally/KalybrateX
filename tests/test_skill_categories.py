# Tests for Skill Categories
"""Tests for evaluator/skill_categories.py"""

import pytest

from evaluator.skill_categories import (
    SkillCategory,
    get_skill_category,
    requires_execution,
    get_output_type,
)


class TestGetSkillCategory:
    """Tests for skill category detection."""

    def test_file_artifact_skills(self):
        assert get_skill_category("pdf") == SkillCategory.FILE_ARTIFACT
        assert get_skill_category("xlsx") == SkillCategory.FILE_ARTIFACT
        assert get_skill_category("docx") == SkillCategory.FILE_ARTIFACT
        assert get_skill_category("pptx") == SkillCategory.FILE_ARTIFACT

    def test_code_generation_skills(self):
        assert get_skill_category("mcp-builder") == SkillCategory.CODE_GENERATION
        assert get_skill_category("webapp-testing") == SkillCategory.CODE_GENERATION
        assert get_skill_category("elixir-thinking") == SkillCategory.CODE_GENERATION

    def test_configuration_skills(self):
        assert get_skill_category("skill-homeassistant") == SkillCategory.CONFIGURATION
        assert get_skill_category("skillforge") == SkillCategory.CONFIGURATION

    def test_advisory_skills(self):
        assert get_skill_category("writing") == SkillCategory.ADVISORY
        assert get_skill_category("career") == SkillCategory.ADVISORY
        assert get_skill_category("design") == SkillCategory.ADVISORY

    def test_unknown_defaults_to_advisory(self):
        assert get_skill_category("unknown-skill") == SkillCategory.ADVISORY
        assert get_skill_category("random-thing") == SkillCategory.ADVISORY

    def test_case_insensitive(self):
        assert get_skill_category("PDF") == SkillCategory.FILE_ARTIFACT
        assert get_skill_category("Pdf") == SkillCategory.FILE_ARTIFACT
        assert get_skill_category("  pdf  ") == SkillCategory.FILE_ARTIFACT


class TestRequiresExecution:
    """Tests for execution requirement detection."""

    def test_file_artifact_requires_execution(self):
        assert requires_execution("pdf") is True
        assert requires_execution("xlsx") is True

    def test_code_generation_requires_execution(self):
        assert requires_execution("mcp-builder") is True
        assert requires_execution("webapp-testing") is True

    def test_configuration_requires_execution(self):
        assert requires_execution("skill-homeassistant") is True

    def test_advisory_does_not_require_execution(self):
        assert requires_execution("writing") is False
        assert requires_execution("career") is False

    def test_unknown_does_not_require_execution(self):
        assert requires_execution("unknown-skill") is False


class TestGetOutputType:
    """Tests for output type detection."""

    def test_pdf_output_type(self):
        assert get_output_type("pdf") == "pdf"

    def test_xlsx_output_type(self):
        assert get_output_type("xlsx") == "xlsx"

    def test_code_generation_defaults_to_py(self):
        assert get_output_type("mcp-builder") == "py"
        assert get_output_type("webapp-testing") == "py"

    def test_configuration_defaults_to_yaml(self):
        assert get_output_type("skill-homeassistant") == "yaml"

    def test_advisory_returns_none(self):
        assert get_output_type("writing") is None
        assert get_output_type("career") is None

    def test_unknown_returns_none(self):
        assert get_output_type("unknown-skill") is None
