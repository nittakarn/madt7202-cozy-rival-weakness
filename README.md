# madt7202-cozy-rival-weakness

**Which Rival Weakness Should Our New Cozy Game Turn Into Its Strength?**
A game × complaint network from Steam negative reviews of 15 rival cozy indie games (MADT 7202 mid-term).

## The idea
Read what players complain about in rival cozy games. Find the complaint that appears in the **most different games**. That is a weakness of the whole market, so it is the best one for a new game to turn into its strength. The decision-maker is the head of studio, before pre-production.

A table only shows the *loudest* complaint, and that can come from one big game. The network shows how many *different* rivals share each complaint: the **degree** of each complaint node.

## Data
| What | Source | Permission |
|---|---|---|
| 15 most-reviewed paid games tagged *Cozy* + *Indie* (≥ 1,000 reviews) | [SteamSpy public API](https://steamspy.com/api.php) | Public documented API, no stated licence; the 1 request/second limit is respected |
| Up to 300 newest **negative** reviews per game, per language (English, Thai) | Steam store public endpoint `appreviews` | Public store data. Only text, language and date are kept; no usernames or Steam IDs |

Sampling bias: over-represents engaged players who write reviews and recent reviews. Under-represents players who quit silently and players writing in other languages (word lists exist for English and Thai only).

## Graph
- 🟠 game nodes · 🔵 complaint-topic nodes (course-sample colours) (decoration, farming, story, progression…)
- **Line:** ≥ 10 % of a game's negative reviews complain about the topic (≥ 5 reviews); weight = conditional, count(game, topic) / count(game) (Ch 6, Scheme 4)
- **Removed before ranking:** bugs/performance, price, "too short/boring", cozy words. Every game gets these, so they are generic.
- **Rule (fixed in advance):** pick the topic linked to the most games; ties are broken by number of complaints
- **Compared with:** the loudest topic (table answer), generic complaints kept in, and NPMI instead of share per game
- **Robustness:** 9 cutoff versions (5/10/15 % × 3/5/8 reviews), leave-one-game-out (15 runs), 500× bootstrap
- **Accuracy check:** `audit_labelled.csv`. 100 random matches; 60 could be judged (in the other 40 the keyword sat past the 400 saved characters). 68% correct overall, Story & Characters 77%, Progression 73%.

## Files in this repo
- `MADT7202_MidTerm_Report.pdf` – the one-page A4
- `Cozy_Rival_Weakness.ipynb` – the full analysis, run in Colab with outputs
- `stats.json` – every number in the A4
- `topic_table.csv` · `edges.csv` · `robustness_sweep.csv` – the graph, the side table and the cutoff test
- `audit_labelled.csv` – the hand check (y / n / unclear, with a reason per row)
- `fig_report.png` + `make_report_fig.py` – the A4 figure and the script that draws it

## Reproduce
Open `Cozy_Rival_Weakness.ipynb` in Colab and choose *Runtime → Run all*. No API key is needed. The first run takes about 5–10 minutes. The notebook saves its result files to `outputs/` and downloads them as `outputs.zip`. Raw reviews (`data/`) are not shared.
