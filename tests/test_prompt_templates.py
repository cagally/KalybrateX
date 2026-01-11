# Tests for Prompt Templates
"""Tests for evaluator/prompt_templates.py"""

import pytest

from evaluator.prompt_templates import (
    get_execution_prompts,
    get_prompt_generation_instruction,
    ExecutionPrompt,
    TIER_1_PDF_PROMPTS,
    TIER_1_XLSX_PROMPTS,
    TIER_1_CODE_PROMPTS,
)


class TestGetExecutionPrompts:
    """Tests for getting execution prompts for skills."""

    def test_pdf_skill_gets_pdf_prompts(self):
        prompts = get_execution_prompts("pdf")
        assert len(prompts) > 0
        # Should include PDF-specific prompts
        assert any("pdf" in p.expected_files[0].lower() for p in prompts)

    def test_xlsx_skill_gets_xlsx_prompts(self):
        prompts = get_execution_prompts("xlsx")
        assert len(prompts) > 0
        # Should include XLSX-specific prompts
        assert any("xlsx" in p.expected_files[0].lower() for p in prompts)

    def test_code_skill_gets_code_prompts(self):
        prompts = get_execution_prompts("mcp-builder")
        assert len(prompts) > 0
        # Should include code-specific prompts
        assert any(".py" in p.expected_files[0] for p in prompts)

    def test_advisory_skill_gets_empty_list(self):
        prompts = get_execution_prompts("writing")
        assert len(prompts) == 0

    def test_count_parameter(self):
        prompts = get_execution_prompts("pdf", count=4)
        assert len(prompts) <= 4

    def test_prompts_have_required_fields(self):
        prompts = get_execution_prompts("pdf")
        for prompt in prompts:
            assert prompt.prompt  # Non-empty prompt text
            assert prompt.tier in (1, 2)
            assert len(prompt.expected_files) > 0
            assert prompt.capability_tested


class TestPromptStructure:
    """Tests for prompt structure and content."""

    def test_tier_1_prompts_are_self_contained(self):
        """Tier 1 prompts should not reference external files."""
        for prompt in TIER_1_PDF_PROMPTS:
            # Should not ask to "extract from" or "process" external files
            assert "extract from" not in prompt.prompt.lower()
            assert "sample.pdf" not in prompt.prompt.lower()

    def test_prompts_dont_mention_dependencies(self):
        """Prompts should not explicitly tell model to install dependencies."""
        all_prompts = TIER_1_PDF_PROMPTS + TIER_1_XLSX_PROMPTS + TIER_1_CODE_PROMPTS
        for prompt in all_prompts:
            assert "pip install" not in prompt.prompt.lower()
            assert "install dependencies" not in prompt.prompt.lower()
            assert "install any dependencies" not in prompt.prompt.lower()

    def test_prompts_specify_output_filename(self):
        """Prompts should specify expected output filenames."""
        all_prompts = TIER_1_PDF_PROMPTS + TIER_1_XLSX_PROMPTS + TIER_1_CODE_PROMPTS
        for prompt in all_prompts:
            # The expected filename should appear in the prompt
            for expected_file in prompt.expected_files:
                assert expected_file in prompt.prompt or expected_file.replace("'", "") in prompt.prompt


class TestPromptGenerationInstruction:
    """Tests for dynamic prompt generation instructions."""

    def test_file_artifact_instruction(self):
        instruction = get_prompt_generation_instruction("pdf")
        assert "FILE ARTIFACT" in instruction
        assert "pip install" not in instruction.lower() or "DO NOT" in instruction

    def test_code_generation_instruction(self):
        instruction = get_prompt_generation_instruction("mcp-builder")
        assert "CODE GENERATION" in instruction

    def test_configuration_instruction(self):
        instruction = get_prompt_generation_instruction("skill-homeassistant")
        assert "CONFIGURATION" in instruction

    def test_instructions_warn_about_dependencies(self):
        """All instructions should warn not to mention dependencies."""
        for skill in ["pdf", "mcp-builder", "skill-homeassistant"]:
            instruction = get_prompt_generation_instruction(skill)
            assert "DO NOT" in instruction
            assert "dependencies" in instruction.lower() or "install" in instruction.lower()


class TestExecutionPromptDataclass:
    """Tests for the ExecutionPrompt dataclass."""

    def test_expected_properties_structure(self):
        """Expected properties should be properly structured."""
        prompt = ExecutionPrompt(
            prompt="Create test.pdf",
            tier=1,
            expected_files=["test.pdf"],
            expected_properties={"test.pdf": {"pages": 2}},
            capability_tested="test",
        )
        assert "test.pdf" in prompt.expected_properties
        assert prompt.expected_properties["test.pdf"]["pages"] == 2

    def test_multiple_expected_files(self):
        """Should support multiple expected output files."""
        prompt = ExecutionPrompt(
            prompt="Create files",
            tier=2,
            expected_files=["output.py", "result.json"],
            expected_properties={},
            capability_tested="multi_file",
        )
        assert len(prompt.expected_files) == 2
