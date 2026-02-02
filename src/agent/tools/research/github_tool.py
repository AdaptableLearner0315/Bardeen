"""GitHub API tool implementation."""

import logging
import json
import os
from typing import Dict, Any, Optional, List
import urllib.request
import urllib.parse
import urllib.error

from src.agent.tools.base import BaseTool, RateLimiters
from src.shared.models import ToolMode

logger = logging.getLogger(__name__)


class GitHubTool(BaseTool):
    """
    GitHub API tool for accessing organization and repository data.

    Provides information about company's open source presence,
    technology stack, and developer activity.
    """

    TOOL_NAME = "github"
    TOOL_DESCRIPTION = (
        "Search GitHub for company organizations and repositories. "
        "Returns information about open source projects, tech stack indicators, "
        "repository statistics, and developer activity. "
        "Use this to understand a company's engineering culture and technology choices."
    )
    TOOL_MODE = ToolMode.EXTENDED
    DEFAULT_TIMEOUT = 10.0
    MAX_RETRIES = 2
    CACHE_TTL = 3600.0  # 1 hour for GitHub data

    RATE_LIMIT_RPS = 0.0167  # 60/hr unauthenticated
    RATE_LIMIT_BURST = 5

    # GitHub API base URL
    BASE_URL = "https://api.github.com"

    def __init__(
        self,
        token: Optional[str] = None,
        max_repos: int = 10,
        **kwargs
    ):
        """
        Initialize GitHub tool.

        Args:
            token: GitHub personal access token (optional, increases rate limit)
            max_repos: Maximum number of repositories to return
            **kwargs: Additional BaseTool arguments
        """
        # Use token from environment if not provided
        self.token = token or os.getenv("GITHUB_TOKEN")

        # Set appropriate rate limiter based on authentication
        if "rate_limiter" not in kwargs:
            kwargs["rate_limiter"] = RateLimiters.github_api(authenticated=bool(self.token))

        super().__init__(**kwargs)
        self.max_repos = max_repos

    def _execute(self, org_name: str) -> Dict[str, Any]:
        """
        Get GitHub organization data.

        Args:
            org_name: GitHub organization name

        Returns:
            Dictionary with organization and repository data
        """
        # Validate input
        if not org_name or not org_name.strip():
            return {
                "success": False,
                "error": "Empty organization name",
                "org_name": org_name
            }

        org_name = org_name.strip().lower()

        # Remove common suffixes
        for suffix in ["-inc", "-corp", "-io", "-ai", "-hq"]:
            if org_name.endswith(suffix):
                org_name = org_name[:-len(suffix)]

        try:
            # Get organization info
            org_data = self._get_org(org_name)

            if not org_data:
                # Try searching for organization
                search_results = self._search_org(org_name)
                if search_results:
                    return {
                        "success": True,
                        "org_name": org_name,
                        "found": False,
                        "message": f"Organization '{org_name}' not found directly.",
                        "suggestions": search_results[:3]
                    }

                return {
                    "success": False,
                    "error": f"GitHub organization '{org_name}' not found",
                    "org_name": org_name
                }

            # Get repositories
            repos = self._get_repos(org_name)

            result = {
                "success": True,
                "org_name": org_data.get("login"),
                "display_name": org_data.get("name") or org_data.get("login"),
                "description": org_data.get("description"),
                "url": org_data.get("html_url"),
                "website": org_data.get("blog"),
                "public_repos": org_data.get("public_repos", 0),
                "followers": org_data.get("followers", 0),
                "created_at": org_data.get("created_at"),
            }

            if repos:
                result["top_repositories"] = repos
                result["total_stars"] = sum(r.get("stars", 0) for r in repos)

                # Infer tech stack from languages
                languages = {}
                for repo in repos:
                    lang = repo.get("language")
                    if lang:
                        languages[lang] = languages.get(lang, 0) + 1
                if languages:
                    result["top_languages"] = dict(
                        sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
                    )

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"GitHub error: {error_msg}")

            if "rate limit" in error_msg.lower():
                return {
                    "success": False,
                    "error": "GitHub API rate limit exceeded. Try again later.",
                    "org_name": org_name,
                    "error_code": "RATE_LIMITED"
                }

            return {
                "success": False,
                "error": f"GitHub lookup failed: {error_msg}",
                "org_name": org_name
            }

    def _make_request(self, url: str) -> Optional[Dict[str, Any]]:
        """Make authenticated request to GitHub API."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "B2BAccountAgent/1.0"
        }

        if self.token:
            headers["Authorization"] = f"token {self.token}"

        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 403:
                raise Exception("Rate limit exceeded")
            raise
        except Exception as e:
            logger.debug(f"GitHub request failed: {e}")
            return None

    def _get_org(self, org_name: str) -> Optional[Dict[str, Any]]:
        """Get organization data."""
        url = f"{self.BASE_URL}/orgs/{org_name}"
        return self._make_request(url)

    def _get_repos(self, org_name: str) -> List[Dict[str, Any]]:
        """Get organization repositories sorted by stars."""
        url = f"{self.BASE_URL}/orgs/{org_name}/repos?sort=stars&direction=desc&per_page={self.max_repos}"
        data = self._make_request(url)

        if not data:
            return []

        repos = []
        for repo in data:
            repos.append({
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "description": repo.get("description"),
                "url": repo.get("html_url"),
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "open_issues": repo.get("open_issues_count", 0),
                "last_updated": repo.get("updated_at"),
                "topics": repo.get("topics", [])[:5],
            })

        return repos

    def _search_org(self, query: str) -> List[Dict[str, str]]:
        """Search for organizations."""
        url = f"{self.BASE_URL}/search/users?q={urllib.parse.quote(query)}+type:org&per_page=5"
        data = self._make_request(url)

        if not data:
            return []

        suggestions = []
        for item in data.get("items", []):
            suggestions.append({
                "login": item.get("login"),
                "url": item.get("html_url"),
            })

        return suggestions

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "org_name": {
                    "type": "string",
                    "description": (
                        "GitHub organization name. "
                        "Examples: 'stripe', 'microsoft', 'google', 'facebook', 'netflix'"
                    )
                }
            },
            "required": ["org_name"]
        }

    @staticmethod
    def is_available() -> bool:
        """GitHub API is always available."""
        return True
