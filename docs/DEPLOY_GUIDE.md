# Deploy guide: putting Agam on the internet

This guide takes you from "it works on my laptop" to a public address anyone can open. It uses Render, which hosts both parts for free. Follow the parts in order. It takes about 30 minutes, most of it waiting.

The button names on Render change a little over time. If a name differs, look for the closest one.

## What you are deploying

Agam has two parts, and each gets its own address:

| Part | What it is | Folder | Render calls it |
| --- | --- | --- | --- |
| The API | The Python program with the data, the model and the rules | `backend` | Web Service |
| The web app | The screens people see | `frontend` | Static Site |

The web app needs the API's address, so the API goes first.

## Before you start

1. **The latest work is on GitHub.** Open <https://github.com/Tamim2276/DIU_HACKATHON> and check that the newest commit is the one your teammate just pushed. Render takes the code from there, not from anyone's laptop. You do not need the project on your own computer to deploy it.

2. **You have the Gemini key.** It is the long text after `GEMINI_API_KEY=` in `backend/.env`. Ask your teammate for it in a private message, or make your own free key at <https://aistudio.google.com/apikey>. You will paste it into Render. Never put it on GitHub or in a group chat.

3. **You have a Render account.** Sign up at <https://render.com> with any email or with GitHub. The free plan is enough and needs no card.

## Which way to connect the repository

Render has two ways to take the code. Which one you use depends on who is deploying.

| Who deploys | Use | What it means |
| --- | --- | --- |
| The owner of the repository | **Git Provider**: sign in with GitHub and pick the repository | Every push redeploys by itself |
| A teammate who does not own it | **Public Git Repository**: paste the address of the repository | After each push you click one button to redeploy |

The address to paste is:

```text
https://github.com/Tamim2276/DIU_HACKATHON
```

The steps below work for both. Where they differ, both are given.

## Part 1: the API

1. Open <https://render.com> and sign in.
2. Click **New**, then **Web Service**.
3. Give Render the code. The owner picks `Tamim2276/DIU_HACKATHON` under **Git Provider**. A teammate chooses **Public Git Repository**, pastes the address above and continues.
4. Fill in the form. Root Directory may sit under **Advanced**:

   | Field | Value |
   | --- | --- |
   | Name | `agam-api` |
   | Language | Python 3 |
   | Branch | `main` |
   | Region | Singapore (the closest to Bangladesh) |
   | Root Directory | `backend` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | Instance Type | Free |

5. In the same form, find **Environment Variables** and add these three:

   | Key | Value |
   | --- | --- |
   | `PYTHON_VERSION` | `3.12.12` |
   | `ALLOWED_ORIGINS` | `http://localhost:5173` |
   | `GEMINI_API_KEY` | your Gemini key |

   `PYTHON_VERSION` matters. Without it Render uses a newer Python, and the saved model may not load.

6. Click **Create Web Service** and wait. The log scrolls while it installs the packages. After a few minutes the status turns to **Live**.
7. Copy the address at the top of the page. It looks like `https://agam-api-xxxx.onrender.com`. This is your **API address**.

### Check the API

Open these in your browser, with your own API address:

- `https://agam-api-xxxx.onrender.com/health` should show `{"status":"ok"}`.
- `https://agam-api-xxxx.onrender.com/docs` should show the list of calls. Open the forecast call, click "Try it out", then "Execute". You should get a `200`.

Do not go on until both work.

## Part 2: the web app

1. On Render, click **New**, then **Static Site**.
2. Give Render the same repository, the same way as in Part 1.
3. Fill in the form:

   | Field | Value |
   | --- | --- |
   | Name | `agam` |
   | Branch | `main` |
   | Root Directory | `frontend` |
   | Build Command | `npm install && npm run build` |
   | Publish Directory | `dist` |

4. Add these two **Environment Variables**:

   | Key | Value |
   | --- | --- |
   | `VITE_API_URL` | your API address, with no `/` at the end |
   | `NODE_VERSION` | `24.15.0` |

5. Click **Create Static Site** and wait about two minutes for **Live**.
6. Copy the address at the top. It looks like `https://agam-xxxx.onrender.com`. This is your **site address**, the live address for the README and the judges.

If you open the site now, it stays on "Starting the server". That is expected. Part 3 fixes it.

## Part 3: let the API accept the web app

The API only answers browsers that come from addresses on its list. Your site is not on the list yet.

1. On Render, open the `agam-api` service.
2. Click **Environment**.
3. Change `ALLOWED_ORIGINS` to your site address, then a comma, then the local one:

   ```text
   https://agam-xxxx.onrender.com,http://localhost:5173
   ```

   No spaces, no `/` at the end, and `https` for the first one.

4. Save. Render restarts the API by itself. Wait for **Live** again.

## Part 4: check the live site

1. Open your site address. Within a minute the bottom line should read "API connected · 300 users".
2. Click the five tabs. Each should show figures.
3. On **Ask**, tap a suggested question. An answer should appear after a few seconds.
4. Open the site address on your phone. It should look right, with the tabs along the bottom.
5. Open it in a private browser window too, to be sure it does not depend on your own browser.

When all five pass, the deploy is done. Put the site address in the README.

## Things to know about the free plan

- **The API falls asleep** after 15 minutes with no visitors. The next visit wakes it, which takes about a minute. The site shows "Starting the server" while it waits. If it gives up, click "Try again".
- **Before the judges look**, open the site two or three minutes early so the API is awake.
- **Changing `VITE_API_URL` needs a rebuild.** After changing it, open the static site and choose **Manual Deploy**, then **Clear build cache & deploy**.

## After a new push to GitHub

When your teammate pushes new work, the live site has to take it.

- **Connected with Git Provider:** nothing to do. Both parts redeploy by themselves within a few minutes.
- **Connected with Public Git Repository:** open each of the two services on Render, click **Manual Deploy**, then **Deploy latest commit**. Do the API first, then the site. Wait for **Live** on both.

Either way, you never repeat the setup in this guide. Check the live site again after each redeploy with Part 4.

## If something goes wrong

| What you see | Likely cause | What to do |
| --- | --- | --- |
| The API build fails while installing packages | `PYTHON_VERSION` is missing or mistyped | Set it to `3.12.12` exactly and deploy again |
| The API build works but the service never turns Live | The start command is wrong | Check it is exactly `uvicorn app.main:app --host 0.0.0.0 --port $PORT` and Root Directory is `backend` |
| The site stays on "Starting the server" for minutes | `ALLOWED_ORIGINS` does not match the site address | Copy the site address again. `https`, no `/` at the end, no spaces |
| The site says "The server did not answer" and shows `127.0.0.1` | `VITE_API_URL` was not set when the site was built | Set it, then Manual Deploy with a cleared build cache |
| The site build fails | Node version | Check `NODE_VERSION` is `24.15.0`, and Root Directory is `frontend` |
| Ask says the assistant could not give a checked answer | `GEMINI_API_KEY` is missing, or the free limit was hit | Check the key on the API service. If it is there, wait a minute |
| The site loads but figures never appear | The API crashed | Open the API service, click **Logs**, and read the last lines |

To see why the API refuses a browser, open the site, press F12, and look at the **Console** tab. A line mentioning "CORS" means `ALLOWED_ORIGINS` is wrong.
