"""The API, called the way the web app will call it, against the real data and model."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

FORECAST = "/users/{}/forecast"


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200 and response.json() == {"status": "ok"}


def test_meta_gives_the_days_a_forecast_can_be_asked_for(client):
    assert client.get("/meta").json() == {"first_day": "2026-01-04", "last_day": "2026-09-30",
                                          "default_day": "2026-08-12", "horizon_days": 30, "data": "synthetic"}


def test_users_lists_all_300_with_their_persona(client):
    users = client.get("/users").json()
    assert len(users) == 300
    assert users[0] == {"user_id": "U0001", "persona": "rider", "persona_label": "Ride-share rider"}
    assert {user["persona"] for user in users} == {"rider", "garment", "student", "shopkeeper", "freelancer"}


def test_forecast_has_the_agreed_shape(client):
    body = client.get(FORECAST.format("U0121"), params={"as_of": "2026-08-12"}).json()
    assert set(body) == {"user_id", "persona", "persona_label", "as_of", "balance", "typical_daily_spending", "cushion",
                         "under_cushion_now", "safe_to_spend", "window_days", "window_until", "safe_to_spend_parts",
                         "income", "alert", "points", "regular_payments", "actions"}
    assert body["user_id"] == "U0121" and body["as_of"] == "2026-08-12" and body["persona"] == "student"
    assert len(body["points"]) == 30 and body["points"][0]["date"] == "2026-08-13"
    for point in body["points"]:
        assert set(point) == {"date", "p10", "p25", "p50", "p75", "p90", "actual"}
        assert 0 <= point["p10"] <= point["p25"] <= point["p50"] <= point["p75"] <= point["p90"]
        assert point["actual"] is not None  # the data covers all 30 days after 12 August
    assert body["safe_to_spend"] >= 0 and body["window_days"] >= 1
    assert set(body["safe_to_spend_parts"]) == {"balance", "cautious_income", "payments_due", "cushion", "savings", "left_over"}
    assert body["income"]["kind"] == "monthly" and body["income"]["next_day"] is not None


def test_a_user_at_risk_gets_an_alert_and_actions(client):
    body = client.get(FORECAST.format("U0121"), params={"as_of": "2026-08-12"}).json()
    assert set(body["alert"]) == {"date", "probability", "gap", "cushion"}
    assert body["alert"]["date"] == "2026-08-23" and body["alert"]["probability"] >= 0.40
    assert body["alert"]["cushion"] == body["cushion"]
    assert body["actions"] and set(body["actions"][0]) == {"id", "title", "effect"}
    assert body["actions"][0]["id"] == "keep_to_safe_spend" and "৳" in body["actions"][0]["title"]


def test_a_comfortable_user_gets_no_alert(client):
    body = client.get(FORECAST.format("U0061"), params={"as_of": "2026-08-12"}).json()
    assert body["alert"] is None
    assert body["regular_payments"] and set(body["regular_payments"][0]) == {"recipient", "label", "date", "amount"}
    assert body["regular_payments"][0]["date"] == "2026-08-13"  # money sent home, due the next day


def test_today_defaults_to_the_demo_day(client):
    assert client.get(FORECAST.format("U0001")).json()["as_of"] == "2026-08-12"


def test_actual_is_empty_when_the_data_ends_today(client):
    body = client.get(FORECAST.format("U0001"), params={"as_of": "2026-09-30"}).json()
    assert all(point["actual"] is None for point in body["points"])
    partly = client.get(FORECAST.format("U0001"), params={"as_of": "2026-09-20"}).json()
    assert [point["actual"] is not None for point in partly["points"]] == [True] * 10 + [False] * 20


def test_later_data_does_not_change_an_earlier_forecast(client):
    # the same question twice gives the same answer; the actual line is the only part that uses later data
    first = client.get(FORECAST.format("U0181"), params={"as_of": "2026-07-15"}).json()
    again = client.get(FORECAST.format("U0181"), params={"as_of": "2026-07-15"}).json()
    assert first == again


def test_unknown_user_is_404(client):
    response = client.get(FORECAST.format("U9999"), params={"as_of": "2026-08-12"})
    assert response.status_code == 404 and "U9999" in response.json()["detail"]


@pytest.mark.parametrize("day", ["2025-12-01", "2026-10-15", "not-a-date"])
def test_a_day_that_cannot_be_forecast_is_422_with_a_reason(client, day):
    response = client.get(FORECAST.format("U0001"), params={"as_of": day})
    assert response.status_code == 422 and response.json()["detail"]


def test_the_web_app_address_is_allowed_and_others_are_not(client):
    allowed = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    other = client.get("/health", headers={"Origin": "http://example.com"})
    assert "access-control-allow-origin" not in other.headers
