# Skill Categories
"""
Categorizes skills by their output type to determine appropriate verification method.

Categories:
- FILE_ARTIFACT: Skills that produce files (PDF, XLSX, DOCX, images)
- CODE_GENERATION: Skills that produce runnable code
- CONFIGURATION: Skills that produce config files (YAML, JSON schemas)
- ADVISORY: Skills that provide guidance/text (no execution verification)
"""

from enum import Enum
from typing import Optional


class SkillCategory(str, Enum):
    """Category determining verification method for a skill."""
    FILE_ARTIFACT = "file_artifact"      # pdf, xlsx, docx, images
    CODE_GENERATION = "code_generation"  # mcp-builder, webapp-testing
    CONFIGURATION = "configuration"      # homeassistant, skillforge
    ADVISORY = "advisory"                # writing, career, design


# Known skill category mappings
# Skills not in this map default to ADVISORY (response quality only)
SKILL_CATEGORIES: dict[str, SkillCategory] = {
    # File Artifact Skills - produce actual files
    "pdf": SkillCategory.FILE_ARTIFACT,
    "xlsx": SkillCategory.FILE_ARTIFACT,
    "docx": SkillCategory.FILE_ARTIFACT,
    "pptx": SkillCategory.FILE_ARTIFACT,
    "csv": SkillCategory.FILE_ARTIFACT,
    "image": SkillCategory.FILE_ARTIFACT,
    "svg": SkillCategory.FILE_ARTIFACT,

    # Code Generation Skills - produce runnable code
    "mcp-builder": SkillCategory.CODE_GENERATION,
    "webapp-testing": SkillCategory.CODE_GENERATION,
    "elixir-thinking": SkillCategory.CODE_GENERATION,
    "phoenix-thinking": SkillCategory.CODE_GENERATION,
    "otp-thinking": SkillCategory.CODE_GENERATION,
    "ecto-thinking": SkillCategory.CODE_GENERATION,
    "oban-thinking": SkillCategory.CODE_GENERATION,
    "web-artifacts-builder": SkillCategory.CODE_GENERATION,
    "algorithmic-art": SkillCategory.CODE_GENERATION,
    "canvas-design": SkillCategory.CODE_GENERATION,
    "frontend-design": SkillCategory.CODE_GENERATION,
    "slack-gif-creator": SkillCategory.CODE_GENERATION,

    # Configuration Skills - produce config files
    "skill-homeassistant": SkillCategory.CONFIGURATION,
    "skillforge": SkillCategory.CONFIGURATION,
    "skill-creator": SkillCategory.CONFIGURATION,
    "template": SkillCategory.CONFIGURATION,
    "marketplace-manager": SkillCategory.CONFIGURATION,
    "marketplace-release": SkillCategory.CONFIGURATION,
    "marketplace-audit": SkillCategory.CONFIGURATION,
    "marketplace-bump": SkillCategory.CONFIGURATION,

    # Advisory Skills - text/guidance output (default)
    "writing": SkillCategory.ADVISORY,
    "design": SkillCategory.ADVISORY,
    "product": SkillCategory.ADVISORY,
    "founder": SkillCategory.ADVISORY,
    "career": SkillCategory.ADVISORY,
    "counsel": SkillCategory.ADVISORY,
    "recall": SkillCategory.ADVISORY,
    "gate": SkillCategory.ADVISORY,
    "trace": SkillCategory.ADVISORY,
    "internal-comms": SkillCategory.ADVISORY,
    "doc-coauthoring": SkillCategory.ADVISORY,
    "brand-guidelines": SkillCategory.ADVISORY,
    "notebooklm-skill": SkillCategory.ADVISORY,
    "codex": SkillCategory.ADVISORY,
    "gemini": SkillCategory.ADVISORY,
}


def get_skill_category(skill_name: str) -> SkillCategory:
    """
    Get the category for a skill.

    Args:
        skill_name: Name of the skill (e.g., "pdf", "mcp-builder")

    Returns:
        SkillCategory for the skill, defaults to ADVISORY if unknown
    """
    # Normalize skill name (lowercase, strip whitespace)
    normalized = skill_name.lower().strip()
    return SKILL_CATEGORIES.get(normalized, SkillCategory.ADVISORY)


def requires_execution(skill_name: str) -> bool:
    """
    Check if a skill requires execution verification.

    Args:
        skill_name: Name of the skill

    Returns:
        True if the skill produces executable output (file, code, or config)
    """
    category = get_skill_category(skill_name)
    return category in (
        SkillCategory.FILE_ARTIFACT,
        SkillCategory.CODE_GENERATION,
        SkillCategory.CONFIGURATION,
    )


def get_output_type(skill_name: str) -> Optional[str]:
    """
    Get the expected output type for a skill.

    Args:
        skill_name: Name of the skill

    Returns:
        Expected output file extension or type, None for advisory skills
    """
    category = get_skill_category(skill_name)

    # Map skills to their primary output type
    output_types = {
        "pdf": "pdf",
        "xlsx": "xlsx",
        "docx": "docx",
        "pptx": "pptx",
        "csv": "csv",
        "image": "png",
        "svg": "svg",
        "skill-homeassistant": "yaml",
        "skillforge": "md",
        "skill-creator": "md",
        "template": "md",
    }

    if skill_name in output_types:
        return output_types[skill_name]

    if category == SkillCategory.CODE_GENERATION:
        return "py"  # Default to Python for code generation

    if category == SkillCategory.CONFIGURATION:
        return "yaml"  # Default to YAML for configs

    return None  # Advisory skills have no specific output type
