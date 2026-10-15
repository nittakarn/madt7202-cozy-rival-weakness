# MADT 7202 — Cozy-rival weakness (rebuilt)

This branch rebuilds the earlier submission rather than silently editing it. It keeps the same decision question and 15-rival comparison frame, but replaces the old bare-keyword coding with a documented complaint-coding rule and creates a new frozen, de-identified snapshot.

## Decision

**Turn Story & Characters into the new cozy game’s strength.** In the frozen run, the topic qualifies in 4 of 15 rival games. `Progression & Pacing` has more coded matches but qualifies in 3 rivals, so it is the loudest issue rather than the broadest shared weakness.

The one-page submission is [report/MADT7202_MidTerm_Rebuilt_Nittakarn.pdf](report/MADT7202_MidTerm_Rebuilt_Nittakarn.pdf).

## What changed from the earlier report

- The old method counted bare words such as `story` or `progress` anywhere in a negative review. This version requires either a complaint phrase or a topic word within roughly ten words of a negative cue in the same sentence.
- The graph’s edge definition is explicit: at least 5 coded reviews and at least 5% of that game’s sampled negative reviews.
- The report says exactly what the edges mean: a game–complaint relationship, **not** a direct game–game relationship.
- Inputs and derived outputs are retained. Raw review text is not published; the frozen snapshot contains only game, app ID, review ID, language, timestamp, text hash, and codes.

## Data, scope and access basis

- **Frame:** the 15 Steam games used in the prior submission, fixed before the new collection.
- **Source:** recent negative reviews from Steam’s public `appreviews` endpoint, English and Thai, up to 200 per game/language.
- **Run:** 2,270 reviews; English 2,266 and Thai 4; 2019-09-14 through 2026-10-15.
- **Access basis:** public endpoint used for an educational course analysis, paced at about one page request per second. No account credentials, usernames, profile URLs, or Steam IDs are saved or published.
- **Limits:** recent, self-selected and English-heavy negative reviews are not representative of every player; coding identifies associations, not causal effects.

## Reproduce

```bash
python3 -m pytest -q tests/test_rebuild_analysis.py
python3 rebuild_analysis.py
python3 build_report.py
```

`rebuild_analysis.py` refetches a current public snapshot, so a later run may produce different counts. The submitted report is reproducible from the committed `data/review_snapshot.*` and `outputs/` artifacts; its SHA-256 is printed in the PDF footer and `outputs/stats.json`.

## Repository contents

- `rebuild_analysis.py` — collection, coding, edge construction, ranking, and robustness sweep
- `build_report.py` — one-page A4 report generator
- `data/review_snapshot.*` — de-identified frozen data snapshot
- `outputs/edges.csv`, `topic_table.csv`, `robustness_sweep.csv`, `stats.json` — derived analysis outputs
- `tests/test_rebuild_analysis.py` — checks that bare feature mentions are not coded as complaints

The original report and notebook remain in the history of the default branch for comparison.
