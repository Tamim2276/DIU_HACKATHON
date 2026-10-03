"""The API, called the way the web app will call it, against the real data and model."""
import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app.application.ports.explainer import numbers_in
from app.application.use_cases.explain_alert import ExplainAlert
from app.infrastructure.config.settings import settings
from app.infrastructure.llm.llm_explainer import LlmExplainer
from app.infrastructure.llm.template_explainer import TemplateExplainer
from app.infrastructure.ml.evaluation import load_metrics
from app.main import app, make_explainer

FORECAST = "/users/{}/forecast"
WHAT_IF = "/users/{}/what-if"
EXPLAIN = "/users/{}/explain"


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200 and response.json() == {"status": "ok"}


def test_meta_gives_the_days_a_forecast_can_be_asked_for(client):
    assert client.get("/meta").json() == {"first_day": "2026-01-04", "last_day": "2026-09-30",
                                          "default_day": "2026-08-12", "horizon_days": 30, "warning_days": 14,
                                          "alert_level": 0.4, "data": "synthetic"}


def test_users_lists_all_300_with_their_persona(client):
    users = client.get("/users").json()
    assert len(users) == 300
    assert users[0] == {"user_id": "U0001", "persona": "rider", "persona_label": "Ride-share rider"}
    assert {user["persona"] for user in users} == {"rider", "garment", "student", "shopkeeper", "freelancer"}


def test_forecast_has_the_agreed_shape(client):
    body = client.get(FORECAST.format("U0121"), params={"as_of": "2026-08-12"}).json()
    assert set(body) == {"user_id", "persona", "persona_label", "as_of", "balance", "typical_daily_spending", "cushion",
                         "under_cushion_now", "safe_to_spend", "window_days", "window_until", "safe_to_spend_parts",
                         "usual_everyday_spending", "savings_goal", "income", "alert", "points", "regular_payments",
                         "actions"}
    assert body["savings_goal"] is None and body["usual_everyday_spending"] == 638.96
    assert body["user_id"] == "U0121" and body["as_of"] == "2026-08-12" and body["persona"] == "student"
    assert len(body["points"]) == 30 and body["points"][0]["date"] == "2026-08-13"
    for point in body["points"]:
        assert set(point) == {"date", "p10", "p25", "p50", "p75", "p90", "actual"}
        assert 0 <= point["p10"] <= point["p25"] <= point["p50"] <= point["p75"] <= point["p90"]
        assert point["actual"] is not None  # the data covers all 30 days after 12 August
    assert body["safe_to_spend"] >= 0 and body["window_days"] >= 1
    assert set(body["safe_to_spend_parts"]) == {"date", "days", "balance", "cautious_income", "payments_due", "cushion",
                                                "savings", "left_over"}
    # for this student the last day of the period is the tightest one
    assert body["safe_to_spend_parts"]["date"] == body["window_until"]
    assert body["safe_to_spend_parts"]["days"] == body["window_days"]
    assert body["income"]["kind"] == "monthly" and body["income"]["next_day"] is not None


def test_a_user_at_risk_gets_an_alert_and_actions(client):
    body = client.get(FORECAST.format("U0121"), params={"as_of": "2026-08-12"}).json()
    assert set(body["alert"]) == {"date", "probability", "gap", "cushion"}
    assert body["alert"]["date"] == "2026-08-23" and body["alert"]["probability"] >= 0.40
    assert body["alert"]["cushion"] == body["cushion"]
    assert body["actions"] and set(body["actions"][0]) == {"id", "title", "effect", "details"}
    assert body["actions"][0]["id"] == "keep_to_safe_spend" and "৳" in body["actions"][0]["title"]
    # the figures behind the sentence, so the web app can write it in Bangla
    assert body["actions"][0]["details"] == {"safe_per_day": 34.0, "usual_per_day": 638.96, "saving_per_day": 604.96,
                                              "until": "2026-09-08"}


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


# ---------- what-if ----------

def test_what_if_changes_the_forecast_and_the_alert(client):
    plain = client.get(FORECAST.format("U0121"), params={"as_of": "2026-08-12"}).json()
    changed = client.post(WHAT_IF.format("U0121"), json={"as_of": "2026-08-12", "actions": ["keep_to_safe_spend"]})
    assert changed.status_code == 200
    body = changed.json()
    assert set(body) == set(plain) | {"applied", "alert_before"}
    assert body["applied"] == ["keep_to_safe_spend"]
    assert body["alert_before"] == plain["alert"] and plain["alert"]["date"] == "2026-08-23"
    assert body["alert"] is None  # keeping to the safe amount removes this user's shortfall
    assert all(now["p50"] > was["p50"] for was, now in zip(plain["points"], body["points"]))
    for unchanged in ("balance", "cushion", "safe_to_spend", "window_days", "regular_payments", "actions"):
        assert body[unchanged] == plain[unchanged]


def test_what_if_with_no_actions_returns_the_plain_forecast(client):
    plain = client.get(FORECAST.format("U0001")).json()
    body = client.post(WHAT_IF.format("U0001"), json={"actions": []}).json()  # no day given: the demo day
    assert body["applied"] == [] and body["as_of"] == "2026-08-12"
    assert body["points"] == plain["points"] and body["alert"] == body["alert_before"] == plain["alert"]


def test_what_if_can_leave_the_alert_in_place(client):
    # this rider's wallet is nearly empty: keeping to the safe amount helps, but the shortfall stays
    body = client.post(WHAT_IF.format("U0024"), json={"as_of": "2026-08-12", "actions": ["keep_to_safe_spend"]}).json()
    assert body["alert_before"] is not None and body["alert"] is not None
    assert body["alert"]["probability"] < body["alert_before"]["probability"]


def test_a_payment_due_before_the_income_arrives_leaves_nothing_safe_to_spend(client):
    # This rider has 1 taka, earns every day, and has 7,300 to send home in two days. Over the whole 14 days
    # the money adds up to about 90 a day. By the day the payment is due it does not, so nothing is safe.
    body = client.get(FORECAST.format("U0001"), params={"as_of": "2026-08-12"}).json()
    parts = body["safe_to_spend_parts"]
    assert body["safe_to_spend"] == 0.0 and body["window_days"] == 14
    assert parts["date"] == "2026-08-14" and parts["days"] == 2 and parts["cushion"] == 0.0
    assert parts["payments_due"] == 7300.0 and parts["left_over"] < 0
    # with no safe amount there is nothing to keep to, so that action is not offered
    assert "keep_to_safe_spend" not in [action["id"] for action in body["actions"]]


def test_what_if_refuses_an_action_that_was_not_suggested(client):
    response = client.post(WHAT_IF.format("U0121"), json={"as_of": "2026-08-12", "actions": ["take_a_loan"]})
    assert response.status_code == 422
    assert "take_a_loan" in response.json()["detail"] and "keep_to_safe_spend" in response.json()["detail"]


def test_what_if_for_an_unknown_user_is_404(client):
    assert client.post(WHAT_IF.format("U9999"), json={"actions": []}).status_code == 404


def prefilled(schema: dict, path: str, method: str) -> dict:
    """What the docs page puts in each parameter box. It reads `example` there; a list of `examples` is ignored."""
    return {p["name"]: p["schema"]["example"] for p in schema["paths"][path][method]["parameters"]
            if "example" in p["schema"]}  # a box with no example, such as the savings goal, starts empty


def test_the_example_the_docs_page_pre_fills_really_works(client):
    schema = client.get("/openapi.json").json()
    body = schema["components"]["schemas"]["WhatIfIn"]["examples"][0]  # for a request body the page reads the list
    assert body["as_of"] == client.get("/meta").json()["default_day"]
    user_id = prefilled(schema, "/users/{user_id}/what-if", "post")["user_id"]
    response = client.post(WHAT_IF.format(user_id), json=body)
    assert response.status_code == 200 and response.json()["applied"] == body["actions"]

    boxes = prefilled(schema, "/users/{user_id}/forecast", "get")
    assert boxes == {"user_id": user_id, "as_of": body["as_of"]}
    assert client.get(FORECAST.format(boxes["user_id"]), params={"as_of": boxes["as_of"]}).status_code == 200

    question = schema["components"]["schemas"]["ExplainIn"]["examples"][0]
    assert prefilled(schema, "/users/{user_id}/explain", "post") == {"user_id": user_id}
    answer = client.post(EXPLAIN.format(user_id), json=question)
    assert answer.status_code == 200 and answer.json()["has_alert"]  # the example shows a warning, in Bangla


# ---------- explanation ----------

def test_explain_gives_the_warning_in_bangla_and_english(client):
    bangla = client.post(EXPLAIN.format("U0121"), json={"as_of": "2026-08-12", "language": "bn"})
    english = client.post(EXPLAIN.format("U0121"), json={"as_of": "2026-08-12", "language": "en"})
    assert bangla.status_code == english.status_code == 200
    bn, en = bangla.json(), english.json()
    assert set(en) == {"user_id", "as_of", "language", "has_alert", "question", "source", "text", "facts"}
    assert en["user_id"] == "U0121" and en["as_of"] == "2026-08-12" and en["has_alert"] and bn["has_alert"]
    assert en["source"] == bn["source"] == "template" and en["question"] is None  # no question: the fixed sentences
    assert (bn["language"], en["language"]) == ("bn", "en") and bn["facts"] == en["facts"]
    assert "23 August" in en["text"] and "২৩ আগস্ট" in bn["text"]
    assert sorted(numbers_in(bn["text"])) == sorted(numbers_in(en["text"]))  # the same figures in both


def test_the_explanation_uses_the_same_figures_as_the_forecast_and_what_if_calls(client):
    forecast = client.get(FORECAST.format("U0121"), params={"as_of": "2026-08-12"}).json()
    facts = client.post(EXPLAIN.format("U0121"), json={"as_of": "2026-08-12", "language": "en"}).json()["facts"]
    alert = forecast["alert"]
    assert (facts["alert_day"], facts["alert_chance"], facts["alert_gap"]) == (alert["date"], alert["probability"], alert["gap"])
    assert (facts["balance"], facts["cushion"]) == (forecast["balance"], forecast["cushion"])
    assert (facts["safe_to_spend"], facts["window_until"]) == (forecast["safe_to_spend"], forecast["window_until"])
    assert facts["payments_due"] == forecast["safe_to_spend_parts"]["payments_due"]
    assert facts["next_income_day"] == forecast["income"]["next_day"]
    assert facts["reasons"] == ["income_later", "payments_due", "spending_above_safe"]
    assert facts["payment_label"] in {payment["label"] for payment in forecast["regular_payments"]}
    # the action it recommends is one of the suggested ones, and what-if agrees about what it does
    assert facts["action_id"] in [action["id"] for action in forecast["actions"]]
    what_if = client.post(WHAT_IF.format("U0121"), json={"as_of": "2026-08-12", "actions": [facts["action_id"]]}).json()
    assert facts["outcome"] == "removes_alert" and what_if["alert"] is None


def test_an_alert_that_stays_is_explained_with_the_chance_that_remains(client):
    facts = client.post(EXPLAIN.format("U0024"), json={"as_of": "2026-08-12", "language": "en"}).json()["facts"]
    what_if = client.post(WHAT_IF.format("U0024"), json={"as_of": "2026-08-12", "actions": [facts["action_id"]]}).json()
    assert facts["under_cushion_now"] and facts["outcome"] == "lowers_chance"
    assert facts["chance_after"] == what_if["alert"]["probability"] < facts["alert_chance"]


def test_a_comfortable_user_gets_the_all_clear(client):
    body = client.post(EXPLAIN.format("U0061"), json={"as_of": "2026-08-12", "language": "en"}).json()
    assert not body["has_alert"] and body["facts"]["alert_day"] is None
    assert body["facts"]["reasons"] == [] and body["facts"]["action_id"] is None
    assert "•" not in body["text"] and "৳8,022" in body["text"]  # no reasons or steps, just where things stand


def test_explain_defaults_to_bangla_on_the_demo_day(client):
    body = client.post(EXPLAIN.format("U0001"), json={}).json()
    assert body["language"] == "bn" and body["as_of"] == "2026-08-12"


def test_explain_refuses_what_it_cannot_do(client):
    assert client.post(EXPLAIN.format("U0121"), json={"language": "fr"}).status_code == 422
    assert client.post(EXPLAIN.format("U9999"), json={"language": "en"}).status_code == 404
    assert client.post(EXPLAIN.format("U0121"), json={"as_of": "2026-10-15", "language": "en"}).status_code == 422
    assert client.post(EXPLAIN.format("U0121"), json={"language": "en", "question": "why? " * 80}).status_code == 422


# ---------- follow-up questions ----------
# The real model is never called in tests: a made-up reply stands in for it, so no key or network is needed.

def with_model(monkeypatch, reply):
    """Make the app answer questions with `reply` as the model's answer. None stands for "no key"."""
    asked = []

    def model(instructions, message):
        asked.append(message)
        return reply

    explainer = LlmExplainer(TemplateExplainer(), None if reply is None else model)
    monkeypatch.setattr(app.state, "explain_alert", ExplainAlert(app.state.get_forecast, explainer))
    return asked


QUESTION = {"as_of": "2026-08-12", "language": "en", "question": "Why do I run short?"}


def test_a_question_is_answered_by_the_model_from_the_users_facts(client, monkeypatch):
    asked = with_model(monkeypatch, "Your next income is expected on 8 September, 27 days from now.")
    body = client.post(EXPLAIN.format("U0121"), json=QUESTION).json()
    assert body["source"] == "llm" and body["question"] == "Why do I run short?"
    assert body["text"] == "Your next income is expected on 8 September, 27 days from now."
    assert "Wallet balance today: ৳1,771" in asked[0] and "Why do I run short?" in asked[0]


def test_an_answer_with_a_made_up_number_is_replaced_by_the_standard_explanation(client, monkeypatch):
    standard = client.post(EXPLAIN.format("U0121"), json={"as_of": "2026-08-12", "language": "en"}).json()
    with_model(monkeypatch, "You will be ৳2,500 short on 23 August.")
    body = client.post(EXPLAIN.format("U0121"), json=QUESTION).json()
    assert body["source"] == "template" and body["text"] == standard["text"]
    assert body["question"] == "Why do I run short?"  # the web app can tell the question was not answered


def test_without_a_key_a_question_gets_the_standard_explanation_and_no_error(client, monkeypatch):
    standard = client.post(EXPLAIN.format("U0121"), json={"as_of": "2026-08-12", "language": "en"}).json()
    with_model(monkeypatch, None)
    response = client.post(EXPLAIN.format("U0121"), json=QUESTION)
    assert response.status_code == 200
    assert response.json()["source"] == "template" and response.json()["text"] == standard["text"]


def test_the_standard_explanation_never_calls_the_model(client, monkeypatch):
    asked = with_model(monkeypatch, "anything")
    body = client.post(EXPLAIN.format("U0121"), json={"as_of": "2026-08-12", "language": "bn"}).json()
    assert body["source"] == "template" and asked == []


def test_the_app_only_uses_a_model_when_a_key_is_set(monkeypatch):
    question = ("U0121", settings.demo_today, "en", "Why do I run short?")
    monkeypatch.setenv("GEMINI_API_KEY", "  ")
    without = ExplainAlert(app.state.get_forecast, make_explainer())
    assert without.execute(*question).source == "template"

    calls = []
    monkeypatch.setenv("GEMINI_API_KEY", "a-key")
    monkeypatch.setenv("GEMINI_MODELS", "model-a, model-b")
    monkeypatch.setattr(main, "gemini", lambda key, models: calls.append((key, models)) or (lambda rules, message: "No."))
    assert ExplainAlert(app.state.get_forecast, make_explainer()).execute(*question).source == "llm"
    assert calls == [("a-key", ("model-a", "model-b"))]


# ---------- savings goal ----------

GOAL = {"goal_amount": 2000, "goal_date": "2026-09-08"}  # 2,000 taka by the next income day, 27 days away


def test_a_savings_goal_lowers_the_safe_to_spend_amount(client):
    plain = client.get(FORECAST.format("U0061"), params={"as_of": "2026-08-12"}).json()
    saving = client.get(FORECAST.format("U0061"), params={"as_of": "2026-08-12", **GOAL}).json()
    assert plain["safe_to_spend"] == 118.0 and saving["safe_to_spend"] == 44.0
    # the whole goal falls inside the 27-day period: 2,000 less to spend, about 74 a day
    assert saving["savings_goal"] == {"amount": 2000.0, "date": "2026-09-08", "per_day": 74.07, "set_aside": 2000.0,
                                      "safe_to_spend_before": 118.0}
    assert saving["safe_to_spend_parts"]["savings"] == 2000.0
    assert saving["safe_to_spend_parts"]["left_over"] == round(plain["safe_to_spend_parts"]["left_over"] - 2000, 2)
    # the forecast itself and the warning do not change
    assert saving["points"] == plain["points"] and saving["alert"] == plain["alert"]


def test_a_goal_further_away_takes_only_its_share_of_the_period(client):
    far = client.get(FORECAST.format("U0061"), params={"as_of": "2026-08-12", "goal_amount": 2000,
                                                       "goal_date": "2026-10-05"}).json()  # 54 days away
    assert far["savings_goal"]["per_day"] == 37.04 and far["savings_goal"]["set_aside"] == 1000.0
    assert 44.0 < far["safe_to_spend"] < 118.0


def test_the_goal_reaches_the_actions_the_what_if_and_the_explanation(client):
    forecast = client.get(FORECAST.format("U0061"), params={"as_of": "2026-08-12", **GOAL}).json()
    keep = next(action for action in forecast["actions"] if action["id"] == "keep_to_safe_spend")
    assert keep["details"]["safe_per_day"] == 44.0
    what_if = client.post(WHAT_IF.format("U0061"), json={"as_of": "2026-08-12", "actions": ["keep_to_safe_spend"], **GOAL})
    assert what_if.status_code == 200 and what_if.json()["safe_to_spend"] == 44.0
    explained = client.post(EXPLAIN.format("U0061"), json={"as_of": "2026-08-12", "language": "en", **GOAL}).json()
    assert explained["facts"]["safe_to_spend"] == 44.0 and "৳44" in explained["text"]


@pytest.mark.parametrize("goal", [
    {"goal_amount": 2000},  # no date
    {"goal_date": "2026-09-08"},  # no amount
    {"goal_amount": 0, "goal_date": "2026-09-08"},
    {"goal_amount": 2000, "goal_date": "2026-08-12"},  # today is too late
    {"goal_amount": 2000, "goal_date": "2028-01-01"},  # more than a year away
    {"goal_amount": "inf", "goal_date": "2026-09-08"},  # not an amount anyone can save
    {"goal_amount": "nan", "goal_date": "2026-09-08"},
])
def test_a_goal_that_cannot_be_used_is_422_with_a_reason(client, goal):
    response = client.get(FORECAST.format("U0061"), params={"as_of": "2026-08-12", **goal})
    assert response.status_code == 422 and response.json()["detail"]
    assert client.post(WHAT_IF.format("U0061"), json={"as_of": "2026-08-12", "actions": [], **goal}).status_code == 422


# ---------- model report ----------

def test_metrics_returns_the_saved_test_results(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.json()
    assert body == load_metrics(settings.report_dir)
    assert all(body["checks"].values())
    assert body["early_warning"]["alert_level_used_in_the_app"] == 0.4


def test_impact_returns_the_saved_impact_results(client):
    path = settings.report_dir / "impact.json"
    response = client.get("/impact")
    if not path.exists():  # the full impact test has not been run on this machine
        assert response.status_code == 503 and "scripts.impact_test" in response.json()["detail"]
        return
    assert response.status_code == 200
    body = response.json()
    assert body == json.loads(path.read_text(encoding="utf-8"))
    assert set(body["runs"]) == {"without", "when_warned", "every_day"}
