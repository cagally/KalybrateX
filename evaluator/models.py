# Evaluator Models
"""
Pydantic models for the Evaluator phase of KalybrateX.
These models represent prompts, evaluations, and scoring data.
"""

from datetime import datetime
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

    # Cost
    avg_tokens_per_use: float = Field(
        ge=0, description="Average output tokens per use"
    )
    cost_per_use_usd: float = Field(
        ge=0, description="Estimated cost per use in USD"
    )

    # Metadata
    total_comparisons: int = Field(
        ge=0, description="Total number of A/B comparisons performed"
    )
    scored_at: datetime = Field(description="When this score was calculated")
