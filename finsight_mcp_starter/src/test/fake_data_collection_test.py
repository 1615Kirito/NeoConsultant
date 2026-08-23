from datetime import datetime, date, timezone

import pytest

from finsight_mcp.agent import workflow

from finsight_mcp.schemas import (
    PriceHistory,
    PricePoint,
    NewsBundle,
    NewsItem,
    CompanyFactsSummary,
)


class FakeAlphaVantageClient:

    async def get_price_history(
        self,
        ticker: str,
    ) -> PriceHistory:

        return PriceHistory(
            ticker=ticker,
            prices=[
                PricePoint(
                    date="2026-08-20",
                    open=100.0,
                    high=105.0,
                    low=99.0,
                    close=103.0,
                    volume=1_000_000,
                ),
                PricePoint(
                    date="2026-08-21",
                    open=103.0,
                    high=108.0,
                    low=102.0,
                    close=107.0,
                    volume=1_200_000,
                ),
            ],
            source_id=f"alpha_vantage:{ticker}:daily",
            source_url="https://fake-alpha-vantage.test",
            date_time=datetime(
                2026,
                8,
                23,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        )

    async def get_recent_news(
        self,
        ticker: str,
    ) -> NewsBundle:

        return NewsBundle(
            ticker=ticker,
            articles=[
                NewsItem(
                    title="Fake test article",
                    summary="Fake news data for testing.",
                    source_id=f"alpha_vantage_news:{ticker}:fake",
                    source_url="https://fake-news.test/article",
                    published_at="20260820T120000",
                    publication_date=date(
                        2026,
                        8,
                        20,
                    ),
                    sentiment_score=0.5,
                )
            ],
        )


class FakeSECEdgarClient:

    async def get_company_facts(
        self,
        ticker: str,
    ) -> CompanyFactsSummary:

        return CompanyFactsSummary(
            ticker=ticker,
            revenue=100_000_000.0,
            net_income=20_000_000.0,
            assets=500_000_000.0,
            liabilities=200_000_000.0,
            source_id="sec_edgar:0000000001:companyfacts",
            source_url="https://fake-sec.test/companyfacts",
        )


@pytest.mark.asyncio
async def test_data_collection_node(
    monkeypatch,
):

    # 把 workflow 里的真实 Alpha Vantage client
    # 临时替换成 fake client
    monkeypatch.setattr(
        workflow,
        "alpha_client",
        FakeAlphaVantageClient(),
    )

    # 把 workflow 里的真实 SEC client
    # 临时替换成 fake client
    monkeypatch.setattr(
        workflow,
        "sec_client",
        FakeSECEdgarClient(),
    )

    state = {
        "ticker": "aapl",
    }

    result = await workflow.data_collection_node(
        state
    )

    # ticker 应该被转换成大写
    assert result["ticker"] == "AAPL"

    # -------------------------
    # Price history
    # -------------------------

    price_history = result["price_history"]

    assert price_history.ticker == "AAPL"
    assert len(price_history.prices) == 2

    assert (
        price_history.prices[0].close
        == 103.0
    )

    assert (
        price_history.prices[1].close
        == 107.0
    )

    # -------------------------
    # News
    # -------------------------

    news = result["news"]

    assert news.ticker == "AAPL"
    assert len(news.articles) == 1

    assert (
        news.articles[0].title
        == "Fake test article"
    )

    assert (
        news.articles[0].sentiment_score
        == 0.5
    )

    # -------------------------
    # Company facts
    # -------------------------

    company_facts = result[
        "company_facts"
    ]

    assert company_facts.ticker == "AAPL"

    assert (
        company_facts.revenue
        == 100_000_000.0
    )

    assert (
        company_facts.net_income
        == 20_000_000.0
    )

    assert (
        company_facts.assets
        == 500_000_000.0
    )

    assert (
        company_facts.liabilities
        == 200_000_000.0
    )