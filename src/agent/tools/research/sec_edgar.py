"""SEC EDGAR tool implementation."""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import urllib.request
import urllib.parse

from src.agent.tools.base import BaseTool, RateLimiters
from src.shared.models import ToolMode

logger = logging.getLogger(__name__)


class SECEdgarTool(BaseTool):
    """
    SEC EDGAR tool for accessing SEC filings.

    Provides access to 10-K, 10-Q, 8-K filings and other SEC documents
    for publicly traded US companies.
    """

    TOOL_NAME = "sec_edgar"
    TOOL_DESCRIPTION = (
        "Access SEC EDGAR filings for US public companies. "
        "Returns recent filings including 10-K (annual), 10-Q (quarterly), "
        "and 8-K (current events) reports. "
        "Use this for official financial reports, risk factors, and regulatory filings."
    )
    TOOL_MODE = ToolMode.EXTENDED
    DEFAULT_TIMEOUT = 15.0
    MAX_RETRIES = 2
    CACHE_TTL = 3600.0  # 1 hour for SEC data

    RATE_LIMIT_RPS = 10.0  # SEC allows 10 requests/second
    RATE_LIMIT_BURST = 5

    # SEC API base URL
    BASE_URL = "https://data.sec.gov"
    SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"

    def __init__(
        self,
        user_agent: str = "B2BAccountAgent/1.0 (contact@example.com)",
        **kwargs
    ):
        """
        Initialize SEC EDGAR tool.

        Args:
            user_agent: User agent for SEC API (required by SEC)
            **kwargs: Additional BaseTool arguments
        """
        if "rate_limiter" not in kwargs:
            kwargs["rate_limiter"] = RateLimiters.sec_edgar()

        super().__init__(**kwargs)
        self.user_agent = user_agent

    def _execute(self, company: str, filing_type: str = "10-K") -> Dict[str, Any]:
        """
        Search for SEC filings.

        Args:
            company: Company name or CIK number
            filing_type: Type of filing (10-K, 10-Q, 8-K)

        Returns:
            Dictionary with filing information
        """
        # Validate input
        if not company or not company.strip():
            return {
                "success": False,
                "error": "Empty company name",
                "company": company
            }

        company = company.strip()
        filing_type = filing_type.strip().upper()

        # Validate filing type
        valid_types = ["10-K", "10-Q", "8-K", "DEF 14A", "S-1", "20-F"]
        if filing_type not in valid_types:
            return {
                "success": False,
                "error": f"Invalid filing type. Supported: {', '.join(valid_types)}",
                "company": company,
                "filing_type": filing_type
            }

        try:
            # First, try to get CIK from company name
            cik = self._get_cik(company)

            if not cik:
                return {
                    "success": False,
                    "error": f"Company '{company}' not found in SEC database. "
                             "Company may be private or non-US.",
                    "company": company
                }

            # Get company filings
            filings = self._get_filings(cik, filing_type)

            if not filings:
                return {
                    "success": True,
                    "company": company,
                    "cik": cik,
                    "filing_type": filing_type,
                    "filings": [],
                    "message": f"No {filing_type} filings found for {company}"
                }

            return {
                "success": True,
                "company": company,
                "cik": cik,
                "filing_type": filing_type,
                "filings": filings[:5],  # Return top 5 most recent
                "total_filings": len(filings)
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"SEC EDGAR error: {error_msg}")

            return {
                "success": False,
                "error": f"SEC lookup failed: {error_msg}",
                "company": company
            }

    def _get_cik(self, company: str) -> Optional[str]:
        """
        Get CIK number for a company.

        Args:
            company: Company name or CIK

        Returns:
            CIK number as string, or None if not found
        """
        # Check if already a CIK
        if company.isdigit():
            return company.zfill(10)

        try:
            # Use SEC's company tickers JSON
            url = f"{self.BASE_URL}/submissions/CIK0000000000.json"

            # Try searching company_tickers.json
            tickers_url = "https://www.sec.gov/files/company_tickers.json"
            req = urllib.request.Request(
                tickers_url,
                headers={"User-Agent": self.user_agent}
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())

            # Search for company
            company_lower = company.lower()
            for key, item in data.items():
                if company_lower in item.get("title", "").lower():
                    cik = str(item.get("cik_str", "")).zfill(10)
                    return cik

            return None

        except Exception as e:
            logger.debug(f"CIK lookup failed: {e}")
            return None

    def _get_filings(self, cik: str, filing_type: str) -> List[Dict[str, Any]]:
        """
        Get filings for a CIK.

        Args:
            cik: Company CIK number
            filing_type: Type of filing

        Returns:
            List of filing information
        """
        try:
            # Get company submissions
            url = f"{self.BASE_URL}/submissions/CIK{cik}.json"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": self.user_agent}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

            company_name = data.get("name", "Unknown")
            filings_data = data.get("filings", {}).get("recent", {})

            if not filings_data:
                return []

            # Extract filings
            forms = filings_data.get("form", [])
            dates = filings_data.get("filingDate", [])
            accessions = filings_data.get("accessionNumber", [])
            descriptions = filings_data.get("primaryDocument", [])

            filings = []
            for i, form in enumerate(forms):
                if form == filing_type or (filing_type == "10-K" and form in ["10-K", "10-K/A"]):
                    accession = accessions[i].replace("-", "")
                    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{descriptions[i]}"

                    filings.append({
                        "form": form,
                        "filing_date": dates[i],
                        "accession_number": accessions[i],
                        "document": descriptions[i],
                        "url": doc_url
                    })

            return filings

        except Exception as e:
            logger.debug(f"Filings lookup failed: {e}")
            return []

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "company": {
                    "type": "string",
                    "description": (
                        "Company name or CIK number. "
                        "Examples: 'Apple Inc', 'Tesla', 'Microsoft', '320193' (Apple's CIK)"
                    )
                },
                "filing_type": {
                    "type": "string",
                    "description": (
                        "Type of SEC filing. Default: '10-K'. "
                        "Options: '10-K' (annual), '10-Q' (quarterly), '8-K' (current events)"
                    ),
                    "default": "10-K"
                }
            },
            "required": ["company"]
        }

    @staticmethod
    def is_available() -> bool:
        """SEC EDGAR is always available (no dependencies)."""
        return True
