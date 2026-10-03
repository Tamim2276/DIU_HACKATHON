"""The fixed-sentence explanation, on hand-made facts.

The tests check what the text says (which facts, which parts), not the exact
wording, so a sentence in SENTENCES can be reworded without touching them.
"""
import re
from dataclasses import replace
from datetime import date
from string import Formatter

import pytest

from app.application.ports.explainer import (
    BANGLA,
    BANGLA_DIGITS,
    ENGLISH,
    INCOME_DAILY,
    INCOME_IRREGULAR,
    INCOME_LATER,
    LANGUAGES,
    LITTLE_CHANGE,
    LOWERS_CHANCE,
    OUTCOMES,
    PAYMENTS_DUE,
    REASONS,
    REMOVES_ALERT,
    SPENDING_ABOVE_SAFE,
    TEMPLATE,
    Facts,
    numbers_in,
    unknown_numbers,
)
from app.domain.services.actions import ACTION_IDS, KEEP_TO_SAFE_SPEND, MOVE_PAYMENT, PAY_DIRECTLY
from app.infrastructure.llm.template_explainer import BULLET, LABELS, MONTHS, SENTENCES, TemplateExplainer

TODAY = date(2026, 8, 12)
PAYDAY = date(2026, 9, 8)

# a comfortable wallet: no warning
CLEAR = Facts(as_of=TODAY, balance=8021.8, cushion=479.4, under_cushion_now=False, warning_days=14,
              safe_to_spend=118.0, window_until=PAYDAY, next_income_day=PAYDAY, days_to_income=27,
              payments_due=4900.0, payment_label="send_home", payment_day=date(2026, 8, 13), payment_amount=4900.0,
              usual_spending=369.17)

# a student likely to run short on 23 August; keeping to the safe amount removes the warning
WARNING = replace(
    CLEAR, balance=1771.4, cushion=744.6, safe_to_spend=34.0,
    alert_day=date(2026, 8, 23), alert_chance=0.4454, alert_gap=678.66,
    reasons=(INCOME_LATER, PAYMENTS_DUE, SPENDING_ABOVE_SAFE),
    payments_due=4510.0, payment_label="mess_rent", payment_day=date(2026, 9, 7), payment_amount=4000.0,
    usual_spending=638.96,
    action_id=KEEP_TO_SAFE_SPEND,
    action={"safe_per_day": 34.0, "usual_per_day": 638.96, "saving_per_day": 604.96, "until": PAYDAY},
    outcome=REMOVES_ALERT,
)

# a rider whose wallet is already empty; the action lowers the chance but the warning stays
LOW_NOW = replace(
    WARNING, balance=0.7, cushion=1020.47, under_cushion_now=True, safe_to_spend=90.0, window_until=date(2026, 8, 26),
    alert_day=date(2026, 8, 13), alert_chance=0.7544, alert_gap=1020.47,
    reasons=(INCOME_DAILY, PAYMENTS_DUE, SPENDING_ABOVE_SAFE), next_income_day=None, days_to_income=None,
    payments_due=10700.0, payment_label="send_home", payment_day=date(2026, 8, 14), payment_amount=7300.0,
    usual_spending=471.32,
    action={"safe_per_day": 90.0, "usual_per_day": 471.32, "saving_per_day": 381.32, "until": date(2026, 8, 26)},
    outcome=LOWERS_CHANCE, chance_after=0.6312,
)

MOVE = replace(WARNING, action_id=MOVE_PAYMENT, outcome=LITTLE_CHANGE,
               action={"recipient": "W-1", "label": "mess_rent", "amount": 4000.0, "from": date(2026, 9, 7),
                       "to": date(2026, 9, 9)})
PAY = replace(WARNING, action_id=PAY_DIRECTLY, outcome=LITTLE_CHANGE,
              action={"fees_last_30_days": 88.9, "saving_per_day": 1.48, "replaced_share": 0.5})
NO_ACTION = replace(WARNING, action_id=None, action={}, outcome=None)
NOTHING_LEFT = replace(LOW_NOW, safe_to_spend=0.0, reasons=(INCOME_IRREGULAR, SPENDING_ABOVE_SAFE),
                       action_id=None, action={}, outcome=None, chance_after=None)
CLEAR_BUT_LOW = replace(CLEAR, balance=467.2, cushion=838.08, under_cushion_now=True, safe_to_spend=0.0)
RUNS_EMPTY = replace(WARNING, alert_gap=744.6)  # the cautious forecast reaches zero: the gap is the whole cushion
TINY_GAP = replace(WARNING, alert_gap=0.3)

EVERY_CASE = {"clear": CLEAR, "clear_but_low": CLEAR_BUT_LOW, "warning": WARNING, "low_now": LOW_NOW, "move": MOVE,
              "pay": PAY, "no_action": NO_ACTION, "nothing_left": NOTHING_LEFT, "runs_empty": RUNS_EMPTY,
              "tiny_gap": TINY_GAP}


def explain(facts: Facts, language: str = ENGLISH) -> str:
    return TemplateExplainer().explain(facts, language).text


def bangla(text: str) -> str:
    return text.translate(str.maketrans("0123456789", BANGLA_DIGITS))


def bullets(text: str) -> list[str]:
    return [line for line in text.split("\n") if line.startswith(BULLET)]


# ---------- every number comes from the facts ----------

@pytest.mark.parametrize("language", LANGUAGES)
@pytest.mark.parametrize("case", EVERY_CASE)
def test_every_number_in_the_text_exists_in_the_facts(case, language):
    facts = EVERY_CASE[case]
    text = explain(facts, language)
    assert numbers_in(text)  # there are numbers to check
    assert unknown_numbers(text, facts) == []


@pytest.mark.parametrize("language", LANGUAGES)
@pytest.mark.parametrize("case", EVERY_CASE)
def test_no_gap_is_left_empty(case, language):
    text = explain(EVERY_CASE[case], language)
    assert "{" not in text and "None" not in text
    assert not re.search(r"৳(?![0-9০-৯])", text)  # every taka sign is followed by an amount
    assert "  " not in text and " ." not in text and " ," not in text


def test_the_check_catches_a_number_that_is_not_a_fact():
    assert unknown_numbers("You will be ৳999 short on 23 August.", WARNING) == [999]
    assert unknown_numbers("আপনার ৳৯৯৯ কম পড়বে।", WARNING) == [999]
    assert unknown_numbers("About ৳678.66 short.", WARNING) == [678.66]  # amounts are written in whole taka
    # a number from the customer's own question may be repeated in the answer
    assert unknown_numbers("৳500 is more than ৳34.", WARNING) == [500]
    assert unknown_numbers("৳500 is more than ৳34.", WARNING, "Can I spend ৳500 tomorrow?") == []


def test_numbers_are_read_in_both_kinds_of_digits():
    assert numbers_in("৳4,510 by 8 September, 45%") == [4510, 8, 45]
    assert numbers_in("৳৪,৫১০, ৮ সেপ্টেম্বর, ৪৫%") == [4510, 8, 45]
    assert numbers_in("no numbers here") == []


def test_the_numbers_a_text_may_use():
    allowed = WARNING.numbers()
    assert {1771, 745, 34, 14, 679, 45, 23, 8, 27, 4510, 4000, 7, 639} <= allowed  # rounded as they are written
    assert 0.4454 not in allowed and 44 not in allowed  # a chance is written as a whole percentage: 45
    assert 0 not in allowed and 1 not in replace(WARNING, under_cushion_now=True).numbers()  # yes/no is not a number


# ---------- what the text says ----------

def test_a_user_with_no_alert_gets_the_all_clear():
    for language in LANGUAGES:
        text, sentences = explain(CLEAR, language), SENTENCES[language]
        assert sentences["why"] not in text and sentences["do"] not in text and bullets(text) == []
        assert text.endswith(sentences["note"])
    english = explain(CLEAR)
    assert "14 days" in english and "৳8,022" in english and "৳479" in english
    assert "৳118" in english and "8 September" in english


def test_the_all_clear_says_so_when_the_balance_is_low_today_or_nothing_is_left_to_spend():
    text = explain(CLEAR_BUT_LOW)
    assert "৳467" in text and "৳838" in text
    assert "৳0" not in text  # "nothing left" is said in words
    assert text != explain(replace(CLEAR_BUT_LOW, under_cushion_now=False))


def test_a_warning_says_what_why_and_what_to_do():
    text = explain(WARNING)
    what, why, do, note = text.split("\n\n")
    assert "23 August" in what and "45%" in what and "৳679" in what and "৳745" in what
    assert why.split("\n")[0] == SENTENCES[ENGLISH]["why"] and len(bullets(why)) == 3
    assert "8 September" in why and "27 days" in why  # the next income
    assert "৳4,510" in why and "mess rent" in why and "৳4,000" in why and "7 September" in why  # payments due
    assert "৳639" in why and "৳34" in why  # usual spending against what the money covers
    assert do.split("\n")[0] == SENTENCES[ENGLISH]["do"] and len(bullets(do)) == 1
    assert "৳34" in do and SENTENCES[ENGLISH][REMOVES_ALERT] in do
    assert note == SENTENCES[ENGLISH]["note"]


def test_the_size_of_the_gap_is_said_in_a_way_that_makes_sense():
    def first(facts):
        return explain(facts).split("\n\n")[0]

    assert "৳679" in first(WARNING) and "৳745" in first(WARNING)
    # a gap as large as the cushion means the wallet is empty: "৳745 below ৳745" would be a puzzle
    assert SENTENCES[ENGLISH]["gap_empty"] in first(RUNS_EMPTY) and "৳745" not in first(RUNS_EMPTY)
    # a gap under one taka is not mentioned
    assert "৳" not in first(TINY_GAP) and "45%" in first(TINY_GAP)


def test_the_bangla_text_says_the_same_things_in_bangla_digits():
    text = explain(WARNING, BANGLA)
    what, why, do, note = text.split("\n\n")
    assert "২৩ আগস্ট" in what and "৪৫%" in what and "৳৬৭৯" in what and "৳৭৪৫" in what
    assert len(bullets(why)) == 3 and "৮ সেপ্টেম্বর" in why and "২৭" in why
    assert "৳৪,৫১০" in why and "মেস ভাড়া" in why and "৳৪,০০০" in why and "৳৬৩৯" in why
    assert len(bullets(do)) == 1 and "৳৩৪" in do
    assert sorted(numbers_in(text)) == sorted(numbers_in(explain(WARNING, ENGLISH)))  # the same figures


@pytest.mark.parametrize("case", EVERY_CASE)
def test_each_language_uses_only_its_own_letters_and_digits(case):
    assert not re.search(r"[0-9A-Za-z]", explain(EVERY_CASE[case], BANGLA))
    assert not re.search(r"[ঀ-৲৴-৿]", explain(EVERY_CASE[case], ENGLISH))  # ৳ is U+09F3


def test_a_balance_already_under_the_cushion_is_said_first():
    text = explain(LOW_NOW)
    what = text.split("\n\n")[0]
    assert "৳1 " in what and "৳1,020" in what and "14 days" in what and "75%" in what
    assert "13 August" not in what  # "today" is said instead of the alert day
    assert "75%" in text.split("\n\n")[2] and "63%" in text.split("\n\n")[2]  # the action lowers the chance


@pytest.mark.parametrize("reason", REASONS)
def test_a_reason_is_only_given_when_it_applies(reason):
    without = explain(replace(WARNING, reasons=()))
    assert SENTENCES[ENGLISH]["why"] not in without and len(bullets(without)) == 1  # only the action
    only = explain(replace(WARNING, reasons=(reason,)))
    assert len(bullets(only)) == 2
    assert bullets(only)[0] not in without


def test_the_largest_payment_is_only_named_when_there_is_one():
    named = explain(WARNING)
    unnamed = explain(replace(WARNING, payment_label=None, payment_day=None, payment_amount=None))
    assert "mess rent" in named and "mess rent" not in unnamed
    assert "৳4,510" in unnamed and "৳4,000" not in unnamed


def test_nothing_left_to_spend_is_said_in_words():
    text = explain(NOTHING_LEFT)
    assert "৳0" not in text and "৳471" in text
    assert SENTENCES[ENGLISH]["no_action"] in text


@pytest.mark.parametrize("facts, expected", [
    (WARNING, ["৳34", "8 September"]),
    (MOVE, ["৳4,000", "mess rent", "7 September", "9 September"]),
    (PAY, ["৳89"]),
])
def test_each_action_is_put_into_words_with_its_figures(facts, expected):
    step = bullets(explain(facts))[-1]
    assert all(part in step for part in expected)


def test_the_outcome_of_the_action_is_said():
    removes, lowers, little = (SENTENCES[ENGLISH][outcome] for outcome in OUTCOMES)
    assert removes in explain(WARNING)
    assert little in explain(MOVE)
    assert "75%" in bullets(explain(LOW_NOW))[-1] and "63%" in bullets(explain(LOW_NOW))[-1]
    assert lowers.format(chance=75, chance_after=63) in explain(LOW_NOW)
    assert not any(outcome in explain(NO_ACTION) for outcome in (removes, little))


# ---------- the sentences themselves ----------

def gaps(sentence: str) -> set[str]:
    return {name for _, name, _, _ in Formatter().parse(sentence) if name}


def test_both_languages_have_the_same_sentences_with_the_same_gaps():
    english, in_bangla = SENTENCES[ENGLISH], SENTENCES[BANGLA]
    assert set(SENTENCES) == set(LANGUAGES) and set(english) == set(in_bangla)
    for name in english:
        assert gaps(english[name]) == gaps(in_bangla[name]), name


def test_every_reason_action_and_outcome_has_a_sentence():
    for language in LANGUAGES:
        assert set(REASONS) | set(ACTION_IDS) | set(OUTCOMES) <= set(SENTENCES[language])


def test_every_payment_label_has_a_name_in_both_languages():
    assert set(LABELS[ENGLISH]) == set(LABELS[BANGLA])
    assert all(len(MONTHS[language]) == 12 for language in LANGUAGES)
    unknown = replace(WARNING, payment_label="something_new")
    assert "something_new" not in explain(unknown) and "something" not in explain(unknown, BANGLA)


def test_amounts_are_written_in_whole_taka_with_separators():
    facts = replace(WARNING, balance=123456.5, under_cushion_now=True)
    assert "৳123,456" in explain(facts) and bangla("৳123,456") in explain(facts, BANGLA)


def test_an_unknown_language_is_refused():
    with pytest.raises(ValueError):
        explain(WARNING, "fr")


def test_the_reply_says_it_came_from_the_fixed_sentences_and_a_question_changes_nothing():
    plain = TemplateExplainer().explain(WARNING, ENGLISH)
    asked = TemplateExplainer().explain(WARNING, ENGLISH, "Why do I run short?")
    assert plain.source == TEMPLATE and asked == plain
