# test_real_alpha_vantage.py

import pytest

from finsight_mcp.clients.alpha_vantage import AlphaVantageClient
from finsight_mcp.clients.sec_edgar import SECEdgarClient
from finsight_mcp.config import settings
from finsight_mcp.agent.workflow import data_collection_node

# #alpha_vantage test
# @pytest.mark.asyncio
# async def test_real_alpha_vantage():
#     client = AlphaVantageClient(settings)

#     print(
#         "KEY FROM SETTINGS:",
#         repr(settings.alpha_vantage_api_key)
#     )

#     result = await client.get_price_history("AAPL")

#     print("\n=== Alpha Vantage REAL DATA ===")
#     print(result)

#     assert result is not None
#     assert result.ticker == "AAPL"
#     assert len(result.prices) > 0

#     first_price = result.prices[0]

#     assert first_price.date is not None
#     assert first_price.close > 0
#     assert first_price.volume >= 0

# #sec_edgar test
# @pytest.mark.asyncio
# async def test_real_sec_edgar():
#     client = SECEdgarClient(settings)

#     result = await client.get_company_facts("AAPL")

#     print("\n=== SEC EDGAR REAL DATA ===")
#     print(result)

#     assert result is not None

#Data collection workflow test

@pytest.mark.asyncio
async def test_real_data_collection():
    state = {
        "ticker": "AAPL"
    }

    result = await data_collection_node(state)

    print("\n=== COMPLETE DATA COLLECTION RESULT ===")
    print(result)

    assert result is not None