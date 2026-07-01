"""FinPulse AI service — free/self-hosted forecasting, technical analysis, sentiment."""
from __future__ import annotations

from fastapi import Depends, FastAPI

from app import forecasting, sentiment, technical
from app.config import settings
from app.schemas import (
    ForecastRequest,
    ForecastResponse,
    SentimentRequest,
    SentimentResponse,
    TechnicalRequest,
    TechnicalResponse,
)
from app.security import require_service_token

app = FastAPI(title="FinPulse AI Service", version=settings.version)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": settings.version}


@app.post("/forecast", response_model=ForecastResponse, dependencies=[Depends(require_service_token)])
def forecast(request: ForecastRequest) -> dict:
    return forecasting.forecast(request.series, request.horizon)


@app.post(
    "/technical", response_model=TechnicalResponse, dependencies=[Depends(require_service_token)]
)
def technical_analysis(request: TechnicalRequest) -> dict:
    return technical.compute(request.series)


@app.post(
    "/sentiment", response_model=SentimentResponse, dependencies=[Depends(require_service_token)]
)
def analyze_sentiment(request: SentimentRequest) -> dict:
    return sentiment.analyze(request.text)
