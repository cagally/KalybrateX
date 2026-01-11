# Tests for Quality Evaluator Phase
"""
Unit tests for the Quality Evaluator module.
Tests written first using TDD approach.
"""

import pytest
from datetime import datetime, timezone
import json
from unittest.mock import Mock, patch, MagicMock


# =============================================================================
# Test: Models - Verdict Enum
# =============================================================================

class TestVerdictEnum:
    """Test Verdict enum."""

    def test_verdict_values(self):
        from evaluator.models import Verdict

        assert Verdict.SKILL_WINS == "skill"
        assert Verdict.BASELINE_WINS == "baseline"
        assert Verdict.TIE == "tie"

    def test_verdict_is_string_enum(self):
        from evaluator.models import Verdict

        # Should be usable as string via .value
        assert Verdict.SKILL_WINS.value == "skill"
        assert Verdict.BASELINE_WINS.value == "baseline"
        # Also accessible via comparison since it's a str subclass
        assert Verdict.SKILL_WINS == "skill"
        assert Verdict.BASELINE_WINS == "baseline"

    def test_verdict_from_string(self):
        from evaluator.models import Verdict

        assert Verdict("skill") == Verdict.SKILL_WINS
        assert Verdict("baseline") == Verdict.BASELINE_WINS
        assert Verdict("tie") == Verdict.TIE

    def test_invalid_verdict_raises_error(self):
        from evaluator.models import Verdict

        with pytest.raises(ValueError):
            Verdict("invalid")


# =============================================================================
# Test: Models - ComparisonResult
# =============================================================================

class TestComparisonResult:
    """Test ComparisonResult model."""

    def test_create_with_all_fields(self):
        from evaluator.models import ComparisonResult, Verdict

        result = ComparisonResult(
            prompt="Help me process this PDF",
            baseline_response="Here's a generic approach...",
            skill_response="Using PDF processing capabilities...",
            verdict=Verdict.SKILL_WINS,
            reasoning="The skill response provides more specific PDF handling instructions.",
            baseline_tokens=150,
            skill_tokens=200,
            position_a="baseline",
            position_b="skill",
            judge_model="claude-sonnet-4-20250514",
            judged_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        assert result.prompt == "Help me process this PDF"
        assert result.verdict == Verdict.SKILL_WINS
        assert result.baseline_tokens == 150
        assert result.skill_tokens == 200
        assert result.position_a == "baseline"
        assert result.position_b == "skill"

    def test_verdict_can_be_string(self):
        from evaluator.models import ComparisonResult, Verdict

        # Should accept string that maps to enum value
        result = ComparisonResult(
            prompt="Test prompt",
            baseline_response="Baseline",
            skill_response="Skill",
            verdict="skill",  # String instead of enum
            reasoning="Test reasoning",
            baseline_tokens=100,
            skill_tokens=100,
            position_a="skill",
            position_b="baseline",
            judge_model="claude-sonnet-4-20250514",
            judged_at=datetime.now(timezone.utc),
        )

        assert result.verdict == Verdict.SKILL_WINS

    def test_position_must_be_baseline_or_skill(self):
        from evaluator.models import ComparisonResult
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ComparisonResult(
                prompt="Test prompt",
                baseline_response="Baseline",
                skill_response="Skill",
                verdict="skill",
                reasoning="Test reasoning",
                baseline_tokens=100,
                skill_tokens=100,
                position_a="invalid",  # Invalid position
                position_b="skill",
                judge_model="claude-sonnet-4-20250514",
                judged_at=datetime.now(timezone.utc),
            )

    def test_serialization_to_dict(self):
        from evaluator.models import ComparisonResult, Verdict

        result = ComparisonResult(
            prompt="Test prompt",
            baseline_response="Baseline response",
            skill_response="Skill response",
            verdict=Verdict.TIE,
            reasoning="Both responses are equally good.",
            baseline_tokens=100,
            skill_tokens=120,
            position_a="skill",
            position_b="baseline",
            judge_model="claude-sonnet-4-20250514",
            judged_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )

        data = result.model_dump()
        assert data["prompt"] == "Test prompt"
        assert data["verdict"] == "tie"
        assert data["baseline_tokens"] == 100
        assert data["skill_tokens"] == 120

    def test_serialization_to_json(self):
        from evaluator.models import ComparisonResult, Verdict

        result = ComparisonResult(
            prompt="Test prompt",
            baseline_response="Baseline response",
            skill_response="Skill response",
            verdict=Verdict.BASELINE_WINS,
            reasoning="Baseline was better.",
            baseline_tokens=200,
            skill_tokens=150,
            position_a="baseline",
            position_b="skill",
            judge_model="claude-sonnet-4-20250514",
            judged_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        )

        json_str = result.model_dump_json()
        data = json.loads(json_str)

        assert data["verdict"] == "baseline"
        assert data["reasoning"] == "Baseline was better."

    def test_can_load_from_json(self):
        from evaluator.models import ComparisonResult, Verdict

        json_data = {
            "prompt": "Test prompt",
            "baseline_response": "Baseline",
            "skill_response": "Skill",
            "verdict": "skill",
            "reasoning": "Skill was better",
            "baseline_tokens": 100,
            "skill_tokens": 150,
            "position_a": "skill",
            "position_b": "baseline",
            "judge_model": "claude-sonnet-4-20250514",
            "judged_at": "2024-06-01T00:00:00Z",
        }

        result = ComparisonResult.model_validate(json_data)

        assert result.verdict == Verdict.SKILL_WINS
        assert result.position_a == "skill"


# =============================================================================
# Test: QualityEvaluator Initialization
# =============================================================================

class TestQualityEvaluatorInit:
    """Test QualityEvaluator initialization."""

    def test_init_with_api_key(self):
        from evaluator.quality_evaluator import QualityEvaluator

        evaluator = QualityEvaluator(api_key="sk-ant-test-key")
        assert evaluator.api_key == "sk-ant-test-key"

    def test_init_loads_from_env(self, monkeypatch):
        from evaluator.quality_evaluator import QualityEvaluator

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-key")

        evaluator = QualityEvaluator()
        assert evaluator.api_key == "sk-ant-env-key"

    def test_init_without_api_key_raises_error(self, monkeypatch):
        from evaluator.quality_evaluator import QualityEvaluator, ConfigurationError

        # Clear any existing env var
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ConfigurationError):
            QualityEvaluator()

    def test_default_models(self):
        from evaluator.quality_evaluator import QualityEvaluator

        evaluator = QualityEvaluator(api_key="sk-ant-test-key")

        # Should use Haiku for execution, Sonnet for judging
        assert "haiku" in evaluator.execution_model.lower()
        assert "sonnet" in evaluator.judge_model.lower()


# =============================================================================
# Test: QualityEvaluator.run_baseline
# =============================================================================

class TestQualityEvaluatorRunBaseline:
    """Test QualityEvaluator.run_baseline method."""

    def test_run_baseline_returns_response_and_tokens(self):
        from evaluator.quality_evaluator import QualityEvaluator

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is a baseline response without skill.")]
        mock_response.usage = MagicMock(input_tokens=50, output_tokens=100)

        with patch("evaluator.quality_evaluator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            evaluator = QualityEvaluator(api_key="sk-ant-test-key")
            response, tokens = evaluator.run_baseline("Help me with a task")

            assert response == "This is a baseline response without skill."
            assert tokens == 150  # input + output

    def test_run_baseline_uses_haiku_model(self):
        from evaluator.quality_evaluator import QualityEvaluator

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_response.usage = MagicMock(input_tokens=50, output_tokens=50)

        with patch("evaluator.quality_evaluator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            evaluator = QualityEvaluator(api_key="sk-ant-test-key")
            evaluator.run_baseline("Test prompt")

            # Verify Haiku model was used
            call_kwargs = mock_client.messages.create.call_args[1]
            assert "haiku" in call_kwargs["model"].lower()

    def test_run_baseline_no_system_prompt(self):
        from evaluator.quality_evaluator import QualityEvaluator

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_response.usage = MagicMock(input_tokens=50, output_tokens=50)

        with patch("evaluator.quality_evaluator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            evaluator = QualityEvaluator(api_key="sk-ant-test-key")
            evaluator.run_baseline("Test prompt")

            # Verify no system prompt was used (or minimal default)
            call_kwargs = mock_client.messages.create.call_args[1]
            # Either no system param or system is empty/None
            system_value = call_kwargs.get("system", None)
            assert system_value is None or system_value == ""


# =============================================================================
# Test: QualityEvaluator.run_with_skill
# =============================================================================

class TestQualityEvaluatorRunWithSkill:
    """Test QualityEvaluator.run_with_skill method."""

    def test_run_with_skill_returns_response_and_tokens(self):
        from evaluator.quality_evaluator import QualityEvaluator

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is an enhanced response with skill capabilities.")]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=150)

        with patch("evaluator.quality_evaluator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            evaluator = QualityEvaluator(api_key="sk-ant-test-key")
            response, tokens = evaluator.run_with_skill(
                "Help me with a task",
                "# PDF Skill\n\nThis skill helps with PDF processing."
            )

            assert response == "This is an enhanced response with skill capabilities."
            assert tokens == 250  # input + output

    def test_run_with_skill_uses_haiku_model(self):
        from evaluator.quality_evaluator import QualityEvaluator

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_response.usage = MagicMock(input_tokens=50, output_tokens=50)

        with patch("evaluator.quality_evaluator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            evaluator = QualityEvaluator(api_key="sk-ant-test-key")
            evaluator.run_with_skill("Test prompt", "# Skill content")

            # Verify Haiku model was used
            call_kwargs = mock_client.messages.create.call_args[1]
            assert "haiku" in call_kwargs["model"].lower()

    def test_run_with_skill_includes_skill_in_system_prompt(self):
        from evaluator.quality_evaluator import QualityEvaluator

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_response.usage = MagicMock(input_tokens=50, output_tokens=50)

        with patch("evaluator.quality_evaluator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            skill_content = "# PDF Skill\n\nThis skill processes PDFs."

            evaluator = QualityEvaluator(api_key="sk-ant-test-key")
            evaluator.run_with_skill("Test prompt", skill_content)

            # Verify skill content is in system prompt
            call_kwargs = mock_client.messages.create.call_args[1]
            assert "system" in call_kwargs
            assert "PDF Skill" in call_kwargs["system"]


# =============================================================================
# Test: QualityEvaluator.judge_comparison
# =============================================================================

class TestQualityEvaluatorJudgeComparison:
    """Test QualityEvaluator.judge_comparison method."""

    def test_judge_comparison_returns_verdict_and_reasoning(self):
        from evaluator.quality_evaluator import QualityEvaluator
        from evaluator.models import Verdict

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''{"verdict": "A", "reasoning": "Response A provides more comprehensive and helpful guidance."}''')]
        mock_response.usage = MagicMock(input_tokens=200, output_tokens=50)

        with patch("evaluator.quality_evaluator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            evaluator = QualityEvaluator(api_key="sk-ant-test-key")
            verdict, reasoning = evaluator.judge_comparison(
                prompt="Help me with PDFs",
                response_a="Response A content",
                response_b="Response B content",
                position_a="skill",  # A is skill
            )

            # Since A wins and A is skill, verdict should be SKILL_WINS
            assert verdict == Verdict.SKILL_WINS
            assert "comprehensive" in reasoning.lower() or len(reasoning) > 0

    def test_judge_comparison_uses_sonnet_model(self):
        from evaluator.quality_evaluator import QualityEvaluator

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"verdict": "A", "reasoning": "Better"}')]
        mock_response.usage = MagicMock(input_tokens=200, output_tokens=50)

        with patch("evaluator.quality_evaluator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            evaluator = QualityEvaluator(api_key="sk-ant-test-key")
            evaluator.judge_comparison(
                prompt="Test",
                response_a="A",
                response_b="B",
                position_a="skill",
            )

            # Verify Sonnet model was used for judging
            call_kwargs = mock_client.messages.create.call_args[1]
            assert "sonnet" in call_kwargs["model"].lower()

    def test_judge_comparison_includes_claude_code_context(self):
        from evaluator.quality_evaluator import QualityEvaluator

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"verdict": "B", "reasoning": "B is better"}')]
        mock_response.usage = MagicMock(input_tokens=200, output_tokens=50)

        with patch("evaluator.quality_evaluator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            evaluator = QualityEvaluator(api_key="sk-ant-test-key")
            evaluator.judge_comparison(
                prompt="Test",
                response_a="A",
                response_b="B",
                position_a="baseline",
            )

            # Verify Claude Code context is in the prompt
            call_kwargs = mock_client.messages.create.call_args[1]
            # Check system prompt or messages contain the critical context
            system_content = call_kwargs.get("system", "")
            messages_content = str(call_kwargs.get("messages", []))
            combined = system_content + messages_content

            assert "Claude Code" in combined
            assert "Hooks" in combined or "hooks" in combined
            assert "SKILL.md" in combined

    def test_judge_comparison_handles_tie(self):
        from evaluator.quality_evaluator import QualityEvaluator
        from evaluator.models import Verdict

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"verdict": "TIE", "reasoning": "Both responses are equally good."}')]
        mock_response.usage = MagicMock(input_tokens=200, output_tokens=50)

        with patch("evaluator.quality_evaluator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            evaluator = QualityEvaluator(api_key="sk-ant-test-key")
            verdict, reasoning = evaluator.judge_comparison(
                prompt="Test",
                response_a="A",
                response_b="B",
                position_a="skill",
            )

            assert verdict == Verdict.TIE

    def test_judge_comparison_maps_b_wins_correctly(self):
        from evaluator.quality_evaluator import QualityEvaluator
        from evaluator.models import Verdict

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"verdict": "B", "reasoning": "B is better"}')]
        mock_response.usage = MagicMock(input_tokens=200, output_tokens=50)

        with patch("evaluator.quality_evaluator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            evaluator = QualityEvaluator(api_key="sk-ant-test-key")

            # If position_a is skill and B wins, then baseline wins
            verdict, _ = evaluator.judge_comparison(
                prompt="Test",
                response_a="A",
                response_b="B",
                position_a="skill",  # A is skill, so B is baseline
            )

            assert verdict == Verdict.BASELINE_WINS

            # If position_a is baseline and B wins, then skill wins
            verdict, _ = evaluator.judge_comparison(
                prompt="Test",
                response_a="A",
                response_b="B",
                position_a="baseline",  # A is baseline, so B is skill
            )

            assert verdict == Verdict.SKILL_WINS


# =============================================================================
# Test: QualityEvaluator.evaluate (Full A/B Comparison)
# =============================================================================

class TestQualityEvaluatorEvaluate:
    """Test QualityEvaluator.evaluate method (full A/B comparison flow)."""

    def test_evaluate_returns_comparison_result(self):
        from evaluator.quality_evaluator import QualityEvaluator
        from evaluator.models import ComparisonResult, Verdict

        # Mock responses for baseline, skill, and judge calls
        baseline_response = MagicMock()
        baseline_response.content = [MagicMock(text="Baseline response")]
        baseline_response.usage = MagicMock(input_tokens=50, output_tokens=100)

        skill_response = MagicMock()
        skill_response.content = [MagicMock(text="Skill response")]
        skill_response.usage = MagicMock(input_tokens=100, output_tokens=150)

        judge_response = MagicMock()
        judge_response.content = [MagicMock(text='{"verdict": "A", "reasoning": "A is better"}')]
        judge_response.usage = MagicMock(input_tokens=200, output_tokens=50)

        with patch("evaluator.quality_evaluator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            # Return different responses for each call
            mock_client.messages.create.side_effect = [
                baseline_response,
                skill_response,
                judge_response,
            ]
            mock_anthropic.return_value = mock_client

            # Patch random to get deterministic position
            with patch("evaluator.quality_evaluator.random.choice", return_value="skill"):
                evaluator = QualityEvaluator(api_key="sk-ant-test-key")
                result = evaluator.evaluate(
                    prompt="Help me with PDFs",
                    skill_content="# PDF Skill",
                )

                assert isinstance(result, ComparisonResult)
                assert result.prompt == "Help me with PDFs"
                assert result.baseline_response == "Baseline response"
                assert result.skill_response == "Skill response"
                assert result.baseline_tokens == 150
                assert result.skill_tokens == 250

    def test_evaluate_randomizes_position(self):
        from evaluator.quality_evaluator import QualityEvaluator

        # Track the positions used
        positions_used = []

        # Mock responses
        baseline_response = MagicMock()
        baseline_response.content = [MagicMock(text="Baseline")]
        baseline_response.usage = MagicMock(input_tokens=50, output_tokens=50)

        skill_response = MagicMock()
        skill_response.content = [MagicMock(text="Skill")]
        skill_response.usage = MagicMock(input_tokens=50, output_tokens=50)

        judge_response = MagicMock()
        judge_response.content = [MagicMock(text='{"verdict": "A", "reasoning": "A"}')]
        judge_response.usage = MagicMock(input_tokens=50, output_tokens=50)

        with patch("evaluator.quality_evaluator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [
                baseline_response, skill_response, judge_response,
                baseline_response, skill_response, judge_response,
            ]
            mock_anthropic.return_value = mock_client

            evaluator = QualityEvaluator(api_key="sk-ant-test-key")

            # Test with skill in position A
            with patch("evaluator.quality_evaluator.random.choice", return_value="skill"):
                result = evaluator.evaluate("Prompt", "# Skill")
                assert result.position_a == "skill"
                assert result.position_b == "baseline"

            # Test with baseline in position A
            mock_client.messages.create.side_effect = [
                baseline_response, skill_response, judge_response,
            ]
            with patch("evaluator.quality_evaluator.random.choice", return_value="baseline"):
                result = evaluator.evaluate("Prompt", "# Skill")
                assert result.position_a == "baseline"
                assert result.position_b == "skill"

    def test_evaluate_records_judge_model(self):
        from evaluator.quality_evaluator import QualityEvaluator

        baseline_response = MagicMock()
        baseline_response.content = [MagicMock(text="Baseline")]
        baseline_response.usage = MagicMock(input_tokens=50, output_tokens=50)

        skill_response = MagicMock()
        skill_response.content = [MagicMock(text="Skill")]
        skill_response.usage = MagicMock(input_tokens=50, output_tokens=50)

        judge_response = MagicMock()
        judge_response.content = [MagicMock(text='{"verdict": "A", "reasoning": "A"}')]
        judge_response.usage = MagicMock(input_tokens=50, output_tokens=50)

        with patch("evaluator.quality_evaluator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [
                baseline_response, skill_response, judge_response,
            ]
            mock_anthropic.return_value = mock_client

            with patch("evaluator.quality_evaluator.random.choice", return_value="skill"):
                evaluator = QualityEvaluator(api_key="sk-ant-test-key")
                result = evaluator.evaluate("Prompt", "# Skill")

                assert "sonnet" in result.judge_model.lower()

    def test_evaluate_records_timestamp(self):
        from evaluator.quality_evaluator import QualityEvaluator
        from datetime import datetime, timezone

        baseline_response = MagicMock()
        baseline_response.content = [MagicMock(text="Baseline")]
        baseline_response.usage = MagicMock(input_tokens=50, output_tokens=50)

        skill_response = MagicMock()
        skill_response.content = [MagicMock(text="Skill")]
        skill_response.usage = MagicMock(input_tokens=50, output_tokens=50)

        judge_response = MagicMock()
        judge_response.content = [MagicMock(text='{"verdict": "A", "reasoning": "A"}')]
        judge_response.usage = MagicMock(input_tokens=50, output_tokens=50)

        with patch("evaluator.quality_evaluator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = [
                baseline_response, skill_response, judge_response,
            ]
            mock_anthropic.return_value = mock_client

            with patch("evaluator.quality_evaluator.random.choice", return_value="skill"):
                evaluator = QualityEvaluator(api_key="sk-ant-test-key")
                before = datetime.now(timezone.utc)
                result = evaluator.evaluate("Prompt", "# Skill")
                after = datetime.now(timezone.utc)

                assert result.judged_at >= before
                assert result.judged_at <= after


# =============================================================================
# Test: Judge Response Parsing
# =============================================================================

class TestJudgeResponseParsing:
    """Test parsing of judge responses."""

    def test_parse_json_response(self):
        from evaluator.quality_evaluator import parse_judge_response

        response = '{"verdict": "A", "reasoning": "Response A is more helpful."}'
        verdict, reasoning = parse_judge_response(response)

        assert verdict == "A"
        assert reasoning == "Response A is more helpful."

    def test_parse_json_with_markdown_code_block(self):
        from evaluator.quality_evaluator import parse_judge_response

        response = '''```json
{"verdict": "B", "reasoning": "B provides better guidance."}
```'''
        verdict, reasoning = parse_judge_response(response)

        assert verdict == "B"
        assert reasoning == "B provides better guidance."

    def test_parse_tie_verdict(self):
        from evaluator.quality_evaluator import parse_judge_response

        response = '{"verdict": "TIE", "reasoning": "Both are equally good."}'
        verdict, reasoning = parse_judge_response(response)

        assert verdict == "TIE"

    def test_parse_invalid_json_raises_error(self):
        from evaluator.quality_evaluator import parse_judge_response, JudgeParseError

        with pytest.raises(JudgeParseError):
            parse_judge_response("Not valid JSON at all")

    def test_parse_missing_verdict_raises_error(self):
        from evaluator.quality_evaluator import parse_judge_response, JudgeParseError

        response = '{"reasoning": "Some reasoning but no verdict"}'

        with pytest.raises(JudgeParseError):
            parse_judge_response(response)


# =============================================================================
# Test: Claude Code Context
# =============================================================================

class TestClaudeCodeContext:
    """Test that Claude Code context is properly included."""

    def test_get_claude_code_context(self):
        from evaluator.quality_evaluator import get_claude_code_context

        context = get_claude_code_context()

        # Must include all key elements from docs/04-learnings.md
        assert "Claude Code" in context
        assert "Hooks" in context
        assert "PreToolUse" in context or "PostToolUse" in context
        assert "slash commands" in context.lower() or "custom slash commands" in context
        assert "SKILL.md" in context
        assert "not fictional" in context.lower() or "REAL" in context

    def test_build_judge_prompt_includes_context(self):
        from evaluator.quality_evaluator import build_judge_prompt

        prompt = build_judge_prompt(
            user_prompt="Help me with PDFs",
            response_a="Response A",
            response_b="Response B",
        )

        # Context must be included
        assert "Claude Code" in prompt
        assert "Hooks" in prompt
        assert "SKILL.md" in prompt
