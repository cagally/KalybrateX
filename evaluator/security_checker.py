# Security Checker
"""
Analyzes SKILL.md content for security risks.

This module:
1. Sends skill content to Sonnet for security analysis
2. Parses the response to identify security issues
3. Determines grade based on issue severity
4. Returns full SecurityResult with all evidence

Risk Categories:
- data_exfiltration: External URLs, webhooks, sending data out
- file_system_abuse: Arbitrary paths, deletion, sensitive files
- credential_theft: Env vars, API keys, secrets
- code_injection: Eval, exec patterns
- malicious_dependencies: Suspicious package names
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import Optional, Tuple, List

from anthropic import Anthropic
from dotenv import load_dotenv

from evaluator.models import SecurityGrade, SecurityIssue, SecurityResult


# Load environment variables
load_dotenv()


# =============================================================================
# Exceptions
# =============================================================================

class SecurityCheckerError(Exception):
    """Base exception for security checker errors."""
    pass


class ConfigurationError(SecurityCheckerError):
    """Raised when configuration is missing or invalid."""
    pass


class SecurityParseError(SecurityCheckerError):
    """Raised when security analysis response cannot be parsed."""
    pass


# =============================================================================
# Constants
# =============================================================================

# Use Sonnet for security analysis (needs to understand code risks)
DEFAULT_MODEL = "claude-sonnet-4-20250514"


# =============================================================================
# Grading Logic
# =============================================================================

def determine_grade(issues: List[SecurityIssue]) -> SecurityGrade:
    """
    Determine the security grade based on identified issues.

    Grading logic:
    - FAIL: Any high severity issue
    - WARNING: Any medium severity issue (no high)
    - SECURE: Only low severity or no issues

    Args:
        issues: List of identified security issues

    Returns:
        SecurityGrade based on the highest severity issue
    """
    if not issues:
        return SecurityGrade.SECURE

    severities = {issue.severity for issue in issues}

    if "high" in severities:
        return SecurityGrade.FAIL
    elif "medium" in severities:
        return SecurityGrade.WARNING
    else:
        return SecurityGrade.SECURE


# =============================================================================
# Prompt Building
# =============================================================================

def build_security_prompt(skill_content: str) -> str:
    """
    Build the prompt for security analysis.

    Args:
        skill_content: The SKILL.md content to analyze

    Returns:
        The complete prompt for security analysis
    """
    return f"""You are a security analyst reviewing a SKILL.md file for Claude Code.
SKILL.md files are used to extend Claude's capabilities in the Claude Code CLI.

Analyze the following SKILL.md content for security risks. Check for these risk categories:

1. **data_exfiltration**: External URLs, webhooks, or patterns that send user data outside the local system
   - Look for: fetch(), HTTP requests to external servers, webhook URLs, sending code/data externally

2. **file_system_abuse**: Dangerous file operations
   - Look for: Arbitrary file paths (especially /etc, ~/.ssh, etc.), file deletion, reading sensitive files

3. **credential_theft**: Attempts to access or exfiltrate credentials
   - Look for: Reading environment variables (especially API keys), accessing .env files, credential patterns

4. **code_injection**: Dynamic code execution patterns
   - Look for: eval(), exec(), Function() constructor, dynamic imports with user input

5. **malicious_dependencies**: Suspicious package names (typosquatting, etc.)
   - Look for: Misspelled package names, unusual package sources

SKILL.md CONTENT TO ANALYZE:
---
{skill_content}
---

For each issue found, classify its severity:
- **high**: Immediate security risk, data could be exfiltrated or system compromised
- **medium**: Potential risk that warrants user awareness
- **low**: Minor concern, legitimate use case but worth noting

Return your analysis as JSON with this exact format:
{{
    "issues": [
        {{
            "category": "category_name",
            "severity": "low|medium|high",
            "description": "Human-readable description of the issue",
            "evidence": "The specific code/text that triggered this concern"
        }}
    ],
    "analysis": "Overall analysis summary explaining your findings"
}}

If no issues are found, return an empty issues array with an analysis explaining why the skill is safe.

Return ONLY the JSON, no additional text."""


# =============================================================================
# Response Parsing
# =============================================================================

def parse_security_response(response_text: str) -> Tuple[List[SecurityIssue], str]:
    """
    Parse the security analysis response to extract issues and analysis.

    Args:
        response_text: Raw text response from Claude

    Returns:
        Tuple of (issues list, analysis text)

    Raises:
        SecurityParseError: If response cannot be parsed
    """
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

    # Try to find JSON object in the text
    if not json_text.startswith("{"):
        match = re.search(r"\{[\s\S]*\}", json_text)
        if match:
            json_text = match.group(0)

    # Parse JSON
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise SecurityParseError(f"Failed to parse JSON response: {e}")

    if "issues" not in data:
        raise SecurityParseError("Response missing 'issues' field")

    # Convert issue dicts to SecurityIssue objects
    issues = []
    for issue_data in data["issues"]:
        issues.append(SecurityIssue(
            category=issue_data["category"],
            severity=issue_data["severity"],
            description=issue_data["description"],
            evidence=issue_data["evidence"],
        ))

    analysis = data.get("analysis", "")

    return issues, analysis


# =============================================================================
# SecurityChecker Class
# =============================================================================

class SecurityChecker:
    """
    Analyzes skill content for security risks.

    Uses Sonnet to analyze SKILL.md content and identify potential
    security issues across multiple risk categories.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
    ):
        """
        Initialize the SecurityChecker.

        Args:
            api_key: Anthropic API key. If not provided, loads from ANTHROPIC_API_KEY env var.
            model: Model for security analysis (default: Sonnet)

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

    def analyze(self, skill_content: str, skill_name: str) -> SecurityResult:
        """
        Analyze skill content for security risks.

        This is the main entry point for security analysis:
        1. Builds the security analysis prompt
        2. Sends to Sonnet for analysis
        3. Parses the response
        4. Determines grade based on issues
        5. Returns full SecurityResult

        Args:
            skill_content: The SKILL.md content to analyze
            skill_name: Name of the skill being analyzed

        Returns:
            SecurityResult with full analysis evidence
        """
        # 1. Build prompt
        prompt = build_security_prompt(skill_content)

        # 2. Send to Sonnet
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text
        total_tokens = response.usage.input_tokens + response.usage.output_tokens

        # 3. Parse response
        issues, analysis = parse_security_response(response_text)

        # 4. Determine grade
        grade = determine_grade(issues)

        # 5. Return full result
        return SecurityResult(
            skill_name=skill_name,
            grade=grade,
            issues=issues,
            analysis=analysis,
            analyzed_at=datetime.now(timezone.utc),
            model_used=self.model,
            tokens_used=total_tokens,
        )
