# Tests for Prompt Generator Phase
"""
Unit tests for the Prompt Generator module.
Tests written first using TDD approach.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
import json
from unittest.mock import Mock, patch, MagicMock


# =============================================================================
# Test: Models
# =============================================================================

class TestGeneratedPrompt:
    """Test GeneratedPrompt model."""

    def test_create_with_all_fields(self):
        from evaluator.models import GeneratedPrompt

        prompt = GeneratedPrompt(
            prompt="Help me merge these two PDF documents into one",
            difficulty="simple",
            capability_tested="pdf_merge",
        )

        assert prompt.prompt == "Help me merge these two PDF documents into one"
        assert prompt.difficulty == "simple"
        assert prompt.capability_tested == "pdf_merge"

    def test_difficulty_must_be_valid(self):
        from evaluator.models import GeneratedPrompt
        from pydantic import ValidationError

        # Valid difficulties
        for difficulty in ["simple", "medium", "complex"]:
            prompt = GeneratedPrompt(
                prompt="Test prompt",
                difficulty=difficulty,
                capability_tested="test",
            )
            assert prompt.difficulty == difficulty

        # Invalid difficulty should raise error
        with pytest.raises(ValidationError):
            GeneratedPrompt(
                prompt="Test prompt",
                difficulty="invalid",
                capability_tested="test",
            )

    def test_prompt_cannot_be_empty(self):
        from evaluator.models import GeneratedPrompt
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GeneratedPrompt(
                prompt="",
                difficulty="simple",
                capability_tested="test",
            )

    def test_serialization_to_dict(self):
        from evaluator.models import GeneratedPrompt

        prompt = GeneratedPrompt(
            prompt="Extract tables from this PDF",
            difficulty="medium",
            capability_tested="table_extraction",
        )

        data = prompt.model_dump()
        assert data["prompt"] == "Extract tables from this PDF"
        assert data["difficulty"] == "medium"
        assert data["capability_tested"] == "table_extraction"


class TestPromptGenerationResult:
    """Test PromptGenerationResult model."""

    def test_create_with_all_fields(self):
        from evaluator.models import GeneratedPrompt, PromptGenerationResult

        prompts = [
            GeneratedPrompt(
                prompt="Help me merge PDFs",
                difficulty="simple",
                capability_tested="merge",
            ),
            GeneratedPrompt(
                prompt="Extract all tables from this document",
                difficulty="medium",
                capability_tested="table_extraction",
            ),
        ]

        result = PromptGenerationResult(
            skill_name="pdf",
            prompts=prompts,
            generated_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=1500,
        )

        assert result.skill_name == "pdf"
        assert len(result.prompts) == 2
        assert result.model_used == "claude-sonnet-4-20250514"
        assert result.tokens_used == 1500

    def test_prompts_list_required(self):
        from evaluator.models import PromptGenerationResult
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PromptGenerationResult(
                skill_name="pdf",
                prompts=None,  # type: ignore
                generated_at=datetime.now(timezone.utc),
                model_used="claude-sonnet-4-20250514",
                tokens_used=100,
            )

    def test_serialization_to_json(self):
        from evaluator.models import GeneratedPrompt, PromptGenerationResult

        prompts = [
            GeneratedPrompt(
                prompt="Test prompt",
                difficulty="simple",
                capability_tested="test",
            ),
        ]

        result = PromptGenerationResult(
            skill_name="pdf",
            prompts=prompts,
            generated_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=500,
        )

        json_str = result.model_dump_json()
        data = json.loads(json_str)

        assert data["skill_name"] == "pdf"
        assert len(data["prompts"]) == 1
        assert data["tokens_used"] == 500

    def test_can_load_from_json(self):
        from evaluator.models import PromptGenerationResult

        json_data = {
            "skill_name": "pdf",
            "prompts": [
                {
                    "prompt": "Merge these PDFs",
                    "difficulty": "simple",
                    "capability_tested": "merge",
                }
            ],
            "generated_at": "2024-06-01T00:00:00Z",
            "model_used": "claude-sonnet-4-20250514",
            "tokens_used": 750,
        }

        result = PromptGenerationResult.model_validate(json_data)

        assert result.skill_name == "pdf"
        assert len(result.prompts) == 1
        assert result.prompts[0].prompt == "Merge these PDFs"


# =============================================================================
# Test: Prompt Parsing
# =============================================================================

class TestParsePromptResponse:
    """Test parsing Claude's response into GeneratedPrompt objects."""

    def test_parse_json_array_response(self):
        from evaluator.prompt_generator import parse_prompt_response

        # Claude returns JSON array
        response_text = '''[
            {
                "prompt": "Help me merge these two PDF files into one document",
                "difficulty": "simple",
                "capability_tested": "pdf_merge"
            },
            {
                "prompt": "Extract all the tables from this financial report PDF",
                "difficulty": "medium",
                "capability_tested": "table_extraction"
            }
        ]'''

        prompts = parse_prompt_response(response_text)

        assert len(prompts) == 2
        assert prompts[0].prompt == "Help me merge these two PDF files into one document"
        assert prompts[0].difficulty == "simple"
        assert prompts[1].capability_tested == "table_extraction"

    def test_parse_json_with_markdown_code_block(self):
        from evaluator.prompt_generator import parse_prompt_response

        # Claude sometimes wraps JSON in markdown code blocks
        response_text = '''```json
[
    {
        "prompt": "I need to add a watermark to this PDF",
        "difficulty": "medium",
        "capability_tested": "watermark"
    }
]
```'''

        prompts = parse_prompt_response(response_text)

        assert len(prompts) == 1
        assert prompts[0].prompt == "I need to add a watermark to this PDF"

    def test_parse_handles_extra_text_before_json(self):
        from evaluator.prompt_generator import parse_prompt_response

        response_text = '''Here are the prompts:

[
    {
        "prompt": "Split this PDF into individual pages",
        "difficulty": "simple",
        "capability_tested": "split"
    }
]

I hope these are helpful!'''

        prompts = parse_prompt_response(response_text)

        assert len(prompts) == 1
        assert "Split this PDF" in prompts[0].prompt

    def test_parse_invalid_json_raises_error(self):
        from evaluator.prompt_generator import parse_prompt_response, PromptParseError

        response_text = "This is not valid JSON at all"

        with pytest.raises(PromptParseError):
            parse_prompt_response(response_text)

    def test_parse_empty_array_raises_error(self):
        from evaluator.prompt_generator import parse_prompt_response, PromptParseError

        response_text = "[]"

        with pytest.raises(PromptParseError) as exc_info:
            parse_prompt_response(response_text)

        assert "empty" in str(exc_info.value).lower()

    def test_parse_validates_each_prompt(self):
        from evaluator.prompt_generator import parse_prompt_response, PromptParseError

        # Missing required field
        response_text = '''[
            {
                "prompt": "Valid prompt",
                "difficulty": "simple"
            }
        ]'''

        with pytest.raises(PromptParseError):
            parse_prompt_response(response_text)


# =============================================================================
# Test: SKILL.md Loading
# =============================================================================

class TestLoadSkillMd:
    """Test loading SKILL.md content."""

    def test_load_skill_md_from_path(self, tmp_path):
        from evaluator.prompt_generator import load_skill_md

        # Create a test SKILL.md
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Test Skill\n\nThis is a test skill.")

        content = load_skill_md(skill_dir)

        assert "# Test Skill" in content
        assert "This is a test skill" in content

    def test_load_skill_md_not_found(self, tmp_path):
        from evaluator.prompt_generator import load_skill_md, SkillNotFoundError

        skill_dir = tmp_path / "nonexistent-skill"
        skill_dir.mkdir()

        with pytest.raises(SkillNotFoundError):
            load_skill_md(skill_dir)

    def test_load_skill_md_by_name(self, tmp_path):
        from evaluator.prompt_generator import load_skill_md_by_name

        # Create skill directory structure
        skills_dir = tmp_path / "skills"
        skill_dir = skills_dir / "pdf"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# PDF Skill\n\nPDF processing capabilities.")

        content = load_skill_md_by_name("pdf", base_dir=skills_dir)

        assert "# PDF Skill" in content


# =============================================================================
# Test: Cache Management
# =============================================================================

class TestCacheManagement:
    """Test prompt caching functionality."""

    def test_check_cache_exists(self, tmp_path):
        from evaluator.prompt_generator import check_cache_exists

        # Create cache file
        skill_dir = tmp_path / "pdf"
        skill_dir.mkdir()
        cache_file = skill_dir / "prompts.json"
        cache_file.write_text('{"skill_name": "pdf", "prompts": []}')

        assert check_cache_exists(skill_dir) is True

    def test_check_cache_not_exists(self, tmp_path):
        from evaluator.prompt_generator import check_cache_exists

        skill_dir = tmp_path / "pdf"
        skill_dir.mkdir()

        assert check_cache_exists(skill_dir) is False

    def test_load_cached_prompts(self, tmp_path):
        from evaluator.prompt_generator import load_cached_prompts
        from evaluator.models import PromptGenerationResult

        # Create cache file
        skill_dir = tmp_path / "pdf"
        skill_dir.mkdir()
        cache_file = skill_dir / "prompts.json"
        cache_data = {
            "skill_name": "pdf",
            "prompts": [
                {
                    "prompt": "Cached prompt",
                    "difficulty": "simple",
                    "capability_tested": "test",
                }
            ],
            "generated_at": "2024-06-01T00:00:00Z",
            "model_used": "claude-sonnet-4-20250514",
            "tokens_used": 500,
        }
        cache_file.write_text(json.dumps(cache_data))

        result = load_cached_prompts(skill_dir)

        assert isinstance(result, PromptGenerationResult)
        assert result.skill_name == "pdf"
        assert len(result.prompts) == 1

    def test_save_prompts_to_cache(self, tmp_path):
        from evaluator.prompt_generator import save_prompts_to_cache
        from evaluator.models import GeneratedPrompt, PromptGenerationResult

        skill_dir = tmp_path / "pdf"
        skill_dir.mkdir()

        result = PromptGenerationResult(
            skill_name="pdf",
            prompts=[
                GeneratedPrompt(
                    prompt="Test prompt",
                    difficulty="simple",
                    capability_tested="test",
                )
            ],
            generated_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
            model_used="claude-sonnet-4-20250514",
            tokens_used=500,
        )

        save_prompts_to_cache(result, skill_dir)

        cache_file = skill_dir / "prompts.json"
        assert cache_file.exists()

        loaded_data = json.loads(cache_file.read_text())
        assert loaded_data["skill_name"] == "pdf"


# =============================================================================
# Test: Prompt Generation System Prompt
# =============================================================================

class TestSystemPrompt:
    """Test the system prompt used for prompt generation."""

    def test_build_generation_prompt(self):
        from evaluator.prompt_generator import build_generation_prompt

        skill_content = """# PDF Skill

## Capabilities
- Merge PDFs
- Split PDFs
- Extract tables
"""

        prompt = build_generation_prompt(skill_content)

        # Should include skill content
        assert "PDF Skill" in prompt

        # Should include instructions for prompt generation
        assert "10" in prompt or "ten" in prompt.lower()  # 10 prompts
        assert "realistic" in prompt.lower()
        assert "difficulty" in prompt.lower()

        # Should not mention skill name in prompts
        assert "don't mention" in prompt.lower() or "do not mention" in prompt.lower()


# =============================================================================
# Test: PromptGenerator Class
# =============================================================================

class TestPromptGeneratorInit:
    """Test PromptGenerator initialization."""

    def test_init_with_api_key(self):
        from evaluator.prompt_generator import PromptGenerator

        generator = PromptGenerator(api_key="sk-ant-test-key")
        assert generator.api_key == "sk-ant-test-key"

    def test_init_loads_from_env(self, monkeypatch):
        from evaluator.prompt_generator import PromptGenerator

        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-key")

        generator = PromptGenerator()
        assert generator.api_key == "sk-ant-env-key"

    def test_init_without_api_key_raises_error(self, monkeypatch):
        from evaluator.prompt_generator import PromptGenerator, ConfigurationError

        # Clear any existing env var
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ConfigurationError):
            PromptGenerator()


class TestPromptGeneratorGenerate:
    """Test PromptGenerator.generate method."""

    def test_generate_returns_result(self):
        from evaluator.prompt_generator import PromptGenerator
        from evaluator.models import PromptGenerationResult

        # Mock the Anthropic client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''[
            {
                "prompt": "Help me merge these PDF documents",
                "difficulty": "simple",
                "capability_tested": "merge"
            },
            {
                "prompt": "Extract all tables from the report",
                "difficulty": "medium",
                "capability_tested": "table_extraction"
            }
        ]''')]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=200)

        with patch("evaluator.prompt_generator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = PromptGenerator(api_key="sk-ant-test-key")
            result = generator.generate(skill_content="# PDF Skill\n\nMerge and extract PDFs")

            assert isinstance(result, PromptGenerationResult)
            assert len(result.prompts) >= 1
            assert result.tokens_used == 700  # input + output

    def test_generate_uses_sonnet_model(self):
        from evaluator.prompt_generator import PromptGenerator

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='[{"prompt": "Test", "difficulty": "simple", "capability_tested": "test"}]')]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)

        with patch("evaluator.prompt_generator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = PromptGenerator(api_key="sk-ant-test-key")
            generator.generate(skill_content="# Test Skill")

            # Verify the model used (sonnet model)
            call_kwargs = mock_client.messages.create.call_args[1]
            assert "sonnet" in call_kwargs["model"]


class TestPromptGeneratorGenerateForSkill:
    """Test PromptGenerator.generate_for_skill method."""

    def test_generate_for_skill_uses_cache(self, tmp_path):
        from evaluator.prompt_generator import PromptGenerator
        from evaluator.models import PromptGenerationResult

        # Create cached prompts
        skill_dir = tmp_path / "pdf"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# PDF Skill")

        cache_data = {
            "skill_name": "pdf",
            "prompts": [
                {"prompt": "Cached prompt", "difficulty": "simple", "capability_tested": "test"}
            ],
            "generated_at": "2024-06-01T00:00:00Z",
            "model_used": "claude-sonnet-4-20250514",
            "tokens_used": 500,
        }
        (skill_dir / "prompts.json").write_text(json.dumps(cache_data))

        with patch("evaluator.prompt_generator.Anthropic"):
            generator = PromptGenerator(api_key="sk-ant-test-key")
            result = generator.generate_for_skill("pdf", skills_dir=tmp_path)

            assert result.prompts[0].prompt == "Cached prompt"

    def test_generate_for_skill_force_regenerate(self, tmp_path):
        from evaluator.prompt_generator import PromptGenerator

        # Create cached prompts and skill file
        skill_dir = tmp_path / "pdf"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# PDF Skill\n\nPDF capabilities")

        cache_data = {
            "skill_name": "pdf",
            "prompts": [
                {"prompt": "Old cached prompt", "difficulty": "simple", "capability_tested": "test"}
            ],
            "generated_at": "2024-06-01T00:00:00Z",
            "model_used": "claude-sonnet-4-20250514",
            "tokens_used": 500,
        }
        (skill_dir / "prompts.json").write_text(json.dumps(cache_data))

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='[{"prompt": "New generated prompt", "difficulty": "medium", "capability_tested": "new_test"}]')]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)

        with patch("evaluator.prompt_generator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = PromptGenerator(api_key="sk-ant-test-key")
            result = generator.generate_for_skill("pdf", skills_dir=tmp_path, force=True)

            # Should have called the API despite cache existing
            assert mock_client.messages.create.called
            assert result.prompts[0].prompt == "New generated prompt"

    def test_generate_for_skill_saves_to_cache(self, tmp_path):
        from evaluator.prompt_generator import PromptGenerator

        # Create skill file but no cache
        skill_dir = tmp_path / "pdf"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# PDF Skill\n\nPDF capabilities")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='[{"prompt": "Generated prompt", "difficulty": "simple", "capability_tested": "test"}]')]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)

        with patch("evaluator.prompt_generator.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = PromptGenerator(api_key="sk-ant-test-key")
            generator.generate_for_skill("pdf", skills_dir=tmp_path)

            # Should have saved to cache
            cache_file = skill_dir / "prompts.json"
            assert cache_file.exists()


# =============================================================================
# Test: Difficulty Distribution
# =============================================================================

class TestDifficultyDistribution:
    """Test that generated prompts have appropriate difficulty mix."""

    def test_prompts_have_difficulty_mix(self):
        from evaluator.prompt_generator import parse_prompt_response

        # A good response should have mixed difficulties
        response_text = '''[
            {"prompt": "Simple task 1", "difficulty": "simple", "capability_tested": "basic"},
            {"prompt": "Simple task 2", "difficulty": "simple", "capability_tested": "basic"},
            {"prompt": "Medium task 1", "difficulty": "medium", "capability_tested": "intermediate"},
            {"prompt": "Medium task 2", "difficulty": "medium", "capability_tested": "intermediate"},
            {"prompt": "Medium task 3", "difficulty": "medium", "capability_tested": "intermediate"},
            {"prompt": "Complex task 1", "difficulty": "complex", "capability_tested": "advanced"},
            {"prompt": "Complex task 2", "difficulty": "complex", "capability_tested": "advanced"},
            {"prompt": "Complex task 3", "difficulty": "complex", "capability_tested": "advanced"},
            {"prompt": "Simple task 3", "difficulty": "simple", "capability_tested": "basic"},
            {"prompt": "Medium task 4", "difficulty": "medium", "capability_tested": "intermediate"}
        ]'''

        prompts = parse_prompt_response(response_text)

        difficulties = [p.difficulty for p in prompts]
        assert "simple" in difficulties
        assert "medium" in difficulties
        assert "complex" in difficulties
