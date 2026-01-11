# Tests for Scorer Phase
"""
Unit tests for the Scorer module.
Tests written first using TDD approach.
"""

import pytest
from datetime import datetime, timezone


# =============================================================================
# Test: Models - SkillScore
# =============================================================================

class TestSkillScoreModel:
    """Test SkillScore model."""

    def test_create_with_all_fields(self):
        from evaluator.models import SkillScore, SecurityGrade

        score = SkillScore(
            skill_name="pdf-processor",
            wins=8,
            losses=2,
            ties=0,
            win_rate=80.0,
            grade="A",
            security_grade=SecurityGrade.SECURE,
            security_issues_count=0,
            avg_tokens_per_use=150.0,
            cost_per_use_usd=0.0001875,
            total_comparisons=10,
            scored_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        assert score.skill_name == "pdf-processor"
        assert score.wins == 8
        assert score.losses == 2
        assert score.ties == 0
        assert score.win_rate == 80.0
        assert score.grade == "A"
        assert score.security_grade == SecurityGrade.SECURE
        assert score.security_issues_count == 0
        assert score.avg_tokens_per_use == 150.0
        assert score.cost_per_use_usd == 0.0001875
        assert score.total_comparisons == 10

    def test_grade_must_be_valid_letter(self):
        from evaluator.models import SkillScore, SecurityGrade
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SkillScore(
                skill_name="test",
                wins=5,
                losses=5,
                ties=0,
                win_rate=50.0,
                grade="X",  # Invalid grade
                security_grade=SecurityGrade.SECURE,
                security_issues_count=0,
                avg_tokens_per_use=100.0,
                cost_per_use_usd=0.0001,
                total_comparisons=10,
                scored_at=datetime.now(timezone.utc),
            )

    def test_serialization_to_dict(self):
        from evaluator.models import SkillScore, SecurityGrade

        score = SkillScore(
            skill_name="test-skill",
            wins=6,
            losses=3,
            ties=1,
            win_rate=66.67,
            grade="B",
            security_grade=SecurityGrade.WARNING,
            security_issues_count=2,
            avg_tokens_per_use=200.0,
            cost_per_use_usd=0.00025,
            total_comparisons=10,
            scored_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )

        data = score.model_dump()
        assert data["skill_name"] == "test-skill"
        assert data["wins"] == 6
        assert data["losses"] == 3
        assert data["ties"] == 1
        assert data["win_rate"] == 66.67
        assert data["grade"] == "B"
        assert data["security_grade"] == "warning"
        assert data["security_issues_count"] == 2

    def test_serialization_to_json(self):
        from evaluator.models import SkillScore, SecurityGrade
        import json

        score = SkillScore(
            skill_name="test-skill",
            wins=4,
            losses=6,
            ties=0,
            win_rate=40.0,
            grade="C",
            security_grade=SecurityGrade.FAIL,
            security_issues_count=3,
            avg_tokens_per_use=100.0,
            cost_per_use_usd=0.000125,
            total_comparisons=10,
            scored_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )

        json_str = score.model_dump_json()
        data = json.loads(json_str)

        assert data["grade"] == "C"
        assert data["security_grade"] == "fail"

    def test_can_load_from_json(self):
        from evaluator.models import SkillScore, SecurityGrade

        json_data = {
            "skill_name": "loaded-skill",
            "wins": 7,
            "losses": 2,
            "ties": 1,
            "win_rate": 77.78,
            "grade": "B",
            "security_grade": "secure",
            "security_issues_count": 0,
            "avg_tokens_per_use": 180.0,
            "cost_per_use_usd": 0.000225,
            "total_comparisons": 10,
            "scored_at": "2024-06-01T00:00:00Z",
        }

        score = SkillScore.model_validate(json_data)

        assert score.skill_name == "loaded-skill"
        assert score.grade == "B"
        assert score.security_grade == SecurityGrade.SECURE


# =============================================================================
# Test: Scorer - Win Rate Calculation
# =============================================================================

class TestScorerWinRate:
    """Test Scorer.calculate_win_rate method."""

    def test_all_wins_gives_100_percent(self):
        from evaluator.scorer import Scorer
        from evaluator.models import ComparisonResult, Verdict
        from datetime import datetime, timezone

        comparisons = [
            ComparisonResult(
                prompt=f"Prompt {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.SKILL_WINS,
                reasoning="Skill is better",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            )
            for i in range(5)
        ]

        scorer = Scorer()
        wins, losses, ties, win_rate = scorer.calculate_win_rate(comparisons)

        assert wins == 5
        assert losses == 0
        assert ties == 0
        assert win_rate == 100.0

    def test_all_losses_gives_0_percent(self):
        from evaluator.scorer import Scorer
        from evaluator.models import ComparisonResult, Verdict
        from datetime import datetime, timezone

        comparisons = [
            ComparisonResult(
                prompt=f"Prompt {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.BASELINE_WINS,
                reasoning="Baseline is better",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            )
            for i in range(5)
        ]

        scorer = Scorer()
        wins, losses, ties, win_rate = scorer.calculate_win_rate(comparisons)

        assert wins == 0
        assert losses == 5
        assert ties == 0
        assert win_rate == 0.0

    def test_mixed_results(self):
        from evaluator.scorer import Scorer
        from evaluator.models import ComparisonResult, Verdict
        from datetime import datetime, timezone

        # 6 wins, 4 losses = 60% win rate
        comparisons = []
        for i in range(6):
            comparisons.append(ComparisonResult(
                prompt=f"Prompt {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.SKILL_WINS,
                reasoning="Skill wins",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ))
        for i in range(4):
            comparisons.append(ComparisonResult(
                prompt=f"Prompt loss {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.BASELINE_WINS,
                reasoning="Baseline wins",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ))

        scorer = Scorer()
        wins, losses, ties, win_rate = scorer.calculate_win_rate(comparisons)

        assert wins == 6
        assert losses == 4
        assert ties == 0
        assert win_rate == 60.0

    def test_ties_dont_count(self):
        from evaluator.scorer import Scorer
        from evaluator.models import ComparisonResult, Verdict
        from datetime import datetime, timezone

        # 4 wins, 2 losses, 4 ties = 4/(4+2) = 66.67% win rate
        comparisons = []
        for i in range(4):
            comparisons.append(ComparisonResult(
                prompt=f"Win {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.SKILL_WINS,
                reasoning="Skill wins",
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
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.BASELINE_WINS,
                reasoning="Baseline wins",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ))
        for i in range(4):
            comparisons.append(ComparisonResult(
                prompt=f"Tie {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.TIE,
                reasoning="Equal",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ))

        scorer = Scorer()
        wins, losses, ties, win_rate = scorer.calculate_win_rate(comparisons)

        assert wins == 4
        assert losses == 2
        assert ties == 4
        # 4 wins / (4 wins + 2 losses) = 4/6 = 66.67%
        assert abs(win_rate - 66.67) < 0.01

    def test_all_ties_returns_none_win_rate(self):
        from evaluator.scorer import Scorer
        from evaluator.models import ComparisonResult, Verdict
        from datetime import datetime, timezone

        comparisons = [
            ComparisonResult(
                prompt=f"Tie {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.TIE,
                reasoning="Equal",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            )
            for i in range(5)
        ]

        scorer = Scorer()
        wins, losses, ties, win_rate = scorer.calculate_win_rate(comparisons)

        assert wins == 0
        assert losses == 0
        assert ties == 5
        # No decisive comparisons - win_rate should be None
        assert win_rate is None

    def test_empty_comparisons_raises_error(self):
        from evaluator.scorer import Scorer, ScorerError

        scorer = Scorer()

        with pytest.raises(ScorerError):
            scorer.calculate_win_rate([])


# =============================================================================
# Test: Scorer - Grade Calculation
# =============================================================================

class TestScorerGrade:
    """Test Scorer.calculate_grade method."""

    def test_grade_a_at_80_percent(self):
        from evaluator.scorer import Scorer

        scorer = Scorer()
        assert scorer.calculate_grade(80.0) == "A"

    def test_grade_a_at_100_percent(self):
        from evaluator.scorer import Scorer

        scorer = Scorer()
        assert scorer.calculate_grade(100.0) == "A"

    def test_grade_b_at_60_percent(self):
        from evaluator.scorer import Scorer

        scorer = Scorer()
        assert scorer.calculate_grade(60.0) == "B"

    def test_grade_b_at_79_percent(self):
        from evaluator.scorer import Scorer

        scorer = Scorer()
        assert scorer.calculate_grade(79.0) == "B"
        assert scorer.calculate_grade(79.99) == "B"

    def test_grade_c_at_40_percent(self):
        from evaluator.scorer import Scorer

        scorer = Scorer()
        assert scorer.calculate_grade(40.0) == "C"

    def test_grade_c_at_59_percent(self):
        from evaluator.scorer import Scorer

        scorer = Scorer()
        assert scorer.calculate_grade(59.0) == "C"
        assert scorer.calculate_grade(59.99) == "C"

    def test_grade_d_at_20_percent(self):
        from evaluator.scorer import Scorer

        scorer = Scorer()
        assert scorer.calculate_grade(20.0) == "D"

    def test_grade_d_at_39_percent(self):
        from evaluator.scorer import Scorer

        scorer = Scorer()
        assert scorer.calculate_grade(39.0) == "D"
        assert scorer.calculate_grade(39.99) == "D"

    def test_grade_f_below_20_percent(self):
        from evaluator.scorer import Scorer

        scorer = Scorer()
        assert scorer.calculate_grade(19.99) == "F"
        assert scorer.calculate_grade(0.0) == "F"

    def test_grade_f_at_0_percent(self):
        from evaluator.scorer import Scorer

        scorer = Scorer()
        assert scorer.calculate_grade(0.0) == "F"

    def test_grade_none_win_rate_returns_f(self):
        from evaluator.scorer import Scorer

        scorer = Scorer()
        # None win rate (all ties) should return F
        assert scorer.calculate_grade(None) == "F"


# =============================================================================
# Test: Scorer - Cost Calculation
# =============================================================================

class TestScorerCost:
    """Test Scorer.calculate_cost method."""

    def test_cost_calculation_basic(self):
        from evaluator.scorer import Scorer
        from evaluator.models import ComparisonResult, Verdict
        from datetime import datetime, timezone

        # 5 comparisons with 100, 150, 200, 250, 300 skill tokens
        # Average = (100+150+200+250+300)/5 = 200 tokens
        comparisons = []
        for i, tokens in enumerate([100, 150, 200, 250, 300]):
            comparisons.append(ComparisonResult(
                prompt=f"Prompt {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.SKILL_WINS,
                reasoning="Skill wins",
                baseline_tokens=50,
                skill_tokens=tokens,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ))

        scorer = Scorer()
        avg_tokens, cost_usd = scorer.calculate_cost(comparisons)

        assert avg_tokens == 200.0
        # Cost = 200 * $1.25/1M = 200 * 0.00000125 = 0.00025
        assert abs(cost_usd - 0.00025) < 0.00001

    def test_cost_with_single_comparison(self):
        from evaluator.scorer import Scorer
        from evaluator.models import ComparisonResult, Verdict
        from datetime import datetime, timezone

        comparisons = [ComparisonResult(
            prompt="Test",
            baseline_response="Baseline",
            skill_response="Skill",
            verdict=Verdict.SKILL_WINS,
            reasoning="Win",
            baseline_tokens=50,
            skill_tokens=1000,  # 1000 output tokens
            position_a="skill",
            position_b="baseline",
            judge_model="claude-sonnet-4-20250514",
            judged_at=datetime.now(timezone.utc),
        )]

        scorer = Scorer()
        avg_tokens, cost_usd = scorer.calculate_cost(comparisons)

        assert avg_tokens == 1000.0
        # Cost = 1000 * $1.25/1M = 0.00125
        assert abs(cost_usd - 0.00125) < 0.00001

    def test_cost_empty_comparisons_raises_error(self):
        from evaluator.scorer import Scorer, ScorerError

        scorer = Scorer()

        with pytest.raises(ScorerError):
            scorer.calculate_cost([])


# =============================================================================
# Test: Scorer - Full Score Calculation
# =============================================================================

class TestScorerScore:
    """Test Scorer.score method (full scoring)."""

    def test_score_returns_skill_score(self):
        from evaluator.scorer import Scorer
        from evaluator.models import (
            ComparisonResult, Verdict, SecurityResult,
            SecurityGrade, SkillScore
        )
        from datetime import datetime, timezone

        # 8 wins, 2 losses = 80% = grade A
        comparisons = []
        for i in range(8):
            comparisons.append(ComparisonResult(
                prompt=f"Win {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.SKILL_WINS,
                reasoning="Win",
                baseline_tokens=100,
                skill_tokens=200,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ))
        for i in range(2):
            comparisons.append(ComparisonResult(
                prompt=f"Loss {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.BASELINE_WINS,
                reasoning="Loss",
                baseline_tokens=100,
                skill_tokens=200,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ))

        security_result = SecurityResult(
            skill_name="test-skill",
            grade=SecurityGrade.SECURE,
            issues=[],
            analysis="No issues found",
            analyzed_at=datetime.now(timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=500,
        )

        scorer = Scorer()
        result = scorer.score("test-skill", comparisons, security_result)

        assert isinstance(result, SkillScore)
        assert result.skill_name == "test-skill"
        assert result.wins == 8
        assert result.losses == 2
        assert result.ties == 0
        assert result.win_rate == 80.0
        assert result.grade == "A"
        assert result.security_grade == SecurityGrade.SECURE
        assert result.security_issues_count == 0
        assert result.total_comparisons == 10
        assert result.avg_tokens_per_use == 200.0

    def test_score_with_security_issues(self):
        from evaluator.scorer import Scorer
        from evaluator.models import (
            ComparisonResult, Verdict, SecurityResult,
            SecurityGrade, SecurityIssue, SkillScore
        )
        from datetime import datetime, timezone

        # 5 wins, 5 losses = 50% = grade C
        comparisons = []
        for i in range(5):
            comparisons.append(ComparisonResult(
                prompt=f"Win {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.SKILL_WINS,
                reasoning="Win",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ))
        for i in range(5):
            comparisons.append(ComparisonResult(
                prompt=f"Loss {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.BASELINE_WINS,
                reasoning="Loss",
                baseline_tokens=100,
                skill_tokens=150,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ))

        security_result = SecurityResult(
            skill_name="risky-skill",
            grade=SecurityGrade.WARNING,
            issues=[
                SecurityIssue(
                    category="file_system_abuse",
                    severity="medium",
                    description="Accesses sensitive paths",
                    evidence="/etc/passwd",
                ),
                SecurityIssue(
                    category="credential_theft",
                    severity="low",
                    description="Reads env vars",
                    evidence="process.env",
                ),
            ],
            analysis="Found some issues",
            analyzed_at=datetime.now(timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=600,
        )

        scorer = Scorer()
        result = scorer.score("risky-skill", comparisons, security_result)

        assert result.skill_name == "risky-skill"
        assert result.win_rate == 50.0
        assert result.grade == "C"
        assert result.security_grade == SecurityGrade.WARNING
        assert result.security_issues_count == 2

    def test_score_with_ties(self):
        from evaluator.scorer import Scorer
        from evaluator.models import (
            ComparisonResult, Verdict, SecurityResult,
            SecurityGrade, SkillScore
        )
        from datetime import datetime, timezone

        # 6 wins, 2 losses, 2 ties = 6/(6+2) = 75% = grade B
        comparisons = []
        for i in range(6):
            comparisons.append(ComparisonResult(
                prompt=f"Win {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.SKILL_WINS,
                reasoning="Win",
                baseline_tokens=100,
                skill_tokens=175,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ))
        for i in range(2):
            comparisons.append(ComparisonResult(
                prompt=f"Loss {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.BASELINE_WINS,
                reasoning="Loss",
                baseline_tokens=100,
                skill_tokens=175,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ))
        for i in range(2):
            comparisons.append(ComparisonResult(
                prompt=f"Tie {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.TIE,
                reasoning="Tie",
                baseline_tokens=100,
                skill_tokens=175,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            ))

        security_result = SecurityResult(
            skill_name="decent-skill",
            grade=SecurityGrade.SECURE,
            issues=[],
            analysis="Safe skill",
            analyzed_at=datetime.now(timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=400,
        )

        scorer = Scorer()
        result = scorer.score("decent-skill", comparisons, security_result)

        assert result.wins == 6
        assert result.losses == 2
        assert result.ties == 2
        assert result.win_rate == 75.0
        assert result.grade == "B"
        assert result.total_comparisons == 10

    def test_score_all_ties_gives_f_grade(self):
        from evaluator.scorer import Scorer
        from evaluator.models import (
            ComparisonResult, Verdict, SecurityResult,
            SecurityGrade, SkillScore
        )
        from datetime import datetime, timezone

        # All ties = no decisive comparisons
        comparisons = [
            ComparisonResult(
                prompt=f"Tie {i}",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict=Verdict.TIE,
                reasoning="Tie",
                baseline_tokens=100,
                skill_tokens=120,
                position_a="skill",
                position_b="baseline",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            )
            for i in range(5)
        ]

        security_result = SecurityResult(
            skill_name="tie-skill",
            grade=SecurityGrade.SECURE,
            issues=[],
            analysis="Safe",
            analyzed_at=datetime.now(timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=300,
        )

        scorer = Scorer()
        result = scorer.score("tie-skill", comparisons, security_result)

        assert result.wins == 0
        assert result.losses == 0
        assert result.ties == 5
        assert result.win_rate is None
        assert result.grade == "F"  # No decisive comparisons = F grade

    def test_score_records_timestamp(self):
        from evaluator.scorer import Scorer
        from evaluator.models import (
            ComparisonResult, Verdict, SecurityResult, SecurityGrade
        )
        from datetime import datetime, timezone

        comparisons = [ComparisonResult(
            prompt="Test",
            baseline_response="Baseline",
            skill_response="Skill",
            verdict=Verdict.SKILL_WINS,
            reasoning="Win",
            baseline_tokens=100,
            skill_tokens=150,
            position_a="skill",
            position_b="baseline",
            judge_model="claude-sonnet-4-20250514",
            judged_at=datetime.now(timezone.utc),
        )]

        security_result = SecurityResult(
            skill_name="test",
            grade=SecurityGrade.SECURE,
            issues=[],
            analysis="Safe",
            analyzed_at=datetime.now(timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=300,
        )

        scorer = Scorer()
        before = datetime.now(timezone.utc)
        result = scorer.score("test", comparisons, security_result)
        after = datetime.now(timezone.utc)

        assert result.scored_at >= before
        assert result.scored_at <= after

    def test_score_no_comparisons_raises_error(self):
        from evaluator.scorer import Scorer, ScorerError
        from evaluator.models import SecurityResult, SecurityGrade
        from datetime import datetime, timezone

        security_result = SecurityResult(
            skill_name="test",
            grade=SecurityGrade.SECURE,
            issues=[],
            analysis="Safe",
            analyzed_at=datetime.now(timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=300,
        )

        scorer = Scorer()

        with pytest.raises(ScorerError):
            scorer.score("test", [], security_result)


# =============================================================================
# Test: Cost Constants
# =============================================================================

class TestCostConstants:
    """Test that cost constants are correct."""

    def test_haiku_output_price(self):
        from evaluator.scorer import HAIKU_OUTPUT_PRICE

        # Should be $1.25 per 1M tokens
        expected = 1.25 / 1_000_000
        assert abs(HAIKU_OUTPUT_PRICE - expected) < 1e-12

    def test_haiku_input_price(self):
        from evaluator.scorer import HAIKU_INPUT_PRICE

        # Should be $0.25 per 1M tokens
        expected = 0.25 / 1_000_000
        assert abs(HAIKU_INPUT_PRICE - expected) < 1e-12
