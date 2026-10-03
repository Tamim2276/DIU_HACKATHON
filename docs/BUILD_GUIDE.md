# Agam build guide

How to build Agam from the empty folder structure to the final submission, one small step at a time.

- **What we are building:** the SRS, at <https://claude.ai/artifact/89817Tm47NrKpKCWBPAo56>
- **Submission deadline:** 4 October 2026, 10:00 AM
- **Written:** 3 October 2026, about 2:00 PM. Nothing was built yet.

## How to use this guide

1. Do the steps in order. Start a step only when the one before it passes its test.
2. Every step has the same four parts:
   - **Build:** what to create and where it goes.
   - **Test:** commands to run and what you should see.
   - **Done when:** the condition for moving on.
   - **Commit:** the commit message to use.
3. Commit and push after every step. The hackathon rules require a step-by-step commit history. One large upload at the end does not count.
4. Before moving on, both of you should be able to explain what the step does. Judges can ask any member.
5. If you build with Claude Code, say "build step N". It builds that step only. Then run the Test commands yourself.

## Time plan

| Part | Steps | Estimate |
| --- | --- | --- |
| A. Setup | 1 to 3 | 30 min |
| B. Data | 4 to 6 | 1.5 h |
| C. Forecast model | 7 to 10 | 2.5 h |
| D. Rules | 11 to 14 | 2 h |
| E. API and first deploy | 15 to 17 | 1.5 h |
| F. Explanation | 18 to 19 | 1 h |
| G. Web app | 20 to 26 | 4 h |
| H. Finish | 28 to 31 | 3.5 h |

That is about 16.5 hours of work. About 20 hours remained when this was written. The estimates are guesses, so protect the end of the schedule:

- **Work in parallel.** After step 15 the shape of the API is fixed. One person can start Part G while the other continues with Parts E and F.
- **Feature freeze at 6:00 AM on 4 October.** After that, only Part H.
- **Everything pushed and submitted by 9:30 AM.**
- **If you are behind, drop in this order:** step 27 (extras), then step 19 (the template from step 18 is enough), then the question box in step 25.

Steps 19 and 27 are optional. Every other step is needed for the Must requirements in the SRS.

## Progress

Tick a step when its test passes and it is committed.

**A. Setup:**

- [x] 1. Check tools
- [x] 2. Git repository and first push
- [x] 3. Virtual environment and packages

**B. Data:**

- [x] 4. Settings and first entities
- [x] 5. Synthetic data generator
- [ ] 6. Reading the data

**C. Forecast model:**

- [ ] 7. Daily panel, features and baselines
- [ ] 8. Train the model
- [ ] 9. Test the model against the baselines
- [ ] 10. Forecaster the app can call

**D. Rules:**

- [ ] 11. Shortfall alert
- [ ] 12. Regular payments and income day
- [ ] 13. Safe to spend
- [ ] 14. Actions and what-if

**E. API:**

- [ ] 15. First endpoints: health, users, forecast
- [ ] 16. Deploy the API
- [ ] 17. What-if and model report endpoints

**F. Explanation:**

- [ ] 18. Template explanation in Bangla and English
- [ ] 19. LLM explanation with fallback (optional)

**G. Web app:**

- [ ] 20. App skeleton connected to the API
- [ ] 21. Home screen
- [ ] 22. Deploy the web app
- [ ] 23. Forecast screen
- [ ] 24. Actions screen
- [ ] 25. Ask screen
- [ ] 26. Model report screen

**H. Finish:**

- [ ] 27. Extras (optional)
- [ ] 28. README
- [ ] 29. Clean clone test
- [ ] 30. Report and video
- [ ] 31. Submit

## Before you start

**Where code goes.** The project follows clean architecture. Imports only point inward.

| Folder in `backend/app` | Holds | May import |
| --- | --- | --- |
| `domain` | Entities and pure rules: alert, safe to spend, actions | nothing from the other three |
| `application` | Use cases, and ports (the interfaces the use cases need) | `domain` |
| `infrastructure` | Real implementations: data files, model, LLM, settings | `application`, `domain` |
| `presentation` | The HTTP API | `application`, `domain` |

`backend/app/main.py` is the one place that connects the real implementations to the use cases.

**Terminals.** Keep two open: one in `backend` with the virtual environment active, one in `frontend`.

**Commands** work the same in Git Bash and PowerShell unless a step shows two versions. The main difference is how you activate the environment, from the `backend` folder:

| Terminal | Activate with |
| --- | --- |
| Git Bash | `source .venv/Scripts/activate` |
| PowerShell | `.\.venv\Scripts\Activate.ps1` |
| macOS or Linux | `source .venv/bin/activate` |

If `python` cannot find a package such as `fastapi`, the environment is not active.

**Backend commands** always run from the `backend` folder with the environment active. The prompt then starts with `(.venv)`.

**Simulated dates.** The synthetic data covers 1 October 2025 to 30 September 2026. The model trains on data up to 30 June 2026 and is tested on July and August 2026. Use `2026-08-12` as "today" when trying things, so you are looking at a date the model never trained on.

**Marker files.** Each folder holds an empty `.gitkeep` or `__init__.py`. Delete a `.gitkeep` when its folder gets a real file. Keep every `__init__.py`.

**Commit command** for every step:

```bash
git add -A
git commit -m "the message given in the step"
git push
```

---

## Part A. Setup

### Step 1. Check tools

**Test:**

```bash
uv --version
node --version
npm --version
git --version
```

**Done when:** all four print a version number, and Node is version 22 or newer.

If `uv` is missing, install it from <https://docs.astral.sh/uv/> or use plain Python as shown in step 3.

No commit for this step.

### Step 2. Git repository and first push

**Build:**

1. Create `.gitignore` in the project root (the folder that holds `backend`, `frontend` and `docs`):

   ```gitignore
   # Python
   .venv/
   __pycache__/
   *.pyc
   .pytest_cache/

   # Secrets
   .env
   .env.*
   !.env.example

   # Node
   node_modules/
   dist/

   # Organizer PDFs in the project root
   /*.pdf
   ```

2. On github.com, create a new **public** repository. Do not add a README, a .gitignore or a license there, because the project already has files.
3. Add your teammate under Settings, Collaborators.
4. In the project root:

   ```bash
   git init -b main
   git add -A
   git commit -m "Add project structure and build guide"
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
   git push -u origin main
   ```

**Test:**

```bash
git status
```

**Done when:** `git status` says "nothing to commit, working tree clean", and the GitHub page shows `backend`, `frontend` and `docs` and no PDFs.

The generated data and the trained model are committed in later steps on purpose. The deployed server needs them.

### Step 3. Virtual environment and packages

**Build:**

In Git Bash:

```bash
cd backend
uv venv .venv --python 3.12
source .venv/Scripts/activate
uv pip install numpy pandas scikit-learn joblib fastapi "uvicorn[standard]" python-dotenv pytest httpx
uv pip freeze > requirements.txt
```

In PowerShell, two lines differ:

```powershell
cd backend
uv venv .venv --python 3.12
.\.venv\Scripts\Activate.ps1
uv pip install numpy pandas scikit-learn joblib fastapi "uvicorn[standard]" python-dotenv pytest httpx
uv pip freeze | Out-File -Encoding ascii requirements.txt
```

Without `uv`, replace `uv venv .venv --python 3.12` with `py -3.12 -m venv .venv`, and `uv pip` with `python -m pip`.

In PowerShell, if activation fails with "running scripts is disabled on this system", run this and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Test:**

```bash
python -c "import sklearn, pandas, fastapi; print('ok', sklearn.__version__, pandas.__version__, fastapi.__version__)"
python --version
```

**Done when:** the first command prints `ok` and three version numbers, and the second prints `Python 3.12.x`. Write that exact Python version down. The host needs it in step 16.

Both of you must use the same Python version and the same `requirements.txt`. The saved model only loads reliably when the scikit-learn version matches. Your teammate sets up after cloning with:

```bash
cd backend
uv venv .venv --python 3.12
source .venv/Scripts/activate
uv pip install -r requirements.txt
```

**Commit:** `Add Python environment and dependencies`

---

## Part B. Data

### Step 4. Settings and first entities

**Build:**

- `app/infrastructure/config/settings.py`: one place for the data, model and report folders, the random seed, the simulated date range, the 30-day forecast length, the train and test dates, and the assumed cash-out fee rate.
- `app/domain/entities/transaction.py` and `user.py`: plain data classes with no imports from other layers.
- `tests/unit/test_entities.py`: creates one of each.
- `tests/unit/test_architecture.py`: fails if a file in `domain` imports from `application`, `infrastructure` or `presentation`, or if a file in `application` imports from `infrastructure` or `presentation`. This keeps the architecture honest for the rest of the build.

**Test:**

```bash
python -m pytest tests/unit -q
```

**Done when:** all tests pass.

**Commit:** `Add settings, Transaction and User entities, architecture test`

### Step 5. Synthetic data generator

**Build:**

- `app/infrastructure/synthetic/personas.py`: the five personas from SRS section 2. For each: how income arrives, regular payments, and the share of spending done in cash.
- `app/infrastructure/synthetic/generator.py`: simulates each user day by day and includes the patterns from SRS section 6. It also records the hidden truth for every day.
- `scripts/generate_data.py`: writes `data/users.csv`, `data/transactions.csv.gz`, `data/truth_daily.csv.gz` (the hidden truth per day) and `data/user_truth.csv` (each user's hidden settings, including their regular payments), then prints a summary.
- `docs/SYNTHETIC_DATA.md`: every assumption, in plain words.
- `tests/integration/test_generator.py`: the same seed gives the same data; each user's balance can be rebuilt from their transactions; no balance goes below zero.

**Test:**

```bash
python -m scripts.generate_data
python -m pytest tests/integration/test_generator.py -q
python -c "import pandas as pd; print(pd.read_csv('data/transactions.csv.gz').head(20))"
```

You should see about 300 users and roughly 200,000 to 250,000 transactions, generated in under a minute. The summary shows, per persona, the average monthly income and the share of days users ran short. Every persona should run short on some days but not on most days.

**Done when:** the tests pass, and the transactions of one user look believable when you read them.

**Commit:** `Add synthetic data generator and generated data`

### Step 6. Reading the data

**Build:**

- `app/application/ports/transaction_repository.py`: the interface. List the users; get one user's transactions up to a given date.
- `app/infrastructure/repositories/csv_transaction_repository.py`: reads the files from step 5.
- `tests/integration/test_repository.py`.

**Test:**

```bash
python -m pytest tests/integration/test_repository.py -q
```

**Done when:** the tests pass. They check that 300 users are listed and that asking for transactions up to `2026-08-12` returns nothing after that date.

**Commit:** `Add transaction repository`

---

## Part C. Forecast model

### Step 7. Daily panel, features and baselines

**Build:**

- `app/infrastructure/ml/panel.py`: for each user and day, money in, money out and the end-of-day balance.
- `app/infrastructure/ml/features.py`: the inputs from SRS section 5.3, for a user, a "today" and a number of days ahead. It may use data up to "today" only.
- `app/infrastructure/ml/baselines.py`: the three baselines from SRS section 5.4.
- `tests/integration/test_features.py`: the leak test. Change every transaction after "today" and check that the features do not change.

**Test:**

```bash
python -m pytest tests/integration/test_features.py -q
```

**Done when:** the leak test passes. This is the most important test in the project. If the model can see the future, every result after this step is wrong.

**Commit:** `Add daily panel, forecast features and baselines`

### Step 8. Train the model

**Build:**

- `app/infrastructure/ml/training.py`: gradient-boosted quantile models (scikit-learn `HistGradientBoostingRegressor` with `loss="quantile"`). Five predict the net flow at P10, P25, P50, P75 and P90. One predicts money coming in at P25, which the safe-to-spend formula uses as the cautious income. Training uses only forecasts whose 30-day window ends on or before 30 June 2026.
- `scripts/train_model.py`: trains and saves `models/forecaster.joblib`.

**Test:**

```bash
python -m scripts.train_model
```

It prints the number of training rows, the time for each model and the size of the saved file. Expect a few minutes in total. If it runs longer than about 10 minutes, train on every third day instead of every day.

**Done when:** `models/forecaster.joblib` exists.

**Commit:** `Add model training and trained forecaster`

### Step 9. Test the model against the baselines

**Build:**

- `app/infrastructure/ml/evaluation.py`: the measures from SRS section 5.5, on forecasts that start between 1 July and 31 August 2026.
- `scripts/evaluate_model.py`: prints a table and writes `reports/metrics.json`.

**Test:**

```bash
python -m scripts.evaluate_model
```

**Done when:**

- The model's average error is lower than all three baselines at 7, 14 and 30 days.
- The real balance falls between P10 and P90 in 70% to 90% of cases.
- Early warning is better than the three-month baseline.

If the model loses to a baseline, spend at most one hour on the features and settings. If it still loses, write the result down as it is and continue. The SRS says we report it.

**Commit:** `Add model evaluation against baselines`

### Step 10. Forecaster the app can call

**Build:**

- `app/domain/entities/forecast.py`: a `Forecast` with 30 points (date, P10, P50, P90) and the cautious income.
- `app/application/ports/forecaster.py`: the interface. Given a user's transactions and a "today", return a `Forecast`.
- `app/infrastructure/ml/quantile_forecaster.py`: loads the saved model, builds the features and returns a `Forecast`.
- `tests/integration/test_forecaster.py`.

**Test:**

```bash
python -m pytest tests/integration/test_forecaster.py -q
```

**Done when:** the tests pass. They check that there are 30 points, that P10 is never above P50 and P50 never above P90, that one forecast takes under 2 seconds, and that changing data after "today" does not change the forecast.

**Commit:** `Add forecaster port and model adapter`

---

## Part D. Rules

These are pure functions in `domain`. They need no files, no model and no network, so their tests run in milliseconds.

### Step 11. Shortfall alert

**Build:**

- `app/domain/entities/alert.py`: date, gap in taka, probability.
- `app/domain/services/shortfall.py`: takes a forecast and the safety cushion and returns an alert or nothing. The cushion is one day of the user's typical spending.
- `tests/unit/test_shortfall.py`: a hand-made forecast that dips below the cushion gives an alert with the right date and gap; one that stays above gives none.

**Test:**

```bash
python -m pytest tests/unit -q
```

**Done when:** all unit tests pass, including the architecture test from step 4.

**Commit:** `Add shortfall alert rule`

### Step 12. Regular payments and income day

**Build:**

- `app/domain/entities/regular_payment.py`: recipient, usual day of the month, usual amount.
- `app/domain/services/regular_payments.py`: a payment is regular when the same recipient was paid a similar amount in at least three of the last four months. Returns the ones due in the next 30 days.
- `app/domain/services/income_pattern.py`: the usual day of the user's large income, or "paid daily".
- `tests/unit/test_regular_payments.py`: a small hand-made history.
- One integration check: for a generated user, the detected payments match the ones in `data/user_truth.csv`.

**Test:**

```bash
python -m pytest -q
```

**Done when:** all tests pass.

**Commit:** `Add regular payment and income day detection`

### Step 13. Safe to spend

**Build:**

- `app/domain/services/safe_to_spend.py`: the formula from SRS section 4.4.
- `tests/unit/test_safe_to_spend.py`: one example worked by hand. Balance 5,000, cautious income 0, regular payments 2,000, cushion 600, no savings goal, window 12 days. The answer must be (5,000 + 0 - 2,000 - 600) / 12 = 200. A second example where the result would be negative must give 0.

**Test:**

```bash
python -m pytest tests/unit -q
```

**Done when:** the tests pass and you get the same numbers on paper.

**Commit:** `Add safe-to-spend rule`

### Step 14. Actions and what-if

**Build:**

- `app/domain/entities/action.py`: id, title, estimated effect in taka. The effect is how much the action raises the forecast balance on its lowest day.
- `app/domain/services/actions.py`: three action types, each with a rule for how it changes the forecast.
  1. Keep daily spending to the safe-to-spend amount.
  2. Move a regular payment to after the usual income day.
  3. Pay shops directly from the wallet instead of cashing out first, which saves the cash-out fee.
- The same file has the function that applies chosen actions to a forecast and returns a new one.
- `tests/unit/test_actions.py`: a forecast with a shortfall has none after the right action; the taka effect of an action equals the rise it causes on the lowest day of the forecast; the action list contains no loans and no paid products.

**Test:**

```bash
python -m pytest tests/unit -q
```

**Done when:** the tests pass.

**Commit:** `Add actions and what-if rule`

---

## Part E. API

### Step 15. First endpoints: health, users, forecast

**Build:**

- `app/application/use_cases/list_users.py` and `get_forecast.py`. `get_forecast` reads the transactions, calls the forecaster, applies the rules from Part D and returns one result.
- `app/presentation/api/schemas/` and `app/presentation/api/routers/health.py`, `users.py`, `forecast.py`.
- `app/main.py`: creates the app and connects the real repository and forecaster to the use cases. It allows browser calls from the addresses listed in `ALLOWED_ORIGINS`.
- `backend/.env.example`: `ALLOWED_ORIGINS=http://localhost:5173`. Copy it to `backend/.env` for local use. `.env` is never committed.
- `tests/unit/test_use_cases.py`: runs the use cases with a fake repository and a fake forecaster.
- `tests/integration/test_api.py`.

The forecast call returns this shape. Part G depends on it, so change both sides together if it changes.

```json
{
  "user_id": "U0001",
  "as_of": "2026-08-12",
  "balance": 5200,
  "cushion": 780,
  "safe_to_spend": 330,
  "window_days": 18,
  "alert": { "date": "2026-08-24", "gap": 650, "probability": 0.78 },
  "points": [
    { "date": "2026-08-13", "p10": 4400, "p50": 4700, "p90": 5000, "actual": null }
  ],
  "regular_payments": [
    { "recipient": "W-123456", "date": "2026-08-20", "amount": 5000 }
  ],
  "actions": [
    { "id": "keep_to_safe_spend", "title": "Keep daily spending to ৳330", "effect": 2700 }
  ]
}
```

The numbers above are examples. `alert` is `null` when there is no shortfall risk. `points` has 30 items. `actual` is the real balance on that day when the data has it, and `null` otherwise.

**Test:**

```bash
python -m pytest -q
uvicorn app.main:app --reload
```

Then open <http://127.0.0.1:8000/docs> and try:

- `GET /health` returns `{"status": "ok"}`.
- `GET /users` returns the users with their persona.
- `GET /users/U0001/forecast?as_of=2026-08-12` returns 30 points, a safe-to-spend number, and an alert or `null`.

**Done when:** all tests pass and the three calls work in the browser.

**Commit:** `Add health, users and forecast endpoints`

### Step 16. Deploy the API

Deploy now, not at the end. Problems on the host are much cheaper to find today than at 8 AM tomorrow.

The steps below use Render, a host with a free plan. Any host that runs a Python web service works. The three settings that matter are the root folder, the build command and the start command.

**Build:**

1. Sign in at render.com with GitHub.
2. New, Web Service, and pick the repository.
3. Settings:
   - Root Directory: `backend`
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Instance Type: Free
4. Environment variables:
   - `PYTHON_VERSION`: the exact version from step 3, for example `3.12.12`
   - `ALLOWED_ORIGINS`: `http://localhost:5173` for now
5. Deploy and wait until the service is live.

**Test:**

Open `https://YOUR-SERVICE.onrender.com/health` on your phone, then `/docs` and the forecast call from step 15.

**Done when:** the forecast call works on the public address.

Things to know:

- A free service sleeps after a period with no visits. The next visit can take about a minute. The web app must show a "starting the server" message instead of a blank screen (step 20).
- After this step, every push to `main` redeploys the API.
- If the model fails to load on the host, the Python or scikit-learn version differs from your machine. Check `PYTHON_VERSION` and that `requirements.txt` is the frozen file from step 3.
- If the host reports that it ran out of memory, the data is being loaded wastefully. Load fewer columns.

**Commit:** none needed, unless you had to change code to make the deploy work.

### Step 17. What-if and model report endpoints

**Build:**

- `app/application/use_cases/run_what_if.py` and `get_metrics.py`.
- `app/application/ports/metrics_store.py` and `app/infrastructure/repositories/json_metrics_store.py`, which reads `reports/metrics.json`.
- `app/presentation/api/routers/what_if.py` and `metrics.py`.
- Tests added to `tests/unit/test_use_cases.py` and `tests/integration/test_api.py`.

**Test:**

```bash
python -m pytest -q
uvicorn app.main:app --reload
```

In <http://127.0.0.1:8000/docs>:

- `POST /users/U0001/what-if` with `{"as_of": "2026-08-12", "actions": ["keep_to_safe_spend"]}` returns a forecast that differs from step 15.
- `GET /metrics` returns the numbers from step 9.

**Done when:** tests pass, both calls work locally, and after the push they work on the public address.

**Commit:** `Add what-if and metrics endpoints`

---

## Part F. Explanation

### Step 18. Template explanation in Bangla and English

**Build:**

- `app/application/ports/explainer.py`: the interface. Given a list of facts and a language, return text.
- `app/infrastructure/llm/template_explainer.py`: builds the text from the facts with fixed sentences. No LLM. The facts are the alert date, gap and probability, the main reasons, and the best action with its effect.
- `app/application/use_cases/explain_alert.py` and `app/presentation/api/routers/explain.py`.
- `tests/unit/test_template_explainer.py`: every number in the text exists in the facts; both languages work; a user with no alert gets the all-clear text.

**Test:**

```bash
python -m pytest -q
uvicorn app.main:app --reload
```

In `/docs`: `POST /users/U0001/explain` with `{"as_of": "2026-08-12", "language": "bn"}`, then with `"language": "en"`.

**Done when:** tests pass, and you have read the Bangla text yourselves and fixed anything that sounds unnatural.

**Commit:** `Add template explanation in Bangla and English`

### Step 19. LLM explanation with fallback (optional)

Skip this step if you have no API key or are short of time. Step 18 already meets the Must requirement.

**Decide first:** which LLM provider, and whose key. The default is Claude, with the `anthropic` package and an `ANTHROPIC_API_KEY`. With a different provider, only `llm_explainer.py` changes.

**Build:**

- `app/infrastructure/llm/llm_explainer.py`: sends the facts and the user's question to the LLM and tells it to use only those facts. It checks that every number in the answer exists in the facts. With no key, an error or a failed check, it returns the template text from step 18.
- Install the provider's package and freeze `requirements.txt` again, as in step 3.
- Put the key in `backend/.env`. Add the variable name with a placeholder value to `.env.example`.
- `tests/unit/test_llm_explainer.py`: with no key the template is used; an answer containing an unknown number is rejected. The tests use a fake LLM reply, so they need no key.

**Test:**

```bash
python -m pytest -q
uvicorn app.main:app --reload
```

In `/docs`, call `/explain` with `"question": "Why do I run short?"`. Remove the key from `.env`, restart, and call it again. You should get the template text and no error.

**Done when:** it works with a key and without one. Then add the key as an environment variable on the host. Never commit it.

**Commit:** `Add LLM explanation with template fallback`

---

## Part G. Web app

The screens are tabs inside one page. Do not use a URL router. A static host then needs no extra rules.

### Step 20. App skeleton connected to the API

**Build:**

- `frontend/package.json`, `vite.config.js`, `index.html`, `src/main.jsx`: a React app built with Vite. Packages: `react`, `react-dom`, `recharts`, and for development `vite` and `@vitejs/plugin-react`.
- `src/infrastructure/apiClient.js`: all calls to the API, in one file. The address comes from `VITE_API_URL`.
- `src/presentation/App.jsx` and `styles.css`: the page frame with the five tabs, empty for now.
- `frontend/.env.example`: `VITE_API_URL=http://127.0.0.1:8000`. Copy it to `frontend/.env.local`.

**Test:**

Terminal 1, in `backend`:

```bash
uvicorn app.main:app --reload
```

Terminal 2:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

**Done when:**

- The page shows "API connected" and the number of users.
- When you stop the backend and reload, the page shows a clear "starting the server" or error message, not a blank screen.

**Commit:** `Add web app skeleton connected to the API`

### Step 21. Home screen

**Build:**

- `src/application/useForecast.js`: loads the forecast for the chosen user and date.
- `src/presentation/pages/Home.jsx`, with `components/UserSwitcher.jsx`, `AlertCard.jsx` and `SafeToSpend.jsx`.

**Test:**

- Change the user and the date. The numbers change.
- Compare one user and date with the same call in `/docs`. The numbers are equal.
- Pick a user with no alert. The screen shows the all-clear.
- Press Ctrl+Shift+M in Chrome DevTools and set the width to 400. Nothing scrolls sideways.

**Done when:** all four checks pass.

**Commit:** `Add home screen`

### Step 22. Deploy the web app

**Build:**

1. On Render: New, Static Site, same repository.
   - Root Directory: `frontend`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `dist`
   - Environment variable `VITE_API_URL`: the API address from step 16
2. On the API service, change `ALLOWED_ORIGINS` to the new site address, keeping `http://localhost:5173` after a comma.

**Test:**

Open the site address on your phone and in a private browser window.

**Done when:** the home screen loads real numbers on the phone. This address is the live deployment URL for the README.

**Commit:** none needed.

### Step 23. Forecast screen

**Build:**

- `src/presentation/pages/Forecast.jsx`, with `components/ForecastChart.jsx` (the P50 line, the P10 to P90 band and the cushion line) and `RegularPayments.jsx`.

**Test:**

- The band and the cushion line are visible and labelled.
- Hover over two days and compare the values with `/docs`.
- The list of regular payments matches the API.
- Check at width 400.

**Done when:** all checks pass.

**Commit:** `Add forecast screen`

### Step 24. Actions screen

**Build:**

- `src/application/useWhatIf.js` and `src/presentation/pages/Actions.jsx`: a switch for each action. Switching calls the what-if endpoint.

**Test:**

Pick a user with an alert.

- Switch an action on. The chart changes without a page reload, and the alert disappears or the gap shrinks.
- Switch it off. The original forecast returns.

**Done when:** both checks pass.

**Commit:** `Add actions screen with what-if`

### Step 25. Ask screen

**Build:**

- `src/presentation/pages/Ask.jsx`: the explanation text and a Bangla or English switch.
- If step 19 is done and there is time: a box for a follow-up question.

**Test:**

- Both languages show.
- The date and amounts in the text equal those on the home screen.

**Done when:** both checks pass.

**Commit:** `Add ask screen`

### Step 26. Model report screen

**Build:**

- `src/presentation/pages/ModelReport.jsx`: the model against the three baselines, the results per persona, the list of synthetic assumptions, and one sentence saying that all results come from synthetic data.

**Test:**

Compare the numbers on the screen with `backend/reports/metrics.json`.

**Done when:** they are equal.

**Commit:** `Add model report screen`

---

## Part H. Finish

### Step 27. Extras (optional)

Only before the feature freeze, and only when steps 1 to 26 are done. Each one is built, tested and committed like any other step. In order of value:

1. "What actually happened": for a past "today", draw the real balance over the forecast (FR-25). The API already returns `actual` for each point.
2. Follow-up question box (FR-19), if not done in step 25.
3. Impact test (SRS section 5.6).
4. Savings goal (FR-26).
5. Voice input in Bangla (FR-20).

### Step 28. README

**Build:**

`README.md` in the project root with all ten items the rulebook requires:

- [ ] Project overview: the problem, the solution, the purpose
- [ ] Features, and how the AI parts are used
- [ ] Technology stack
- [ ] Requirements: software and versions needed
- [ ] Installation and setup, step by step
- [ ] Environment variables: names, purpose, placeholder values only
- [ ] Run and build commands, exact
- [ ] Live deployment URL
- [ ] Testing instructions
- [ ] Other configuration

Also state that all data is synthetic, and give the test results from step 9 including any weak spots.

**Done when:** step 29 passes.

**Commit:** `Add README`

### Step 29. Clean clone test

Judges will follow the README on their own machine. Do the same.

**Test:**

```bash
cd "$TEMP"
git clone https://github.com/Tamim2276/DIU_HACKATHON.git agam-check
```

In PowerShell, use `cd $env:TEMP` for the first line, and `Select-String` in place of `grep` below.

Then follow your README inside `agam-check`, and nothing else.

Also run these inside `agam-check`:

```bash
git ls-files | grep "\.env"
git log --oneline
```

**Done when:**

- The tests pass, the API starts and the web app starts in the clone, using only the README.
- The first command lists `.env.example` files only.
- The second shows one commit per step.
- The live URL works in a private browser window and on a phone.

Fix the README where you got stuck, commit, and delete `agam-check`.

### Step 30. Report and video

**Report.** The rulebook asks for the problem, the proposed idea, the implemented solution, the key features, the AI approach and the intended real-life impact. Add:

- The test results against the baselines, with the weak spots
- The responsible AI points from SRS section 9
- How Agam could later be validated with real, governed data
- A clear statement that all data is synthetic

**Video.** The rulebook asks you to show how it works, explain the features and AI parts, and describe the real-life value. A simple order:

1. The problem, in two or three sentences.
2. One user with an alert: Home, Forecast, Actions with an action switched on, Ask in Bangla.
3. The Model report screen: how the model was tested and what it beat.
4. Who benefits, and what would come next.

Check the organizers' announcement for the required file formats and where to submit.

### Step 31. Submit

- [ ] Everything is committed and pushed
- [ ] The repository is public
- [ ] The README has the live URL, and the URL works
- [ ] The video is uploaded and opens for someone who is not signed in
- [ ] The report file is ready
- [ ] Submitted through the official channel, before 9:30 AM

After 10:00 AM, push nothing until the on-site session starts on 7 October. The rules allow pushes only during the two contest periods.

---

## If something goes wrong

| Problem | Likely cause |
| --- | --- |
| `No module named app` | You are not in the `backend` folder, or you ran a file directly. Use `python -m ...` from `backend`. |
| `No module named fastapi`, or another package | The environment is not active. Activate it; the prompt then starts with `(.venv)`. |
| `command not found` when activating | You used the PowerShell command in Git Bash. Use `source .venv/Scripts/activate`. |
| `Activate.ps1 cannot be loaded` in PowerShell | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again. |
| The web app shows a CORS error in the browser console | The app's address is missing from `ALLOWED_ORIGINS` on the API. |
| The web app calls the wrong address | `VITE_API_URL` is wrong or missing. Restart `npm run dev` after changing it. On the host, redeploy the site. |
| The live site is slow on the first visit | The free API service was asleep. Wait about a minute. |
| The model loads locally but not on the host | Different Python or scikit-learn version. See step 16. |
| `git push` is rejected | Your teammate pushed first. Run `git pull --rebase`, then push again. |
