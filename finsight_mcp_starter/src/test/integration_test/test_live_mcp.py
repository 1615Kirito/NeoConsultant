"""Live MCP/API integration tests. Run explicitly from src.
Uses existing local_mcp_tools(): no mocked MCP, HTTP, signals or evidence.
"""
import asyncio
import math

import pytest

REQUIRED_TOOLS = {'get_price_history', 'get_company_facts', 'get_recent_news'}


@pytest.fixture(scope='module')
def live_collection():
    # Imports are deferred to make this test's setup explicit.
    from finsight_mcp.mcp_client import local_mcp_tools
    from finsight_mcp.agent.workflow import data_collection_node

    async def collect():
        async with local_mcp_tools() as tools:
            listing = await tools.session.list_tools()
            registered = {tool.name: tool for tool in listing.tools}
            missing = REQUIRED_TOOLS - registered.keys()
            assert not missing, f'MCP server is missing tools: {sorted(missing)}'
            properties = registered['get_price_history'].input_schema.get('properties', {})
            assert 'days' in properties, (
                'Interface mismatch: data_collection_node passes days, but MCP '
                'get_price_history does not declare days. Add days: int = 100 '
                'to the server tool and forward it to AlphaVantageClient.'
            )
            state = await data_collection_node({'ticker': 'aapl', 'days': 50}, tools)
            return registered, state

    # Transport and all awaits stay in one event loop/context.
    # Fetch once per module to avoid repeating external API requests.
    return asyncio.run(collect())


def test_live_mcp_registration(live_collection):
    registered, _ = live_collection
    assert REQUIRED_TOOLS <= registered.keys()
    assert 'days' in registered['get_price_history'].input_schema['properties']


def test_live_data_collection_models(live_collection):
    from finsight_mcp.schemas import PriceHistory, CompanyFactsSummary, NewsBundle
    _, state = live_collection
    assert state['ticker'] == 'AAPL'
    assert isinstance(state['price_history'], PriceHistory)
    assert isinstance(state['company_facts'], CompanyFactsSummary)
    assert isinstance(state['news'], NewsBundle)
    for name in ('price_history', 'company_facts', 'news'):
        assert state[name].ticker == 'AAPL'
    prices = state['price_history'].prices
    assert 0 < len(prices) <= 50, 'days=50 must limit the returned price history'
    assert all(math.isfinite(p.close) and p.close > 0 and p.volume >= 0 for p in prices)
    for name in ('price_history', 'company_facts'):
        model = state[name]
        assert model.source_id
        assert model.source_url.startswith(('https://', 'http://'))
    # News may be empty; do not require a fixed headline or sentiment.
    for article in state['news'].articles:
        assert article.source_id
        assert article.source_url.startswith(('https://', 'http://'))
        if article.sentiment_score is not None:
            assert math.isfinite(article.sentiment_score)


def test_live_data_to_signals_and_evidence(live_collection):
    from finsight_mcp.agent.workflow import quantitative_analysis_node, evidence_assembly_node
    from finsight_mcp.schemas import TechnicalSignals, ResearchBundle
    _, collected = live_collection
    state = {key: value.model_copy(deep=True) if hasattr(value, 'model_copy') else value
             for key, value in collected.items()}
    state.update(quantitative_analysis_node(state))
    technicals = state['technicals']
    assert isinstance(technicals, TechnicalSignals)
    for value in technicals.model_dump().values():
        if value is not None:
            assert math.isfinite(value)
    if technicals.sma_20 is not None:
        assert technicals.sma_20 > 0
    if technicals.volatility is not None:
        assert technicals.volatility >= 0
    state.update(evidence_assembly_node(state))
    bundle = state['research_bundle']
    assert isinstance(bundle, ResearchBundle)
    assert bundle.ticker == 'AAPL'
    assert any(e.category == 'price' for e in bundle.evidence)
    assert len({e.evidence_id for e in bundle.evidence}) == len(bundle.evidence)
    valid_sources = {state['price_history'].source_id, state['company_facts'].source_id,
                     *(a.source_id for a in state['news'].articles)}
    for item in bundle.evidence:
        assert item.source_id in valid_sources
        assert item.description.strip()
        assert item.source_url.startswith(('https://', 'http://'))
    news_evidence = [e for e in bundle.evidence if e.category == 'news']
    assert len(news_evidence) == len(state['news'].articles)
    for item, article in zip(news_evidence, state['news'].articles):
        assert item.source_id == article.source_id
        assert item.source_url == article.source_url
        assert item.sentiment_score == article.sentiment_score
