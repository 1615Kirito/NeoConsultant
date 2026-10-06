import asyncio
from unittest.mock import AsyncMock, Mock
import pytest
from pydantic import ValidationError
from finsight_mcp.evidence import build_evidence
from finsight_mcp.agent import workflow as wf
from finsight_mcp.schemas import Citation, StockScoreBreakdown, CriticResult, TechnicalSignals, ResearchBundle

@pytest.mark.parametrize('scores,expected', [
    ((0, 0, 0, 0, 0), 0), ((100, 100, 100, 100, 100), 100),
    ((80, 70, 90, 60, 75), 77),
    ((100, 0, 0, 0, 0), 15), ((0, 100, 0, 0, 0), 20),
    ((0, 0, 100, 0, 0), 30), ((0, 0, 0, 100, 0), 15),
    ((0, 0, 0, 0, 100), 20),
    ((0, 0, 0, 0, 2), 0), ((0, 0, 0, 0, 3), 1),
    ((10, 0, 0, 0, 0), 2), ((30, 0, 0, 0, 0), 4),
])
def test_score_weights_and_rounding(scores, expected):
    fields = ('price_score', 'technical_score', 'fundamental_score', 'news_score', 'reasoning_score')
    assert wf.calculate_overall_score(StockScoreBreakdown(**dict(zip(fields, scores)))) == expected


def test_attach_urls_overwrites_known_and_preserves_unknown(state):
    report = state['draft_report']
    report.citations[0].source_url = 'https://wrong.example.com'
    report.citations.extend([
        Citation(evidence_id='missing', claim='Unknown'),
        Citation(evidence_id='missing-again', claim='Unknown', source_url='https://keep.example.com'),
        Citation(evidence_id='AAPL_price_latest', claim='Another claim'),
    ])
    result = wf.attach_citation_urls(report, state['research_bundle'])
    assert result is report
    assert [c.source_url for c in result.citations] == [
        'https://example.com/prices', None, 'https://keep.example.com', 'https://example.com/prices']


def test_attach_urls_empty_citations(state):
    state['draft_report'].citations = []
    assert wf.attach_citation_urls(state['draft_report'], state['research_bundle']).citations == []


@pytest.mark.parametrize('bad_source,bad_citation', [(False, False), (True, False), (False, True), (True, True)])
def test_validation_accumulates_issues(state, bad_source, bad_citation):
    if bad_source:
        state['research_bundle'].evidence[0].source_id = 'fake_source'
    if bad_citation:
        state['draft_report'].citations[0].evidence_id = 'missing'
    issues = wf.validate_evidence(state)
    assert len(issues) == int(bad_source) + int(bad_citation)
    if bad_source:
        issue = next(i for i in issues if 'unknown source_id' in i.content)
        assert issue.evidence_id == 'AAPL_price_latest'
        assert 'fake_source' in issue.content and issue.suggestion
    if bad_citation:
        issue = next(i for i in issues if 'unknown evidence_id' in i.content)
        assert issue.evidence_id == 'missing' and issue.suggestion


def test_validation_empty_bundle_and_citations(state):
    state['research_bundle'].evidence = []
    state['draft_report'].citations = []
    assert wf.validate_evidence(state) == []


@pytest.mark.parametrize('quality,severity,count,maximum,expected', [
    (90, 'low', 0, 2, 'finalize'), (80, 'medium', 0, 2, 'finalize'),
    (79, 'low', 0, 2, 'revision'), (90, 'high', 0, 2, 'revision'),
    (50, 'high', 2, 2, 'finalize'), (50, 'high', 3, 2, 'finalize'),
    (50, 'high', 0, 0, 'finalize'), (50, 'low', 1, 2, 'revision'),
])
def test_routing_boundaries(quality, severity, count, maximum, expected):
    critique = CriticResult(conclusion='Review', quality_score=quality, severity_level=severity, issues=[])
    assert wf.route_after_critic(dict(critique=critique, revision_count=count, max_revisions=maximum)) == expected


def test_routing_defaults():
    critique = CriticResult(conclusion='Review', quality_score=79, severity_level='low', issues=[])
    assert wf.route_after_critic({'critique': critique}) == 'revision'
    assert wf.route_after_critic({'critique': critique, 'revision_count': 2}) == 'finalize'


@pytest.mark.parametrize('days', [None, 50])
def test_data_collection_arguments_and_models(data, monkeypatch, days):
    payloads = {name: data[key].model_dump(mode='json') for name, key in [
        ('get_price_history', 'price_history'), ('get_company_facts', 'company_facts'), ('get_recent_news', 'news')]}
    tools = Mock()
    tools.call = AsyncMock(side_effect=lambda name, args: payloads[name])
    monkeypatch.setattr(wf.asyncio, 'sleep', AsyncMock())
    input_state = {'ticker': 'aapl'}
    if days is not None:
        input_state['days'] = days
    result = asyncio.run(wf.data_collection_node(input_state, tools))
    tools.call.assert_any_await('get_price_history', {'ticker': 'AAPL', 'days': 100 if days is None else days})
    tools.call.assert_any_await('get_company_facts', {'ticker': 'AAPL'})
    tools.call.assert_any_await('get_recent_news', {'ticker': 'AAPL'})
    assert tools.call.await_count == 3
    assert result['ticker'] == 'AAPL'
    for key in ('price_history', 'company_facts', 'news'):
        assert result[key] == data[key]
        assert isinstance(result[key], type(data[key]))


def test_data_collection_rejects_invalid_payload(data, monkeypatch):
    payloads = {'get_price_history': {}, 'get_company_facts': data['company_facts'].model_dump(), 'get_recent_news': data['news'].model_dump()}
    tools = Mock(call=AsyncMock(side_effect=lambda name, args: payloads[name]))
    monkeypatch.setattr(wf.asyncio, 'sleep', AsyncMock())
    with pytest.raises(ValidationError):
        asyncio.run(wf.data_collection_node({'ticker': 'AAPL'}, tools))


def test_data_collection_propagates_tool_error(monkeypatch):
    tools = Mock(call=AsyncMock(side_effect=RuntimeError('tool unavailable')))
    monkeypatch.setattr(wf.asyncio, 'sleep', AsyncMock())
    with pytest.raises(RuntimeError, match='tool unavailable'):
        asyncio.run(wf.data_collection_node({'ticker': 'AAPL'}, tools))


def test_quantitative_node_passes_history(data, monkeypatch):
    expected = TechnicalSignals(return_30d=.1)
    calculate = Mock(return_value=expected)
    monkeypatch.setattr(wf, 'calculate_technical_signals', calculate)
    assert wf.quantitative_analysis_node(data) == {'technicals': expected}
    calculate.assert_called_once_with(data['price_history'])


def test_evidence_assembly_passes_inputs(data, monkeypatch):
    expected = build_evidence(**data)
    build = Mock(return_value=expected)
    monkeypatch.setattr(wf, 'build_evidence', build)
    result = wf.evidence_assembly_node(dict(ticker='AAPL', **data))
    build.assert_called_once_with(**data)
    assert result == {'research_bundle': ResearchBundle(ticker='AAPL', evidence=expected)}


