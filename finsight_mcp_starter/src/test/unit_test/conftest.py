from datetime import datetime, timezone
import pytest
from finsight_mcp.evidence import build_evidence
from finsight_mcp.schemas import (PriceHistory, PricePoint, TechnicalSignals, CompanyFactsSummary, NewsBundle, NewsItem, ResearchBundle, Citation, DraftResearchReport, StockScoreBreakdown)

@pytest.fixture
def data():
    return dict(
        price_history=PriceHistory(ticker='aapl', prices=[
            PricePoint(date='2026-10-01', open=99, high=102, low=98, close=100, volume=10),
            PricePoint(date='2026-10-02', open=100, high=104, low=99, close=103.25, volume=20),
        ], source_id='prices', source_url='https://example.com/prices',
            date_time=datetime(2026, 10, 2, tzinfo=timezone.utc)),
        technicals=TechnicalSignals(),
        company_facts=CompanyFactsSummary(ticker='AAPL', source_id='sec', source_url='https://example.com/sec'),
        news=NewsBundle(ticker='AAPL', articles=[NewsItem(
            title='Launch', summary='New product', source_id='article',
            source_url='https://example.com/news', published_at='20261002T120000',
            publication_date='2026-10-02', sentiment_score=0.72)]),
    )


@pytest.fixture
def state(data):
    return dict(ticker='AAPL', **data,
        research_bundle=ResearchBundle(ticker='AAPL', evidence=build_evidence(**data)),
        draft_report=DraftResearchReport(ticker='AAPL',
            score_breakdown=StockScoreBreakdown(price_score=80, technical_score=70,
                fundamental_score=90, news_score=60, reasoning_score=75),
            overall_score=77, classification='neutral_monitor', confidence='medium',
            summary='Summary', catalysts=[], risks=[], data_gaps=[],
            citations=[Citation(evidence_id='AAPL_price_latest', claim='Latest close')]))


