# Scorer
"""
Calculates final scores for skills based on comparison and security results.

This module:
1. Calculates win rate from A/B comparison results
2. Assigns letter grades based on win rate
3. Estimates cost per use based on token usage
4. Combines all metrics into a final SkillScore

Scoring Formula:
    Win Rate = Skill Wins / (Skill Wins + Baseline Wins)
    # Ties don't count against either side

Grading Scale:
    - A: 80%+
    - B: 60-79%
    - C: 40-59%
    - D: 20-39%
    - F: <20%
"""

from datetime import datetime, timezone
from typing import Optional, Tuple

from evaluator.models import (
    ComparisonResult,
    SecurityResult,
    SkillScore,
    Verdict,
)


# =============================================================================
# Exceptions
# =============================================================================

class ScorerError(Exception):
    """Base exception for scorer errors."""
    pass


# =============================================================================
# Constants - Haiku Pricing (as of 2024)
# =============================================================================

# $0.25 per 1M input tokens
HAIKU_INPUT_PRICE = 0.25 / 1_000_000

# $1.25 per 1M output tokens
HAIKU_OUTPUT_PRICE = 1.25 / 1_000_000


# =============================================================================
# Scorer Class
# =============================================================================

class Scorer:
    """
    Calculates scores for skills based on evaluation results.

    Takes comparison results from A/B evaluations and security results,
    then computes win rate, grade, cost, and combines into final score.
    """

    def calculate_win_rate(
        self, comparisons: list[ComparisonResult]
    ) -> Tuple[int, int, int, Optional[float]]:
        """
        Calculate win rate from comparison results.

        Win Rate = Skill Wins / (Skill Wins + Baseline Wins)
        Ties don't count against either side.

        Args:
            comparisons: List of A/B comparison results

        Returns:
            Tuple of (wins, losses, ties, win_rate_percentage)
            win_rate_percentage is None if all comparisons are ties

        Raises:
            ScorerError: If no comparisons provided
        """
        if not comparisons:
            raise ScorerError("No comparisons provided - cannot calculate win rate")

        wins = 0
        losses = 0
        ties = 0

        for comparison in comparisons:
            if comparison.verdict == Verdict.SKILL_WINS:
                wins += 1
            elif comparison.verdict == Verdict.BASELINE_WINS:
                losses += 1
            else:  # TIE
                ties += 1

        # Calculate win rate excluding ties
        decisive_comparisons = wins + losses

        if decisive_comparisons == 0:
            # All ties - no decisive comparisons
            return wins, losses, ties, None

        win_rate = (wins / decisive_comparisons) * 100

        # Round to 2 decimal places
        win_rate = round(win_rate, 2)

        return wins, losses, ties, win_rate

    def calculate_grade(self, win_rate: Optional[float]) -> str:
        """
        Assign letter grade based on win rate.

        Grading Scale:
            - A: 80%+
            - B: 60-79%
            - C: 40-59%
            - D: 20-39%
            - F: <20% or None (all ties)

        Args:
            win_rate: Win rate percentage (0-100), or None if all ties

        Returns:
            Letter grade (A, B, C, D, or F)
        """
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

    def calculate_cost(
        self, comparisons: list[ComparisonResult]
    ) -> Tuple[float, float]:
        """
        Calculate average tokens and cost per use.

        Uses skill_tokens from each comparison (which represents output tokens
        from the skill-enhanced response) to estimate cost.

        Args:
            comparisons: List of A/B comparison results

        Returns:
            Tuple of (avg_tokens_per_use, cost_per_use_usd)

        Raises:
            ScorerError: If no comparisons provided
        """
        if not comparisons:
            raise ScorerError("No comparisons provided - cannot calculate cost")

        total_skill_tokens = sum(c.skill_tokens for c in comparisons)
        avg_tokens = total_skill_tokens / len(comparisons)

        # Cost is based on output tokens at Haiku pricing
        cost_usd = avg_tokens * HAIKU_OUTPUT_PRICE

        return avg_tokens, cost_usd

    def score(
        self,
        skill_name: str,
        comparisons: list[ComparisonResult],
        security_result: SecurityResult,
    ) -> SkillScore:
        """
        Calculate complete score for a skill.

        Combines win rate, grade, security, and cost metrics into
        a final SkillScore object.

        Args:
            skill_name: Name of the skill being scored
            comparisons: List of A/B comparison results
            security_result: Security analysis result

        Returns:
            SkillScore with all metrics

        Raises:
            ScorerError: If no comparisons provided
        """
        if not comparisons:
            raise ScorerError("No comparisons provided - cannot score skill")

        # Calculate quality metrics
        wins, losses, ties, win_rate = self.calculate_win_rate(comparisons)
        grade = self.calculate_grade(win_rate)

        # Calculate cost metrics
        avg_tokens, cost_usd = self.calculate_cost(comparisons)

        # Build final score
        return SkillScore(
            skill_name=skill_name,
            wins=wins,
            losses=losses,
            ties=ties,
            win_rate=win_rate,
            grade=grade,
            security_grade=security_result.grade,
            security_issues_count=len(security_result.issues),
            avg_tokens_per_use=avg_tokens,
            cost_per_use_usd=cost_usd,
            total_comparisons=len(comparisons),
            scored_at=datetime.now(timezone.utc),
        )
