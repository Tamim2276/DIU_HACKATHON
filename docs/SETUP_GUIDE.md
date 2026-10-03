# Setup guide: running Agam on your own computer

This guide takes a computer that has never seen the project to a working copy with both parts running. Follow the steps in order. It takes about 20 minutes, most of it downloads.

The commands are for **Git Bash on Windows**. Where macOS or Linux differ, the difference is noted.

## Step 1: install three tools

You need these on the computer. If one is already there, check its version and move on.

| Tool | Version | Where to get it |
| --- | --- | --- |
| Git | any recent one | <https://git-scm.com/downloads> (on Windows this also installs Git Bash) |
| Python | 3.12 | <https://www.python.org/downloads/> (tick "Add python.exe to PATH" in the installer) |
| Node.js | 22 or 24 | <https://nodejs.org> (the LTS download) |

Open Git Bash and check:

```bash
git --version
py -3.12 --version
node --version
```

You should see a version for each, with Python `3.12.x` and Node `v22` or `v24`. On macOS or Linux, use `python3.12 --version` in place of the second line.

Python must be 3.12. The saved forecast model was made with it, and another version may fail to load it.

## Step 2: get the code

```bash
cd ~/Desktop
git clone https://github.com/Tamim2276/DIU_HACKATHON.git
cd DIU_HACKATHON
```

You now have a `DIU_HACKATHON` folder with `backend`, `frontend` and `docs` inside.

## Step 3: set up the API (the backend)

```bash
cd backend
py -3.12 -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
```

On macOS or Linux, the second and third lines are `python3.12 -m venv .venv` and `source .venv/bin/activate`.

The install takes a few minutes. When it ends, your prompt starts with `(.venv)`. That means the project's own Python is active.

Now create the settings file:

```bash
cp .env.example .env
```

Open `backend/.env` in an editor. It has a line `GEMINI_API_KEY=`. Paste the Gemini key after the `=`, with no spaces or quotes, and save.

- Ask your teammate for the key in a private message. Never post it in a group chat or on GitHub.
- Or make your own free key at <https://aistudio.google.com/apikey>.
- With no key the app still works. Only the follow-up questions on the Ask screen go unanswered.

## Step 4: check the API

Still in `backend`, with `(.venv)` showing:

```bash
python -m pytest -q
```

After about half a minute the last line should say `376 passed`.

Then start the API:

```bash
uvicorn app.main:app --reload
```

Wait for the line `Application startup complete`. Open <http://127.0.0.1:8000/docs> in a browser. You should see a list of calls. Leave this terminal running.

## Step 5: set up and start the web app (the frontend)

Open a **second** Git Bash window. The first one stays busy with the API.

```bash
cd ~/Desktop/DIU_HACKATHON/frontend
npm install
cp .env.example .env.local
npm run dev
```

`npm install` takes a minute or two. When `npm run dev` prints `Local: http://localhost:5173/`, it is running.

## Step 6: open the app

Open <http://localhost:5173> in Chrome. Type `localhost`, not `127.0.0.1`: the API only accepts the first spelling.

It works when:

- The bottom line reads "API connected · 300 users".
- The Home screen shows a warning for the Student, for Sun, 23 Aug.
- The five tabs each show figures.

## Every day after that

You do not repeat the installs. Each time you sit down:

```bash
cd ~/Desktop/DIU_HACKATHON
git pull
```

Then, in two terminals:

```bash
cd backend
source .venv/Scripts/activate
uvicorn app.main:app --reload
```

```bash
cd frontend
npm run dev
```

If `git pull` brought new packages, the app will complain about a missing one. Run `python -m pip install -r requirements.txt` in `backend` or `npm install` in `frontend` again.

To stop either program, click its terminal and press Ctrl+C.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| `py: command not found` | Python is not installed, or not on the PATH. Reinstall it and tick "Add python.exe to PATH". On macOS or Linux use `python3.12` |
| `No module named 'fastapi'` or `'app'` | The environment is not active, or you are in the wrong folder. Run `cd backend` and `source .venv/Scripts/activate` |
| `source: .venv/Scripts/activate: No such file` | You are on macOS or Linux (use `.venv/bin/activate`), or step 3 did not finish |
| The tests fail with an error about the model or scikit-learn | Python is not 3.12. Delete the `.venv` folder and redo step 3 with `py -3.12` |
| `Port 5173 is already in use` | The web app is already running in another terminal. Use that one, or close it |
| `Address already in use` on port 8000 | The API is already running in another terminal |
| The page says "Starting the server" | The API is not running. Start it (step 4) and the page connects by itself |
| The page opened at `127.0.0.1:5173` stays on "Starting the server" | Use `http://localhost:5173` instead |
| Ask says the assistant could not give a checked answer | The key is missing from `backend/.env`, or the free limit was hit. Check the key, restart the API, wait a minute |

## What is where

| Folder | What it holds |
| --- | --- |
| `backend/app` | The API: the rules, the model code and the calls |
| `backend/data` | The synthetic customers and their transactions |
| `backend/models` | The trained forecast model |
| `backend/tests` | The automated tests |
| `frontend/src` | The web app's screens |
| `docs` | The guides: build, setup, deploy, demo, idea, and the notes on the synthetic data |
