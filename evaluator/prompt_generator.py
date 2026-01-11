# Prompt Generator
"""
Generates evaluation prompts from SKILL.md files using Claude Sonnet.

This module reads a skill's SKILL.md file and uses Claude to generate
realistic user prompts that would naturally benefit from the skill's capabilities.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from dotenv import load_dotenv

from evaluator.models import GeneratedPrompt, PromptGenerationResult


# Load environment variables
load_dotenv()


# =============================================================================
# Exceptions
# =============================================================================

class PromptGeneratorError(Exception):
    """Base exception for prompt generator errors."""
    pass


class ConfigurationError(PromptGeneratorError):
    """Raised when configuration is missing or invalid."""
    pass


class SkillNotFoundError(PromptGeneratorError):
    """Raised when SKILL.md file cannot be found."""
    pass


class PromptParseError(PromptGeneratorError):
    """Raised when Claude's response cannot be parsed into prompts."""
    pass


# =============================================================================
# Constants
# =============================================================================

DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_SKILLS_DIR = Path("data/skills")


# =============================================================================
# SKILL.md Loading Functions
# =============================================================================

def load_skill_md(skill_dir: Path) -> str:
    """
    Load SKILL.md content from a skill directory.

    Args:
        skill_dir: Path to the skill directory containing SKILL.md

    Returns:
        Content of the SKILL.md file

    Raises:
        SkillNotFoundError: If SKILL.md doesn't exist in the directory
    """
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        raise SkillNotFoundError(f"SKILL.md not found in {skill_dir}")

    return skill_file.read_text(encoding="utf-8")


def load_skill_md_by_name(skill_name: str, base_dir: Optional[Path] = None) -> str:
    """
    Load SKILL.md content by skill name.

    Args:
        skill_name: Name of the skill (directory name)
        base_dir: Base directory containing skill directories

    Returns:
        Content of the SKILL.md file
    """
    if base_dir is None:
        base_dir = DEFAULT_SKILLS_DIR

    skill_dir = base_dir / skill_name
    return load_skill_md(skill_dir)


# =============================================================================
# Cache Management Functions
# =============================================================================

def check_cache_exists(skill_dir: Path) -> bool:
    """
    Check if cached prompts exist for a skill.

    Args:
        skill_dir: Path to the skill directory

    Returns:
        True if prompts.json exists, False otherwise
    """
    cache_file = skill_dir / "prompts.json"
    return cache_file.exists()


def load_cached_prompts(skill_dir: Path) -> PromptGenerationResult:
    """
    Load cached prompts from a skill directory.

    Args:
        skill_dir: Path to the skill directory

    Returns:
        Cached PromptGenerationResult
    """
    cache_file = skill_dir / "prompts.json"
    cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
    return PromptGenerationResult.model_validate(cache_data)


def save_prompts_to_cache(result: PromptGenerationResult, skill_dir: Path) -> None:
    """
    Save prompts to cache file.

    Args:
        result: PromptGenerationResult to save
        skill_dir: Path to the skill directory
    """
    cache_file = skill_dir / "prompts.json"
    cache_file.write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8"
    )


# =============================================================================
# Prompt Building Functions
# =============================================================================

def build_generation_prompt(skill_content: str) -> str:
    """
    Build the prompt for Claude to generate evaluation prompts.

    Args:
        skill_content: Content of the SKILL.md file

    Returns:
        The system prompt for Claude
    """
    return f"""You are an expert at creating realistic user prompts for testing AI capabilities.

Given the following SKILL.md file content, generate exactly 10 diverse prompts that a real user might ask, which would naturally benefit from the capabilities described in this skill.

SKILL.md Content:
---
{skill_content}
---

REQUIREMENTS:
1. Generate exactly 10 prompts
2. Make prompts sound like realistic user requests (natural language, not formal)
3. Do NOT mention the skill name or that a skill exists - pretend you're a user who just has a task to do
4. Include a mix of difficulty levels:
   - 3-4 "simple" prompts: Basic, single-step tasks
   - 3-4 "medium" prompts: Multi-step or more nuanced tasks
   - 2-3 "complex" prompts: Advanced, multi-part tasks requiring deep skill knowledge
5. Each prompt should test a specific capability from the skill
6. Prompts should be diverse - test different capabilities

RESPONSE FORMAT:
Return a JSON array with exactly 10 objects, each containing:
- "prompt": The user's request (string)
- "difficulty": One of "simple", "medium", or "complex"
- "capability_tested": Brief description of which skill capability this tests

Example format:
```json
[
    {{
        "prompt": "I need to combine these 5 PDF reports into a single document",
        "difficulty": "simple",
        "capability_tested": "pdf_merge"
    }},
    ...
]
```

Return ONLY the JSON array, no additional text."""


# =============================================================================
# Response Parsing Functions
# =============================================================================

def parse_prompt_response(response_text: str) -> list[GeneratedPrompt]:
    """
    Parse Claude's response into GeneratedPrompt objects.

    Args:
        response_text: Raw text response from Claude

    Returns:
        List of GeneratedPrompt objects

    Raises:
        PromptParseError: If response cannot be parsed
    """
    # Try to extract JSON from the response
    json_text = response_text.strip()

    # Remove markdown code blocks if present
    if "```json" in json_text:
        match = re.search(r"```json\s*([\s\S]*?)\s*```", json_text)
        if match:
            json_text = match.group(1)
    elif "```" in json_text:
        match = re.search(r"```\s*([\s\S]*?)\s*```", json_text)
        if match:
            json_text = match.group(1)

    # Try to find JSON array in the text
    if not json_text.startswith("["):
        match = re.search(r"\[[\s\S]*\]", json_text)
        if match:
            json_text = match.group(0)

    # Parse JSON
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise PromptParseError(f"Failed to parse JSON response: {e}")

    if not isinstance(data, list):
        raise PromptParseError("Response is not a JSON array")

    if len(data) == 0:
        raise PromptParseError("Response contains empty array of prompts")

    # Convert to GeneratedPrompt objects
    prompts = []
    for i, item in enumerate(data):
        try:
            prompt = GeneratedPrompt.model_validate(item)
            prompts.append(prompt)
        except Exception as e:
            raise PromptParseError(f"Failed to parse prompt {i}: {e}")

    return prompts


# =============================================================================
# PromptGenerator Class
# =============================================================================

class PromptGenerator:
    """
    Generates evaluation prompts for skills using Claude Sonnet.

    This class reads SKILL.md files and uses Claude to generate realistic
    user prompts that would benefit from the skill's capabilities.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        """
        Initialize the PromptGenerator.

        Args:
            api_key: Anthropic API key. If not provided, loads from ANTHROPIC_API_KEY env var.
            model: Claude model to use for generation.

        Raises:
            ConfigurationError: If no API key is available.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "ANTHROPIC_API_KEY not found. Set it in .env or pass api_key parameter."
            )

        self.model = model
        self.client = Anthropic(api_key=self.api_key)

    def generate(self, skill_content: str, skill_name: str = "unknown") -> PromptGenerationResult:
        """
        Generate evaluation prompts for a skill.

        Args:
            skill_content: Content of the SKILL.md file
            skill_name: Name of the skill (for metadata)

        Returns:
            PromptGenerationResult with generated prompts
        """
        # Build the prompt
        system_prompt = build_generation_prompt(skill_content)

        # Call Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": "Generate the prompts as specified."}
            ],
            system=system_prompt,
        )

        # Extract response text
        response_text = response.content[0].text

        # Parse the response
        prompts = parse_prompt_response(response_text)

        # Calculate tokens used
        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        return PromptGenerationResult(
            skill_name=skill_name,
            prompts=prompts,
            generated_at=datetime.now(timezone.utc),
            model_used=self.model,
            tokens_used=tokens_used,
        )

    def generate_for_skill(
        self,
        skill_name: str,
        skills_dir: Optional[Path] = None,
        force: bool = False,
    ) -> PromptGenerationResult:
        """
        Generate evaluation prompts for a skill by name.

        Args:
            skill_name: Name of the skill (directory name)
            skills_dir: Base directory containing skill directories
            force: If True, regenerate even if cached prompts exist

        Returns:
            PromptGenerationResult with generated (or cached) prompts
        """
        if skills_dir is None:
            skills_dir = DEFAULT_SKILLS_DIR

        skill_dir = skills_dir / skill_name

        # Check cache unless force is True
        if not force and check_cache_exists(skill_dir):
            return load_cached_prompts(skill_dir)

        # Load SKILL.md content
        skill_content = load_skill_md(skill_dir)

        # Generate prompts
        result = self.generate(skill_content, skill_name=skill_name)

        # Save to cache
        save_prompts_to_cache(result, skill_dir)

        return result
