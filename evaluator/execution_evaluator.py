# Execution Evaluator
"""
Orchestrates execution verification for skills.

This module:
1. Gets execution prompts appropriate for the skill category
2. Runs both baseline and skill responses through execution
3. Compares execution results to determine winner
4. Returns execution score metrics

Key principle: Execute BOTH baseline and skill responses to get
a fair comparison (execution win rate), not just pass/fail.
"""

import os
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from anthropic import Anthropic
from dotenv import load_dotenv

from evaluator.code_extractor import extract_code
from evaluator.execution_verifier import (
    verify_response,
    is_docker_available,
    VerificationResult,
)
from evaluator.models import (
    ExecutionComparisonResult,
    ExecutionScore,
    SkillCategory,
    Verdict,
)
from evaluator.prompt_templates import get_execution_prompts, ExecutionPrompt
from evaluator.skill_categories import get_skill_category, requires_execution


# Load environment variables
load_dotenv()


# =============================================================================
# Exceptions
# =============================================================================

class ExecutionEvaluatorError(Exception):
    """Base exception for execution evaluator errors."""
    pass


class ConfigurationError(ExecutionEvaluatorError):
    """Raised when configuration is missing or invalid."""
    pass


# =============================================================================
# Constants
# =============================================================================

# Use Haiku for execution (cost efficient)
DEFAULT_EXECUTION_MODEL = "claude-3-5-haiku-20241022"


# =============================================================================
# ExecutionEvaluator Class
# =============================================================================

class ExecutionEvaluator:
    """
    Evaluates skill execution by running generated code.

    Runs execution prompts with and without the skill, executes the
    generated code, and compares which produces better results.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        execution_model: str = DEFAULT_EXECUTION_MODEL,
        use_docker: bool = True,
    ):
        """
        Initialize the ExecutionEvaluator.

        Args:
            api_key: Anthropic API key. If not provided, loads from env.
            execution_model: Model for running prompts (default: Haiku)
            use_docker: Whether to use Docker for sandboxed execution

        Raises:
            ConfigurationError: If no API key is available.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "ANTHROPIC_API_KEY not found. Set it in .env or pass api_key parameter."
            )

        self.execution_model = execution_model
        self.use_docker = use_docker and is_docker_available()
        self.client = Anthropic(api_key=self.api_key)

        if use_docker and not self.use_docker:
            print("    [WARN] Docker not available, using local execution (less secure)")

    def run_prompt(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Run a prompt through the LLM.

        Args:
            prompt: The user prompt
            system: Optional system prompt (skill content)

        Returns:
            The LLM response text
        """
        kwargs = {
            "model": self.execution_model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def compare_verifications(
        self,
        baseline: VerificationResult,
        skill: VerificationResult,
    ) -> Tuple[Verdict, str]:
        """
        Compare two verification results to determine winner.

        Args:
            baseline: Verification result for baseline response
            skill: Verification result for skill response

        Returns:
            Tuple of (verdict, reasoning)
        """
        b_valid = baseline.output_valid
        s_valid = skill.output_valid
        b_ran = baseline.execution_success
        s_ran = skill.execution_success
        b_code = baseline.code_extracted
        s_code = skill.code_extracted

        # Case 1: Only skill produced valid output
        if s_valid and not b_valid:
            return Verdict.SKILL_WINS, "Skill produced valid output, baseline did not"

        # Case 2: Only baseline produced valid output
        if b_valid and not s_valid:
            return Verdict.BASELINE_WINS, "Baseline produced valid output, skill did not"

        # Case 3: Both produced valid output
        if b_valid and s_valid:
            return Verdict.TIE, "Both produced valid output"

        # Case 4: Neither produced valid output, but one ran successfully
        if s_ran and not b_ran:
            return Verdict.SKILL_WINS, "Skill code ran, baseline code failed"

        if b_ran and not s_ran:
            return Verdict.BASELINE_WINS, "Baseline code ran, skill code failed"

        # Case 5: Neither ran, but one extracted code
        if s_code and not b_code:
            return Verdict.SKILL_WINS, "Skill produced code, baseline did not"

        if b_code and not s_code:
            return Verdict.BASELINE_WINS, "Baseline produced code, skill did not"

        # Case 6: Equal failure
        return Verdict.TIE, "Both failed equally"

    def evaluate_prompt(
        self,
        execution_prompt: ExecutionPrompt,
        skill_content: str,
        skill_name: str,
    ) -> ExecutionComparisonResult:
        """
        Evaluate a single execution prompt.

        Runs the prompt with and without the skill, executes both,
        and compares results.

        Args:
            execution_prompt: The execution prompt to evaluate
            skill_content: The SKILL.md content
            skill_name: Name of the skill

        Returns:
            ExecutionComparisonResult with full comparison details
        """
        prompt_text = execution_prompt.prompt

        # Run baseline (no skill)
        baseline_response = self.run_prompt(prompt_text)

        # Run with skill
        skill_response = self.run_prompt(prompt_text, system=skill_content)

        # Verify baseline execution
        baseline_verification = verify_response(
            response=baseline_response,
            skill_name=f"{skill_name}_baseline",
            prompt=prompt_text,
            expected_files=execution_prompt.expected_files,
            expected_properties=execution_prompt.expected_properties,
            use_docker=self.use_docker,
        )

        # Verify skill execution
        skill_verification = verify_response(
            response=skill_response,
            skill_name=skill_name,
            prompt=prompt_text,
            expected_files=execution_prompt.expected_files,
            expected_properties=execution_prompt.expected_properties,
            use_docker=self.use_docker,
        )

        # Compare results
        verdict, reasoning = self.compare_verifications(
            baseline_verification,
            skill_verification,
        )

        return ExecutionComparisonResult(
            prompt=prompt_text,
            tier=execution_prompt.tier,
            baseline_verification=baseline_verification,
            skill_verification=skill_verification,
            execution_verdict=verdict,
            verdict_reasoning=reasoning,
        )

    def evaluate(
        self,
        skill_content: str,
        skill_name: str,
        num_prompts: int = 8,
    ) -> Tuple[List[ExecutionComparisonResult], ExecutionScore]:
        """
        Run full execution evaluation for a skill.

        Args:
            skill_content: The SKILL.md content
            skill_name: Name of the skill
            num_prompts: Number of execution prompts to run

        Returns:
            Tuple of (list of comparison results, execution score)
        """
        category = get_skill_category(skill_name)

        # Get execution prompts for this skill
        execution_prompts = get_execution_prompts(skill_name, count=num_prompts)

        if not execution_prompts:
            # Advisory skill - no execution verification
            return [], self._empty_score(skill_name, category)

        comparisons: List[ExecutionComparisonResult] = []

        for i, exec_prompt in enumerate(execution_prompts):
            try:
                comparison = self.evaluate_prompt(
                    exec_prompt,
                    skill_content,
                    skill_name,
                )
                comparisons.append(comparison)
            except Exception as e:
                print(f"        [ERROR] Execution prompt {i+1}: {e}")
                # Continue with other prompts

        # Calculate execution score
        score = self._calculate_score(skill_name, category, comparisons)

        return comparisons, score

    def _empty_score(self, skill_name: str, category: SkillCategory) -> ExecutionScore:
        """Create an empty score for skills that don't require execution."""
        return ExecutionScore(
            skill_name=skill_name,
            category=category,
            prompts_tested=0,
            code_extracted_count=0,
            executions_attempted=0,
            executions_succeeded=0,
            outputs_valid=0,
            execution_wins=0,
            execution_losses=0,
            execution_ties=0,
            extraction_rate=0.0,
            execution_success_rate=0.0,
            validation_rate=0.0,
            execution_win_rate=None,
            execution_grade="F",
            scored_at=datetime.now(timezone.utc),
        )

    def _calculate_score(
        self,
        skill_name: str,
        category: SkillCategory,
        comparisons: List[ExecutionComparisonResult],
    ) -> ExecutionScore:
        """Calculate execution score from comparison results."""
        if not comparisons:
            return self._empty_score(skill_name, category)

        # Count metrics from skill verification results
        prompts_tested = len(comparisons)
        code_extracted = sum(1 for c in comparisons if c.skill_verification.code_extracted)
        executions_attempted = sum(1 for c in comparisons if c.skill_verification.executed)
        executions_succeeded = sum(1 for c in comparisons if c.skill_verification.execution_success)
        outputs_valid = sum(1 for c in comparisons if c.skill_verification.output_valid)

        # Count wins/losses/ties
        wins = sum(1 for c in comparisons if c.execution_verdict == Verdict.SKILL_WINS)
        losses = sum(1 for c in comparisons if c.execution_verdict == Verdict.BASELINE_WINS)
        ties = sum(1 for c in comparisons if c.execution_verdict == Verdict.TIE)

        # Calculate rates
        extraction_rate = (code_extracted / prompts_tested * 100) if prompts_tested > 0 else 0.0
        execution_success_rate = (executions_succeeded / executions_attempted * 100) if executions_attempted > 0 else 0.0
        validation_rate = (outputs_valid / executions_succeeded * 100) if executions_succeeded > 0 else 0.0

        # Calculate execution win rate (excluding ties)
        decisive = wins + losses
        execution_win_rate = (wins / decisive * 100) if decisive > 0 else None

        # Calculate grade
        execution_grade = self._calculate_grade(execution_win_rate)

        return ExecutionScore(
            skill_name=skill_name,
            category=category,
            prompts_tested=prompts_tested,
            code_extracted_count=code_extracted,
            executions_attempted=executions_attempted,
            executions_succeeded=executions_succeeded,
            outputs_valid=outputs_valid,
            execution_wins=wins,
            execution_losses=losses,
            execution_ties=ties,
            extraction_rate=round(extraction_rate, 2),
            execution_success_rate=round(execution_success_rate, 2),
            validation_rate=round(validation_rate, 2),
            execution_win_rate=round(execution_win_rate, 2) if execution_win_rate is not None else None,
            execution_grade=execution_grade,
            scored_at=datetime.now(timezone.utc),
        )

    def _calculate_grade(self, win_rate: Optional[float]) -> str:
        """Calculate letter grade from win rate."""
        if win_rate is None:
            return "F"

        if win_rate >= 80:
            return "A"
        elif win_rate >= 60:
            return "B"
        elif win_rate >= 40:
            return "C"
        elif win_rate >= 20:
            return "D"
        else:
            return "F"
