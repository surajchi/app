"""Portfolio write-side (apply transactions -> holdings) and valuation."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db import transaction as db_transaction
from django.utils import timezone

from apps.markets.models import Instrument
from apps.markets.services import latest_quote
from apps.portfolios.constants import TransactionType
from apps.portfolios.models import Holding, Portfolio, Transaction

_ZERO = Decimal("0")


class InsufficientHoldingError(ValueError):
    """Raised when a sell exceeds the current holding quantity."""


def _q(value: Decimal | float | str) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


@db_transaction.atomic
def apply_transaction(
    *,
    portfolio: Portfolio,
    instrument: Instrument,
    type: str,
    quantity: Decimal,
    price: Decimal,
    fee: Decimal = _ZERO,
    executed_at: Any = None,
    note: str = "",
) -> Transaction:
    """Record a transaction and update the derived holding atomically."""
    quantity, price, fee = _q(quantity), _q(price), _q(fee)
    holding, _ = Holding.objects.select_for_update().get_or_create(
        portfolio=portfolio, instrument=instrument
    )

    if type == TransactionType.SELL and quantity > holding.quantity:
        raise InsufficientHoldingError(f"Cannot sell {quantity}; holding is {holding.quantity}.")

    if type == TransactionType.BUY:
        cost_added = quantity * price + fee
        new_qty = holding.quantity + quantity
        prior_cost = holding.quantity * holding.avg_cost
        holding.avg_cost = (prior_cost + cost_added) / new_qty if new_qty > 0 else _ZERO
        holding.quantity = new_qty
    else:  # SELL
        holding.realized_pnl += quantity * (price - holding.avg_cost) - fee
        holding.quantity -= quantity
        if holding.quantity <= 0:
            holding.quantity = _ZERO
            holding.avg_cost = _ZERO

    holding.save(update_fields=["quantity", "avg_cost", "realized_pnl", "updated_at"])

    return Transaction.objects.create(
        portfolio=portfolio,
        instrument=instrument,
        type=type,
        quantity=quantity,
        price=price,
        fee=fee,
        executed_at=executed_at or timezone.now(),
        note=note,
    )


def _f(value: Decimal) -> float:
    return float(value)


def portfolio_valuation(portfolio: Portfolio) -> dict[str, Any]:
    """Mark holdings to market using the latest cached quotes and total up P&L."""
    holdings = list(
        portfolio.holdings.filter(quantity__gt=0).select_related("instrument__exchange")
    )

    positions: list[dict[str, Any]] = []
    total_mv = _ZERO
    total_cost = _ZERO
    total_realized = _ZERO

    for holding in holdings:
        quote = latest_quote(holding.instrument)
        raw_price = quote.get("price") if quote else None
        priced = raw_price is not None
        price = _q(raw_price) if raw_price is not None else holding.avg_cost
        market_value = holding.quantity * price
        cost_basis = holding.quantity * holding.avg_cost
        unrealized = market_value - cost_basis
        total_mv += market_value
        total_cost += cost_basis
        total_realized += holding.realized_pnl
        positions.append(
            {
                "instrument_id": str(holding.instrument_id),
                "symbol": holding.instrument.symbol,
                "name": holding.instrument.name,
                "quantity": _f(holding.quantity),
                "avg_cost": _f(holding.avg_cost),
                "price": _f(price),
                "priced": priced,
                "market_value": _f(market_value),
                "cost_basis": _f(cost_basis),
                "unrealized_pnl": _f(unrealized),
                "unrealized_pct": _f(unrealized / cost_basis * 100) if cost_basis > 0 else 0.0,
                "realized_pnl": _f(holding.realized_pnl),
            }
        )

    for position in positions:
        position["allocation_pct"] = (
            round(position["market_value"] / _f(total_mv) * 100, 4) if total_mv > 0 else 0.0
        )

    total_unrealized = total_mv - total_cost
    return {
        "portfolio_id": str(portfolio.id),
        "name": portfolio.name,
        "base_currency": portfolio.base_currency,
        "positions": positions,
        "totals": {
            "market_value": _f(total_mv),
            "cost_basis": _f(total_cost),
            "unrealized_pnl": _f(total_unrealized),
            "unrealized_pct": (_f(total_unrealized / total_cost * 100) if total_cost > 0 else 0.0),
            "realized_pnl": _f(total_realized),
            "position_count": len(positions),
        },
    }
