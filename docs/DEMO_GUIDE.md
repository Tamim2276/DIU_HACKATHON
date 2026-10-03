# Demo guide: showing Agam to the judges

This guide is for the two of you as presenters. For each step it gives what to click, what should appear, and a line you can say. Every figure is for the demo day, 12 August 2026, and was checked against the API.

The whole story in one sentence:

> A student will run short on 23 August. The app sees it 11 days early, and one small change makes the warning go away.

## Before the judges arrive

Do these in order, about ten minutes before.

1. **Open the app.** Use the live address from the deploy guide. On the free host the server sleeps when nobody visits, so open it two or three minutes early and wait for "Connected · 300 customers" at the bottom.
2. **Reset the view.** Go to Home, click the **Student** chip, and click "Back to the demo day" if it shows. The date should read "Wed, 12 Aug 2026".
3. **Set the language to English** with the switch at the top right. You will switch to Bangla during the demo.
4. **Switch off any action** left on in the Actions tab, and remove any savings goal on Home.
5. **Test one question.** On Ask, tap "Why do I run short?". If an answer comes, the assistant is ready. Do not ask more than three or four questions in a minute, or the free limit stops it for a while.
6. **Make it readable.** Press Ctrl and + until the text is easy to read from the back of the room. On a projector, light mode reads better than dark; the app follows the computer's own light or dark setting.
7. **Have a backup.** Keep the app running on a laptop too (see "If something goes wrong"). Open the live address on a phone as well.

## The demo, step by step

About six minutes. The short version below takes three.

### Step 1: the problem (20 seconds, no clicks)

Say:

> Many wallet customers do not earn a fixed salary on a fixed day. Rent and bills still come on fixed dates. They find out they are short only on the day it happens. Agam tells them before.

### Step 2: Home, the warning

| Do | You should see |
| --- | --- |
| Point at the orange card | "You may run short around Sun, 23 Aug", with 45% and ৳679 |
| Point at Safe to spend | ৳34 a day, and "You usually spend about ৳639 a day" |
| Point at Coming up | Internet bill, mess rent ৳4,000 on 7 Sep, income ৳13,360 on 8 Sep |

Say:

> This is a university student. Today he has ৳1,771. His next allowance is 27 days away. At his usual ৳639 a day the money will not last, and the app says so 11 days before it happens.

### Step 3: Home, how the safe amount is worked out

| Do | You should see |
| --- | --- |
| Click "How we worked this out" | ৳1,771 + ৳4,403 − ৳4,510 − ৳745 = ৳920 left for 27 days |

Say:

> This number is not a guess by AI. It is a fixed formula, and every part is on the screen. The AI only predicts the balance. The rules decide what to tell the customer.

### Step 4: Forecast, the chart

| Do | You should see |
| --- | --- |
| Click the **Forecast** tab | A green line, two shaded bands, a dashed cushion line, a "Warning: 23 Aug" marker |
| Hover over 23 August | We expect ৳1,107, could be ৳0 to ৳3,099 |
| Tick "Show what really happened" | A black line appears. On 23 August it reads ৳1,118 |

Say:

> The model does not give one number. It gives a range, because income is uncertain. And because this is test data, we can show what really happened next. The forecast said ৳1,107 for the 23rd. The real balance was ৳1,118.

Do not claim the forecast is always this close. On other days the black line is far from the green one. That is why there is a range.

### Step 5: Actions, the what-if

| Do | You should see |
| --- | --- |
| Click the **Actions** tab | Two actions, both switched off |
| Switch on "Keep to the safe amount" | The card turns green: "With this action, the warning goes away" |
| Point at the table | Chance 45% → under 40%. Lowest balance ৳702 → ৳2,600 |

Say:

> The app does not just warn. It suggests what to do, and shows what that would change before the customer commits. None of the actions is a loan or a paid product.

### Step 6: Ask, in Bangla

| Do | You should see |
| --- | --- |
| Click the **Ask** tab | The explanation in English: what, why, what to do |
| Click **বাংলা** at the top right | The whole app turns Bangla, with Bangla digits |
| Tap "আমার টাকা কেন কম পড়বে?" | After about five seconds, an answer marked as written by AI |

Say:

> Our customers read Bangla, so the whole app works in Bangla. The explanation is fixed text. The follow-up answer is written by a language model, but it only gets this customer's figures, and we check every number in its answer. If one number is wrong, the answer is thrown away.

Switch back to English before the next step if the judges do not read Bangla.

### Step 7: other customers (optional, one minute)

| Do | You should see |
| --- | --- |
| Home, click **Rider** | "Your balance is already low", 75% chance |
| Actions, switch on the first action | "The warning stays, but the risk is lower": 75% → 63% |
| Home, click **Garment worker** | "No warning for the next 14 days" |
| In Savings goal, type 2000 and click "Set goal" | Safe to spend drops from ৳118 to ৳44 a day |

Say:

> The app is honest when it cannot fix the problem: for the rider the warning stays. And a customer with no problem can set a savings goal, which comes out of the safe-to-spend amount.

### Step 8: Model, the evidence

| Do | You should see |
| --- | --- |
| Click the **Model** tab | The orange note: all results come from synthetic data |
| Point at the first chart and table | Model error 3.37, 4.27, 4.86 against 4.71, 5.82, 6.70. Better by 27% to 29% |
| Scroll to "Is the range honest?" | 79% of real balances fell in the range meant to hold 80% |
| Scroll to "Does following the advice help?" | Borrowing ৳1,049 → ৳426 per customer |

Say:

> We tested the model on two months it never saw, against three simple methods. It was 27 to 29 percent better. Then we simulated customers who follow the warnings. They borrowed about 60 percent less and had fewer days with almost nothing to spend. The cost is that they spent about 4 percent less. All of this is on synthetic data, and the screen says so.

### Step 9: close (20 seconds)

Say:

> Agam turns a wallet from a record of the past into a view of the next 30 days. The next step is to test it on real data, with consent, inside a wallet like upay.

## The three-minute version

Keep steps 1, 2, 4, 5 and 6, and one sentence from step 8: "It beat three simple methods by 27 to 29 percent on months it never saw, on synthetic data."

## Who says what

The rules say every member must be able to explain the solution. Split it, but each of you should be able to do the other half.

| Part | Presenter |
| --- | --- |
| Steps 1 to 5: problem, Home, Forecast, Actions | First member |
| Steps 6 to 9: Ask, other customers, Model, close | Second member |
| Questions on the model, the test and the data | Whoever knows that part best, then the other adds |

## What each step shows the judges

| What judges score | Where the demo shows it |
| --- | --- |
| Problem relevance | Step 1, and the warning in step 2 |
| AI and ML depth | Steps 4 and 8: a range forecast, tested against baselines on unseen months |
| Customer and business impact | Steps 5 and 8: the what-if, and the impact test |
| Working prototype | The live address, on a laptop and a phone |
| Innovation | A wallet that looks forward, with a what-if before the customer acts |
| Scalability | See the question on scale below |
| Responsible AI | Steps 3, 6 and 8: fixed rules, checked answers, limits stated on screen |

## Questions judges may ask

Answer in your own words. These are the facts to build the answer from.

**Is the data real?**
No. A program generated 300 customers and one year of transactions. No real customer data was used. The assumptions are listed on the Model screen and in `docs/SYNTHETIC_DATA.md`. So the results show the method works on these patterns. They do not show how it would do with real customers.

**What is the model?**
Gradient-boosted trees from scikit-learn, trained with quantile loss. There are six small models: five give the balance at the 10%, 25%, 50%, 75% and 90% levels, and one gives a cautious estimate of income. They use 29 inputs, all built from the customer's own past transactions: the balance, the day of the month, what happened in the same days of the last three months, the pace of the last 7 and 30 days, and the days before Eid.

**Why a range and not one number?**
Income is uncertain, so one number would be wrong most of the time. The range also gives the chance of a shortfall, which is what the warning uses.

**How was it tested?**
It learned from data up to 30 June 2026 and was tested on forecasts made in July and August: 558,000 forecasts. Sixty of the 300 customers were kept out of training completely. It was compared with three simple methods. Its error was 27% to 29% lower, and 19% to 26% lower for the customers it had never seen.

**Why warn at 40%?**
It is a trade-off, shown in the table on the Model screen. At 40% the warning caught 52% of real shortfalls, 63% of warnings were right, and 11% of safe periods got a false alarm. At 30% it catches more and cries wolf more. At 50% it is right more often and misses more.

**What does the language model do? Can it invent numbers?**
It only answers follow-up questions. It decides nothing: the warning, the safe amount and the actions are fixed before it is called. It gets the customer's figures and the standard explanation, and is told to use nothing else. Every number in its answer is checked against those figures. One unknown number and the answer is thrown away, and the customer sees the standard explanation. This matters: when we tried smaller models, they wrote ৳1,711 for a balance of ৳1,771. That is exactly the kind of answer the check rejects, so those models are not used.

**Can it give bad advice in words?**
The number check cannot catch that. The instructions tell it to recommend only the app's own action and never a loan or a paid product. In our tests it refused questions about loans and unrelated topics. That is a limit we state, not a guarantee.

**Does following the advice help customers?**
We simulated the same 300 customers with and without it. Those who kept to the safe amount on warned days borrowed about 60% less (৳426 against ৳1,049 each). Days with under a quarter of the day's need met fell from 6.3% to 4.1%. Days with under half did not change (7.4% against 7.3%). They spent about 4 points less of what they wanted. The app does not create money. It swaps borrowing for spending less, earlier.

**Where is it weak?**
Warnings are least reliable for shop owners and riders, whose income arrives day by day. The range is too narrow for freelancers. The Model screen marks all three. Also, the warning looks only at the balance: a customer who pays a bill late keeps a higher balance, so a missed payment does not always raise a warning.

**The freelancer shows "No warning" but ৳0 safe to spend. Why?**
The warning comes from the forecast balance, and the forecast expects money to come in. The safe-to-spend formula is stricter: it counts every payment due. The card says so in words. It is the limit described above.

**How would it scale?**
One forecast takes about 17 milliseconds on a laptop, and the model file is about 1 MB. A wallet could compute forecasts once a night for every customer. We have not load-tested it, so say that if asked.

**What about privacy?**
The model uses only amounts, dates and types of transactions. It does not need names or phone numbers. A real launch would need the customer's consent and governed data. Only synthetic figures are sent to the language model in this demo.

**Does it push loans?**
No. The list of actions is closed: keep to the safe amount, move a payment to after income, pay shops directly to save the cash-out fee. There is a test that checks the list.

**Did you use AI tools to build this?**
Answer honestly. The rules allow AI tools and ask you to disclose them when asked. Say which tools you used and for what, then show that you can explain any part of the code.

**What would you do next?**
Test on real, governed data. Add notifications, so the warning reaches the customer without opening the app. Tune the warning for people paid day by day.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| "Starting the server" | The free host is waking up. Wait up to two minutes. Keep talking through step 1 |
| "The server did not answer" | Click "Try again". If it fails twice, switch to the laptop copy |
| Ask says the assistant could not give a checked answer | That is the designed fallback. Say so, show the explanation above it, and try again a minute later |
| The wrong customer or date shows | Home, click **Student**, then "Back to the demo day" |
| The internet is down | Run it on the laptop, as below |

To run it on a laptop, open two Git Bash windows:

```bash
cd ~/Desktop/DIU_HACKATHON/backend
source .venv/Scripts/activate
uvicorn app.main:app
```

```bash
cd ~/Desktop/DIU_HACKATHON/frontend
npm run dev
```

Then open <http://localhost:5173>. The follow-up questions need the internet; everything else works without it.

## Recording the video

Follow the same steps. A few extra points:

- Record at full screen with the browser zoomed in, so the text is readable on a phone.
- Do the reset from "Before the judges arrive" first.
- Never show the `.env` file, the Render settings page or anything else with the key on it.
- Speak the problem before you touch the app, and end on the Model screen.
- Check the organizers' announcement for the length and file format they ask for.
