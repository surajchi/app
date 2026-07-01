"""Technical indicators + a simple combined signal (pandas/numpy)."""
from __future__ import annotations

import pandas as pd

_MIN_POINTS = 30


def compute(series: list[float]) -> dict:
    s = pd.Series(series, dtype=float)
    if s.size < _MIN_POINTS:
        return {"indicators": {}, "signal": "hold", "strength": 0.0, "model": "ta-v1"}

    price = float(s.iloc[-1])
    sma20 = float(s.rolling(20).mean().iloc[-1])

    ema12 = s.ewm(span=12, adjust=False).mean()
    ema26 = s.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd = float(macd_line.iloc[-1])
    macd_signal = float(signal_line.iloc[-1])

    delta = s.diff()
    gain = float(delta.clip(lower=0).rolling(14).mean().iloc[-1])
    loss = float(-delta.clip(upper=0).rolling(14).mean().iloc[-1])
    rsi = 100.0 if loss == 0 else 100.0 - 100.0 / (1.0 + gain / loss)

    score = 0
    if rsi < 30:
        score += 1
    elif rsi > 70:
        score -= 1
    score += 1 if macd > macd_signal else -1
    score += 1 if price > sma20 else -1

    signal = "buy" if score >= 2 else "sell" if score <= -2 else "hold"
    return {
        "indicators": {
            "price": round(price, 4),
            "sma20": round(sma20, 4),
            "ema12": round(float(ema12.iloc[-1]), 4),
            "ema26": round(float(ema26.iloc[-1]), 4),
            "macd": round(macd, 4),
            "macd_signal": round(macd_signal, 4),
            "rsi": round(rsi, 2),
        },
        "signal": signal,
        "strength": round(abs(score) / 3, 2),
        "model": "ta-v1",
    }
