import asyncio
import datetime
from functools import partial
from time import timezone
from typing import TypedDict

from langgraph import graph
from langgraph.graph import StateGraph, START, END

from typing import TypedDict

from finsight_mcp.schemas import (
    CriticItem,
    PriceHistory,
    NewsBundle,
    CompanyFactsSummary,
    TechnicalSignals,
    ResearchBundle,
    DraftResearchReport,
    CriticResult,
    StockResearchReport,
)
from finsight_mcp.agent.prompts import *

from finsight_mcp.analytics.signals import calculate_technical_signals
from finsight_mcp.clients.alpha_vantage import (
    AlphaVantageClient,
)

from finsight_mcp.clients.sec_edgar import (
    SECEdgarClient,
)

from finsight_mcp.config import settings
from finsight_mcp.llm import llm
from finsight_mcp.mcp_client import MCPToolClient


alpha_client = AlphaVantageClient(settings)
sec_client = SECEdgarClient(settings)


class StockResearchState(TypedDict, total=False):
    # Input
    ticker: str

    # Data Collection
    price_history: PriceHistory
    news: NewsBundle
    company_facts: CompanyFactsSummary

    # Quantitative Analysis
    technicals: TechnicalSignals

    # Evidence Assembly
    research_bundle: ResearchBundle

    # Revision Agent
    revision_count : int
    max_revisions : int

    # Agents
    draft_report: DraftResearchReport
    critique: CriticResult
    final_report: StockResearchReport

from finsight_mcp.evidence import build_evidence #not sure if need to add build_research_bundle


async def data_collection_node(
    state: StockResearchState,
    tools: MCPToolClient,
) -> dict:

    ticker = state["ticker"].upper()

    price_raw, company_facts_raw = await asyncio.gather(
        tools.call(
            "get_price_history",
            {
                "ticker": ticker,
            },
        ),
        tools.call(
            "get_company_facts",
            {
                "ticker": ticker,
            },
        ),
    )

    news_raw = await tools.call(
        "get_recent_news",
        {
            "ticker": ticker,
        },
    )

    price_history = PriceHistory.model_validate(
        price_raw
    )

    company_facts = CompanyFactsSummary.model_validate(
        company_facts_raw
    )

    news = NewsBundle.model_validate(
        news_raw
    )

    return {
        "ticker": ticker,
        "price_history": price_history,
        "news": news,
        "company_facts": company_facts,
    }


def quantitative_analysis_node(
    state: StockResearchState
) -> dict:

    price_history = state["price_history"]

    technicals = calculate_technical_signals(
        price_history
    )

    return {
        "technicals": technicals,
    }

#Evidnec
def evidence_assembly_node(
    state: StockResearchState
) -> dict:

    
    evidence = build_evidence(
        price_history=state["price_history"],
        technicals=state["technicals"],
        company_facts=state["company_facts"],
        news=state["news"],
    )

    research_bundle = ResearchBundle(
        ticker=state["ticker"],
        evidence=evidence,
    )

    return {
        "research_bundle": research_bundle,
    }


async def research_agent(
    state: StockResearchState,
    llm,
) -> dict:

    bundle = state["research_bundle"]

    draft = await llm.generate(
        DraftResearchReport,
        RESEARCH_INSTRUCTIONS,
        {
            "ticker": state["ticker"],
            "evidence": bundle.model_dump(mode="json"),
        },
        "draft_research_report",
    )

    draft.ticker = state["ticker"].upper()

    return {
        "draft_report": draft,
    }



#TODO: Add manual evidence validation in the critic agent: go through evidence's source id, check if it's aligned with the data source id. if not passed, revision.
async def critic_agent(
    state: StockResearchState,
    llm,
) -> dict:

    critique = await llm.generate(
        CriticResult,
        CRITIC_INSTRUCTIONS,
        {
            "ticker": state["ticker"],
            "evidence": state[
                "research_bundle"
            ].model_dump(mode="json"),
            "draft": state[
                "draft_report"
            ].model_dump(mode="json"),
        },
        "critic_result",
    )

    validation_issues = validate_evidence(state)

    if validation_issues:
        critique.issues.extend(validation_issues)
        critique.severity_level = "high"
        critique.quality_score = min(
            critique.quality_score,
            50,
        )

    return {
        "critique": critique,
    }
# Based on the critique + evidence + draft, revision
async def revision_agent(
    state: StockResearchState,
    llm,
) -> dict:

    revised_draft = await llm.generate(
        DraftResearchReport,
        REVISION_INSTRUCTIONS,
        {
            "ticker": state["ticker"],
            "evidence": state[
                "research_bundle"
            ].model_dump(mode="json"),

            "draft": state[
                "draft_report"
            ].model_dump(mode="json"),

            "critique": state[
                "critique"
            ].model_dump(mode="json"),
        },
        "revised_research_report",
    )

    revised_draft.ticker = state["ticker"].upper()

    return {
        "draft_report": revised_draft,
        "revision_count": state.get(
            "revision_count", 0
        ) + 1,
    }


DISCLAIMER = (
    "For research and educational use only; "
    "not personalized investment advice."
)


async def finalizer_agent(
    state: StockResearchState,
    llm,
) -> dict:

    final = await llm.generate(
        StockResearchReport,
        FINALIZER_INSTRUCTIONS,
        {
            "ticker": state["ticker"],
            "evidence": state[
                "research_bundle"
            ].model_dump(mode="json"),
            "draft": state[
                "draft_report"
            ].model_dump(mode="json"),
            "critique": state[
                "critique"
            ].model_dump(mode="json"),
            "required_disclaimer": DISCLAIMER,
        },
        "stock_research_report",
    )

    # Enforce deterministic / system fields
    final.ticker = state["ticker"].upper()

    final.generated_at = datetime.now(
        timezone.utc
    ).isoformat()

    final.disclaimer = DISCLAIMER

    return {
        "final_report": final,
    }

#Helper Functions
def route_after_critic(
    state: StockResearchState
) -> str:

    critique = state["critique"]

    revision_count = state.get(
        "revision_count", 0
    )

    max_revisions = state.get(
        "max_revisions", 2
    )

    # If we have reached the maximum number of revisions, we finalize the report
    if revision_count >= max_revisions:
        return "finalize"

    # If the score is below 80, we route to revision
    if critique.quality_score < 80:
        return "revision"

    if critique.severity_level == "high":
        return "revision"

    return "finalize"


def validate_evidence(
    state: StockResearchState,
) -> list[CriticItem]:

    issues = []

    # Collect all ids
    valid_source_ids = {
        state["price_history"].source_id,
        state["company_facts"].source_id,
    }

    for article in state["news"].articles:
        valid_source_ids.add(article.source_id)

    # 2. check if every source id exists
    valid_evidence_ids = set()

    for evidence in state["research_bundle"].evidence:

        valid_evidence_ids.add(evidence.evidence_id)

        if evidence.source_id not in valid_source_ids:
            issues.append(
                CriticItem(
                    content=(
                        f"Evidence {evidence.evidence_id} "
                        f"references unknown source_id: "
                        f"{evidence.source_id}"
                    ),
                    evidence_id=evidence.evidence_id,
                )
            )

    # 3. Check evidence id
    for citation in state["draft_report"].citations:

        if citation.evidence_id not in valid_evidence_ids:
            issues.append(
                CriticItem(
                    content=(
                        f"Citation references unknown evidence_id: "
                        f"{citation.evidence_id}"
                    ),
                    evidence_id=citation.evidence_id,
                )
            )

    return issues


def build_workflow(
    tools: MCPToolClient,
    llm,
):

    graph = StateGraph(StockResearchState)

    # Define the nodes in the workflow
    graph.add_node(
        "data_collection",
        partial(
            data_collection_node,
            tools=tools,
        ),
    )

    graph.add_node(
        "quantitative_analysis",
        quantitative_analysis_node,
    )

    graph.add_node(
        "evidence_assembly",
        evidence_assembly_node,
    )

    graph.add_node(
        "research",
        partial(
            research_agent,
            llm=llm,
        ),
    )

    graph.add_node(
        "critic",
        partial(
            critic_agent,
            llm=llm,
        ),
    )

    graph.add_node(
        "revision",
        partial(
            revision_agent,
            llm=llm,
        ),
    )

    graph.add_node(
        "finalize",
        partial(
            finalizer_agent,
            llm=llm,
        ),
    )
    
    # Define the edges between nodes 
    graph.add_edge(
        START,
        "data_collection",
    )

    graph.add_edge(
        "data_collection",
        "quantitative_analysis",
    )

    graph.add_edge(
        "quantitative_analysis",
        "evidence_assembly",
    )

    graph.add_edge(
        "evidence_assembly",
        "research",
    )

    graph.add_edge(
        "research",
        "critic",
    )

    #critic may go back to research if risk or score is too low
    # add a revision agent

    graph.add_conditional_edges(
    "critic",
    route_after_critic,
    {
        "revision": "revision",
        "finalize": "finalize",
    }
    )

    graph.add_edge(
        "revision",
        "critic",
    )

    graph.add_edge(
        "finalize",
        END,
    )

    return graph.compile()

