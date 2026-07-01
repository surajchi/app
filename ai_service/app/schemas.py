"""Pydantic request/response contracts for the AI service."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    series: list[float] = Field(..., description="Chronological close prices (oldest first)")
    horizon: int = Field(7, ge=1, le=60)


class ForecastPoint(BaseModel):
    step: int
    mean: float
    low: float
    high: float


class ForecastResponse(BaseModel):
    points: list[ForecastPoint]
    confidence: float
    model: str


class TechnicalRequest(BaseModel):
    series: list[float]


class TechnicalResponse(BaseModel):
    indicators: dict[str, float | None]
    signal: str
    strength: float
    model: str


class SentimentRequest(BaseModel):
    text: str


class SentimentResponse(BaseModel):
    label: str
    score: float
    confidence: float
    model: str
