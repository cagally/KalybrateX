# Code Extractor
"""
Extracts executable code blocks from LLM responses.

Handles various markdown code block formats and attempts to combine
multiple related blocks into a single executable script.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class CodeBlock:
    """A single code block extracted from a response."""
    language: str
    code: str
    start_line: int
    end_line: int


@dataclass
class ExtractedCode:
    """Result of code extraction from a response."""
    blocks: list[CodeBlock]
    primary_language: str
    combined_code: str
    has_executable_code: bool


# Language aliases for normalization
LANGUAGE_ALIASES: dict[str, str] = {
    "python": "python",
    "py": "python",
    "python3": "python",
    "javascript": "javascript",
    "js": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "bash": "bash",
    "sh": "bash",
    "shell": "bash",
    "zsh": "bash",
    "yaml": "yaml",
    "yml": "yaml",
    "json": "json",
    "html": "html",
    "css": "css",
    "sql": "sql",
    "rust": "rust",
    "go": "go",
    "golang": "go",
    "ruby": "ruby",
    "rb": "ruby",
    "elixir": "elixir",
    "ex": "elixir",
}

# Languages that can be executed
EXECUTABLE_LANGUAGES = {"python", "javascript", "typescript", "bash", "ruby", "elixir"}


def normalize_language(lang: str) -> str:
    """
    Normalize a language identifier.

    Args:
        lang: Raw language string from code block

    Returns:
        Normalized language name
    """
    normalized = lang.lower().strip()
    return LANGUAGE_ALIASES.get(normalized, normalized)


def extract_code_blocks(response: str) -> list[CodeBlock]:
    """
    Extract all code blocks from a markdown response.

    Args:
        response: The full LLM response text

    Returns:
        List of CodeBlock objects
    """
    blocks = []

    # Pattern for fenced code blocks: ```language\ncode\n```
    pattern = r"```(\w*)\n(.*?)```"
    matches = re.finditer(pattern, response, re.DOTALL)

    for match in matches:
        lang = match.group(1) or "text"
        code = match.group(2)

        # Calculate line numbers
        start_pos = match.start()
        start_line = response[:start_pos].count("\n") + 1
        end_line = start_line + code.count("\n")

        blocks.append(CodeBlock(
            language=normalize_language(lang),
            code=code.strip(),
            start_line=start_line,
            end_line=end_line,
        ))

    return blocks


def detect_primary_language(blocks: list[CodeBlock]) -> str:
    """
    Detect the primary programming language from code blocks.

    Prioritizes executable languages and uses frequency as tiebreaker.

    Args:
        blocks: List of extracted code blocks

    Returns:
        The primary language, or "text" if none detected
    """
    if not blocks:
        return "text"

    # Count language occurrences
    lang_counts: dict[str, int] = {}
    for block in blocks:
        lang = block.language
        lang_counts[lang] = lang_counts.get(lang, 0) + 1

    # Prioritize executable languages
    executable = [lang for lang in lang_counts if lang in EXECUTABLE_LANGUAGES]
    if executable:
        # Return most frequent executable language
        return max(executable, key=lambda l: lang_counts[l])

    # Fall back to most frequent overall
    return max(lang_counts, key=lambda l: lang_counts[l])


def combine_code_blocks(blocks: list[CodeBlock], target_language: str) -> str:
    """
    Combine multiple code blocks of the same language into one script.

    Args:
        blocks: List of code blocks
        target_language: Language to filter for

    Returns:
        Combined code as a single string
    """
    relevant_blocks = [b for b in blocks if b.language == target_language]

    if not relevant_blocks:
        return ""

    # Simple combination: join with newlines
    # Could be smarter about imports, etc. in the future
    combined = "\n\n".join(b.code for b in relevant_blocks)
    return combined


def extract_code(response: str) -> ExtractedCode:
    """
    Extract and analyze code from an LLM response.

    This is the main entry point for code extraction.

    Args:
        response: The full LLM response text

    Returns:
        ExtractedCode with all blocks and combined executable code
    """
    blocks = extract_code_blocks(response)
    primary_lang = detect_primary_language(blocks)
    combined = combine_code_blocks(blocks, primary_lang)

    has_executable = primary_lang in EXECUTABLE_LANGUAGES and bool(combined.strip())

    return ExtractedCode(
        blocks=blocks,
        primary_language=primary_lang,
        combined_code=combined,
        has_executable_code=has_executable,
    )


def extract_python_code(response: str) -> Optional[str]:
    """
    Extract Python code specifically from a response.

    Convenience function for Python-focused skills.

    Args:
        response: The full LLM response text

    Returns:
        Combined Python code, or None if no Python found
    """
    blocks = extract_code_blocks(response)
    python_blocks = [b for b in blocks if b.language == "python"]

    if not python_blocks:
        return None

    return "\n\n".join(b.code for b in python_blocks)


def extract_file_content(response: str, filename: str) -> Optional[str]:
    """
    Extract content intended for a specific file from the response.

    Looks for patterns like "Save to filename:" or code blocks followed
    by file path mentions.

    Args:
        response: The full LLM response text
        filename: Target filename to look for

    Returns:
        Content for that file, or None if not found
    """
    # Pattern 1: Look for "filename:" followed by code block
    pattern1 = rf"(?:{re.escape(filename)}|`{re.escape(filename)}`)\s*:?\s*```\w*\n(.*?)```"
    match = re.search(pattern1, response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern 2: Look for "save to filename" near a code block
    pattern2 = rf"(?:save|write|create|output).*?{re.escape(filename)}.*?```\w*\n(.*?)```"
    match = re.search(pattern2, response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None
