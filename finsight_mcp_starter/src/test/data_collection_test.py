# test_real_alpha_vantage.py

import pytest

from finsight_mcp.clients.alpha_vantage import AlphaVantageClient
from finsight_mcp.clients.sec_edgar import SECEdgarClient
from finsight_mcp.config import settings
from finsight_mcp.agent.workflow import data_collection_node, evidence_assembly_node, quantitative_analysis_node

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

# @pytest.mark.asyncio
# async def test_real_data_collection():
#     state = {
#         "ticker": "AAPL"
#     }

#     result = await data_collection_node(state)

#     print("\n=== COMPLETE DATA COLLECTION RESULT ===")
#     print(result)

#     assert result is not None


# @pytest.mark.asyncio
# async def test_quantitative_analysis_node():
#     # Step 1: get real market data
#     state = {
#         "ticker": "AAPL"
#     }

#     collected = await data_collection_node(state)
#     state.update(collected)

#     # Step 2: run quantitative analysis
#     result = quantitative_analysis_node(state)

#     assert "technicals" in result

#     technicals = result["technicals"]

#     # -------------------------
#     # Basic structure
#     # -------------------------
#     assert technicals.return_30d is not None
#     assert technicals.sma_20 is not None
#     assert technicals.volatility is not None
#     assert technicals.max_drawdown is not None

#     # -------------------------
#     # Type checks
#     # -------------------------
#     assert isinstance(technicals.return_30d, float)
#     assert isinstance(technicals.sma_20, float)
#     assert isinstance(technicals.volatility, float)
#     assert isinstance(technicals.max_drawdown, float)

#     # -------------------------
#     # Reasonable value checks
#     # -------------------------

#     # stock price average should be positive
#     assert technicals.sma_20 > 0

#     # volatility should never be negative
#     assert technicals.volatility >= 0

#     # drawdown normally should be <= 0
#     assert technicals.max_drawdown <= 0

#     # return should at least be a finite value
#     assert -10 < technicals.return_30d < 10

#     print("\n=== TECHNICAL SIGNALS ===")
#     print(technicals)


@pytest.mark.asyncio
async def test_evidence_assembly_node():
    state = {
        "ticker": "AAPL"
    }

    # ==========================================
    # Step 1: Data Collection
    # ==========================================
    collected = await data_collection_node(state)
    state.update(collected)

    # ==========================================
    # Step 2: Quantitative Analysis
    # ==========================================
    quantitative = quantitative_analysis_node(state)
    state.update(quantitative)

    # ==========================================
    # Step 3: Evidence Assembly
    # ==========================================
    result = evidence_assembly_node(state)

    assert "research_bundle" in result

    bundle = result["research_bundle"]

    # ==========================================
    # ResearchBundle structure
    # ==========================================

    assert bundle.ticker == "AAPL"

    assert bundle.technicals == state["technicals"]
    assert bundle.company_facts == state["company_facts"]
    assert bundle.news == state["news"]

    # ==========================================
    # Evidence list
    # ==========================================

    assert isinstance(bundle.evidence, list)
    assert len(bundle.evidence) > 0

    # ==========================================
    # Every evidence item should be valid
    # ==========================================

    for evidence in bundle.evidence:
        assert evidence.evidence_id
        assert evidence.source_id
        assert evidence.source_url
        assert evidence.category
        assert evidence.description

        assert isinstance(evidence.evidence_id, str)
        assert isinstance(evidence.source_id, str)
        assert isinstance(evidence.source_url, str)
        assert isinstance(evidence.category, str)
        assert isinstance(evidence.description, str)

        # URL should look like an actual URL
        assert evidence.source_url.startswith(
            ("http://", "https://")
        )

        # description should contain useful content
        assert len(evidence.description.strip()) > 0

    print("\n=== RESEARCH BUNDLE ===")
    print(bundle)