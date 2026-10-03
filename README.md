# Agam (আগাম)

A wallet feature that warns you before you run short of money, and tells you what to do about it.

We built Agam for the AI DEV FEST 2026 AI Hackathon (DIU CPC × upay), Track 03: Customer Innovation & Financial Independence. "Agam" means "in advance".

**Live app:** <https://agam-dtw9.onrender.com>

**All data in this project is synthetic.** A program generated every customer and every transaction. No real customer data was used anywhere.

## 1. Project overview

### The problem

A lot of wallet customers in Bangladesh are not paid a fixed salary on a fixed day. Riders are paid per trip, freelancers when a client pays, students when the allowance arrives. Rent and bills still fall on fixed dates. So people find out they are short on the day it happens, and then they delay a payment, go without, or borrow.

A wallet shows the balance and the past transactions. It does not show what is coming.

### What Agam does

Agam reads a customer's past transactions and forecasts their balance for the next 30 days. If a shortfall looks likely in the next two weeks, it warns them early. It also works out how much they can safely spend each day, suggests a step that would help, and shows what that step would change before they take it. It explains all of this in plain Bangla or English.

### One example

A student has ৳1,771 on 12 August. He usually spends about ৳639 a day, and his next allowance is 27 days away. Agam warns him that he may run short around 23 August, tells him he can safely spend ৳34 a day, and shows that keeping to that amount makes the warning go away.

The idea is explained at more length, with this example worked through, in [docs/IDEA.md](docs/IDEA.md).

## 2. Features, and how the AI parts are used

| Feature | What the customer gets | How it is made |
| --- | --- | --- |
| 30-day forecast | A chart of the expected balance with a range around it | Machine learning |
| Shortfall warning | A warning when the chance of a shortfall reaches 40% within 14 days | A fixed rule applied to the forecast |
| Safe to spend | A daily amount that still lets every regular payment be made on time, with the sum behind it shown | A fixed formula, checked for every day until the next income |
| Suggested actions | Up to three steps: keep to the safe amount, move a payment to after income, pay shops directly | Fixed rules |
| What-if | Switch an action on and the forecast redraws | The same rules, run again |
| Explanation | What will happen, why, and what to do, in Bangla or English | Fixed sentences |
| Follow-up questions | A short answer to a typed question | A language model, with every number checked |
| Savings goal | Set an amount and a date; the safe-to-spend amount drops to make room | A fixed formula |
| Bangla mode | The whole app in Bangla, with Bangla digits | Translation in the app |
| Model report | How the model was tested, and where it is weak | Saved test results |

There are two AI parts, and both are kept on a short lead.

**The forecasting model** is a set of gradient-boosted tree models (scikit-learn, quantile loss). Five of them give the balance at the 10%, 25%, 50%, 75% and 90% levels for each of the next 30 days; a sixth gives a cautious estimate of income. They use 29 inputs built from the customer's own history, such as the balance today, the day of the month, and what happened over the same days in the last three months. The model only predicts. Whether to warn, and how much is safe to spend, are decided by fixed rules that anyone can read.

**The language model** (Google Gemini) answers follow-up questions on the Ask screen. It is given the customer's figures and the standard explanation, and told to use nothing else. Before an answer is shown, every number in it is checked against those figures. If one number does not match, the answer is thrown away and the customer sees the standard explanation instead. The app works without a key for the language model; only the follow-up answers are missing.

The app never suggests a loan, new spending or a paid product. A test checks this.

## 3. Technology stack

| Layer | What we used |
| --- | --- |
| Backend | Python 3.12, FastAPI, Uvicorn |
| Model | scikit-learn (`HistGradientBoostingRegressor`), pandas, NumPy, joblib |
| Language model | Google Gemini, called over HTTPS with `httpx` |
| Tests | pytest |
| Frontend | React 19, Vite 8, Recharts |
| Hosting | Render: a web service for the API and a static site for the web app |

Both halves follow clean architecture. In the backend the layers are `domain` (the rules, standard library only), `application` (use cases), `infrastructure` (data, model, language model) and `presentation` (the API). A test fails if a layer imports from a layer it should not.

## 4. Requirements

| Software | Version |
| --- | --- |
| Git | any recent version |
| Python | 3.12 |
| Node.js | 22 or 24 |

Python must be 3.12. The saved model was made with it and may not load on another version.

## 5. Installation and setup

The commands are for Git Bash on Windows. On macOS or Linux, use `python3.12` in place of `py -3.12` and `.venv/bin/activate` in place of `.venv/Scripts/activate`.

```bash
git clone https://github.com/Tamim2276/DIU_HACKATHON.git
cd DIU_HACKATHON
```

Backend:

```bash
cd backend
py -3.12 -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Frontend, in a second terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
```

The data, the trained model and the test results are already in the repository, so nothing has to be generated or trained before the app runs.

A longer version with fixes for common problems is in [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md).

## 6. Environment variables

Backend, in `backend/.env`:

| Name | Purpose | Example value |
| --- | --- | --- |
| `ALLOWED_ORIGINS` | Addresses of the web app that may call the API, separated by commas | `http://localhost:5173` |
| `GEMINI_API_KEY` | Optional. Key for Google Gemini, used for follow-up questions | `your-key-here` |
| `GEMINI_MODELS` | Optional. Gemini models to try, in order, separated by commas | `gemini-3.5-flash,gemini-3.6-flash` |

Frontend, in `frontend/.env.local`:

| Name | Purpose | Example value |
| --- | --- | --- |
| `VITE_API_URL` | Address of the API, with no slash at the end | `http://127.0.0.1:8000` |

On the host only:

| Name | Purpose | Value |
| --- | --- | --- |
| `PYTHON_VERSION` | Python version for the API service | `3.12.12` |
| `NODE_VERSION` | Node version for building the web app | `24.15.0` |

No real key is in the repository. `.env` and `.env.local` are ignored by git.

## 7. Run and build commands

Start the API, from `backend` with the environment active:

```bash
uvicorn app.main:app --reload
```

Start the web app, from `frontend`:

```bash
npm run dev
```

Then open <http://localhost:5173>. Use `localhost`, not `127.0.0.1`: the API only accepts the first spelling.

The API's own documentation, where every call can be tried, is at <http://127.0.0.1:8000/docs>.

Build the web app for production, from `frontend`:

```bash
npm run build
```

The result is in `frontend/dist`. On a host, the API starts with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## 8. Live deployment

**Live app:** <https://agam-dtw9.onrender.com>

**Live API:** <https://agam-api-suu9.onrender.com> (docs at [/docs](https://agam-api-suu9.onrender.com/docs))

The API is on a free plan and sleeps when nobody visits. The first visit after a pause can take about a minute, and the page shows "Starting the server" while it waits.

How to deploy it yourself is in [docs/DEPLOY_GUIDE.md](docs/DEPLOY_GUIDE.md).

## 9. Testing

From `backend` with the environment active:

```bash
python -m pytest -q
```

The last line should read `376 passed`. It takes about half a minute and needs no key and no internet.

The tests cover the data generator, the model's inputs, the forecast, every rule (warning, regular payments, safe to spend, actions, savings goal), the explanation in both languages, the check on the language model's answers, the impact test and every API call. Two of them are worth knowing about:

- One checks that the forecast never uses a transaction dated after "today".
- One checks that no layer of the code imports from a layer it should not.

The web app has no automated tests. To check it by hand, open it and go through the five tabs with the Student chosen: Home shows a warning for Sun, 23 Aug and ৳34 a day; switching on the first action on the Actions tab makes the warning go away.

## 10. Other configuration

### Rebuilding the data, the model and the results

Everything is already in the repository. To rebuild it from scratch, from `backend`:

```bash
python -m scripts.generate_data
python -m scripts.train_model
python -m scripts.evaluate_model
python -m scripts.impact_test
```

The same settings always give the same files. The last command takes about five minutes.

### Settings

The seed, the simulated period, the test period and the day the demo opens on are in `backend/app/infrastructure/config/settings.py`.

### The API

| Call | What it returns |
| --- | --- |
| `GET /health` | Whether the service is up |
| `GET /meta` | The days a forecast can be asked for, and the settings of the warning rule |
| `GET /users` | The 300 synthetic customers |
| `GET /users/{id}/forecast` | The forecast, the warning, safe to spend, payments due and actions |
| `POST /users/{id}/what-if` | The forecast with chosen actions switched on |
| `POST /users/{id}/explain` | The explanation, or the answer to a question |
| `GET /metrics` | The model's test results |
| `GET /impact` | The impact test's results |

### Where things are

```text
backend/
  app/domain/           the rules: warning, safe to spend, actions, savings goal
  app/application/      use cases
  app/infrastructure/   data files, the model, the language model, the simulator
  app/presentation/     the API
  data/                 synthetic customers and transactions
  models/               the trained model
  reports/              test results
  tests/                automated tests
frontend/
  src/domain/           formatting and small rules for the screens
  src/application/      hooks that load data
  src/infrastructure/   calls to the API
  src/presentation/     screens, components and the text in both languages
docs/                   guides and notes
```

## How well it works

All of these come from synthetic data. They show that the method finds the patterns we put into that data. They do not show how it would do with real customers.

The model learned from data up to 30 June 2026 and was tested on 558,000 forecasts made in July and August 2026, months it never saw. Sixty of the 300 customers were kept out of training altogether.

**Against simple methods.** Error is in days of the customer's usual spending; lower is better.

| Days ahead | Model | Best simple method | Model is better by |
| --- | --- | --- | --- |
| 7 | 3.37 | 4.71 | 29% |
| 14 | 4.27 | 5.82 | 27% |
| 30 | 4.86 | 6.70 | 28% |

For the 60 customers the model never saw, it is still better by 19% to 26%.

**The range.** The range meant to hold the real balance 80% of the time held it 79% of the time. The narrower one, meant to hold 50%, held 51%.

**Warnings.** At the 40% level used in the app, the warning caught 52% of real shortfalls, 63% of warnings were right, and 11% of safe periods got a false alarm.

**Following the advice.** We simulated the same 300 customers twice over July and August: once as they were, and once keeping to the safe-to-spend amount on warned days.

| | Without Agam | Following the warnings |
| --- | --- | --- |
| Borrowed per customer | ৳1,049 | ৳367 |
| Days with under a quarter of the day's need met | 6.3% | 4.0% |
| Days with under half of the day's need met | 7.4% | 7.7% |
| Share of wanted spending actually spent | 93.5% | 88.9% |

So following the warnings cut borrowing by about 65% and reduced the worst days, at the price of spending about 5 points less. The third row did not improve; its small rise is within what chance alone gives (between 0.3 points down and 0.9 up). The app does not create money; it swaps borrowing for spending less, earlier.

### Where it is weak

- Warnings are least reliable for small shop owners and ride-share riders, whose income arrives day by day (ranking quality 0.61 and 0.71, against 0.84 overall).
- The range is too narrow for freelancers: it held the real balance 69% of the time instead of 80%.
- The warning looks only at the forecast balance. A customer who pays a bill late keeps a higher balance, so a missed payment does not always raise a warning.
- Safe to spend is often ৳0 for people paid day by day whose wallet is nearly empty: in a sample of July and August days, on 17% of rider days and 24% of shop-owner days. The number is honest, because a payment falls due before the money for it has come in, but the app then has no spending step to offer.
- The amounts and probabilities in the synthetic data are our guesses. They were not fitted to real data.
- The follow-up answers depend on a free language model plan that allows only a few questions a minute.

The assumptions behind the data are listed in full in [docs/SYNTHETIC_DATA.md](docs/SYNTHETIC_DATA.md).

## More to read

| File | What it is for |
| --- | --- |
| [docs/IDEA.md](docs/IDEA.md) | The idea in plain words, with one worked example |
| [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) | Running it on your own computer |
| [docs/DEPLOY_GUIDE.md](docs/DEPLOY_GUIDE.md) | Putting it on the internet |
| [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md) | Showing it to the judges |
| [docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md) | How it was built, step by step |
| [docs/SYNTHETIC_DATA.md](docs/SYNTHETIC_DATA.md) | Every assumption behind the data |
