# deterministic calculations

import math

from finsight_mcp_starter.src.finsight_mcp.schemas import (
    PriceHistory,
    TechnicalSignals,
)


def calculate_technical_signals(
    price_history: PriceHistory,
) -> TechnicalSignals:
    """
    Calculate basic technical indicators from price history.

    Assumes price_history.prices is sorted
    from oldest to newest.
    """

    prices = price_history.prices

    if not prices:
        return TechnicalSignals()

    closes = [
        point.close
        for point in prices
    ]

    # -------------------------
    # 30-day return
    # -------------------------

    return_30d = None

    if len(closes) >= 31:
        current_price = closes[-1]
        price_30d_ago = closes[-31]

        if price_30d_ago != 0:
            return_30d = (
                current_price / price_30d_ago
                - 1
            )

    # -------------------------
    # 20-day simple moving average
    # -------------------------

    sma_20 = None

    if len(closes) >= 20:
        sma_20 = (
            sum(closes[-20:])
            / 20
        )

    # -------------------------
    # Volatility
    # -------------------------

    volatility = None

    if len(closes) >= 2:
        daily_returns = []

        for i in range(1, len(closes)):
            previous = closes[i - 1]
            current = closes[i]

            if previous != 0:
                daily_returns.append(
                    current / previous - 1
                )

        if len(daily_returns) >= 2:
            mean_return = (
                sum(daily_returns)
                / len(daily_returns)
            )

            variance = (
                sum(
                    (r - mean_return) ** 2
                    for r in daily_returns
                )
                / (len(daily_returns) - 1)
            )

            daily_volatility = math.sqrt(
                variance
            )

            # Annualized volatility
            volatility = (
                daily_volatility
                * math.sqrt(252)
            )

    # -------------------------
    # Maximum drawdown
    # -------------------------

    max_drawdown = None

    if closes:
        peak = closes[0]
        worst_drawdown = 0.0

        for price in closes:

            if price > peak:
                peak = price

            if peak != 0:
                drawdown = (
                    price / peak
                    - 1
                )

                if drawdown < worst_drawdown:
                    worst_drawdown = drawdown

        max_drawdown = worst_drawdown

    return TechnicalSignals(
        return_30d=return_30d,
        sma_20=sma_20,
        volatility=volatility,
        max_drawdown=max_drawdown,
    )