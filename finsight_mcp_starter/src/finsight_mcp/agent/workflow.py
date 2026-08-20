import asyncio
import datetime
from time import timezone
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from typing import TypedDict

from finsight_mcp.schemas import (
    PriceHistory,
    NewsBundle,
    CompanyFactsSummary,
    TechnicalSignals,
    ResearchBundle,
    DraftResearchReport,
    CriticResult,
    StockResearchReport,
)
from finsight_mcp_starter.src.finsight_mcp.agent.prompts import *

from finsight_mcp_starter.src.finsight_mcp.analytics.signals import calculate_technical_signals
from finsight_mcp_starter.src.finsight_mcp.clients.alpha_vantage import (
    AlphaVantageClient,
)

from finsight_mcp_starter.src.finsight_mcp.clients.sec_edgar import (
    SECEdgarClient,
)

from finsight_mcp_starter.src.finsight_mcp.config import settings


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

from finsight_mcp.evidence import build_evidence, build_research_bundle

#TODO: Add Data Collection Node, Quantitative Analysis Node


async def data_collection_node(
    state: StockResearchState
) -> dict:

    ticker = state["ticker"].upper()

    price_history, news, company_facts = await asyncio.gather(
        alpha_client.get_price_history(ticker),
        alpha_client.get_recent_news(ticker),
        sec_client.get_company_facts(ticker),
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
        technicals=state["technicals"],
        company_facts=state["company_facts"],
        news=state["news"],
        evidence=evidence,
    )

    return {
        "research_bundle": research_bundle,
    }



async def research_agent(
    state: StockResearchState
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

    # deterministic field
    draft.ticker = state["ticker"].upper()

    return {
        "draft_report": draft,
    }

#Add evidence validation in the critic agent: go through evidence's source id, check if it's aligned with the data source id. if not passed, revision.
async def critic_agent(
    state: StockResearchState
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

    return {
        "critique": critique,
    }

# Based on the critique + evidence + draft, revision
async def revision_agent(
    state: StockResearchState
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
    state: StockResearchState
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


def build_workflow():

    graph = StateGraph(StockResearchState)

    # Define the nodes in the workflow
    graph.add_node(
        "data_collection",
        data_collection_node,
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
        research_agent,
    )

    graph.add_node(
        "critic",
        critic_agent,
    )

    graph.add_node(
        "revision",
        revision_agent,
    )

    graph.add_node(
        "finalize",
        finalizer_agent,
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




# def critic_node(state: StockResearchState):

#     draft_report = state["draft_report"]
#     research_bundle = state["research_bundle"]

#     critique = None  # TODO: Critic LLM

#     return {
#         "critique": critique
#     }


# def finalize_node(state: StockResearchState):

#     draft_report = state["draft_report"]
#     critique = state["critique"]

#     final_report = None  # TODO: Finalizer LLM

#     return {
#         "final_report": final_report
#     }

#TODO: Based on the example below, try to implement all three agents (research, critic, finalizer) in the workflow.py file.
# def finalizer_agent(state: AgentState) -> dict:
#         score = ScoringBreakdown.model_validate(state["scores"])
#         source_catalog = state["evidence"]["source_catalog"]
#         citations = [
#             Citation(source_id=s["source_id"], label=s["label"], url=s["url"])
#             for s in source_catalog
#         ]
#         final = await llm.generate(
#             EquityReport,
#             FINALIZER_INSTRUCTIONS,
#             {
#                 "ticker": state["ticker"].upper(),
#                 "as_of": datetime.now(timezone.utc).isoformat(),
#                 "classification_rule": _classification(score.overall),
#                 "deterministic_scores": score.model_dump(mode="json"),
#                 "evidence": state["evidence"],
#                 "draft": state["draft"],
#                 "critique": state["critique"],
#                 "required_citations": [c.model_dump(mode="json") for c in citations],
#                 "required_disclaimer": (
#                     "For research and educational use only; not personalized investment advice."
#                 ),
#             },
#             "equity_research_report",
#         )

#         # Enforce deterministic fields after generation.
#         final.ticker = state["ticker"].upper()
#         final.as_of = datetime.now(timezone.utc)
#         final.classification = _classification(score.overall)  # type: ignore[assignment]
#         final.score = score.overall
#         final.component_scores = score
#         final.citations = citations
#         final.disclaimer = "For research and educational use only; not personalized investment advice."
#         return {"report": final.model_dump(mode="json")}
