# Demo guide: showing Agam to the judges, live and on video

This guide is for the two of you as presenters. For each step it gives what to click, what should appear, and a line you can say. Every figure is for the demo day, 12 August 2026, and was checked against the API.

It has two parts:

- **The live demo**, for the on-site session. It starts just below.
- **The video**, which goes in with the submission. If that is what you are making now, go straight to [Recording the video](#recording-the-video). It has its own script, shot by shot.

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

> This number is not a guess by AI. It is a fixed formula, and every part is on the screen. It is checked for every day until his next income, so a payment that falls due early cannot hide behind money that arrives later. The AI only predicts the balance. The rules decide what to tell the customer.

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
| Home, click **Rider** | "Your balance is already low", 75% chance. Safe to spend is ৳0 |
| Click "How we worked this out" | The tightest day is Fri, 14 Aug: ৳1 + ৳1,511 − ৳7,300 = −৳5,788 |
| In the Customer list, choose **U0024** | Another rider with ৳1. Safe to spend is ৳196 a day |
| Actions, switch on "Keep to the safe amount" | "The warning stays, but the risk is lower": 65% → 50% |
| Home, click **Garment worker** | "No warning for the next 14 days" |
| In Savings goal, type 2000 and click "Set goal" | Safe to spend drops from ৳118 to ৳44 a day |

Say:

> Both riders have one taka today and earn every day. The first must send ৳7,300 home in two days, before he has earned it, so the app says nothing is safe to spend. It does not average that away. The second has no payment that close, so he gets ৳196 a day, and keeping to it lowers his risk from 65% to 50%. The warning stays, and the app says so. And a customer with no problem can set a savings goal, which comes out of the safe-to-spend amount.

### Step 8: Model, the evidence

| Do | You should see |
| --- | --- |
| Click the **Model** tab | The orange note: all results come from synthetic data |
| Point at the first chart and table | Model error 3.37, 4.27, 4.86 against 4.71, 5.82, 6.70. Better by 27% to 29% |
| Scroll to "Is the range honest?" | 79% of real balances fell in the range meant to hold 80% |
| Scroll to "Does following the advice help?" | Borrowing ৳1,049 → ৳367 per customer |

Say:

> We tested the model on two months it never saw, against three simple methods. It was 27 to 29 percent better. Then we simulated customers who follow the warnings. They borrowed about 65 percent less and had fewer days with almost nothing to spend. The cost is that they spent about 5 percent less. All of this is on synthetic data, and the screen says so.

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
We simulated the same 300 customers with and without it. Those who kept to the safe amount on warned days borrowed about 65% less (৳367 against ৳1,049 each). Days with under a quarter of the day's need met fell from 6.3% to 4.0%. Days with under half did not improve (7.4% against 7.7%, a difference small enough to be chance). They spent about 5 points less of what they wanted. The app does not create money. It swaps borrowing for spending less, earlier.

**Where is it weak?**
Warnings are least reliable for shop owners and riders, whose income arrives day by day. The range is too narrow for freelancers. The Model screen marks all three. Also, the warning looks only at the balance: a customer who pays a bill late keeps a higher balance, so a missed payment does not always raise a warning.

**The rider earns every day. Why is his safe-to-spend amount ৳0?**
He has ৳1 and must send ৳7,300 home in two days. On a careful count he will have earned about ৳1,500 by then. So that payment takes everything, whatever he spends, and the honest answer is ৳0. Over the whole 14 days his money does add up to about ৳90 a day, and our first version of the formula showed that. It was wrong, because it ignored the order in which money comes and goes. We changed the formula to check every day.

**The freelancer shows "No warning" but ৳0 safe to spend. Why?**
The warning comes from the forecast balance, and the forecast expects money to come in. The safe-to-spend formula is stricter: it checks that every payment can be made on the day it is due. He has ৳467 and ৳10,745 falls due tomorrow. The card says so in words. It is the limit described above.

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

A video has no questions afterwards, so it has to say on its own what a judge would otherwise ask: what is AI, how it was tested, where it is weak, and that the data is synthetic. The script below does that in about five minutes.

The rulebook asks the video to show how the app works, explain the features and the AI parts, and describe the real-life value. **Check the organizers' announcement for the length limit and the file format before you record.** If the limit is shorter than five minutes, see "If it has to be shorter" below.

Plan about one hour: 10 minutes to set up, 10 to practise once, 20 to record, 20 to check and upload.

### 1. Check you are on the newest version

The script uses figures that changed on 4 October. Before anything else, open the app and check two of them:

| Where | It must say |
| --- | --- |
| Home, **Rider** chip, Safe to spend | ৳0 a day |
| **Model** tab, "Does following the advice help?", first row | ৳1,049 and ৳367 |

If you see ৳90 or ৳426, you are on an old version. On your own computer, stop the backend and start it again. On the live address, the newest commit has not been deployed yet: see the deploy guide.

Record on the live address if it is up. The address bar then shows the judges that the app is really hosted. If it is not up yet, record on your own computer; the app is the same.

### 2. Set up the screen

1. **Close what should not be seen.** Other tabs, chat apps, email. Turn on "Do not disturb" in Windows (click the clock at the bottom right, then the bell) so no notification pops up.
2. **Use a clean browser window.** A new Chrome window with only the app open. Hide the bookmarks bar with Ctrl + Shift + B.
3. **Zoom in.** Press Ctrl and + until the browser shows 125%. The video will be watched on small screens.
4. **Pick light mode and keep it.** The app follows the computer's light or dark setting. Light reads better after a video is compressed. In Windows: Settings, Personalization, Colors, "Choose your mode", Light.
5. **Reset the app.** Do steps 2 to 4 of "Before the judges arrive" at the top of this guide: Student, the demo day, English, no action switched on, no savings goal.
6. **Warm up the assistant.** On Ask, switch to **বাংলা**, tap "আমার টাকা কেন কম পড়বে?" and wait for the answer. Then switch back to English and go to Home. The server remembers a checked answer, so in the recording the same question is answered at once.

### 3. Set up the recording

Windows 11 has a recorder built in. You do not need to install anything.

| Step | Keys |
| --- | --- |
| Click on the browser window first, so it is the one recorded | |
| Start recording | Windows + Alt + R |
| Switch the microphone on (a small bar shows a microphone icon) | Windows + Alt + M |
| Stop recording | Windows + Alt + R again |

The clips are saved as MP4 files in your **Videos** folder, inside **Captures**. This recorder captures one window, which is what you want: nothing else on the computer can appear.

If those keys do nothing, press Windows + Shift + R instead. That opens the Snipping Tool recorder: drag a box around the browser, switch the microphone on in its bar, and press Start.

Before the real recording, record ten seconds of yourself talking and play it back. Check that the voice is clear and the text is readable. Use a headset microphone if you have one, in a quiet room.

### 4. How to record

- **Record each shot as its own clip.** Start, do one shot, stop. A mistake then costs one shot, not the whole video. Join the clips at the end.
- **Move the mouse slowly** and rest it on the thing you are talking about. After each click, wait one or two seconds before you speak.
- **Do not read fast.** The lines are written for a calm pace. If a shot runs over its time, that is fine.
- **Both of you should be heard.** The rules say every member must be able to explain the solution. The first member records shots 1 to 5, the second records shots 6 to 9.
- **Say the lines in your own words** if that is easier. Keep the figures exactly as written: each one is on the screen while you say it.

### 5. The script

About five minutes and fifteen seconds. Each shot gives what to do and what to say.

#### Shot 1: the problem (0:00 to 0:35)

Do: Home, with the Student showing. Click nothing.

> This is Agam, by team [your team name], for Track 3: Customer Innovation and Financial Independence. Agam means "in advance".
>
> Many wallet customers are not paid a fixed salary on a fixed day: students, riders, shop owners, freelancers. But rent and bills come on fixed dates. A wallet today shows only the past. So people find out they are short on the day it happens. Agam looks 30 days ahead and warns them before.

#### Shot 2: the warning (0:35 to 1:10)

Do: rest the mouse on the orange card, then on Safe to spend, then on Coming up.

> This is a university student in our test data. All the data in this app is synthetic. No real customer is shown.
>
> Today, 12 August, he has ৳1,771. His next allowance is 27 days away. The app warns that he may run short around 23 August, with a 45% chance. That is 11 days of notice. And it gives him one number he can act on: ৳34 a day is safe to spend. He usually spends ৳639.

#### Shot 3: where the number comes from (1:10 to 1:35)

Do: click "How we worked this out". Move the mouse down the rows.

> This number is not written by AI. It is a fixed formula, and every part is on the screen: what he has, the money likely to come in, the payments he must make, and a safety cushion. The app does this sum for every day until his next income. So a payment that is due early cannot hide behind money that comes later.

#### Shot 4: the forecast (1:35 to 2:20)

Do: click the **Forecast** tab. Hold the mouse over 23 August. Then tick "Show what really happened" and hold the mouse over 23 August again.

> This is the first AI part: a machine learning model that forecasts the balance for each of the next 30 days. It does not give one number. It gives a range, because income is uncertain. For 23 August it expects ৳1,107, and it could be anywhere from ৳0 to ৳3,099.
>
> Because this is test data, we can show what really happened. The black line is the real balance. On the 23rd it was ৳1,118. It is not always this close, and that is why there is a range.

#### Shot 5: what to do about it (2:20 to 2:50)

Do: click the **Actions** tab. Switch on "Keep to the safe amount". Rest the mouse on the table.

> A warning alone is not enough. The app suggests what to do, and shows what that would change before the customer commits. If he keeps to ৳34 a day, the chance of running short falls from 45% to under 40%, and the warning goes away. None of the actions is a loan or a paid product.

#### Shot 6: the explanation, in Bangla (2:50 to 3:35)

Do: click the **Ask** tab. Click **বাংলা** at the top right. Tap "আমার টাকা কেন কম পড়বে?". When the answer shows, switch back to **English**.

> The Ask screen explains the warning: what will happen, why, and what to do. Our customers read Bangla, so the whole app switches to Bangla, with Bangla digits. This explanation is fixed text.
>
> Here is the second AI part. A language model answers follow-up questions. It is given only this customer's figures, and we check every number in its answer. If one number is wrong, the answer is thrown away and the customer sees the fixed text instead.

#### Shot 7: when the news is bad (3:35 to 4:00)

Do: click **Home**, then the **Rider** chip. Click "How we worked this out".

> The app does not always have good news. This rider has one taka today, and must send ৳7,300 home in two days, before he has earned it. So the app says nothing is safe to spend, and shows why. It does not hide the problem.

#### Shot 8: the evidence (4:00 to 4:50)

Do: click the **Model** tab. Scroll slowly: the first chart, "Is the range honest?", "Does following the advice help?", then "Limits".

> How do we know it works? The model learned from data up to June and was tested on July and August, two months it never saw. Against three simple methods, its error was 27 to 29 percent lower. The range that should hold the real balance 80 percent of the time held it 79 percent.
>
> Then we simulated customers who follow the warnings. They borrowed about 65 percent less: ৳367 each, against ৳1,049. The cost is that they spent about 5 percent less. The app is weaker for riders and shop owners, whose income comes day by day, and this screen says so. All of these results are on synthetic data.

#### Shot 9: the value, and the close (4:50 to 5:15)

Do: click **Home**, then the **Student** chip.

> For the customer, Agam means fewer surprises and less borrowing. For a wallet like upay, it gives customers a reason to open the app to plan, not only to pay. The next step is to test it on real data, with the customer's consent.
>
> Agam turns a wallet from a record of the past into a view of the next 30 days. Thank you.

### If it has to be shorter

| Limit | What to do |
| --- | --- |
| Four minutes | Leave out shots 3 and 7 |
| Three minutes | Also shorten shot 8 to its first paragraph plus "All of these results are on synthetic data", and in shot 6 leave out the follow-up question |

Do not cut shot 1, the sentence that the data is synthetic, or the two sentences that name the AI parts. Those are what the judges score.

### 6. Join, check, upload

1. **Join the clips.** Clipchamp comes with Windows 11: open it, drag the clips in, put them in order, cut any silence at the ends, and export at 1080p. If you recorded one clip, skip this.
2. **Watch the whole video once, with sound.** Use this list:
   - [ ] Every figure can be read, and matches what is said
   - [ ] Both voices are clear, with no long silence
   - [ ] No notification, no other tab, no personal account shows
   - [ ] The `.env` file, the Render settings page and the key never appear
   - [ ] It says that all data is synthetic
   - [ ] It is within the organizers' length limit and in the format they asked for
3. **Upload it** where the organizers ask. If they only want a link, YouTube with visibility "Unlisted" works, or Google Drive with sharing set to "Anyone with the link".
4. **Test the link.** Open it in a private browser window, where you are not signed in. If it plays there, it will play for the judges.
5. **Submit the link** through the official channel. If you also put it in the README, push that change before 9:30 AM.

### Things that go wrong while recording

| What happens | What to do |
| --- | --- |
| The follow-up answer does not come, and a notice says no checked answer could be given | Stop the clip. Wait one minute, tap the question once without recording, then record shot 6 again |
| "Starting the server" shows on the live address | The free host was asleep. Wait up to two minutes, then start the clip again |
| The wrong customer or date shows | Home, click **Student**, then "Back to the demo day" |
| The recording has no sound | The microphone was off. Press Windows + Alt + M while recording, and test with a ten-second clip |
| A figure on screen differs from the script | Stop. You are on an old version or the wrong day. Go back to "Check you are on the newest version" |
