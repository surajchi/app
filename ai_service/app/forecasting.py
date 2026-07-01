"""Price forecasting with a linear-trend model + conformal-ish intervals.

Free/self-hosted (numpy + scikit-learn). The interface (series, horizon -> points
+ confidence) is stable, so heavier models (Prophet/LSTM) can replace it later.
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LinearRegression

_WINDOW = 90
_MIN_POINTS = 5


def forecast(series: list[float], horizon: int) -> dict:
    y = np.asarray(series[-_WINDOW:], dtype=float)
    n = y.size

    if n < _MIN_POINTS:
        last = float(y[-1]) if n else 0.0
        points = [
            {"step": i + 1, "mean": last, "low": last * 0.98, "high": last * 1.02}
            for i in range(horizon)
        ]
        return {"points": points, "confidence": 0.2, "model": "naive-v1"}

    x = np.arange(n).reshape(-1, 1)
    model = LinearRegression().fit(x, y)
    scale = abs(float(np.mean(y))) + 1e-9
    # Floor the residual std so intervals are always meaningful (perfect linear
    # fits produce ~0 residuals in floating point).
    residual_std = max(float(np.std(y - model.predict(x))), scale * 0.005)
    r2 = max(0.0, float(model.score(x, y)))

    points = []
    for step in range(1, horizon + 1):
        mean = float(model.predict([[n - 1 + step]])[0])
        band = 1.96 * residual_std * np.sqrt(step)
        points.append(
            {
                "step": step,
                "mean": round(mean, 4),
                "low": round(mean - band, 4),
                "high": round(mean + band, 4),
            }
        )

    stability = 1.0 / (1.0 + residual_std / scale)
    confidence = round(max(0.0, min(1.0, 0.5 * r2 + 0.5 * stability)), 3)
    return {"points": points, "confidence": confidence, "model": "linreg-v1"}
