# Quality Evaluator
"""
Runs A/B comparisons between baseline (no skill) and skill-enhanced responses.

This module:
1. Runs prompts with Haiku (no skill) for baseline
2. Runs prompts with Haiku (skill in system prompt) for enhanced response
3. Randomizes A/B order to avoid position bias
4. Uses Sonnet to judge which response is better
5. Records full evidence including tokens and reasoning
"""

import json
import os
import random
import re
from datetime import datetime, timezone
from typing import Optional, Tuple

from anthropic import Anthropic
from dotenv import load_dotenv

from evaluator.models import ComparisonResult, Verdict


# Load environment variables
load_dotenv()


# =============================================================================
# Exceptions
# =============================================================================

class QualityEvaluatorError(Exception):
    """Base exception for quality evaluator errors."""
    pass


class ConfigurationError(QualityEvaluatorError):
    """Raised when configuration is missing or invalid."""
    pass


class JudgeParseError(QualityEvaluatorError):
    """Raised when judge response cannot be parsed."""
    pass


# =============================================================================
# Constants
# =============================================================================

# Use Haiku for execution (cost efficient)
DEFAULT_EXECUTION_MODEL = "claude-haiku-4-20250514"
# Use Sonnet for judging (needs nuance)
DEFAULT_JUDGE_MODEL = "claude-sonnet-4-20250514"


# =============================================================================
# Claude Code Context (CRITICAL - from docs/04-learnings.md)
# =============================================================================

CLAUDE_CODE_CONTEXT = """IMPORTANT CONTEXT:
These skills are designed for Claude Code users. Claude Code is Anthropic's
CLI coding assistant with features including:
- Hooks (PreToolUse, PostToolUse, Notification, Stop, etc.)
- Custom slash commands
- SKILL.md files for specialized capabilities
- Rules for validation and automation
- Custom agents

A response that provides Claude Code-specific configuration (hooks, rules,
SKILL.md files) is VALUABLE and REAL, not fictional. Judge based on value
to Claude Code users."""


def get_claude_code_context() -> str:
    """
    Get the Claude Code context that must be included in all judge prompts.

    This is critical - without it, the judge will penalize Claude Code-specific
    outputs as "fictional" since Sonnet's training predates Claude Code features.

    Returns:
        The context string to include in judge prompts
    """
    return CLAUDE_CODE_CONTEXT


# =============================================================================
# Judge Prompt Building
# =============================================================================

def build_judge_prompt(user_prompt: str, response_a: str, response_b: str) -> str:
    """
    Build the prompt for the judge to compare two responses.

    Args:
        user_prompt: The original user prompt
        response_a: First response (could be baseline or skill)
        response_b: Second response (could be baseline or skill)

    Returns:
        The complete prompt for the judge
    """
    return f"""{CLAUDE_CODE_CONTEXT}

You are an expert judge evaluating two AI assistant responses to a user's request.
Your job is to determine which response is more helpful, accurate, and valuable to the user.

USER'S REQUEST:
{user_prompt}

---

RESPONSE A:
{response_a}

---

RESPONSE B:
{response_b}

---

EVALUATION CRITERIA:
1. Helpfulness: Which response better addresses the user's needs?
2. Accuracy: Which response is more correct and reliable?
3. Completeness: Which response provides more comprehensive guidance?
4. Practicality: Which response is more actionable and useful?

For Claude Code-specific content (hooks, rules, SKILL.md files, slash commands):
- These ARE real features, not fictional
- Judge based on whether the configuration would actually work and be valuable

INSTRUCTIONS:
Compare the two responses and determine which is better overall.
Return your judgment as JSON with exactly this format:

{{"verdict": "A" or "B" or "TIE", "reasoning": "Your explanation here"}}

If Response A is clearly better, verdict is "A".
If Response B is clearly better, verdict is "B".
If they are roughly equal in quality, verdict is "TIE".

Return ONLY the JSON, no additional text."""


# =============================================================================
# Response Parsing
# =============================================================================

def parse_judge_response(response_text: str) -> Tuple[str, str]:
    """
    Parse the judge's response to extract verdict and reasoning.

    Args:
        response_text: Raw text response from the judge

    Returns:
        Tuple of (verdict, reasoning) where verdict is "A", "B", or "TIE"

    Raises:
        JudgeParseError: If response cannot be parsed
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
        raise JudgeParseError(f"Failed to parse JSON response: {e}")

    if "verdict" not in data:
        raise JudgeParseError("Response missing 'verdict' field")

    verdict = data["verdict"].upper()
    reasoning = data.get("reasoning", "")

    return verdict, reasoning


# =============================================================================
# QualityEvaluator Class
# =============================================================================

class QualityEvaluator:
    """
    Evaluates skill quality through A/B comparisons.

    Runs prompts with and without a skill, then has Sonnet judge which
    response is better. Randomizes position to avoid bias.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        execution_model: str = DEFAULT_EXECUTION_MODEL,
        judge_model: str = DEFAULT_JUDGE_MODEL,
    ):
        """
        Initialize the QualityEvaluator.

        Args:
            api_key: Anthropic API key. If not provided, loads from ANTHROPIC_API_KEY env var.
            execution_model: Model for running prompts (default: Haiku)
            judge_model: Model for judging comparisons (default: Sonnet)

        Raises:
            ConfigurationError: If no API key is available.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "ANTHROPIC_API_KEY not found. Set it in .env or pass api_key parameter."
            )

        self.execution_model = execution_model
        self.judge_model = judge_model
        self.client = Anthropic(api_key=self.api_key)

    def run_baseline(self, prompt: str) -> Tuple[str, int]:
        """
        Run a prompt without any skill (baseline).

        Args:
            prompt: The user prompt to run

        Returns:
            Tuple of (response_text, total_tokens)
        """
        response = self.client.messages.create(
            model=self.execution_model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            # No system prompt for baseline
        )

        response_text = response.content[0].text
        total_tokens = response.usage.input_tokens + response.usage.output_tokens

        return response_text, total_tokens

    def run_with_skill(self, prompt: str, skill_content: str) -> Tuple[str, int]:
        """
        Run a prompt with a skill in the system prompt.

        Args:
            prompt: The user prompt to run
            skill_content: The SKILL.md content to include

        Returns:
            Tuple of (response_text, total_tokens)
        """
        response = self.client.messages.create(
            model=self.execution_model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            system=skill_content,
        )

        response_text = response.content[0].text
        total_tokens = response.usage.input_tokens + response.usage.output_tokens

        return response_text, total_tokens

    def judge_comparison(
        self,
        prompt: str,
        response_a: str,
        response_b: str,
        position_a: str,
    ) -> Tuple[Verdict, str]:
        """
        Have Sonnet judge which response is better.

        Args:
            prompt: The original user prompt
            response_a: First response shown to judge
            response_b: Second response shown to judge
            position_a: What position_a represents ("baseline" or "skill")

        Returns:
            Tuple of (verdict, reasoning) where verdict indicates skill/baseline/tie
        """
        judge_prompt = build_judge_prompt(prompt, response_a, response_b)

        response = self.client.messages.create(
            model=self.judge_model,
            max_tokens=1024,
            messages=[{"role": "user", "content": judge_prompt}],
        )

        response_text = response.content[0].text
        raw_verdict, reasoning = parse_judge_response(response_text)

        # Map A/B/TIE verdict to skill/baseline/tie based on position
        if raw_verdict == "TIE":
            verdict = Verdict.TIE
        elif raw_verdict == "A":
            # A won - what was in position A?
            verdict = Verdict.SKILL_WINS if position_a == "skill" else Verdict.BASELINE_WINS
        else:  # B won
            # B won - what was in position B?
            verdict = Verdict.BASELINE_WINS if position_a == "skill" else Verdict.SKILL_WINS

        return verdict, reasoning

    def evaluate(self, prompt: str, skill_content: str) -> ComparisonResult:
        """
        Run a full A/B comparison for a prompt.

        This is the main entry point for evaluation:
        1. Runs baseline (no skill)
        2. Runs with skill
        3. Randomizes A/B position
        4. Judges the comparison
        5. Returns full result with all evidence

        Args:
            prompt: The user prompt to evaluate
            skill_content: The SKILL.md content

        Returns:
            ComparisonResult with full comparison evidence
        """
        # 1. Run baseline
        baseline_response, baseline_tokens = self.run_baseline(prompt)

        # 2. Run with skill
        skill_response, skill_tokens = self.run_with_skill(prompt, skill_content)

        # 3. Randomize position to avoid bias
        position_a = random.choice(["skill", "baseline"])
        position_b = "baseline" if position_a == "skill" else "skill"

        if position_a == "skill":
            response_a = skill_response
            response_b = baseline_response
        else:
            response_a = baseline_response
            response_b = skill_response

        # 4. Judge the comparison
        verdict, reasoning = self.judge_comparison(
            prompt=prompt,
            response_a=response_a,
            response_b=response_b,
            position_a=position_a,
        )

        # 5. Return full result
        return ComparisonResult(
            prompt=prompt,
            baseline_response=baseline_response,
            skill_response=skill_response,
            verdict=verdict,
            reasoning=reasoning,
            baseline_tokens=baseline_tokens,
            skill_tokens=skill_tokens,
            position_a=position_a,
            position_b=position_b,
            judge_model=self.judge_model,
            judged_at=datetime.now(timezone.utc),
        )
