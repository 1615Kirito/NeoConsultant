from finsight_mcp.schemas import (
    CompanyFactsSummary,
    Evidence,
    NewsBundle,
    PriceHistory,
    TechnicalSignals,
)


def build_evidence(
    price_history: PriceHistory,
    technicals: TechnicalSignals,
    company_facts: CompanyFactsSummary,
    news: NewsBundle,
) -> list[Evidence]:
    """
    Convert collected and calculated data into concise evidence items.

    Design rules:
    - evidence_id identifies the Evidence item itself.
    - source_id identifies the underlying data source.
    - evidence_id and source_id are independent.
    - Related facts from the same source are grouped when they support
      the same analytical point.
    """

    evidence: list[Evidence] = []
    ticker = price_history.ticker.upper()

    # ==================================================
    # Price evidence
    # ==================================================

    if price_history.prices:
        latest_price = price_history.prices[-1]

        evidence.append(
            Evidence(
                evidence_id=f"{ticker}_price_latest",
                source_id=price_history.source_id,
                source_url=price_history.source_url,
                category="price",
                description=(
                    f"{ticker} closed at ${latest_price.close:.2f} "
                    f"on {latest_price.date}."
                ),
            )
        )

    # ==================================================
    # Technical evidence
    # ==================================================

    momentum_parts: list[str] = []

    if technicals.return_30d is not None:
        momentum_parts.append(
            f"approximately 30-day return was "
            f"{technicals.return_30d:.2%}"
        )

    if technicals.sma_20 is not None:
        momentum_parts.append(
            f"the 20-day simple moving average was "
            f"${technicals.sma_20:.2f}"
        )

    if momentum_parts:
        evidence.append(
            Evidence(
                evidence_id=f"{ticker}_technical_momentum",
                source_id=price_history.source_id,
                source_url=price_history.source_url,
                category="technical",
                description=(
                    f"For {ticker}, "
                    + "; ".join(momentum_parts)
                    + "."
                ),
            )
        )

    risk_parts: list[str] = []

    if technicals.volatility is not None:
        risk_parts.append(
            f"annualized historical volatility was "
            f"approximately {technicals.volatility:.2%}"
        )

    if technicals.max_drawdown is not None:
        risk_parts.append(
            f"maximum drawdown over the available price history "
            f"was {technicals.max_drawdown:.2%}"
        )

    if risk_parts:
        evidence.append(
            Evidence(
                evidence_id=f"{ticker}_technical_risk",
                source_id=price_history.source_id,
                source_url=price_history.source_url,
                category="technical",
                description=(
                    f"For {ticker}, "
                    + "; ".join(risk_parts)
                    + "."
                ),
            )
        )

    # ==================================================
    # Fundamental evidence
    # ==================================================

    fundamental_parts: list[str] = []

    if company_facts.revenue is not None:
        fundamental_parts.append(
            f"reported revenue was ${company_facts.revenue:,.0f}"
        )

    if company_facts.net_income is not None:
        fundamental_parts.append(
            f"reported net income was "
            f"${company_facts.net_income:,.0f}"
        )

    if company_facts.assets is not None:
        fundamental_parts.append(
            f"reported total assets were "
            f"${company_facts.assets:,.0f}"
        )

    if company_facts.liabilities is not None:
        fundamental_parts.append(
            f"reported total liabilities were "
            f"${company_facts.liabilities:,.0f}"
        )

    if fundamental_parts:
        evidence.append(
            Evidence(
                evidence_id=f"{ticker}_fundamental_financials",
                source_id=company_facts.source_id,
                source_url=company_facts.source_url,
                category="fundamental",
                description=(
                    f"For {ticker}, "
                    + "; ".join(fundamental_parts)
                    + "."
                ),
            )
        )

    # ==================================================
    # News evidence
    # ==================================================

    for index, article in enumerate(news.articles, start=1):
        evidence.append(
            Evidence(
                evidence_id=f"{ticker}_news_{index}",
                source_id=article.source_id,
                source_url=article.source_url,
                category="news",
                description=(
                    f"{article.title}. {article.summary}"
                ),
            )
        )

    return evidence
