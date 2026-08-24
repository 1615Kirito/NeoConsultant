# test_real_alpha_vantage.py

import pytest

from finsight_mcp.clients.alpha_vantage import AlphaVantageClient
from finsight_mcp.config import settings

@pytest.mark.asyncio
async def test_real_alpha_vantage():
    client = AlphaVantageClient(settings)

    print(
        "KEY FROM SETTINGS:",
        repr(settings.alpha_vantage_api_key)
    )

    result = await client.get_price_history("AAPL")

    print("\n=== Alpha Vantage REAL DATA ===")
    print(result)

    assert result is not None
    assert result.ticker == "AAPL"
    assert len(result.prices) > 0

    first_price = result.prices[0]

    assert first_price.date is not None
    assert first_price.close > 0
    assert first_price.volume >= 0


