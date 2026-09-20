# MCP Tools / resources for the MCP system


from __future__ import annotations


from finsight_mcp.clients.alpha_vantage import AlphaVantageClient
from finsight_mcp.clients.sec_edgar import SECEdgarClient

from finsight_mcp.config import settings

from mcp.server import MCPServer

mcp = MCPServer("finsight-stock-tools")


# -------------------------------------------------
# Alpha Vantage tools
# -------------------------------------------------

@mcp.tool()
async def get_price_history(
    ticker: str,

) -> dict:
    """
    Get historical stock price data for a ticker.

    Args:
        ticker: Stock ticker symbol, e.g. AAPL.
        days: Number of recent trading days to return.
    """
    client = AlphaVantageClient(settings)

    result = await client.get_price_history(
        ticker=ticker,
    )

    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")

    return result

@mcp.tool()
async def get_recent_news(ticker: str) -> dict:
    """
    Get recent news articles for a ticker.
    """
    
    client = AlphaVantageClient(settings)

    result = await client.get_recent_news(ticker)

    return result.model_dump(mode="json")


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
    client = SECEdgarClient(settings)

    result = await client.get_company_facts(
        ticker=ticker,
    )

    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")

    return result








if __name__ == "__main__":
    mcp.run()