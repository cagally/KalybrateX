# Tests for Data Logger Phase
"""
Unit tests for the DataLogger module.
Tests written first using TDD approach.
"""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import shutil


# =============================================================================
# Test: DataLogger Initialization
# =============================================================================

class TestDataLoggerInit:
    """Test DataLogger initialization."""

    def test_init_with_default_directory(self):
        from evaluator.data_logger import DataLogger

        logger = DataLogger()
        assert logger.base_dir == Path("data/evaluations")

    def test_init_with_custom_directory(self, tmp_path):
        from evaluator.data_logger import DataLogger

        custom_dir = tmp_path / "custom_evaluations"
        logger = DataLogger(base_dir=custom_dir)
        assert logger.base_dir == custom_dir

    def test_creates_base_directory_if_not_exists(self, tmp_path):
        from evaluator.data_logger import DataLogger

        custom_dir = tmp_path / "new_dir" / "evaluations"
        assert not custom_dir.exists()

        logger = DataLogger(base_dir=custom_dir)
        logger._ensure_skill_dir("test-skill")

        # Skill dir should be created
        assert (custom_dir / "test-skill").exists()


# =============================================================================
# Test: Save SKILL.md
# =============================================================================

class TestSaveSkillMd:
    """Test DataLogger.save_skill_md method."""

    def test_save_skill_md_creates_file(self, tmp_path):
        from evaluator.data_logger import DataLogger

        logger = DataLogger(base_dir=tmp_path)
        skill_content = "# PDF Skill\n\nThis skill creates PDFs."

        logger.save_skill_md("pdf", skill_content)

        skill_file = tmp_path / "pdf" / "skill.md"
        assert skill_file.exists()
        assert skill_file.read_text() == skill_content

    def test_save_skill_md_overwrites_existing(self, tmp_path):
        from evaluator.data_logger import DataLogger

        logger = DataLogger(base_dir=tmp_path)

        logger.save_skill_md("pdf", "Old content")
        logger.save_skill_md("pdf", "New content")

        skill_file = tmp_path / "pdf" / "skill.md"
        assert skill_file.read_text() == "New content"

    def test_save_skill_md_creates_skill_directory(self, tmp_path):
        from evaluator.data_logger import DataLogger

        logger = DataLogger(base_dir=tmp_path)

        logger.save_skill_md("new-skill", "Content")

        skill_dir = tmp_path / "new-skill"
        assert skill_dir.exists()
        assert skill_dir.is_dir()


# =============================================================================
# Test: Save Prompts
# =============================================================================

class TestSavePrompts:
    """Test DataLogger.save_prompts method."""

    def test_save_prompts_creates_json(self, tmp_path):
        from evaluator.data_logger import DataLogger
        from evaluator.models import GeneratedPrompt, PromptGenerationResult

        logger = DataLogger(base_dir=tmp_path)

        prompts_result = PromptGenerationResult(
            skill_name="pdf",
            prompts=[
                GeneratedPrompt(
                    prompt="Create a PDF from this text",
                    difficulty="simple",
                    capability_tested="pdf_creation"
                ),
                GeneratedPrompt(
                    prompt="Merge these 3 PDFs",
                    difficulty="medium",
                    capability_tested="pdf_merge"
                ),
            ],
            generated_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=500,
        )

        logger.save_prompts("pdf", prompts_result)

        prompts_file = tmp_path / "pdf" / "prompts.json"
        assert prompts_file.exists()

        data = json.loads(prompts_file.read_text())
        assert data["skill_name"] == "pdf"
        assert len(data["prompts"]) == 2
        assert data["prompts"][0]["prompt"] == "Create a PDF from this text"
        assert data["prompts"][0]["difficulty"] == "simple"
        assert data["model_used"] == "claude-sonnet-4-20250514"
        assert data["tokens_used"] == 500

    def test_save_prompts_preserves_timestamps(self, tmp_path):
        from evaluator.data_logger import DataLogger
        from evaluator.models import GeneratedPrompt, PromptGenerationResult

        logger = DataLogger(base_dir=tmp_path)

        prompts_result = PromptGenerationResult(
            skill_name="pdf",
            prompts=[
                GeneratedPrompt(
                    prompt="Test prompt",
                    difficulty="simple",
                    capability_tested="test"
                ),
            ],
            generated_at=datetime(2024, 6, 1, 12, 30, 45, tzinfo=timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=100,
        )

        logger.save_prompts("pdf", prompts_result)

        prompts_file = tmp_path / "pdf" / "prompts.json"
        data = json.loads(prompts_file.read_text())

        # Should preserve timestamp
        assert "2024-06-01" in data["generated_at"]


# =============================================================================
# Test: Save Comparison
# =============================================================================

class TestSaveComparison:
    """Test DataLogger.save_comparison method."""

    def test_save_comparison_creates_json(self, tmp_path):
        from evaluator.data_logger import DataLogger
        from evaluator.models import ComparisonResult, Verdict

        logger = DataLogger(base_dir=tmp_path)

        comparison = ComparisonResult(
            prompt="Create a simple PDF",
            baseline_response="I can help you create text content for a PDF.",
            skill_response="Here is a complete PDF creation script...",
            verdict=Verdict.SKILL_WINS,
            reasoning="The skill response provides actual PDF creation code.",
            baseline_tokens=100,
            skill_tokens=250,
            position_a="skill",
            position_b="baseline",
            judge_model="claude-sonnet-4-20250514",
            judged_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        logger.save_comparison("pdf", 0, comparison)

        comparison_file = tmp_path / "pdf" / "comparisons" / "0.json"
        assert comparison_file.exists()

        data = json.loads(comparison_file.read_text())
        assert data["prompt"] == "Create a simple PDF"
        assert data["verdict"] == "skill"
        assert data["reasoning"] == "The skill response provides actual PDF creation code."
        assert data["baseline_tokens"] == 100
        assert data["skill_tokens"] == 250

    def test_save_comparison_creates_comparisons_directory(self, tmp_path):
        from evaluator.data_logger import DataLogger
        from evaluator.models import ComparisonResult, Verdict

        logger = DataLogger(base_dir=tmp_path)

        comparison = ComparisonResult(
            prompt="Test",
            baseline_response="Baseline",
            skill_response="Skill",
            verdict=Verdict.SKILL_WINS,
            reasoning="Better",
            baseline_tokens=100,
            skill_tokens=150,
            position_a="skill",
            position_b="baseline",
            judge_model="claude-sonnet-4-20250514",
            judged_at=datetime.now(timezone.utc),
        )

        logger.save_comparison("pdf", 0, comparison)

        comparisons_dir = tmp_path / "pdf" / "comparisons"
        assert comparisons_dir.exists()
        assert comparisons_dir.is_dir()

    def test_save_multiple_comparisons(self, tmp_path):
        from evaluator.data_logger import DataLogger
        from evaluator.models import ComparisonResult, Verdict

        logger = DataLogger(base_dir=tmp_path)

        for i in range(3):
            comparison = ComparisonResult(
                prompt=f"Test prompt {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.SKILL_WINS if i % 2 == 0 else Verdict.BASELINE_WINS,
                reasoning=f"Reasoning {i}",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            )
            logger.save_comparison("pdf", i, comparison)

        comparisons_dir = tmp_path / "pdf" / "comparisons"
        assert (comparisons_dir / "0.json").exists()
        assert (comparisons_dir / "1.json").exists()
        assert (comparisons_dir / "2.json").exists()

    def test_save_comparison_preserves_full_responses(self, tmp_path):
        from evaluator.data_logger import DataLogger
        from evaluator.models import ComparisonResult, Verdict

        logger = DataLogger(base_dir=tmp_path)

        # Create a long response (should NOT be truncated)
        long_response = "This is a very long response. " * 500

        comparison = ComparisonResult(
            prompt="Test",
            baseline_response=long_response,
            skill_response=long_response,
            verdict=Verdict.TIE,
            reasoning="Equal",
            baseline_tokens=1000,
            skill_tokens=1000,
            position_a="baseline",
            position_b="skill",
            judge_model="claude-sonnet-4-20250514",
            judged_at=datetime.now(timezone.utc),
        )

        logger.save_comparison("pdf", 0, comparison)

        comparison_file = tmp_path / "pdf" / "comparisons" / "0.json"
        data = json.loads(comparison_file.read_text())

        # Full response should be preserved (not truncated)
        assert data["baseline_response"] == long_response
        assert data["skill_response"] == long_response


# =============================================================================
# Test: Save Security Result
# =============================================================================

class TestSaveSecurity:
    """Test DataLogger.save_security method."""

    def test_save_security_creates_json(self, tmp_path):
        from evaluator.data_logger import DataLogger
        from evaluator.models import SecurityResult, SecurityGrade, SecurityIssue

        logger = DataLogger(base_dir=tmp_path)

        security_result = SecurityResult(
            skill_name="pdf",
            grade=SecurityGrade.SECURE,
            issues=[],
            analysis="No security issues found.",
            analyzed_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=300,
        )

        logger.save_security("pdf", security_result)

        security_file = tmp_path / "pdf" / "security.json"
        assert security_file.exists()

        data = json.loads(security_file.read_text())
        assert data["skill_name"] == "pdf"
        assert data["grade"] == "secure"
        assert data["issues"] == []
        assert data["analysis"] == "No security issues found."

    def test_save_security_with_issues(self, tmp_path):
        from evaluator.data_logger import DataLogger
        from evaluator.models import SecurityResult, SecurityGrade, SecurityIssue

        logger = DataLogger(base_dir=tmp_path)

        security_result = SecurityResult(
            skill_name="risky-skill",
            grade=SecurityGrade.WARNING,
            issues=[
                SecurityIssue(
                    category="file_system_abuse",
                    severity="medium",
                    description="Accesses sensitive paths",
                    evidence="/etc/passwd"
                ),
                SecurityIssue(
                    category="credential_theft",
                    severity="low",
                    description="Reads env vars",
                    evidence="process.env.API_KEY"
                ),
            ],
            analysis="Found potential security concerns.",
            analyzed_at=datetime.now(timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=400,
        )

        logger.save_security("risky-skill", security_result)

        security_file = tmp_path / "risky-skill" / "security.json"
        data = json.loads(security_file.read_text())

        assert data["grade"] == "warning"
        assert len(data["issues"]) == 2
        assert data["issues"][0]["category"] == "file_system_abuse"
        assert data["issues"][0]["severity"] == "medium"


# =============================================================================
# Test: Save Score
# =============================================================================

class TestSaveScore:
    """Test DataLogger.save_score method."""

    def test_save_score_creates_json(self, tmp_path):
        from evaluator.data_logger import DataLogger
        from evaluator.models import SkillScore, SecurityGrade

        logger = DataLogger(base_dir=tmp_path)

        score = SkillScore(
            skill_name="pdf",
            wins=8,
            losses=2,
            ties=0,
            win_rate=80.0,
            grade="A",
            security_grade=SecurityGrade.SECURE,
            security_issues_count=0,
            avg_tokens_per_use=200.0,
            cost_per_use_usd=0.00025,
            total_comparisons=10,
            scored_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        logger.save_score("pdf", score)

        score_file = tmp_path / "pdf" / "score.json"
        assert score_file.exists()

        data = json.loads(score_file.read_text())
        assert data["skill_name"] == "pdf"
        assert data["wins"] == 8
        assert data["losses"] == 2
        assert data["ties"] == 0
        assert data["win_rate"] == 80.0
        assert data["grade"] == "A"
        assert data["security_grade"] == "secure"
        assert data["total_comparisons"] == 10

    def test_save_score_with_none_win_rate(self, tmp_path):
        from evaluator.data_logger import DataLogger
        from evaluator.models import SkillScore, SecurityGrade

        logger = DataLogger(base_dir=tmp_path)

        score = SkillScore(
            skill_name="tie-skill",
            wins=0,
            losses=0,
            ties=10,
            win_rate=None,  # All ties
            grade="F",
            security_grade=SecurityGrade.SECURE,
            security_issues_count=0,
            avg_tokens_per_use=100.0,
            cost_per_use_usd=0.000125,
            total_comparisons=10,
            scored_at=datetime.now(timezone.utc),
        )

        logger.save_score("tie-skill", score)

        score_file = tmp_path / "tie-skill" / "score.json"
        data = json.loads(score_file.read_text())

        assert data["win_rate"] is None
        assert data["grade"] == "F"


# =============================================================================
# Test: Save Summary
# =============================================================================

class TestSaveSummary:
    """Test DataLogger.save_summary method."""

    def test_save_summary_creates_json(self, tmp_path):
        from evaluator.data_logger import DataLogger
        from evaluator.models import (
            SkillScore, SecurityGrade, PromptGenerationResult,
            GeneratedPrompt, ComparisonResult, Verdict, SecurityResult
        )

        logger = DataLogger(base_dir=tmp_path)

        score = SkillScore(
            skill_name="pdf",
            wins=8,
            losses=2,
            ties=0,
            win_rate=80.0,
            grade="A",
            security_grade=SecurityGrade.SECURE,
            security_issues_count=0,
            avg_tokens_per_use=200.0,
            cost_per_use_usd=0.00025,
            total_comparisons=10,
            scored_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        prompts_result = PromptGenerationResult(
            skill_name="pdf",
            prompts=[
                GeneratedPrompt(prompt="Test", difficulty="simple", capability_tested="test")
            ],
            generated_at=datetime(2024, 6, 1, 11, 0, 0, tzinfo=timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=500,
        )

        comparisons = [
            ComparisonResult(
                prompt="Test",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.SKILL_WINS,
                reasoning="Better",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            )
        ]

        security_result = SecurityResult(
            skill_name="pdf",
            grade=SecurityGrade.SECURE,
            issues=[],
            analysis="Safe",
            analyzed_at=datetime.now(timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=300,
        )

        logger.save_summary(
            skill_name="pdf",
            score=score,
            prompts=prompts_result,
            comparisons=comparisons,
            security_result=security_result,
        )

        summary_file = tmp_path / "pdf" / "summary.json"
        assert summary_file.exists()

        data = json.loads(summary_file.read_text())

        # Should contain aggregated info
        assert data["skill_name"] == "pdf"
        assert data["grade"] == "A"
        assert data["win_rate"] == 80.0
        assert data["security_grade"] == "secure"
        assert data["total_comparisons"] == 10
        assert "evaluated_at" in data
        assert data["prompt_count"] == 1
        assert "verdict_breakdown" in data

    def test_save_summary_includes_verdict_breakdown(self, tmp_path):
        from evaluator.data_logger import DataLogger
        from evaluator.models import (
            SkillScore, SecurityGrade, PromptGenerationResult,
            GeneratedPrompt, ComparisonResult, Verdict, SecurityResult
        )

        logger = DataLogger(base_dir=tmp_path)

        score = SkillScore(
            skill_name="pdf",
            wins=6,
            losses=2,
            ties=2,
            win_rate=75.0,
            grade="B",
            security_grade=SecurityGrade.WARNING,
            security_issues_count=1,
            avg_tokens_per_use=150.0,
            cost_per_use_usd=0.00019,
            total_comparisons=10,
            scored_at=datetime.now(timezone.utc),
        )

        prompts_result = PromptGenerationResult(
            skill_name="pdf",
            prompts=[
                GeneratedPrompt(prompt=f"Test {i}", difficulty="simple", capability_tested="test")
                for i in range(10)
            ],
            generated_at=datetime.now(timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=500,
        )

        comparisons = []
        for i in range(6):
            comparisons.append(ComparisonResult(
                prompt=f"Win {i}",
                baseline_response="B",
                skill_response="S",
                verdict=Verdict.SKILL_WINS,
                reasoning="Win",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ))
        for i in range(2):
            comparisons.append(ComparisonResult(
                prompt=f"Loss {i}",
                baseline_response="B",
                skill_response="S",
                verdict=Verdict.BASELINE_WINS,
                reasoning="Loss",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ))
        for i in range(2):
            comparisons.append(ComparisonResult(
                prompt=f"Tie {i}",
                baseline_response="B",
                skill_response="S",
                verdict=Verdict.TIE,
                reasoning="Tie",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ))

        security_result = SecurityResult(
            skill_name="pdf",
            grade=SecurityGrade.WARNING,
            issues=[],
            analysis="Minor issues",
            analyzed_at=datetime.now(timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=300,
        )

        logger.save_summary(
            skill_name="pdf",
            score=score,
            prompts=prompts_result,
            comparisons=comparisons,
            security_result=security_result,
        )

        summary_file = tmp_path / "pdf" / "summary.json"
        data = json.loads(summary_file.read_text())

        assert data["verdict_breakdown"]["skill_wins"] == 6
        assert data["verdict_breakdown"]["baseline_wins"] == 2
        assert data["verdict_breakdown"]["ties"] == 2


# =============================================================================
# Test: Clear Evaluation
# =============================================================================

class TestClearEvaluation:
    """Test DataLogger.clear_evaluation method."""

    def test_clear_removes_skill_directory(self, tmp_path):
        from evaluator.data_logger import DataLogger

        logger = DataLogger(base_dir=tmp_path)

        # Create some files
        logger.save_skill_md("pdf", "Content")

        skill_dir = tmp_path / "pdf"
        assert skill_dir.exists()

        logger.clear_evaluation("pdf")

        assert not skill_dir.exists()

    def test_clear_nonexistent_skill_does_not_error(self, tmp_path):
        from evaluator.data_logger import DataLogger

        logger = DataLogger(base_dir=tmp_path)

        # Should not raise
        logger.clear_evaluation("nonexistent-skill")


# =============================================================================
# Test: Check Evaluation Exists
# =============================================================================

class TestCheckEvaluationExists:
    """Test DataLogger.evaluation_exists method."""

    def test_returns_true_when_score_exists(self, tmp_path):
        from evaluator.data_logger import DataLogger
        from evaluator.models import SkillScore, SecurityGrade

        logger = DataLogger(base_dir=tmp_path)

        score = SkillScore(
            skill_name="pdf",
            wins=8,
            losses=2,
            ties=0,
            win_rate=80.0,
            grade="A",
            security_grade=SecurityGrade.SECURE,
            security_issues_count=0,
            avg_tokens_per_use=200.0,
            cost_per_use_usd=0.00025,
            total_comparisons=10,
            scored_at=datetime.now(timezone.utc),
        )

        logger.save_score("pdf", score)

        assert logger.evaluation_exists("pdf") is True

    def test_returns_false_when_no_score(self, tmp_path):
        from evaluator.data_logger import DataLogger

        logger = DataLogger(base_dir=tmp_path)

        # Only save skill.md, not score
        logger.save_skill_md("pdf", "Content")

        assert logger.evaluation_exists("pdf") is False

    def test_returns_false_for_nonexistent_skill(self, tmp_path):
        from evaluator.data_logger import DataLogger

        logger = DataLogger(base_dir=tmp_path)

        assert logger.evaluation_exists("nonexistent") is False


# =============================================================================
# Test: Load Score
# =============================================================================

class TestLoadScore:
    """Test DataLogger.load_score method."""

    def test_load_saved_score(self, tmp_path):
        from evaluator.data_logger import DataLogger
        from evaluator.models import SkillScore, SecurityGrade

        logger = DataLogger(base_dir=tmp_path)

        original_score = SkillScore(
            skill_name="pdf",
            wins=8,
            losses=2,
            ties=0,
            win_rate=80.0,
            grade="A",
            security_grade=SecurityGrade.SECURE,
            security_issues_count=0,
            avg_tokens_per_use=200.0,
            cost_per_use_usd=0.00025,
            total_comparisons=10,
            scored_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        logger.save_score("pdf", original_score)
        loaded_score = logger.load_score("pdf")

        assert loaded_score.skill_name == original_score.skill_name
        assert loaded_score.wins == original_score.wins
        assert loaded_score.losses == original_score.losses
        assert loaded_score.grade == original_score.grade
        assert loaded_score.security_grade == original_score.security_grade

    def test_load_score_returns_none_for_nonexistent(self, tmp_path):
        from evaluator.data_logger import DataLogger

        logger = DataLogger(base_dir=tmp_path)

        score = logger.load_score("nonexistent")
        assert score is None


# =============================================================================
# Test: All Files Saved Together
# =============================================================================

class TestFullEvaluationSave:
    """Test saving a complete evaluation (all files)."""

    def test_full_evaluation_creates_all_files(self, tmp_path):
        from evaluator.data_logger import DataLogger
        from evaluator.models import (
            SkillScore, SecurityGrade, PromptGenerationResult,
            GeneratedPrompt, ComparisonResult, Verdict, SecurityResult
        )

        logger = DataLogger(base_dir=tmp_path)

        # Create all data
        skill_content = "# PDF Skill\nCreates PDFs"

        prompts_result = PromptGenerationResult(
            skill_name="pdf",
            prompts=[
                GeneratedPrompt(prompt="Test 1", difficulty="simple", capability_tested="test"),
                GeneratedPrompt(prompt="Test 2", difficulty="medium", capability_tested="test"),
            ],
            generated_at=datetime.now(timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=500,
        )

        comparisons = [
            ComparisonResult(
                prompt="Test 1",
                baseline_response="Baseline 1",
                skill_response="Skill 1",
                verdict=Verdict.SKILL_WINS,
                reasoning="Better 1",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ),
            ComparisonResult(
                prompt="Test 2",
                baseline_response="Baseline 2",
                skill_response="Skill 2",
                verdict=Verdict.BASELINE_WINS,
                reasoning="Better 2",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="baseline",
                position_b="skill",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ),
        ]

        security_result = SecurityResult(
            skill_name="pdf",
            grade=SecurityGrade.SECURE,
            issues=[],
            analysis="Safe skill",
            analyzed_at=datetime.now(timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=300,
        )

        score = SkillScore(
            skill_name="pdf",
            wins=1,
            losses=1,
            ties=0,
            win_rate=50.0,
            grade="C",
            security_grade=SecurityGrade.SECURE,
            security_issues_count=0,
            avg_tokens_per_use=150.0,
            cost_per_use_usd=0.00019,
            total_comparisons=2,
            scored_at=datetime.now(timezone.utc),
        )

        # Save everything
        logger.save_skill_md("pdf", skill_content)
        logger.save_prompts("pdf", prompts_result)
        for i, comp in enumerate(comparisons):
            logger.save_comparison("pdf", i, comp)
        logger.save_security("pdf", security_result)
        logger.save_score("pdf", score)
        logger.save_summary("pdf", score, prompts_result, comparisons, security_result)

        # Verify all files exist
        skill_dir = tmp_path / "pdf"
        assert (skill_dir / "skill.md").exists()
        assert (skill_dir / "prompts.json").exists()
        assert (skill_dir / "comparisons" / "0.json").exists()
        assert (skill_dir / "comparisons" / "1.json").exists()
        assert (skill_dir / "security.json").exists()
        assert (skill_dir / "score.json").exists()
        assert (skill_dir / "summary.json").exists()
