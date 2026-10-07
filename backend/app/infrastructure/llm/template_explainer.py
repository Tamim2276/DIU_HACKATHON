"""The explanation built from fixed sentences. No language model is involved.

Every sentence is written once in English and once in Bangla, with gaps for
the facts. The gaps are filled with the facts and nothing else, so the text
cannot contain a number the model or the rules did not produce.

To change the wording, edit SENTENCES and LABELS below. A gap is a name in
curly brackets, for example {balance}. The Bangla text gets Bangla digits.
"""
from datetime import date

from app.application.ports.explainer import (
    BANGLA,
    BANGLA_DIGITS,
    ENGLISH,
    INCOME_DAILY,
    INCOME_IRREGULAR,
    INCOME_LATER,
    LITTLE_CHANGE,
    LOWERS_CHANCE,
    PAYMENTS_DUE,
    REMOVES_ALERT,
    SPENDING_ABOVE_SAFE,
    TEMPLATE,
    Explainer,
    Facts,
    Reply,
)
from app.domain.services.actions import KEEP_TO_SAFE_SPEND, MOVE_PAYMENT, PAY_DIRECTLY

BULLET = "• "
SMALLEST_AMOUNT = 1.0  # taka; below this an amount would be written as ৳0

SENTENCES = {
    ENGLISH: {
        # no warning
        "clear": "No shortfall warning for the next {days} days.",
        "balance_ok": "Your balance is ৳{balance}, above your safety cushion of ৳{cushion} "
                      "(about a day of your typical spending, rent and other regular payments included).",
        "balance_low": "Your balance is ৳{balance} today, below your safety cushion of ৳{cushion} "
                       "(about a day of your typical spending, rent and other regular payments included), "
                       "but the forecast expects it to rise above that level again.",
        "safe": "You can spend about ৳{safe} a day until {until}.",
        "safe_none": "Until {until} there is no money left over for everyday spending once your regular payments "
                     "are made on time and your safety cushion is kept. Keep it as low as you can.",
        # what is likely to happen
        "alert": "Your wallet may run short around {day}. The chance is about {chance}%.",
        "gap": "In a cautious estimate your balance falls about ৳{gap} below your safety cushion of ৳{cushion} "
              "(about a day of your typical spending, rent and other regular payments included).",
        "gap_empty": "In a cautious estimate your wallet runs empty.",
        "alert_low_now": "Your balance is ৳{balance} today, already below your safety cushion of ৳{cushion} "
                         "(about a day of your typical spending, rent and other regular payments included). "
                         "It may be short again in the next {days} days. The chance is about {chance}%.",
        # why
        "why": "Why:",
        INCOME_LATER: "Your next income is expected on {income_day}, {days_to_income} days from now.",
        INCOME_DAILY: "Your income comes in day by day, not as one amount on a fixed date.",
        INCOME_IRREGULAR: "Your income does not arrive on a fixed date.",
        PAYMENTS_DUE: "Regular payments of ৳{payments} are due by {until}.",
        "payment": "This includes {payment_label}: ৳{payment_amount} on {payment_day}.",
        SPENDING_ABOVE_SAFE: "You usually spend about ৳{usual} a day on everyday things. "
                             "Until {until} your money covers only about ৳{safe} a day.",
        "spending_none": "You usually spend about ৳{usual} a day on everyday things. "
                         "Until {until} there is no money left over for that.",
        # what to do
        "do": "What you can do:",
        KEEP_TO_SAFE_SPEND: "Keep everyday spending to ৳{safe} a day until {until}.",
        MOVE_PAYMENT: "Pay the ৳{move_amount} for {move_label} on {move_to} instead of {move_from}, "
                      "after your income arrives.",
        PAY_DIRECTLY: "Pay shops straight from your wallet instead of cashing out first. "
                      "In the past month you paid about ৳{fees} in cash-out fees.",
        "no_action": "There is no specific step to suggest from your past transactions. "
                     "Keep spending as low as you can until more money comes in.",
        REMOVES_ALERT: "If you do this, the forecast no longer shows a shortfall.",
        LOWERS_CHANCE: "If you do this, the chance falls from about {chance}% to about {chance_after}%.",
        LITTLE_CHANGE: "This helps a little, but the warning stays.",
        "note": "This is a forecast from your past transactions. It is not certain.",
    },
    BANGLA: {
        # no warning
        "clear": "আগামী {days} দিনে টাকার টান পড়ার কোনো সতর্কতা নেই।",
        "balance_ok": "আপনার ব্যালেন্স ৳{balance}, যা নিরাপদ সীমার (৳{cushion}, নিয়মিত খরচসহ আপনার সাধারণ "
                      "একদিনের খরচের সমান) উপরে আছে।",
        "balance_low": "আজ আপনার ব্যালেন্স ৳{balance}, যা নিরাপদ সীমার (৳{cushion}, নিয়মিত খরচসহ আপনার সাধারণ "
                       "একদিনের খরচের সমান) নিচে। তবে পূর্বাভাস অনুযায়ী এটি আবার সীমার উপরে উঠবে।",
        "safe": "{until} পর্যন্ত দিনে প্রায় ৳{safe} খরচ করতে পারেন।",
        "safe_none": "নিয়মিত পেমেন্ট সময়মতো দিলে আর নিরাপদ সীমা ধরে রাখলে {until} পর্যন্ত দৈনন্দিন খরচের জন্য কিছু "
                     "থাকছে না। খরচ যতটা সম্ভব কম রাখুন।",
        # what is likely to happen
        "alert": "{day} নাগাদ আপনার ওয়ালেটে টাকার টান পড়তে পারে। এর সম্ভাবনা প্রায় {chance}%।",
        "gap": "সাবধানী হিসাবে আপনার ব্যালেন্স নিরাপদ সীমার (৳{cushion}, নিয়মিত খরচসহ আপনার সাধারণ একদিনের "
              "খরচের সমান) চেয়ে প্রায় ৳{gap} নিচে নামতে পারে।",
        "gap_empty": "সাবধানী হিসাবে আপনার ওয়ালেট পুরোপুরি খালি হয়ে যেতে পারে।",
        "alert_low_now": "আজ আপনার ব্যালেন্স ৳{balance}, যা এখনই নিরাপদ সীমার (৳{cushion}, নিয়মিত খরচসহ আপনার "
                         "সাধারণ একদিনের খরচের সমান) নিচে। আগামী {days} দিনেও টাকার টান থাকতে পারে। এর সম্ভাবনা "
                         "প্রায় {chance}%।",
        # why
        "why": "কারণ:",
        INCOME_LATER: "আপনার পরের আয় আসার কথা {income_day}, অর্থাৎ আরও {days_to_income} দিন পরে।",
        INCOME_DAILY: "আপনার আয় প্রতিদিন একটু একটু করে আসে, নির্দিষ্ট তারিখে একসাথে আসে না।",
        INCOME_IRREGULAR: "আপনার আয় নির্দিষ্ট কোনো তারিখে আসে না।",
        PAYMENTS_DUE: "{until} পর্যন্ত নিয়মিত পেমেন্ট বাবদ ৳{payments} দিতে হবে।",
        "payment": "এর মধ্যে আছে {payment_label}: {payment_day} ৳{payment_amount}।",
        SPENDING_ABOVE_SAFE: "দৈনন্দিন প্রয়োজনে আপনি সাধারণত দিনে প্রায় ৳{usual} খরচ করেন। "
                             "কিন্তু {until} পর্যন্ত চলতে হলে দিনে প্রায় ৳{safe}-এর বেশি খরচ করা যাবে না।",
        "spending_none": "দৈনন্দিন প্রয়োজনে আপনি সাধারণত দিনে প্রায় ৳{usual} খরচ করেন। "
                         "কিন্তু {until} পর্যন্ত এই খরচের জন্য কোনো টাকা বাকি থাকছে না।",
        # what to do
        "do": "যা করতে পারেন:",
        KEEP_TO_SAFE_SPEND: "{until} পর্যন্ত দৈনন্দিন খরচ দিনে ৳{safe}-এর মধ্যে রাখুন।",
        MOVE_PAYMENT: "{move_label} বাবদ ৳{move_amount} দেওয়ার কথা {move_from}। আয় আসার পরে {move_to} তারিখে দিন।",
        PAY_DIRECTLY: "দোকানে আগে ক্যাশ আউট না করে সরাসরি ওয়ালেট থেকে পেমেন্ট করুন। "
                      "গত এক মাসে ক্যাশ আউটের চার্জ বাবদ আপনার প্রায় ৳{fees} খরচ হয়েছে।",
        "no_action": "আপনার লেনদেন দেখে নির্দিষ্ট কোনো পদক্ষেপ সুপারিশ করা যাচ্ছে না। "
                     "নতুন টাকা না আসা পর্যন্ত খরচ যতটা সম্ভব কম রাখুন।",
        REMOVES_ALERT: "এটি করলে পূর্বাভাসে আর টাকার টান দেখা যায় না।",
        LOWERS_CHANCE: "এটি করলে সম্ভাবনা প্রায় {chance}% থেকে কমে প্রায় {chance_after}% হয়।",
        LITTLE_CHANGE: "এতে কিছুটা উপকার হবে, তবে সতর্কতাটি থেকে যাবে।",
        "note": "এটি আপনার আগের লেনদেনের ভিত্তিতে করা পূর্বাভাস, নিশ্চিত কিছু নয়।",
    },
}

# Names for the regular payments, as they read inside a sentence.
LABELS = {
    ENGLISH: {
        "house_rent": "house rent",
        "mess_rent": "mess rent",
        "shop_rent": "shop rent",
        "send_home": "sending money home",
        "savings_samity": "the savings group (samity)",
        "bike_installment": "the bike installment",
        "electricity": "the electricity bill",
        "internet": "the internet bill",
        "subscriptions": "subscriptions",
        "supplier": "the supplier",
        "grocery": "the grocery shop",
        "food": "food",
        "pharmacy": "the pharmacy",
        "shopping": "shopping",
        "transport": "transport",
    },
    BANGLA: {
        "house_rent": "বাসা ভাড়া",
        "mess_rent": "মেস ভাড়া",
        "shop_rent": "দোকান ভাড়া",
        "send_home": "বাড়িতে টাকা পাঠানো",
        "savings_samity": "সমিতির কিস্তি",
        "bike_installment": "বাইকের কিস্তি",
        "electricity": "বিদ্যুৎ বিল",
        "internet": "ইন্টারনেট বিল",
        "subscriptions": "সাবস্ক্রিপশন",
        "supplier": "সাপ্লায়ারের পাওনা",
        "grocery": "মুদি দোকান",
        "food": "খাবার",
        "pharmacy": "ফার্মেসি",
        "shopping": "কেনাকাটা",
        "transport": "যাতায়াত",
    },
}
OTHER_PAYMENT = {ENGLISH: "a regular payment", BANGLA: "নিয়মিত পেমেন্ট"}  # for a label with no name above

MONTHS = {
    ENGLISH: ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
              "November", "December"),
    BANGLA: ("জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর",
             "নভেম্বর", "ডিসেম্বর"),
}


def _gaps(facts: Facts, language: str) -> dict[str, str]:
    """The facts as they are written inside a sentence: whole taka, whole percent, day and month."""

    def taka(amount: float | None) -> str:
        return "" if amount is None else f"{round(amount):,}"

    def percent(chance: float | None) -> str:
        return "" if chance is None else str(round(chance * 100))

    def day(value: date | None) -> str:
        return "" if value is None else f"{value.day} {MONTHS[language][value.month - 1]}"

    def label(name: str | None) -> str:
        return "" if name is None else LABELS[language].get(name, OTHER_PAYMENT[language])

    action = facts.action
    return {
        "balance": taka(facts.balance),
        "cushion": taka(facts.cushion),
        "days": str(facts.warning_days),
        "safe": taka(facts.safe_to_spend),
        "until": day(facts.window_until),
        "day": day(facts.alert_day),
        "chance": percent(facts.alert_chance),
        "gap": taka(facts.alert_gap),
        "income_day": day(facts.next_income_day),
        "days_to_income": "" if facts.days_to_income is None else str(facts.days_to_income),
        "payments": taka(facts.payments_due),
        "payment_label": label(facts.payment_label),
        "payment_day": day(facts.payment_day),
        "payment_amount": taka(facts.payment_amount),
        "usual": taka(facts.usual_spending),
        "chance_after": percent(facts.chance_after),
        "move_label": label(action.get("label")),
        "move_amount": taka(action.get("amount")),
        "move_from": day(action.get("from")),
        "move_to": day(action.get("to")),
        "fees": taka(action.get("fees_last_30_days")),
    }


def _reason(reason: str, facts: Facts) -> tuple[str, ...]:
    """The sentences that put one reason into words."""
    if reason == PAYMENTS_DUE and facts.payment_label is not None:
        return PAYMENTS_DUE, "payment"
    if reason == SPENDING_ABOVE_SAFE and facts.safe_to_spend < SMALLEST_AMOUNT:
        return ("spending_none",)
    return (reason,)


class TemplateExplainer(Explainer):
    def explain(self, facts: Facts, language: str, question: str | None = None) -> Reply:
        """The standard explanation. Fixed sentences cannot answer a question, so `question` changes nothing."""
        if language not in SENTENCES:
            raise ValueError(f"no sentences written for language {language!r}")
        sentences, gaps = SENTENCES[language], _gaps(facts, language)

        def say(*names: str) -> str:
            return " ".join(sentences[name].format(**gaps) for name in names)

        has_safe_amount = facts.safe_to_spend >= SMALLEST_AMOUNT
        if facts.alert_day is None:
            paragraphs = [say("clear", "balance_low" if facts.under_cushion_now else "balance_ok",
                              "safe" if has_safe_amount else "safe_none")]
        else:
            if facts.under_cushion_now:
                paragraphs = [say("alert_low_now")]
            elif round(facts.alert_gap) >= round(facts.cushion):
                paragraphs = [say("alert", "gap_empty")]  # the whole cushion is gone: the cautious forecast reaches zero
            elif facts.alert_gap >= SMALLEST_AMOUNT:
                paragraphs = [say("alert", "gap")]
            else:
                paragraphs = [say("alert")]
            if facts.reasons:
                reasons = [BULLET + say(*_reason(reason, facts)) for reason in facts.reasons]
                paragraphs.append("\n".join([say("why"), *reasons]))
            step = say("no_action") if facts.action_id is None else say(facts.action_id, facts.outcome)
            paragraphs.append("\n".join([say("do"), BULLET + step]))
        paragraphs.append(say("note"))

        text = "\n\n".join(paragraphs)
        if language == BANGLA:
            text = text.translate(str.maketrans("0123456789", BANGLA_DIGITS))
        return Reply(text, TEMPLATE)
