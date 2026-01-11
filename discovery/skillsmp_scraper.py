# SkillsMP Scraper
"""
Scraper for SkillsMP (skillsmp.com) to discover top starred Claude Code skills.

Uses Playwright to bypass Cloudflare protection and fetch from the API.
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SkillsMPSkill:
    """Skill data from SkillsMP API."""
    id: str
    name: str
    author: str
    description: str
    github_url: Optional[str] = None
    stars: Optional[int] = None
    skill_md_path: Optional[str] = None


class SkillsMPScraper:
    """
    Scraper for SkillsMP website.

    Uses Playwright with non-headless mode to bypass Cloudflare,
    then fetches from the internal API endpoint.
    """

    API_URL = "https://skillsmp.com/api/skills"
    BASE_URL = "https://skillsmp.com"

    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None

    def _start_browser(self) -> None:
        """Start Playwright browser with Cloudflare bypass settings."""
        from playwright.sync_api import sync_playwright

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False,  # Non-headless to bypass Cloudflare
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )
        self.page = self.browser.new_page(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        # Navigate to base URL first to establish session
        logger.info("Loading SkillsMP to establish session...")
        self.page.goto(self.BASE_URL, wait_until="networkidle")
        time.sleep(3)  # Wait for Cloudflare challenge

    def _stop_browser(self) -> None:
        """Stop Playwright browser."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def fetch_skills(
        self,
        limit: int = 100,
        marketplace_only: bool = True,
        sort_by: str = "stars"
    ) -> list[SkillsMPSkill]:
        """
        Fetch skills from SkillsMP API.

        Args:
            limit: Maximum number of skills to fetch
            marketplace_only: Only fetch skills with marketplace.json
            sort_by: Sort order (stars, name, etc.)

        Returns:
            List of SkillsMPSkill objects
        """
        try:
            self._start_browser()

            # Build API URL
            api_url = (
                f"{self.API_URL}?page=1&limit={limit}"
                f"&sortBy={sort_by}&marketplaceOnly={str(marketplace_only).lower()}"
            )

            logger.info(f"Fetching from API: {api_url}")

            # Use JavaScript fetch in browser context to make API call
            result = self.page.evaluate(f"""
                async () => {{
                    const response = await fetch("{api_url}");
                    return await response.json();
                }}
            """)

            if not result or "skills" not in result:
                logger.error("No skills in API response")
                return []

            skills = []
            for skill_data in result["skills"]:
                skill = self._parse_skill(skill_data)
                if skill:
                    skills.append(skill)

            logger.info(f"Fetched {len(skills)} skills from SkillsMP")
            return skills

        finally:
            self._stop_browser()

    def _parse_skill(self, data: dict) -> Optional[SkillsMPSkill]:
        """Parse skill data from API response."""
        try:
            skill_id = data.get("id", "")
            name = data.get("name", "")
            author = data.get("author", "")
            description = data.get("description", "")

            # Extract GitHub URL from the skill ID or construct it
            # ID format: "vercel-next-js-claude-plugin-plugins-cache-components-skills-cache-components-skill-md"
            # Author is the GitHub username

            github_url = None
            skill_md_path = None

            # Try to get GitHub URL from the data
            if "githubUrl" in data:
                github_url = data["githubUrl"]
            elif "repoUrl" in data:
                github_url = data["repoUrl"]
            elif author:
                # The skill ID contains repo info - try to parse it
                # Format seems to be: author-repo-...-skill-md
                parts = skill_id.split("-")
                if len(parts) >= 2:
                    # Try to find repo name in ID
                    # For "vercel-next-js-..." the repo is "next.js"
                    # This is tricky - we'll use the raw GitHub URL field if available
                    pass

            # Get star count if available
            stars = data.get("stars") or data.get("githubStars")
            if stars:
                if isinstance(stars, str):
                    # Parse "137.1k" format
                    stars = self._parse_star_count(stars)
                else:
                    stars = int(stars)

            # Get SKILL.md path if available
            if "skillPath" in data:
                skill_md_path = data["skillPath"]
            elif "path" in data:
                skill_md_path = data["path"]

            return SkillsMPSkill(
                id=skill_id,
                name=name,
                author=author,
                description=description,
                github_url=github_url,
                stars=stars,
                skill_md_path=skill_md_path
            )

        except Exception as e:
            logger.warning(f"Failed to parse skill: {e}")
            return None

    def _parse_star_count(self, star_str: str) -> int:
        """Parse star count string like '137.1k' to int."""
        star_str = star_str.lower().strip()
        multiplier = 1

        if star_str.endswith("k"):
            multiplier = 1000
            star_str = star_str[:-1]
        elif star_str.endswith("m"):
            multiplier = 1000000
            star_str = star_str[:-1]

        try:
            return int(float(star_str) * multiplier)
        except ValueError:
            return 0


def scrape_top_skills(
    limit: int = 20,
    marketplace_only: bool = True
) -> list[dict]:
    """
    Scrape top skills from SkillsMP.

    Args:
        limit: Number of skills to fetch
        marketplace_only: Only fetch skills with marketplace.json

    Returns:
        List of skill dictionaries
    """
    scraper = SkillsMPScraper()
    skills = scraper.fetch_skills(
        limit=limit,
        marketplace_only=marketplace_only,
        sort_by="stars"
    )

    return [
        {
            "id": s.id,
            "name": s.name,
            "author": s.author,
            "description": s.description,
            "github_url": s.github_url,
            "stars": s.stars,
            "skill_md_path": s.skill_md_path,
        }
        for s in skills
    ]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("Scraping top skills from SkillsMP...")
    skills = scrape_top_skills(limit=25, marketplace_only=True)

    print(f"\nFound {len(skills)} skills:")
    for i, skill in enumerate(skills, 1):
        stars = skill.get("stars") or "?"
        print(f"  {i}. {skill['author']}/{skill['name']} - {stars} stars")

    # Save to file
    with open("/tmp/skillsmp_top_skills.json", "w") as f:
        json.dump(skills, f, indent=2)
    print(f"\nSaved to /tmp/skillsmp_top_skills.json")
