"""Provider-agnostic raw article + the news provider interface."""

from __future__ import annotations

import dataclasses
import datetime as dt
from typing import Protocol, runtime_checkable


@dataclasses.dataclass(frozen=True)
class RawArticle:
    source: str
    url: str
    title: str
    body: str
    published_at: dt.datetime
    author: str = ""
    image_url: str = ""
    language: str = "en"


@runtime_checkable
class NewsProvider(Protocol):
    name: str

    def fetch(self) -> list[RawArticle]: ...
