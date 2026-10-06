"""Schema contracts: required fields, defaults, bounds and allowed values."""
from datetime import date, datetime

import pytest
from pydantic import ValidationError
from finsight_mcp.schemas import (
    NewsItem, Evidence, TechnicalSignals, CompanyFactsSummary, Citation,
    StockScoreBreakdown, DraftResearchReport, CriticItem, CriticResult,
    StockResearchReport, PriceHistory, ResearchBundle,
)


@pytest.mark.parametrize('field', [
    'price_score', 'technical_score', 'fundamental_score', 'news_score', 'reasoning_score',
])
@pytest.mark.parametrize('value', [-1, 101])
def test_score_breakdown_rejects_out_of_range(field, value):
    payload = dict.fromkeys(StockScoreBreakdown.model_fields, 50)
    payload[field] = value
    with pytest.raises(ValidationError) as exc:
        StockScoreBreakdown.model_validate(payload)
    assert any(e['loc'] == (field,) for e in exc.value.errors())


@pytest.mark.parametrize('value', [0, 100])
def test_score_breakdown_accepts_boundaries(value):
    result = StockScoreBreakdown.model_validate(dict.fromkeys(StockScoreBreakdown.model_fields, value))
    assert all(v == value for v in result.model_dump().values())


@pytest.mark.parametrize('field,value', [
    ('overall_score', -1), ('overall_score', 101),
    ('classification', 'buy'), ('confidence', 'very_high'),
])
def test_draft_rejects_invalid_values(state, field, value):
    payload = state['draft_report'].model_dump()
    payload[field] = value
    with pytest.raises(ValidationError) as exc:
        DraftResearchReport.model_validate(payload)
    assert any(e['loc'] == (field,) for e in exc.value.errors())


@pytest.mark.parametrize('value', [-1, 101])
def test_critic_rejects_out_of_range_quality(value):
    with pytest.raises(ValidationError):
        CriticResult(conclusion='Review', quality_score=value, severity_level='low', issues=[])


def test_critic_rejects_invalid_severity():
    with pytest.raises(ValidationError):
        CriticResult(conclusion='Review', quality_score=80, severity_level='critical', issues=[])


@pytest.mark.parametrize('model,payload,missing', [
    (Citation, {'evidence_id': 'e1', 'claim': 'Claim'}, 'evidence_id'),
    (CriticItem, {'content': 'Issue', 'evidence_id': 'e1', 'suggestion': 'Fix'}, 'suggestion'),
    (Evidence, {'evidence_id': 'e1', 'source_id': 's1', 'source_url': 'https://example.com', 'category': 'news', 'description': 'News'}, 'source_id'),
])
def test_required_fields(model, payload, missing):
    del payload[missing]
    with pytest.raises(ValidationError) as exc:
        model.model_validate(payload)
    assert any(e['loc'] == (missing,) and e['type'] == 'missing' for e in exc.value.errors())


@pytest.mark.parametrize('sentiment', [None, 0, -.4, .72])
def test_news_and_evidence_sentiment(data, sentiment):
    news_payload = data['news'].articles[0].model_dump()
    news_payload['sentiment_score'] = sentiment
    article = NewsItem.model_validate(news_payload)
    evidence = Evidence(evidence_id='e1', source_id=article.source_id,
        source_url=article.source_url, category='news', description='News', sentiment_score=sentiment)
    assert article.sentiment_score == evidence.sentiment_score == sentiment


def test_optional_defaults(data):
    payload = data['news'].articles[0].model_dump()
    del payload['sentiment_score']
    assert NewsItem.model_validate(payload).sentiment_score is None
    assert Evidence(evidence_id='e1', source_id='s1', source_url='https://example.com',
        category='news', description='News').sentiment_score is None
    assert Citation(evidence_id='e1', claim='Claim').source_url is None
    assert all(v is None for v in TechnicalSignals().model_dump().values())
    facts = CompanyFactsSummary(ticker='AAPL', source_id='sec', source_url='https://example.com')
    assert all(getattr(facts, key) is None for key in ('revenue', 'net_income', 'assets', 'liabilities'))


def test_json_payloads_parse_dates_and_nested_models(data):
    history = PriceHistory.model_validate(data['price_history'].model_dump(mode='json'))
    article = NewsItem.model_validate(data['news'].articles[0].model_dump(mode='json'))
    assert isinstance(history.date_time, datetime)
    assert isinstance(article.publication_date, date)
    assert history.prices[0].close == 100
    assert history == data['price_history']


def test_bundle_parses_nested_evidence(state):
    result = ResearchBundle.model_validate(state['research_bundle'].model_dump(mode='json'))
    assert isinstance(result.evidence[0], Evidence)
    assert result == state['research_bundle']


@pytest.mark.parametrize('missing', ['generated_at', 'disclaimer'])
def test_final_report_requires_added_fields(state, missing):
    payload = dict(state['draft_report'].model_dump(), generated_at='2026-10-02T00:00:00Z', disclaimer='Research only')
    del payload[missing]
    with pytest.raises(ValidationError) as exc:
        StockResearchReport.model_validate(payload)
    assert any(e['loc'] == (missing,) for e in exc.value.errors())


def test_final_report_preserves_inherited_fields(state):
    payload = dict(state['draft_report'].model_dump(), generated_at='2026-10-02T00:00:00Z', disclaimer='Research only')
    report = StockResearchReport.model_validate(payload)
    assert report.model_dump() == payload
