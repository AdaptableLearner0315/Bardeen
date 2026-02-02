"""Yahoo Finance tool implementation."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.agent.tools.base import BaseTool, RateLimiters
from src.shared.models import ToolMode

logger = logging.getLogger(__name__)

# Try to import yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    yf = None
    YFINANCE_AVAILABLE = False


class YahooFinanceTool(BaseTool):
    """
    Yahoo Finance tool for stock and company financial data.

    Provides stock prices, market cap, P/E ratios, revenue, and other
    financial metrics for publicly traded companies.
    """

    TOOL_NAME = "yahoo_finance"
    TOOL_DESCRIPTION = (
        "Get financial data for publicly traded companies from Yahoo Finance. "
        "Returns stock price, market cap, P/E ratio, revenue, earnings, and more. "
        "Use this for current stock data, financial metrics, and company valuations. "
        "Note: Only works for publicly traded companies with ticker symbols."
    )
    TOOL_MODE = ToolMode.EXTENDED
    DEFAULT_TIMEOUT = 10.0
    MAX_RETRIES = 2
    CACHE_TTL = 300.0  # 5 minutes for financial data

    RATE_LIMIT_RPS = 2.0
    RATE_LIMIT_BURST = 3

    def __init__(self, **kwargs):
        """
        Initialize Yahoo Finance tool.

        Args:
            **kwargs: Additional BaseTool arguments
        """
        if "rate_limiter" not in kwargs:
            kwargs["rate_limiter"] = RateLimiters.yahoo_finance()

        super().__init__(**kwargs)

        if not YFINANCE_AVAILABLE:
            logger.warning(
                "yfinance not installed. "
                "Install with: pip install yfinance"
            )

    def _execute(self, ticker: str) -> Dict[str, Any]:
        """
        Get financial data for a ticker symbol.

        Args:
            ticker: Stock ticker symbol (e.g., AAPL, GOOGL)

        Returns:
            Dictionary with financial data
        """
        if not YFINANCE_AVAILABLE:
            return {
                "success": False,
                "error": "Yahoo Finance not available. Install yfinance package.",
                "ticker": ticker
            }

        # Validate input
        if not ticker or not ticker.strip():
            return {
                "success": False,
                "error": "Empty ticker symbol",
                "ticker": ticker
            }

        ticker = ticker.strip().upper()

        # Basic validation - tickers are usually 1-5 chars
        if len(ticker) > 10 or not ticker.replace(".", "").replace("-", "").isalnum():
            return {
                "success": False,
                "error": f"Invalid ticker symbol format: {ticker}",
                "ticker": ticker
            }

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Check if ticker exists
            if not info or info.get("regularMarketPrice") is None:
                # Try to provide suggestions
                return {
                    "success": False,
                    "error": f"Ticker '{ticker}' not found. Check if the company is publicly traded.",
                    "ticker": ticker,
                    "suggestions": self._get_suggestions(ticker)
                }

            # Extract key financial data
            result = {
                "success": True,
                "ticker": ticker,
                "company_name": info.get("longName") or info.get("shortName", "Unknown"),
                "exchange": info.get("exchange", "Unknown"),
                "currency": info.get("currency", "USD"),
            }

            # Stock price data
            price_data = {}
            if info.get("regularMarketPrice"):
                price_data["current_price"] = info.get("regularMarketPrice")
            if info.get("regularMarketOpen"):
                price_data["open"] = info.get("regularMarketOpen")
            if info.get("regularMarketDayHigh"):
                price_data["day_high"] = info.get("regularMarketDayHigh")
            if info.get("regularMarketDayLow"):
                price_data["day_low"] = info.get("regularMarketDayLow")
            if info.get("regularMarketPreviousClose"):
                price_data["previous_close"] = info.get("regularMarketPreviousClose")
            if info.get("fiftyTwoWeekHigh"):
                price_data["52_week_high"] = info.get("fiftyTwoWeekHigh")
            if info.get("fiftyTwoWeekLow"):
                price_data["52_week_low"] = info.get("fiftyTwoWeekLow")
            if price_data:
                result["price_data"] = price_data

            # Market data
            market_data = {}
            if info.get("marketCap"):
                market_data["market_cap"] = self._format_large_number(info.get("marketCap"))
                market_data["market_cap_raw"] = info.get("marketCap")
            if info.get("volume"):
                market_data["volume"] = info.get("volume")
            if info.get("averageVolume"):
                market_data["avg_volume"] = info.get("averageVolume")
            if market_data:
                result["market_data"] = market_data

            # Valuation metrics
            valuation = {}
            if info.get("trailingPE"):
                valuation["pe_ratio"] = round(info.get("trailingPE"), 2)
            elif info.get("forwardPE"):
                valuation["pe_ratio_forward"] = round(info.get("forwardPE"), 2)
            if info.get("priceToBook"):
                valuation["price_to_book"] = round(info.get("priceToBook"), 2)
            if info.get("priceToSalesTrailing12Months"):
                valuation["price_to_sales"] = round(info.get("priceToSalesTrailing12Months"), 2)
            if info.get("enterpriseValue"):
                valuation["enterprise_value"] = self._format_large_number(info.get("enterpriseValue"))
            if valuation:
                result["valuation"] = valuation

            # Financial metrics
            financials = {}
            if info.get("totalRevenue"):
                financials["revenue"] = self._format_large_number(info.get("totalRevenue"))
                financials["revenue_raw"] = info.get("totalRevenue")
            if info.get("revenueGrowth"):
                financials["revenue_growth"] = f"{info.get('revenueGrowth') * 100:.1f}%"
            if info.get("grossProfits"):
                financials["gross_profit"] = self._format_large_number(info.get("grossProfits"))
            if info.get("ebitda"):
                financials["ebitda"] = self._format_large_number(info.get("ebitda"))
            if info.get("netIncomeToCommon"):
                financials["net_income"] = self._format_large_number(info.get("netIncomeToCommon"))
            if info.get("profitMargins"):
                financials["profit_margin"] = f"{info.get('profitMargins') * 100:.1f}%"
            if financials:
                result["financials"] = financials

            # Dividend info
            if info.get("dividendYield"):
                result["dividend_yield"] = f"{info.get('dividendYield') * 100:.2f}%"

            # Additional info
            if info.get("sector"):
                result["sector"] = info.get("sector")
            if info.get("industry"):
                result["industry"] = info.get("industry")
            if info.get("fullTimeEmployees"):
                result["employees"] = info.get("fullTimeEmployees")
            if info.get("website"):
                result["website"] = info.get("website")

            # Add timestamp
            result["data_timestamp"] = datetime.now().isoformat()

            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Yahoo Finance error for {ticker}: {error_msg}")

            return {
                "success": False,
                "error": f"Failed to fetch data: {error_msg}",
                "ticker": ticker
            }

    def _format_large_number(self, num: float) -> str:
        """Format large numbers with appropriate suffix."""
        if num is None:
            return "N/A"

        abs_num = abs(num)
        sign = "-" if num < 0 else ""

        if abs_num >= 1e12:
            return f"{sign}${abs_num/1e12:.2f}T"
        elif abs_num >= 1e9:
            return f"{sign}${abs_num/1e9:.2f}B"
        elif abs_num >= 1e6:
            return f"{sign}${abs_num/1e6:.2f}M"
        elif abs_num >= 1e3:
            return f"{sign}${abs_num/1e3:.2f}K"
        else:
            return f"{sign}${abs_num:.2f}"

    def _get_suggestions(self, ticker: str) -> List[str]:
        """Get suggestions for failed ticker lookup."""
        suggestions = []

        # Common company ticker mappings
        common_tickers = {
            "GOOGLE": "GOOGL",
            "ALPHABET": "GOOGL",
            "FACEBOOK": "META",
            "AMAZON": "AMZN",
            "MICROSOFT": "MSFT",
            "APPLE": "AAPL",
            "TESLA": "TSLA",
            "NVIDIA": "NVDA",
            "NETFLIX": "NFLX",
        }

        upper_ticker = ticker.upper()
        if upper_ticker in common_tickers:
            suggestions.append(common_tickers[upper_ticker])

        return suggestions

    def get_input_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": (
                        "The stock ticker symbol. "
                        "Examples: 'AAPL' (Apple), 'GOOGL' (Google), 'MSFT' (Microsoft), "
                        "'TSLA' (Tesla), 'AMZN' (Amazon)"
                    )
                }
            },
            "required": ["ticker"]
        }

    @staticmethod
    def is_available() -> bool:
        """Check if Yahoo Finance is available."""
        return YFINANCE_AVAILABLE
