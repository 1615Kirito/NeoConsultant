#Facts 


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
    Convert collected data into evidence items
    that can later be cited by the research agent.
    """

    evidence: list[Evidence] = []

    # ==================================================
    # Price evidence
    # ==================================================

    if price_history.prices:

        latest_price = (
            price_history.prices[-1]
        )

        evidence.append(
            Evidence(
                evidence_id="price_latest",
                source_id=price_history.source_id,
                source_url=price_history.source_url,
                category="price",
                description=(
                    f"{price_history.ticker} "
                    f"closed at "
                    f"${latest_price.close:.2f} "
                    f"on {latest_price.date}."
                ),
            )
        )

    # ==================================================
    # Technical evidence
    # ==================================================

    if technicals.return_30d is not None:

        evidence.append(
            Evidence(
                source_id=price_history.source_id,
                source_url=price_history.source_url,
                evidence_id="technical_return_30d",
                category="technical",
                description=(
                    f"The stock's approximately "
                    f"30-day return was "
                    f"{technicals.return_30d:.2%}."
                ),
            )
        )

    if technicals.sma_20 is not None:

        evidence.append(
            Evidence(
                source_id=price_history.source_id,
                source_url=price_history.source_url,
                evidence_id="technical_sma_20",
                category="technical",
                description=(
                    f"The 20-day simple moving "
                    f"average was "
                    f"${technicals.sma_20:.2f}."
                ),
            )
        )

    if technicals.volatility is not None:

        evidence.append(
            Evidence(
                source_id=price_history.source_id,
                source_url=price_history.source_url,
                evidence_id="technical_volatility",
                category="technical",
                description=(
                    f"Annualized historical "
                    f"volatility was approximately "
                    f"{technicals.volatility:.2%}."
                ),
            )
        )

    if technicals.max_drawdown is not None:

        evidence.append(
            Evidence(
                source_id=price_history.source_id,
                source_url=price_history.source_url,
                evidence_id="technical_max_drawdown",
                category="technical",
                description=(
                    f"Maximum drawdown over the "
                    f"available price history was "
                    f"{technicals.max_drawdown:.2%}."
                ),
            )
        )

    # ==================================================
    # Fundamental evidence
    # ==================================================

    if company_facts.revenue is not None:

        evidence.append(
            Evidence(
                source_id=company_facts.source_id,
                source_url=company_facts.source_url,
                evidence_id="fundamental_revenue",
                category="fundamental",
                description=(
                    f"Reported revenue was "
                    f"${company_facts.revenue:,.0f}."
                ),
            )
        )

    if company_facts.net_income is not None:

        evidence.append(
            Evidence(
                source_id=company_facts.source_id,
                source_url=company_facts.source_url,
                evidence_id="fundamental_net_income",
                category="fundamental",
                description=(
                    f"Reported net income was "
                    f"${company_facts.net_income:,.0f}."
                ),
            )
        )

    if company_facts.assets is not None:

        evidence.append(
            Evidence(
                source_id=company_facts.source_id,
                source_url=company_facts.source_url,
                evidence_id="fundamental_assets",
                category="fundamental",
                description=(
                    f"Reported total assets were "
                    f"${company_facts.assets:,.0f}."
                ),
            )
        )

    if company_facts.liabilities is not None:

        evidence.append(
            Evidence(
                source_id=company_facts.source_id,
                source_url=company_facts.source_url,
                evidence_id="fundamental_liabilities",
                category="fundamental",
                description=(
                    f"Reported total liabilities "
                    f"were "
                    f"${company_facts.liabilities:,.0f}."
                ),
            )
        )

    # ==================================================
    # News evidence
    # ==================================================

    for index, article in enumerate(
        news.articles
    ):

        evidence.append(
            Evidence(
                evidence_id=f"news_{index + 1}",
                category="news",
                description=(
                    f"{article.title}. "
                    f"{article.summary}"
                ),
            )
        )

    return evidence