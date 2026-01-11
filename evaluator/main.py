#!/usr/bin/env python3
# CLI Entry Point for Evaluator
"""
CLI for KalybrateX skill evaluation.

Commands:
    python -m evaluator.main --list              # List discovered skills
    python -m evaluator.main --skill pdf         # Evaluate one skill
    python -m evaluator.main --all               # Evaluate all skills
    python -m evaluator.main --skill pdf --force # Force re-evaluation
    python -m evaluator.main --skill pdf --skip-security  # Skip security check
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from dotenv import load_dotenv


# Load environment variables
load_dotenv()


# =============================================================================
# Constants
# =============================================================================

DEFAULT_SKILLS_DIR = Path("data/skills")
DEFAULT_EVALUATIONS_DIR = Path("data/evaluations")
LEADERBOARD_FILE = Path("data/leaderboard.json")


# =============================================================================
# Helper Functions
# =============================================================================

def list_available_skills(skills_dir: Path = DEFAULT_SKILLS_DIR) -> List[str]:
    """
    List all available skills that have SKILL.md files.

    Args:
        skills_dir: Directory containing skill folders

    Returns:
        List of skill names (directory names)
    """
    if not skills_dir.exists():
        return []

    skills = []
    for item in skills_dir.iterdir():
        if item.is_dir() and (item / "SKILL.md").exists():
            skills.append(item.name)

    return sorted(skills)


def print_skills_list(skills: List[str]) -> None:
    """
    Print a formatted list of skills.

    Args:
        skills: List of skill names
    """
    if not skills:
        print("No skills found in data/skills/")
        print("Run discovery first: python -m discovery.main --all")
        return

    print(f"\nDiscovered Skills ({len(skills)} total):")
    print("-" * 40)
    for skill in skills:
        print(f"  - {skill}")
    print()


# =============================================================================
# Evaluation Functions
# =============================================================================

def evaluate_skill(
    skill_name: str,
    force: bool = False,
    skip_security: bool = False,
    skip_execution: bool = False,
    skills_dir: Path = DEFAULT_SKILLS_DIR,
    evaluations_dir: Path = DEFAULT_EVALUATIONS_DIR,
) -> Optional["SkillScore"]:
    """
    Evaluate a single skill.

    This is the main orchestration function that:
    1. Loads SKILL.md from data/skills/{name}/SKILL.md
    2. Generates prompts (or loads cached)
    3. Runs A/B comparisons for each prompt (quality evaluation)
    4. Runs execution verification (unless skipped or not applicable)
    5. Runs security check (unless skipped)
    6. Calculates combined score (quality + execution)
    7. Saves all evidence via DataLogger
    8. Returns SkillScore

    Args:
        skill_name: Name of the skill to evaluate
        force: If True, re-evaluate even if already done
        skip_security: If True, skip security analysis
        skip_execution: If True, skip execution verification
        skills_dir: Directory containing skills
        evaluations_dir: Directory to save evaluation results

    Returns:
        SkillScore if successful, None if error
    """
    # Import here to avoid circular imports and for cleaner error messages
    from evaluator.prompt_generator import (
        PromptGenerator,
        load_skill_md,
        check_cache_exists,
        load_cached_prompts,
        save_prompts_to_cache,
        SkillNotFoundError,
    )
    from evaluator.quality_evaluator import QualityEvaluator
    from evaluator.execution_evaluator import ExecutionEvaluator
    from evaluator.security_checker import SecurityChecker
    from evaluator.scorer import Scorer
    from evaluator.data_logger import DataLogger
    from evaluator.skill_categories import requires_execution, get_skill_category
    from evaluator.models import (
        SecurityResult,
        SecurityGrade,
        SkillScore,
        ComparisonResult,
        ExecutionScore,
    )

    skill_dir = skills_dir / skill_name
    logger = DataLogger(base_dir=evaluations_dir)

    # Check if already evaluated (unless force)
    if not force and logger.evaluation_exists(skill_name):
        print(f"  [SKIP] {skill_name} - already evaluated (use --force to re-evaluate)")
        return logger.load_score(skill_name)

    # Clear previous evaluation if force
    if force:
        logger.clear_evaluation(skill_name)

    print(f"\n{'='*60}")
    print(f"Evaluating: {skill_name}")
    print(f"{'='*60}")

    try:
        # Determine number of steps based on what we're running
        total_steps = 7
        if skip_execution or not requires_execution(skill_name):
            total_steps = 6

        # 1. Load SKILL.md
        print(f"  [1/{total_steps}] Loading SKILL.md...")
        skill_content = load_skill_md(skill_dir)
        logger.save_skill_md(skill_name, skill_content)
        print(f"        Loaded {len(skill_content)} characters")

        # 2. Generate prompts (or load cached)
        print(f"  [2/{total_steps}] Generating prompts...")
        if check_cache_exists(skill_dir) and not force:
            print(f"        Using cached prompts")
            prompts_result = load_cached_prompts(skill_dir)
        else:
            generator = PromptGenerator()
            prompts_result = generator.generate(skill_content, skill_name=skill_name)
            save_prompts_to_cache(prompts_result, skill_dir)
            print(f"        Generated {len(prompts_result.prompts)} prompts ({prompts_result.tokens_used} tokens)")

        logger.save_prompts(skill_name, prompts_result)

        # 3. Run A/B comparisons (quality evaluation)
        print(f"  [3/{total_steps}] Running A/B comparisons...")
        evaluator = QualityEvaluator()
        comparisons: List[ComparisonResult] = []

        for i, prompt in enumerate(prompts_result.prompts):
            print(f"        [{i+1}/{len(prompts_result.prompts)}] {prompt.difficulty}: {prompt.prompt[:50]}...")
            try:
                comparison = evaluator.evaluate(prompt.prompt, skill_content)
                comparisons.append(comparison)
                logger.save_comparison(skill_name, i, comparison)

                # Show verdict
                verdict_symbol = {
                    "skill": "+",
                    "baseline": "-",
                    "tie": "="
                }.get(comparison.verdict.value, "?")
                print(f"              {verdict_symbol} {comparison.verdict.value}")
            except Exception as e:
                print(f"              ERROR: {e}")
                # Continue with other prompts

        if not comparisons:
            print(f"  [ERROR] No comparisons completed - cannot score")
            return None

        # 4. Execution verification (unless skipped or not applicable)
        execution_score: Optional[ExecutionScore] = None
        step_num = 4

        if skip_execution:
            print(f"  [4/{total_steps}] Execution verification...")
            print(f"        Skipped (--skip-execution)")
            step_num = 4
        elif not requires_execution(skill_name):
            category = get_skill_category(skill_name)
            print(f"  [4/{total_steps}] Execution verification...")
            print(f"        N/A for {category.value} skills (quality-only evaluation)")
            step_num = 4
        else:
            print(f"  [4/{total_steps}] Running execution verification...")
            try:
                exec_evaluator = ExecutionEvaluator()
                exec_comparisons, execution_score = exec_evaluator.evaluate(
                    skill_content,
                    skill_name,
                    num_prompts=8,
                )

                # Show execution results
                for i, exec_comp in enumerate(exec_comparisons):
                    verdict_symbol = {
                        "skill": "+",
                        "baseline": "-",
                        "tie": "="
                    }.get(exec_comp.execution_verdict.value, "?")
                    skill_valid = "✓" if exec_comp.skill_verification.output_valid else "✗"
                    print(f"        [{i+1}/{len(exec_comparisons)}] {verdict_symbol} skill:{skill_valid} - {exec_comp.verdict_reasoning[:40]}...")

                if execution_score:
                    print(f"        Execution Grade: {execution_score.execution_grade} ({execution_score.execution_win_rate}% win rate)")
            except Exception as e:
                print(f"        [ERROR] Execution verification failed: {e}")
                # Continue without execution score

            step_num = 5

        # 5. Security check (unless skipped)
        print(f"  [{step_num}/{total_steps}] Running security analysis...")
        if skip_security:
            print(f"        Skipped (--skip-security)")
            security_result = SecurityResult(
                skill_name=skill_name,
                grade=SecurityGrade.SECURE,
                issues=[],
                analysis="Security check skipped by user request.",
                analyzed_at=datetime.now(timezone.utc),
                model_used="skipped",
                tokens_used=0,
            )
        else:
            checker = SecurityChecker()
            security_result = checker.analyze(skill_content, skill_name)
            print(f"        Grade: {security_result.grade.value}, Issues: {len(security_result.issues)}")

        logger.save_security(skill_name, security_result)
        step_num += 1

        # Calculate score (quality + execution combined)
        print(f"  [{step_num}/{total_steps}] Calculating score...")
        scorer = Scorer()
        score = scorer.score(skill_name, comparisons, security_result)

        # Calculate combined score if execution was run
        combined_score = scorer.score_combined(
            skill_name, comparisons, security_result, execution_score
        )

        logger.save_score(skill_name, score)
        print(f"        Quality Grade: {score.grade} ({score.win_rate}% win rate)")
        if execution_score and execution_score.execution_win_rate is not None:
            print(f"        Execution Grade: {execution_score.execution_grade} ({execution_score.execution_win_rate}% win rate)")
            print(f"        Combined Grade: {combined_score.final_grade} ({combined_score.combined_score}% combined)")
        step_num += 1

        # Save summary
        print(f"  [{step_num}/{total_steps}] Saving summary...")
        logger.save_summary(skill_name, score, prompts_result, comparisons, security_result)
        print(f"        Saved to data/evaluations/{skill_name}/")

        # Print summary
        print(f"\n  Result: {skill_name}")
        print(f"    Quality Grade: {score.grade}")
        print(f"    Quality Win Rate: {score.win_rate}%")
        if execution_score and execution_score.execution_win_rate is not None:
            print(f"    Execution Grade: {execution_score.execution_grade}")
            print(f"    Execution Win Rate: {execution_score.execution_win_rate}%")
            print(f"    Combined Grade: {combined_score.final_grade}")
            print(f"    Combined Score: {combined_score.combined_score}%")
        print(f"    Wins: {score.wins}, Losses: {score.losses}, Ties: {score.ties}")
        print(f"    Security: {score.security_grade.value}")
        print(f"    Cost/use: ${score.cost_per_use_usd:.6f}")

        return score

    except SkillNotFoundError:
        print(f"  [ERROR] SKILL.md not found for {skill_name}")
        return None
    except Exception as e:
        print(f"  [ERROR] Failed to evaluate {skill_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def update_leaderboard(
    scores: List["SkillScore"],
    leaderboard_path: Path = LEADERBOARD_FILE,
) -> None:
    """
    Update the leaderboard with new scores.

    Args:
        scores: List of SkillScore objects
        leaderboard_path: Path to leaderboard.json
    """
    from evaluator.models import SkillScore

    # Load existing leaderboard if it exists
    existing_ratings = {}
    if leaderboard_path.exists():
        try:
            data = json.loads(leaderboard_path.read_text(encoding="utf-8"))
            for rating in data.get("ratings", []):
                existing_ratings[rating["skill_name"]] = rating
        except (json.JSONDecodeError, KeyError):
            pass

    # Update with new scores
    for score in scores:
        existing_ratings[score.skill_name] = {
            "skill_name": score.skill_name,
            "grade": score.grade,
            "win_rate": score.win_rate,
            "wins": score.wins,
            "losses": score.losses,
            "ties": score.ties,
            "security_grade": score.security_grade.value,
            "security_issues_count": score.security_issues_count,
            "avg_tokens_per_use": score.avg_tokens_per_use,
            "cost_per_use_usd": score.cost_per_use_usd,
            "total_comparisons": score.total_comparisons,
            "scored_at": score.scored_at.isoformat(),
        }

    # Sort by win_rate descending (None values at end)
    ratings = list(existing_ratings.values())
    ratings.sort(
        key=lambda x: (x["win_rate"] is not None, x["win_rate"] or 0),
        reverse=True
    )

    # Build leaderboard
    leaderboard = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_skills": len(ratings),
        "ratings": ratings,
    }

    # Write atomically by writing to temp file first
    leaderboard_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = leaderboard_path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(leaderboard, indent=2), encoding="utf-8")
    temp_path.rename(leaderboard_path)

    print(f"\nLeaderboard updated: {leaderboard_path}")
    print(f"Total skills: {len(ratings)}")


def print_leaderboard(leaderboard_path: Path = LEADERBOARD_FILE) -> None:
    """
    Print the current leaderboard.

    Args:
        leaderboard_path: Path to leaderboard.json
    """
    if not leaderboard_path.exists():
        print("\nNo leaderboard found. Run some evaluations first.")
        return

    data = json.loads(leaderboard_path.read_text(encoding="utf-8"))
    ratings = data.get("ratings", [])

    if not ratings:
        print("\nLeaderboard is empty.")
        return

    print(f"\n{'='*70}")
    print(f"KalybrateX Leaderboard")
    print(f"{'='*70}")
    print(f"Generated: {data.get('generated_at', 'unknown')}")
    print(f"Total Skills: {data.get('total_skills', 0)}")
    print()
    print(f"{'Rank':<6} {'Skill':<25} {'Grade':<6} {'Win Rate':<10} {'Security':<10}")
    print("-" * 70)

    for i, rating in enumerate(ratings, 1):
        win_rate = f"{rating['win_rate']}%" if rating['win_rate'] is not None else "N/A"
        print(
            f"{i:<6} {rating['skill_name']:<25} {rating['grade']:<6} "
            f"{win_rate:<10} {rating['security_grade']:<10}"
        )

    print()


# =============================================================================
# Main CLI
# =============================================================================

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="KalybrateX Skill Evaluator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m evaluator.main --list              # List discovered skills
  python -m evaluator.main --skill pdf         # Evaluate one skill
  python -m evaluator.main --all               # Evaluate all skills
  python -m evaluator.main --skill pdf --force # Force re-evaluation
  python -m evaluator.main --skill pdf --skip-security  # Skip security check
  python -m evaluator.main --leaderboard       # Show leaderboard
        """
    )

    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all discovered skills"
    )

    parser.add_argument(
        "--skill", "-s",
        type=str,
        help="Evaluate a specific skill by name"
    )

    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Evaluate all discovered skills"
    )

    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-evaluation even if already done"
    )

    parser.add_argument(
        "--skip-security",
        action="store_true",
        help="Skip security analysis"
    )

    parser.add_argument(
        "--skip-execution",
        action="store_true",
        help="Skip execution verification"
    )

    parser.add_argument(
        "--leaderboard", "-b",
        action="store_true",
        help="Show current leaderboard"
    )

    args = parser.parse_args()

    # Validate arguments
    if not any([args.list, args.skill, args.all, args.leaderboard]):
        parser.print_help()
        return 1

    # List skills
    if args.list:
        skills = list_available_skills()
        print_skills_list(skills)
        return 0

    # Show leaderboard
    if args.leaderboard:
        print_leaderboard()
        return 0

    # Evaluate specific skill
    if args.skill:
        skills = list_available_skills()
        if args.skill not in skills:
            print(f"Error: Skill '{args.skill}' not found.")
            print(f"Available skills: {', '.join(skills)}")
            return 1

        score = evaluate_skill(
            args.skill,
            force=args.force,
            skip_security=args.skip_security,
            skip_execution=args.skip_execution,
        )

        if score:
            update_leaderboard([score])
            return 0
        else:
            return 1

    # Evaluate all skills
    if args.all:
        skills = list_available_skills()
        if not skills:
            print("No skills found to evaluate.")
            return 1

        print(f"\nEvaluating {len(skills)} skills...")
        scores = []
        errors = []

        for skill_name in skills:
            try:
                score = evaluate_skill(
                    skill_name,
                    force=args.force,
                    skip_security=args.skip_security,
                    skip_execution=args.skip_execution,
                )
                if score:
                    scores.append(score)
            except Exception as e:
                errors.append((skill_name, str(e)))
                print(f"  [ERROR] {skill_name}: {e}")

        # Update leaderboard with all scores
        if scores:
            update_leaderboard(scores)

        # Summary
        print(f"\n{'='*60}")
        print(f"Evaluation Summary")
        print(f"{'='*60}")
        print(f"  Successful: {len(scores)}")
        print(f"  Errors: {len(errors)}")

        if errors:
            print(f"\n  Failed skills:")
            for skill_name, error in errors:
                print(f"    - {skill_name}: {error}")

        print_leaderboard()
        return 0 if not errors else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
