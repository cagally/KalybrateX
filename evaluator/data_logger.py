# Data Logger
"""
Saves all evaluation evidence for transparency.

This module:
1. Saves SKILL.md content being tested
2. Saves generated prompts
3. Saves A/B comparison results
4. Saves security analysis results
5. Saves final scores
6. Saves aggregated summary

Directory structure:
    data/evaluations/{skill_name}/
    ├── skill.md                    # Copy of SKILL.md tested
    ├── prompts.json                # Generated prompts
    ├── comparisons/
    │   └── {n}.json                # Both responses, verdict, reasoning
    ├── security.json               # Security analysis
    ├── score.json                  # Final score
    └── summary.json                # Aggregated results
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from evaluator.models import (
    ComparisonResult,
    PromptGenerationResult,
    SecurityResult,
    SkillScore,
    Verdict,
)


# =============================================================================
# Constants
# =============================================================================

DEFAULT_BASE_DIR = Path("data/evaluations")


# =============================================================================
# DataLogger Class
# =============================================================================

class DataLogger:
    """
    Saves all evaluation evidence for transparency.

    Creates a structured directory for each skill with all evidence
    from the evaluation process: prompts, comparisons, security, scores.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize the DataLogger.

        Args:
            base_dir: Base directory for evaluations. Defaults to data/evaluations.
        """
        self.base_dir = base_dir if base_dir is not None else DEFAULT_BASE_DIR

    def _ensure_skill_dir(self, skill_name: str) -> Path:
        """
        Ensure the skill directory exists and return its path.

        Args:
            skill_name: Name of the skill

        Returns:
            Path to the skill's evaluation directory
        """
        skill_dir = self.base_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        return skill_dir

    def _ensure_comparisons_dir(self, skill_name: str) -> Path:
        """
        Ensure the comparisons directory exists and return its path.

        Args:
            skill_name: Name of the skill

        Returns:
            Path to the skill's comparisons directory
        """
        comparisons_dir = self._ensure_skill_dir(skill_name) / "comparisons"
        comparisons_dir.mkdir(parents=True, exist_ok=True)
        return comparisons_dir

    def save_skill_md(self, skill_name: str, content: str) -> None:
        """
        Save a copy of the SKILL.md content being tested.

        Args:
            skill_name: Name of the skill
            content: Content of the SKILL.md file
        """
        skill_dir = self._ensure_skill_dir(skill_name)
        skill_file = skill_dir / "skill.md"
        skill_file.write_text(content, encoding="utf-8")

    def save_prompts(self, skill_name: str, prompts: PromptGenerationResult) -> None:
        """
        Save generated prompts for a skill.

        Args:
            skill_name: Name of the skill
            prompts: PromptGenerationResult containing the generated prompts
        """
        skill_dir = self._ensure_skill_dir(skill_name)
        prompts_file = skill_dir / "prompts.json"
        prompts_file.write_text(
            prompts.model_dump_json(indent=2),
            encoding="utf-8"
        )

    def save_comparison(
        self, skill_name: str, index: int, result: ComparisonResult
    ) -> None:
        """
        Save an A/B comparison result.

        Args:
            skill_name: Name of the skill
            index: Index/number of the comparison (0-based)
            result: ComparisonResult with full comparison evidence
        """
        comparisons_dir = self._ensure_comparisons_dir(skill_name)
        comparison_file = comparisons_dir / f"{index}.json"
        comparison_file.write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8"
        )

    def save_security(self, skill_name: str, result: SecurityResult) -> None:
        """
        Save security analysis result.

        Args:
            skill_name: Name of the skill
            result: SecurityResult with full security analysis
        """
        skill_dir = self._ensure_skill_dir(skill_name)
        security_file = skill_dir / "security.json"
        security_file.write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8"
        )

    def save_score(self, skill_name: str, score: SkillScore) -> None:
        """
        Save final score for a skill.

        Args:
            skill_name: Name of the skill
            score: SkillScore with all metrics
        """
        skill_dir = self._ensure_skill_dir(skill_name)
        score_file = skill_dir / "score.json"
        score_file.write_text(
            score.model_dump_json(indent=2),
            encoding="utf-8"
        )

    def save_summary(
        self,
        skill_name: str,
        score: SkillScore,
        prompts: PromptGenerationResult,
        comparisons: List[ComparisonResult],
        security_result: SecurityResult,
    ) -> None:
        """
        Save aggregated summary of the evaluation.

        Args:
            skill_name: Name of the skill
            score: SkillScore with all metrics
            prompts: PromptGenerationResult with generated prompts
            comparisons: List of ComparisonResults
            security_result: SecurityResult with security analysis
        """
        skill_dir = self._ensure_skill_dir(skill_name)
        summary_file = skill_dir / "summary.json"

        # Calculate verdict breakdown
        verdict_breakdown = {
            "skill_wins": sum(1 for c in comparisons if c.verdict == Verdict.SKILL_WINS),
            "baseline_wins": sum(1 for c in comparisons if c.verdict == Verdict.BASELINE_WINS),
            "ties": sum(1 for c in comparisons if c.verdict == Verdict.TIE),
        }

        summary = {
            "skill_name": skill_name,
            "grade": score.grade,
            "win_rate": score.win_rate,
            "security_grade": score.security_grade.value,
            "security_issues_count": score.security_issues_count,
            "total_comparisons": score.total_comparisons,
            "prompt_count": len(prompts.prompts),
            "verdict_breakdown": verdict_breakdown,
            "avg_tokens_per_use": score.avg_tokens_per_use,
            "cost_per_use_usd": score.cost_per_use_usd,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "models_used": {
                "prompt_generation": prompts.model_used,
                "security_analysis": security_result.model_used,
            },
        }

        summary_file.write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8"
        )

    def clear_evaluation(self, skill_name: str) -> None:
        """
        Remove all evaluation data for a skill.

        Args:
            skill_name: Name of the skill to clear
        """
        skill_dir = self.base_dir / skill_name
        if skill_dir.exists():
            shutil.rmtree(skill_dir)

    def evaluation_exists(self, skill_name: str) -> bool:
        """
        Check if a complete evaluation exists for a skill.

        An evaluation is considered complete if score.json exists.

        Args:
            skill_name: Name of the skill

        Returns:
            True if evaluation exists, False otherwise
        """
        score_file = self.base_dir / skill_name / "score.json"
        return score_file.exists()

    def load_score(self, skill_name: str) -> Optional[SkillScore]:
        """
        Load a saved score for a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            SkillScore if exists, None otherwise
        """
        score_file = self.base_dir / skill_name / "score.json"
        if not score_file.exists():
            return None

        score_data = json.loads(score_file.read_text(encoding="utf-8"))
        return SkillScore.model_validate(score_data)
