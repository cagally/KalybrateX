# Discovery CLI
"""
Command-line interface for the Discovery phase of KalybrateX.
Discovers skills from official sources and awesome-lists.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .github_fetcher import GitHubFetcher
from .models import DiscoveryResult, DiscoveredSkill


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def load_env() -> Optional[str]:
    """
    Load environment variables from .env file.

    Returns:
        GitHub token if found, None otherwise
    """
    env_path = get_project_root() / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        logger.info("GitHub token loaded from environment")
    else:
        logger.warning(
            "No GITHUB_TOKEN found - using unauthenticated API (60 requests/hour limit)"
        )
    return token


def load_existing_skills(output_dir: Path) -> dict[str, DiscoveredSkill]:
    """
    Load existing discovered skills from skills.json.

    Args:
        output_dir: Directory containing skills.json

    Returns:
        Dictionary mapping skill slug to DiscoveredSkill
    """
    skills_file = output_dir / "skills.json"
    if not skills_file.exists():
        return {}

    try:
        with open(skills_file, "r") as f:
            data = json.load(f)

        result = DiscoveryResult.model_validate(data)
        return {skill.slug: skill for skill in result.skills}

    except Exception as e:
        logger.warning(f"Failed to load existing skills: {e}")
        return {}


def save_results(
    output_dir: Path,
    skills_dir: Path,
    result: DiscoveryResult
) -> None:
    """
    Save discovery results to disk.

    Saves:
    - output_dir/skills.json - Full discovery result
    - skills_dir/{slug}/SKILL.md - Individual skill files
    - skills_dir/{slug}/metadata.json - Skill metadata

    Args:
        output_dir: Directory for skills.json
        skills_dir: Directory for individual skill files
        result: Discovery result to save
    """
    # Ensure directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Save main skills.json
    skills_file = output_dir / "skills.json"
    with open(skills_file, "w") as f:
        f.write(result.model_dump_json(indent=2))
    logger.info(f"Saved {len(result.skills)} skills to {skills_file}")

    # Save individual skill files
    saved_count = 0
    for skill in result.skills:
        skill_dir = skills_dir / skill.slug
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Save SKILL.md if available
        if skill.skill_md.found and skill.skill_md.content:
            skill_md_file = skill_dir / "SKILL.md"
            with open(skill_md_file, "w") as f:
                f.write(skill.skill_md.content)
            saved_count += 1

        # Save metadata.json (without SKILL.md content for smaller files)
        metadata_file = skill_dir / "metadata.json"
        metadata = skill.model_dump()
        # Remove content from metadata to keep file small
        if metadata.get("skill_md"):
            metadata["skill_md"]["content"] = None
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

    logger.info(f"Saved {saved_count} SKILL.md files to {skills_dir}")


def run_discovery(
    output_dir: Path,
    skills_dir: Path,
    limit: Optional[int] = None,
    force: bool = False,
    sources: Optional[list[str]] = None
) -> DiscoveryResult:
    """
    Run the discovery process.

    Args:
        output_dir: Directory to save skills.json
        skills_dir: Directory to save individual skill files
        limit: Maximum skills per source
        force: Re-fetch even if skill exists
        sources: List of sources to check

    Returns:
        DiscoveryResult with discovered skills
    """
    # Load GitHub token
    token = load_env()

    # Load existing skills (for deduplication)
    existing_skills = {} if force else load_existing_skills(output_dir)
    if existing_skills:
        logger.info(f"Found {len(existing_skills)} existing skills")

    # Create fetcher and run discovery
    fetcher = GitHubFetcher(token=token)

    logger.info("Starting discovery...")
    result = fetcher.run_discovery(sources=sources, limit=limit)

    # Merge with existing skills (new ones take precedence)
    if existing_skills and not force:
        for slug, skill in existing_skills.items():
            # Keep existing skill if not re-discovered
            if not any(s.slug == slug for s in result.skills):
                result.skills.append(skill)

        # Update totals
        result.total_skills = len(result.skills)
        result.total_with_skill_md = sum(
            1 for s in result.skills if s.skill_md.found
        )

    # Save results
    save_results(output_dir, skills_dir, result)

    return result


def show_status(output_dir: Path) -> None:
    """
    Show status of discovered skills.

    Args:
        output_dir: Directory containing skills.json
    """
    skills_file = output_dir / "skills.json"

    if not skills_file.exists():
        print("No discovery has been run yet.")
        print(f"Run: python -m discovery.main --all")
        return

    with open(skills_file, "r") as f:
        data = json.load(f)

    result = DiscoveryResult.model_validate(data)

    print(f"\nDiscovery Status")
    print(f"================")
    print(f"Last run: {result.discovered_at}")
    print(f"Sources checked: {', '.join(result.sources_checked)}")
    print(f"Total skills: {result.total_skills}")
    print(f"With SKILL.md: {result.total_with_skill_md}")
    print(f"Success rate: {result.total_with_skill_md / result.total_skills * 100:.1f}%" if result.total_skills > 0 else "N/A")

    print(f"\nSkills by source:")
    from collections import Counter
    source_counts = Counter(s.source.value for s in result.skills)
    for source, count in source_counts.items():
        print(f"  {source}: {count}")

    print(f"\nTop 10 skills by stars:")
    sorted_skills = sorted(
        result.skills,
        key=lambda s: s.github_metadata.stars,
        reverse=True
    )[:10]
    for skill in sorted_skills:
        md_status = "+" if skill.skill_md.found else "-"
        print(f"  [{md_status}] {skill.name}: {skill.github_metadata.stars} stars")


def main() -> int:
    """
    Main entry point for the discovery CLI.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Discover Claude Code skills from various sources"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run full discovery from all sources"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of skills per source"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-fetch even if skills already exist"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show status of discovered skills"
    )

    parser.add_argument(
        "--source",
        choices=["anthropic_official", "awesome_list"],
        action="append",
        help="Specific source(s) to check (can be repeated)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for skills.json (default: data/discovered)"
    )

    parser.add_argument(
        "--skills-dir",
        type=str,
        default=None,
        help="Directory for individual skill files (default: data/skills)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Set directories
    project_root = get_project_root()
    output_dir = Path(args.output_dir) if args.output_dir else project_root / "data" / "discovered"
    skills_dir = Path(args.skills_dir) if args.skills_dir else project_root / "data" / "skills"

    # Handle --status
    if args.status:
        show_status(output_dir)
        return 0

    # Require --all or --source for discovery
    if not args.all and not args.source:
        parser.print_help()
        print("\nError: Must specify --all or --source to run discovery")
        return 1

    # Run discovery
    sources = args.source if args.source else None

    try:
        result = run_discovery(
            output_dir=output_dir,
            skills_dir=skills_dir,
            limit=args.limit,
            force=args.force,
            sources=sources
        )

        # Print summary
        print(f"\nDiscovery Complete!")
        print(f"===================")
        print(f"Total skills: {result.total_skills}")
        print(f"With SKILL.md: {result.total_with_skill_md}")
        print(f"Results saved to: {output_dir / 'skills.json'}")

        return 0

    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
