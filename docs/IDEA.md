# Agam: the idea in plain words

Agam (আগাম) means "in advance". It is a feature for a mobile wallet that tells a customer they are about to run short of money before it happens, and what to do about it.

This page explains the idea with one example you can follow from start to finish.

## The problem

Many wallet customers in Bangladesh do not get a fixed salary on a fixed day. A rider is paid per trip. A freelancer is paid when a client pays. A student waits for an allowance that sometimes comes late.

Their bills do not wait. Rent, the internet bill and money sent home fall on fixed dates.

So these customers often find out they are short on the very day it happens. Then they delay a payment, skip something they need, or borrow. There is a common phrase for it: মাসের শেষে টানাটানি, running short at the end of the month.

A wallet today shows what already happened: the balance and the past transactions. It does not show what is coming.

## The idea in one line

Look at a customer's past transactions, predict their balance for the next 30 days, and warn them early, in plain Bangla, with a step they can take.

## One example: Rafi, a student

Rafi is not a real person. He is customer `U0121` in our made-up data, and every figure below is what the app really shows for him.

### Where Rafi stands on 12 August

| | |
| --- | --- |
| Money in his wallet | ৳1,771 |
| What he usually spends on everyday things | about ৳639 a day |
| His next allowance | about ৳13,360, expected on 8 September, 27 days away |
| Bills before then | Mess rent ৳4,000 and internet ৳510, both on 7 September |

Rafi does not do this sum. He sees ৳1,771 and feels fine. At ৳639 a day, that money lasts less than three days.

### What Agam does, step by step

**1. It reads his history.** It looks at his transactions up to today: when money came in, when it went out, and how much. It never looks at anything after today.

**2. It forecasts his balance.** For each of the next 30 days it gives a range, not one number, because nobody knows exactly when the next payment will arrive. For 23 August it says: most likely ৳1,107, but it could be anywhere from ৳0 to ৳3,099.

**3. It checks one rule.** The rule is: if the chance of the balance falling below a safety cushion reaches 40% on any day in the next two weeks, warn the customer. Rafi's cushion is ৳745, about one day of his *typical* spending once rent and other regular payments are smoothed in — a little more than the ৳639 a day he spends on everyday things alone. The chance passes 40% on 23 August and reaches 45%. So Agam warns him:

> You may run short around Sun, 23 Aug. That is in 11 days.

**4. It works out what he can safely spend.** This is plain arithmetic, shown to the customer:

| | |
| --- | --- |
| He has today | ৳1,771 |
| Money likely to come in before 8 September, counted carefully | + ৳4,403 |
| Regular payments to make | − ৳4,510 |
| Safety cushion to keep | − ৳745 |
| Left for 27 days | ৳920 |

৳920 over 27 days is ৳34 a day. That is his safe-to-spend amount.

Agam does this sum for every day until his next income, not only for the last one, and takes the smallest answer. So a payment that falls due early cannot hide behind money that arrives later. For Rafi the tightest day is the last one. For a rider with ৳1 in his wallet and ৳7,300 to send home in two days, the tightest day is the day that payment is due, and the answer is ৳0: the app does not pretend there is a safe amount when there is not.

**5. It suggests a step and shows what it would change.** The step: keep everyday spending to ৳34 a day until 8 September. Rafi can switch it on and watch the forecast redraw. The chance of a shortfall falls from 45% to under 40%, and the warning goes away. He sees the result before he commits to anything.

**6. It explains itself in Bangla.** The same message appears in Bangla or English: what is likely to happen, why, and what to do. If Rafi asks "আমার টাকা কেন কম পড়বে?" (why will I run short?), he gets a short answer built from his own figures.

Agam has not given Rafi any money. It has shown him, 11 days early, a problem he could not see, and a way through it.

## What is AI here, and what is not

This matters, because money decisions should be checkable.

| Part | What it does | AI? |
| --- | --- | --- |
| The forecast | Predicts the range the balance will be in | Yes: a machine learning model |
| The warning | Compares the forecast with the cushion | No: a fixed rule |
| Safe to spend | The sum shown above | No: a fixed formula |
| The suggested steps | Chosen from a list of three | No: fixed rules |
| The explanation | Sentences with the figures filled in | No: fixed text |
| Answers to questions | Written from the customer's figures | Yes: a language model, with every number checked |

The AI predicts and puts things into words. It never decides. Anyone can check why a warning was shown.

## What makes it different

- **It looks forward.** Wallets show the past. Agam shows the next 30 days.
- **It warns before, not after.** A low-balance alert tells you when the money is already gone.
- **It is honest about uncertainty.** It gives a range and a chance, not a false promise.
- **It lets you try a step first.** The what-if shows what a change would do before you make it.
- **It never sells.** The suggested steps are: spend within the safe amount, move a payment to after your income, or pay shops directly to save the cash-out fee. No loans, no paid products.
- **It speaks Bangla.** The whole app does, including the numbers.

## It is not only for students

The made-up data has five kinds of customer. On the same day, Agam says something different to each:

| Customer | How they earn | What Agam says on 12 August |
| --- | --- | --- |
| Student | An allowance once a month | Warning for 23 August. One step removes it |
| Rider | Paid per working day | Balance already low, 75% chance it stays so. Nothing is safe to spend, because ৳7,300 falls due in two days |
| Garment worker | A salary once a month | All clear. Can spend ৳118 a day until payday |
| Shop owner | Sales every day, a supplier to pay every week | Balance already low, 50% chance it stays so |
| Freelancer | Paid at random times | No warning, but payments due are more than the money expected |

Notice that the app does not always have good news. For the rider, it says plainly that the warning stays and that no amount is safe to spend.

## How we know it works, and what we do not know

We tested it on data it had never seen.

- **The forecast beats simple methods.** Against three simple ways of guessing, such as "the same as last month", its error was 27% to 29% lower.
- **The range is honest.** The range meant to hold the real balance 80% of the time held it 79% of the time.
- **The advice helps, at a price.** We simulated 300 customers twice, once following the warnings and once not. Those who followed borrowed about 65% less. They also spent about 5% less of what they wanted, because the advice is to spend less on warned days.

What we do not know:

- **All of this is on made-up data.** No real customer data was used. The results show that the method finds the patterns we put in. They do not show how it would do with real people.
- **Warnings are weaker for some.** They work less well for riders and shop owners, whose income changes day by day.
- **The warning looks only at the balance.** A customer who pays a bill late keeps a higher balance, so a missed payment does not always raise a warning.

The app shows these limits on its Model screen.

## The words we use

| Word | Meaning |
| --- | --- |
| Balance | The money in the wallet at the end of a day |
| Forecast | The balance we expect on a future day, with a range around it |
| Safety cushion | The least a customer should keep: about one day of their typical spending, with rent and other regular payments smoothed in — a broader figure than "everyday spending" alone |
| Shortfall | The balance falling below the safety cushion |
| Warning | Shown when the chance of a shortfall reaches 40% within 14 days |
| Safe to spend | What the customer can spend each day and still make every regular payment on time until their next income |
| What-if | The forecast redrawn as if the customer had taken a suggested step |
| Synthetic data | Data made by a program, describing no real person |

## Where to read more

- [BUILD_GUIDE.md](BUILD_GUIDE.md): how the project was built, step by step
- [SETUP_GUIDE.md](SETUP_GUIDE.md): how to run it on your own computer
- [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md): how to put it on the internet
- [DEMO_GUIDE.md](DEMO_GUIDE.md): how to show it to the judges
- [SYNTHETIC_DATA.md](SYNTHETIC_DATA.md): every assumption behind the data
