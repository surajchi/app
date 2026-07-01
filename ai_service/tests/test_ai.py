from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_forecast_linear_uptrend():
    series = [float(i) for i in range(1, 61)]  # strictly increasing
    resp = client.post("/forecast", json={"series": series, "horizon": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["points"]) == 5
    assert data["model"] == "linreg-v1"
    assert data["points"][-1]["mean"] > series[-1]  # trend continues up
    assert data["points"][-1]["high"] > data["points"][-1]["low"]
    assert 0.0 <= data["confidence"] <= 1.0


def test_forecast_naive_for_short_series():
    resp = client.post("/forecast", json={"series": [100.0, 101.0], "horizon": 3})
    assert resp.json()["model"] == "naive-v1"
    assert len(resp.json()["points"]) == 3


def test_technical_returns_indicators_and_signal():
    series = [100 + i * 0.5 for i in range(60)]
    data = client.post("/technical", json={"series": series}).json()
    assert "rsi" in data["indicators"]
    assert "macd" in data["indicators"]
    assert data["signal"] in ("buy", "sell", "hold")


def test_technical_short_series_holds():
    data = client.post("/technical", json={"series": [1.0, 2.0, 3.0]}).json()
    assert data["signal"] == "hold"


def test_sentiment_positive_and_negative():
    pos = client.post(
        "/sentiment", json={"text": "stocks surge on strong profit and record growth"}
    ).json()
    assert pos["label"] == "positive"
    neg = client.post(
        "/sentiment", json={"text": "shares plunge on weak losses and downgrade fears"}
    ).json()
    assert neg["label"] == "negative"
