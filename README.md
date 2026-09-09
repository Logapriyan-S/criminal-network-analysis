# CrimeNet — AI-Powered Criminal Network Analysis (SIH 2026, PS26189)

Working prototype for the Ministry of Home Affairs problem statement.
Turns scattered crime records into a connected criminal network and uses
AI to surface the key players, hidden links, and gangs — with a reason
for every result.

## What it does

1. **Builds a network** from suspects + calls + transactions + shared addresses
2. **Ranks key players** using graph centrality — importantly, betweenness
   centrality finds the "broker" who quietly links two groups, often the
   real coordinator rather than the most obviously-connected person
3. **Detects gangs/modules** automatically using Louvain community detection
4. **Predicts hidden links** — pairs with no recorded direct contact but
   many shared associates (a probable connection)
5. **Explains everything** in plain language, and shows it all on an
   interactive network graph

## Run it

```bash
pip install -r requirements.txt
python run.py
```

This generates data, runs the analytics, and opens the dashboard in your
browser at `http://localhost:8000/dashboard.html`.

To run the pieces separately:

```bash
python generate_data.py    # make synthetic data -> crime_data.json
python analytics.py        # run analytics, print results to console
```

## The demo (what to show the judges — ~3 minutes)

1. **Open the dashboard** — show the whole network, coloured by detected group.
2. **Highlight key players** (button) — the #1 suspect is a *broker*, not the
   most-connected node. Read the AI's reason: "acts as a broker connecting
   otherwise-separate groups." This is the AI finding a hidden coordinator.
3. **Detected groups** — point out the graph auto-split into distinct gangs,
   with no one telling it how many to look for.
4. **Predicted hidden links** — show a pair the system flagged as probably
   connected despite no direct contact, with its reasoning.
5. **Click a key player** — the graph highlights them; explain how an
   investigator would drill in from here.

The key line: *"We don't just draw the network — we rank the key players,
expose hidden links and gangs, and explain every conclusion."*

## Note on the data

The prototype uses synthetic data (generated with Faker) with a known
ground truth deliberately planted in: 3 gangs and 1 broker. This lets us
prove the analytics actually recover the hidden structure — the planted
broker (P025) reliably ranks #1 on betweenness. In production this would
be replaced by real ingested records; the analytics layer is unchanged.

## Files

```
generate_data.py    Synthetic data generator
analytics.py        Graph build + centrality + communities + link prediction
run.py              One-command: build data, run analytics, serve dashboard
dashboard.html      Interactive network visualization (D3.js)
crime_data.json     Generated raw data
dashboard_data.json Analytics results consumed by the dashboard
```

## Tech

Python (NetworkX, python-louvain, scikit-learn, Faker) + D3.js for the
interactive graph. No paid services, runs fully offline.
