from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field


# -------------------------
# Market data
# -------------------------

class PricePoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class PriceHistory(BaseModel):
    ticker: str
    prices: list[PricePoint]
    source_id: str
    source_url: str
    date_time : datetime


# -------------------------
# News
# -------------------------

class NewsItem(BaseModel):
    title: str
    summary: str
    source_id: str
    source_url: str
    published_at: str
    publication_date: date
    sentiment_score: float | None = None


class NewsBundle(BaseModel):
    ticker: str
    articles: list[NewsItem]


# -------------------------
# SEC facts
# -------------------------

class CompanyFactsSummary(BaseModel):
    ticker: str
    revenue: float | None = None
    net_income: float | None = None
    assets: float | None = None
    liabilities: float | None = None
    source_id: str
    source_url: str


# -------------------------
# Analytics
# -------------------------

class TechnicalSignals(BaseModel):
    return_30d: float | None = None
    sma_20: float | None = None
    volatility: float | None = None
    max_drawdown: float | None = None


# -------------------------
# Evidence
# -------------------------

# Is this the same as source ID?
class Evidence(BaseModel):
    evidence_id: str #match source url, source id
    source_id: str
    source_url: str
    category: str
    description: str

# -------------------------
# Research bundle
# -------------------------

class ResearchBundle(BaseModel):
    ticker: str
    technicals: TechnicalSignals
    company_facts: CompanyFactsSummary
    news: NewsBundle
    evidence: list[Evidence]


# -------------------------
# Agent output
# -------------------------

class Citation(BaseModel):
    evidence_id: str #citation id is independent
    claim: str


class DraftResearchReport(BaseModel):
    ticker: str

    #How good the stock is. 0-100
    overall_score: int = Field(ge=0, le=100)

    classification: Literal[
        "positive_watchlist_candidate",
        "neutral_monitor",
        "elevated_risk",
    ]

    confidence: Literal[
        "low",
        "medium",
        "high",
    ]

    summary: str
    catalysts: list[str]
    risks: list[str]
    citations: list[Citation]  #ciations id
    data_gaps: list[str]



# -------------------------
# Should the source id be the same as the evidence id?
# -------------------------

# source id used all the time
class CriticItem(BaseModel):
    content: str
    evidence_id: str

class CriticResult(BaseModel):
    conclusion: str

    #How good the report is written, not how good the stock is. 0-100
    quality_score: int = Field(ge=0, le=100)

    #report specific issue
    issues: list[CriticItem]

    #severity of the issues. 0-100
    severity_level: Literal["low", "medium", "high"]



class StockResearchReport(DraftResearchReport):
    generated_at: str
    disclaimer: str