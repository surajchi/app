"""Entity extraction + linking to market instruments (dictionary/NER-lite)."""

from __future__ import annotations

import re
from typing import Any

from apps.markets.models import Instrument
from apps.news.constants import EntityType

# Generic name tokens that would over-match if used as link terms.
_STOP_TERMS = {
    "the",
    "and",
    "inc",
    "ltd",
    "corp",
    "co",
    "spot",
    "index",
    "industries",
    "fund",
    "etf",
    "dollar",
    "us",
    "group",
    "limited",
    "plc",
}


def _match_terms(instrument: Instrument) -> set[str]:
    terms = {instrument.symbol.lower()}
    for token in re.findall(r"[a-zA-Z]+", instrument.name.lower()):
        if len(token) >= 4 and token not in _STOP_TERMS:
            terms.add(token)
    return terms


def extract_entities(text: str) -> list[dict[str, Any]]:
    """Return entity dicts linked to instruments mentioned in the text."""
    low = f" {text.lower()} "
    results: list[dict[str, Any]] = []
    for instrument in Instrument.objects.filter(is_active=True).only(
        "id", "symbol", "name", "asset_class"
    ):
        for term in _match_terms(instrument):
            if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", low):
                results.append(
                    {
                        "entity_type": str(EntityType.INSTRUMENT),
                        "entity_text": instrument.symbol,
                        "linked_kind": "instrument",
                        "linked_id": instrument.id,
                        "salience": 1.0,
                    }
                )
                break  # one entity per instrument
    return results
