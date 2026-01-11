# Evaluator Models
"""
Pydantic models for the Evaluator phase of KalybrateX.
These models represent prompts, evaluations, and scoring data.
"""

from datetime import datetime
from enum import Enum
from typing import Literal
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
