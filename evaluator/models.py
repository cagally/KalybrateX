# Evaluator Models
"""
Pydantic models for the Evaluator phase of KalybrateX.
These models represent prompts, evaluations, and scoring data.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class Difficulty(str, Enum):
    """Difficulty level for a prompt."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class GeneratedPrompt(BaseModel):
    """A single generated prompt for skill evaluation."""
    prompt: str = Field(
        min_length=1,
        description="The user prompt that would naturally require the skill's capabilities"
    )
    difficulty: Literal["simple", "medium", "complex"] = Field(
        description="Difficulty level of the prompt"
    )
    capability_tested: str = Field(
        description="Which skill capability this prompt tests"
    )

    @field_validator("prompt")
    @classmethod
    def prompt_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Prompt cannot be empty or whitespace")
        return v


class PromptGenerationResult(BaseModel):
    """Result of generating prompts for a skill."""
    skill_name: str = Field(description="Name of the skill these prompts were generated for")
    prompts: list[GeneratedPrompt] = Field(description="List of generated prompts")
    generated_at: datetime = Field(description="When these prompts were generated")
    model_used: str = Field(description="The Claude model used for generation")
    tokens_used: int = Field(description="Total tokens used (input + output)")


# =============================================================================
# Quality Evaluator Models
# =============================================================================

class Verdict(str, Enum):
    """Verdict from A/B comparison judging."""
    SKILL_WINS = "skill"
    BASELINE_WINS = "baseline"
    TIE = "tie"


class ComparisonResult(BaseModel):
    """Result of an A/B comparison between baseline and skill responses."""
    prompt: str = Field(description="The user prompt that was evaluated")
    baseline_response: str = Field(description="Response generated without skill")
    skill_response: str = Field(description="Response generated with skill")
    verdict: Verdict = Field(description="Which response won the comparison")
    reasoning: str = Field(description="Judge's reasoning for the verdict")
    baseline_tokens: int = Field(description="Total tokens used for baseline (input + output)")
    skill_tokens: int = Field(description="Total tokens used for skill (input + output)")
    position_a: Literal["baseline", "skill"] = Field(
        description="Which response was shown first (position A) to the judge"
    )
    position_b: Literal["baseline", "skill"] = Field(
        description="Which response was shown second (position B) to the judge"
    )
    judge_model: str = Field(description="The Claude model used for judging")
    judged_at: datetime = Field(description="When the comparison was judged")


# =============================================================================
# Security Checker Models
# =============================================================================

class SecurityGrade(str, Enum):
    """Security grade for a skill based on identified issues."""
    SECURE = "secure"
    WARNING = "warning"
    FAIL = "fail"


class SecurityIssue(BaseModel):
    """A security issue identified in a skill."""
    category: str = Field(
        description="Issue category: data_exfiltration, file_system_abuse, credential_theft, code_injection, malicious_dependencies"
    )
    severity: str = Field(
        description="Issue severity: low, medium, high"
    )
    description: str = Field(
        description="Human-readable description of the security issue"
    )
    evidence: str = Field(
        description="The problematic code/text from SKILL.md that triggered the issue"
    )


class SecurityResult(BaseModel):
    """Result of security analysis for a skill."""
    skill_name: str = Field(description="Name of the skill that was analyzed")
    grade: SecurityGrade = Field(description="Overall security grade")
    issues: list[SecurityIssue] = Field(description="List of identified security issues")
    analysis: str = Field(description="Full analysis text from Sonnet")
    analyzed_at: datetime = Field(description="When the analysis was performed")
    model_used: str = Field(description="The Claude model used for analysis")
    tokens_used: int = Field(description="Total tokens used (input + output)")


# =============================================================================
# Scorer Models
# =============================================================================

class SkillScore(BaseModel):
    """Final score for a skill after evaluation."""
    skill_name: str = Field(description="Name of the skill that was scored")

    # Quality metrics
    wins: int = Field(ge=0, description="Number of comparisons where skill beat baseline")
    losses: int = Field(ge=0, description="Number of comparisons where baseline beat skill")
    ties: int = Field(ge=0, description="Number of comparisons that were ties")
    win_rate: Optional[float] = Field(
        description="Win rate percentage (0-100), None if all ties"
    )
    grade: Literal["A", "B", "C", "D", "F"] = Field(
        description="Letter grade based on win rate"
    )

    # Security
    security_grade: SecurityGrade = Field(description="Security grade from security analysis")
    security_issues_count: int = Field(
        ge=0, description="Number of security issues identified"
    )

    # Cost - with skill
    avg_tokens_per_use: float = Field(
        ge=0, description="Average output tokens per use (with skill)"
    )
    cost_per_use_usd: float = Field(
        ge=0, description="Estimated cost per use in USD (with skill)"
    )

    # Cost - baseline (without skill)
    avg_baseline_tokens: float = Field(
        ge=0, description="Average output tokens per use (without skill)"
    )
    baseline_cost_usd: float = Field(
        ge=0, description="Estimated cost per use in USD (without skill)"
    )

    # Metadata
    total_comparisons: int = Field(
        ge=0, description="Total number of A/B comparisons performed"
    )
    scored_at: datetime = Field(description="When this score was calculated")


# =============================================================================
# Execution Verification Models
# =============================================================================

class SkillCategory(str, Enum):
    """Category determining verification method for a skill."""
    FILE_ARTIFACT = "file_artifact"      # pdf, xlsx, docx - produce files
    CODE_GENERATION = "code_generation"  # produce runnable code
    CONFIGURATION = "configuration"      # produce config files (YAML, JSON)
    ADVISORY = "advisory"                # text/guidance only


class ExecutionPrompt(BaseModel):
    """A prompt designed to produce executable, verifiable output."""
    prompt: str = Field(description="The execution prompt")
    tier: Literal[1, 2] = Field(description="Prompt tier: 1=synthetic, 2=transform")
    expected_files: list[str] = Field(description="List of expected output filenames")
    expected_properties: dict = Field(
        default_factory=dict,
        description="Expected properties per file for verification"
    )
    capability_tested: str = Field(description="Which capability this prompt tests")


class ExecutionResult(BaseModel):
    """Result of executing code in sandbox."""
    executed: bool = Field(description="Whether execution was attempted")
    exit_code: int = Field(description="Process exit code (-1 if not executed)")
    stdout: str = Field(default="", description="Standard output")
    stderr: str = Field(default="", description="Standard error")
    execution_time_ms: int = Field(ge=0, description="Execution time in milliseconds")
    output_files: list[str] = Field(
        default_factory=list,
        description="List of files created during execution"
    )
    error: Optional[str] = Field(default=None, description="Error message if execution failed")


class VerificationResult(BaseModel):
    """Result of verifying execution output."""
    skill_name: str = Field(description="Name of the skill being verified")
    prompt: str = Field(description="The prompt that was executed")

    # Code extraction
    code_extracted: bool = Field(description="Whether executable code was found")
    code_language: str = Field(description="Detected programming language")
    code_blocks_count: int = Field(ge=0, description="Number of code blocks found")

    # Execution
    executed: bool = Field(description="Whether code was executed")
    execution_success: bool = Field(description="Whether execution completed without errors")
    execution_error: Optional[str] = Field(default=None, description="Error message if any")
    execution_time_ms: int = Field(ge=0, description="Execution time in milliseconds")

    # Output validation
    output_files_created: list[str] = Field(
        default_factory=list,
        description="Files created during execution"
    )
    output_valid: bool = Field(description="Whether output met expected criteria")
    output_properties: dict = Field(
        default_factory=dict,
        description="Actual properties of output files"
    )

    # Metadata
    verified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When verification was performed"
    )


class ExecutionComparisonResult(BaseModel):
    """Result of comparing execution between baseline and skill responses."""
    prompt: str = Field(description="The execution prompt")
    tier: int = Field(description="Prompt tier (1 or 2)")

    # Baseline execution
    baseline_verification: VerificationResult = Field(
        description="Verification result for baseline response"
    )

    # Skill execution
    skill_verification: VerificationResult = Field(
        description="Verification result for skill response"
    )

    # Comparison verdict
    execution_verdict: Verdict = Field(
        description="Which response produced better executable output"
    )
    verdict_reasoning: str = Field(
        description="Explanation for the execution verdict"
    )


class ExecutionScore(BaseModel):
    """Execution verification score for a skill."""
    skill_name: str = Field(description="Name of the skill")
    category: SkillCategory = Field(description="Skill category")

    # Execution metrics
    prompts_tested: int = Field(ge=0, description="Number of execution prompts tested")
    code_extracted_count: int = Field(ge=0, description="Prompts where code was extracted")
    executions_attempted: int = Field(ge=0, description="Execution attempts made")
    executions_succeeded: int = Field(ge=0, description="Executions that completed without error")
    outputs_valid: int = Field(ge=0, description="Outputs that met expected criteria")

    # Win/loss tracking (vs baseline)
    execution_wins: int = Field(ge=0, description="Times skill beat baseline in execution")
    execution_losses: int = Field(ge=0, description="Times baseline beat skill in execution")
    execution_ties: int = Field(ge=0, description="Times both had equal execution results")

    # Calculated rates
    extraction_rate: float = Field(
        ge=0, le=100,
        description="Percentage of prompts where code was extracted"
    )
    execution_success_rate: float = Field(
        ge=0, le=100,
        description="Percentage of executions that succeeded"
    )
    validation_rate: float = Field(
        ge=0, le=100,
        description="Percentage of successful executions with valid output"
    )
    execution_win_rate: Optional[float] = Field(
        default=None,
        description="Win rate vs baseline (0-100), None if no comparisons"
    )

    # Grade
    execution_grade: Literal["A", "B", "C", "D", "F"] = Field(
        description="Letter grade based on execution win rate"
    )

    # Metadata
    scored_at: datetime = Field(description="When this score was calculated")


class CombinedScore(BaseModel):
    """Combined quality + execution score for a skill."""
    skill_name: str = Field(description="Name of the skill")
    category: SkillCategory = Field(description="Skill category")

    # Quality metrics (from A/B comparison)
    quality_win_rate: Optional[float] = Field(
        description="Quality win rate (0-100)"
    )
    quality_grade: Literal["A", "B", "C", "D", "F"] = Field(
        description="Quality letter grade"
    )

    # Execution metrics (from execution verification)
    execution_win_rate: Optional[float] = Field(
        default=None,
        description="Execution win rate (0-100), None if not applicable"
    )
    execution_grade: Optional[Literal["A", "B", "C", "D", "F"]] = Field(
        default=None,
        description="Execution letter grade, None if not applicable"
    )

    # Combined
    combined_score: float = Field(
        ge=0, le=100,
        description="Weighted combined score"
    )
    final_grade: Literal["A", "B", "C", "D", "F"] = Field(
        description="Final letter grade"
    )

    # Security
    security_grade: SecurityGrade = Field(description="Security grade")

    # Metadata
    scored_at: datetime = Field(description="When this score was calculated")
