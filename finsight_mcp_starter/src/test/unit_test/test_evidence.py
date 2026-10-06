import pytest
from finsight_mcp.evidence import build_evidence
from finsight_mcp.schemas import TechnicalSignals

@pytest.mark.parametrize('field,value,fragment,evidence_id', [
    ('return_30d', .12, '12.00%', 'AAPL_technical_momentum'),
    ('sma_20', 101.5, '$101.50', 'AAPL_technical_momentum'),
    ('volatility', .25, '25.00%', 'AAPL_technical_risk'),
    ('max_drawdown', -.2, '-20.00%', 'AAPL_technical_risk'),
    ('return_30d', 0, '0.00%', 'AAPL_technical_momentum'),
    ('max_drawdown', 0, '0.00%', 'AAPL_technical_risk'),
])
def test_single_technical_metric(data, field, value, fragment, evidence_id):
    data['technicals'] = TechnicalSignals(**{field: value})
    items = [e for e in build_evidence(**data) if e.category == 'technical']
    assert len(items) == 1
    assert items[0].evidence_id == evidence_id
    assert fragment in items[0].description
    assert items[0].source_id == data['price_history'].source_id
    assert items[0].source_url == data['price_history'].source_url


def test_technical_metrics_grouped_by_point(data):
    data['technicals'] = TechnicalSignals(return_30d=.1, sma_20=100, volatility=.2, max_drawdown=-.3)
    items = [e for e in build_evidence(**data) if e.category == 'technical']
    assert len(items) == 2
    by_id = {e.evidence_id: e.description for e in items}
    assert '10.00%' in by_id['AAPL_technical_momentum']
    assert '$100.00' in by_id['AAPL_technical_momentum']
    assert '20.00%' in by_id['AAPL_technical_risk']
    assert '-30.00%' in by_id['AAPL_technical_risk']


@pytest.mark.parametrize('field,value,fragment', [
    ('revenue', 1234567, 'revenue was $1,234,567'),
    ('net_income', -1000, 'net income was $-1,000'),
    ('assets', 2000, 'assets were $2,000'),
    ('liabilities', 0, 'liabilities were $0'),
])
def test_fundamental_fields(data, field, value, fragment):
    setattr(data['company_facts'], field, value)
    items = [e for e in build_evidence(**data) if e.category == 'fundamental']
    assert len(items) == 1
    assert fragment in items[0].description
    assert (items[0].source_id, items[0].source_url) == ('sec', 'https://example.com/sec')


@pytest.mark.parametrize('sentiment', [.72, -.4, 0, None])
def test_news_passthrough_and_unique_ids(data, sentiment):
    first = data['news'].articles[0]
    first.sentiment_score = sentiment
    data['news'].articles.append(first.model_copy(update={'title': 'Second'}))
    items = [e for e in build_evidence(**data) if e.category == 'news']
    assert [e.evidence_id for e in items] == ['AAPL_news_1', 'AAPL_news_2']
    for item, article in zip(items, data['news'].articles):
        assert item.source_id == article.source_id
        assert item.source_url == article.source_url
        assert item.sentiment_score == sentiment
        assert article.title in item.description and article.summary in item.description


