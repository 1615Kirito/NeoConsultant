# MCP Tools / resources for the MCP system


from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from finsight_mcp.clients.alpha_vantage import AlphaVantageClient
from finsight_mcp.clients.sec_edgar import SECEdgarClient


mcp = FastMCP("finsight-stock-tools")


# -------------------------------------------------
# Alpha Vantage tools
# -------------------------------------------------

@mcp.tool()
async def get_price_history(
    ticker: str,
    days: int = 100,
) -> dict:
    """
    Get historical stock price data for a ticker.

    Args:
        ticker: Stock ticker symbol, e.g. AAPL.
        days: Number of recent trading days to return.
    """
    client = AlphaVantageClient()

    result = await client.get_price_history(
        ticker=ticker,
        days=days,
    )

    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")

    return result


# -------------------------------------------------
# SEC tools
# -------------------------------------------------

@mcp.tool()
async def get_company_facts(
    ticker: str,
) -> dict:
    """
    Get company financial facts from SEC EDGAR.

    Args:
        ticker: Stock ticker symbol.
    """
    client = SECEdgarClient()

    result = await client.get_company_facts(
        ticker=ticker,
    )

    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")

    return result


@mcp.tool()
async def get_sec_filings(
    ticker: str,
    limit: int = 10,
) -> dict:
    """
    Get recent SEC filings for a company.

    Args:
        ticker: Stock ticker symbol.
        limit: Maximum number of filings.
    """
    client = SECEdgarClient()

    result = await client.get_filings(
        ticker=ticker,
        limit=limit,
    )

    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")

    return result


if __name__ == "__main__":
    mcp.run()