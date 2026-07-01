"""Portfolios, per-instrument holdings, and the transaction ledger.

``Holding`` is a derived aggregate kept in sync by ``services.apply_transaction``
from the immutable ``Transaction`` ledger (buys/sells).
"""

from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.markets.models import Instrument
from apps.portfolios.constants import TransactionType
from common.mixins import BaseModel


class Portfolio(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="portfolios"
    )
    name = models.CharField(max_length=80)
    base_currency = models.CharField(max_length=3, default="USD")
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "portfolios"
        ordering = ["-is_default", "name"]
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="uniq_portfolio_user_name"),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.name}"


class Holding(BaseModel):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="holdings")
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE, related_name="holdings")
    quantity = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))
    avg_cost = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal("0"))
    realized_pnl = models.DecimalField(max_digits=24, decimal_places=8, default=Decimal("0"))

    class Meta:
        db_table = "portfolio_holdings"
        ordering = ["instrument__symbol"]
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "instrument"], name="uniq_holding_portfolio_instrument"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.portfolio_id}:{self.instrument_id}:{self.quantity}"


class Transaction(BaseModel):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="transactions")
    instrument = models.ForeignKey(
        Instrument, on_delete=models.CASCADE, related_name="transactions"
    )
    type = models.CharField(max_length=4, choices=TransactionType.choices)
    quantity = models.DecimalField(max_digits=24, decimal_places=8)
    price = models.DecimalField(max_digits=20, decimal_places=8)
    fee = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal("0"))
    executed_at = models.DateTimeField()
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "portfolio_transactions"
        ordering = ["-executed_at"]
        indexes = [
            models.Index(fields=["portfolio", "-executed_at"], name="txn_portfolio_time_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.portfolio_id}:{self.type}:{self.instrument_id}:{self.quantity}"
