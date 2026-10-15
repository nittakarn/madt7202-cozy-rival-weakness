"""Rebuild the old MADT7202 cozy-rival analysis from a frozen public snapshot.

The old submission is retained in git as a record.  This script deliberately
does not reuse its counts: it downloads a fresh, de-identified review snapshot,
uses complaint phrases (not bare feature words), and writes every derived file.
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
DATA.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)

# Same 15-rival frame as the original submission, now fixed before collection.
# This makes the revised result comparable without retroactively picking games.
GAMES = {
    "Tiny Glade": 2198150, "A Little to the Left": 1629520,
    "Little Kitty, Big City": 1177980,
    "Kind Words (lo fi chill beats to write to)": 1070710,
    "Cozy Grove": 1458100, "Melatonin": 1585220,
    "Alba: A Wildlife Adventure": 1337010, "Sticky Business": 2303350,
    "Good Pizza, Great Pizza": 770810, "Minami Lane": 2678990,
    "My Dream Setup": 2200170, "Lil Gator Game": 1586800,
    "Cats Organized Neatly": 1369340, "LEGO Builder's Journey": 1544360,
    "Snake Pass": 544330,
}
LANGS = ("english", "thai")
N_PER_LANGUAGE = 200
LINK_SHARE, MIN_MATCHES = 0.05, 5
SWEEP_SHARE, SWEEP_MIN = (0.03, 0.05, 0.08), (3, 5, 8)
RNG = np.random.default_rng(7202)

# A hit must contain a complaint-bearing phrase.  This is intentionally more
# conservative than the old bare-keyword approach: recall is traded for a
# much more defensible claim that an edge represents a complaint.
TOPICS = {
    "Story & Characters": [
        r"(?:weak|bad|poor|boring|bland|flat|shallow|forgettable|rushed) (?:story|plot|writing|narrative|dialogue|character)s?",
        r"(?:story|plot|writing|narrative|dialogue|character)s? (?:is|are|was|were|feel|feels) (?:weak|bad|poor|boring|bland|flat|shallow|forgettable|rushed)",
        r"(?:no|lack of|lacks) (?:story|plot|character development|meaningful dialogue)",
        r"เนื้อเรื่อง(?:อ่อน|แย่|น่าเบื่อ)|บทสนทนา(?:น่าเบื่อ|แย่)|ตัวละคร(?:แบน|น่าเบื่อ)",
    ],
    "Progression & Pacing": [
        r"(?:progression|progress|unlocking|upgrade system) (?:is|was|feels?)? ?(?:slow|bad|poor|grindy|tedious|unbalanced)",
        r"(?:too much|endless|forced) grind", r"(?:stuck|blocked) (?:behind|at) (?:a )?(?:grind|progress)",
        r"(?:slow|grindy|tedious) (?:progression|progress|unlocking)",
        r"(?:progression|การปลดล็อก)(?:ช้า|น่าเบื่อ|ฝืด)|ต้องฟาร์ม(?:นาน|เยอะ)",
    ],
    "Building & Decoration": [
        r"(?:building|decoration|customi[sz]ation|furniture) (?:is|was|feels?)? ?(?:limited|bad|poor|awkward|restrictive)",
        r"(?:limited|not enough|lack of) (?:building|decoration|customi[sz]ation|furniture) options",
        r"(?:build|decorate) (?:is|was|feels?)? ?(?:awkward|clunky|restrictive)",
        r"(?:แต่งบ้าน|สร้างบ้าน)(?:ยาก|จำกัด|น้อย)",
    ],
    "Exploration & Discovery": [
        r"(?:exploration|map|world|discovery) (?:is|was|feels?)? ?(?:limited|small|empty|boring|repetitive)",
        r"(?:nothing|little) to explore", r"(?:small|empty) (?:map|world)",
        r"(?:สำรวจ|แผนที่)(?:น้อย|เล็ก|น่าเบื่อ)",
    ],
    "Management & Tasks": [
        r"(?:management|tasks?|customers?|chores?) (?:is|are|was|were|feels?)? ?(?:tedious|repetitive|boring|overwhelming)",
        r"(?:too many|endless) (?:tasks?|chores?)", r"(?:tedious|repetitive) (?:tasks?|chores?)",
        r"(?:งาน|ภารกิจ)(?:ซ้ำ|น่าเบื่อ|เยอะเกิน)",
    ],
    "Multiplayer & Social Play": [
        r"(?:no|lack of|needs?) (?:co-?op|multiplayer|online multiplayer)",
        r"(?:co-?op|multiplayer) (?:is|was|feels?)? ?(?:broken|bad|missing|limited)",
        r"(?:ไม่มี|ขาด)(?:โคออป|มัลติ)",
    ],
}
GENERIC = {
    "Technical problems": [r"\b(?:crash(?:es|ed|ing)?|bug(?:s|gy)?|glitch(?:es)?|lag(?:gy)?|stutter(?:ing)?|performance)\b"],
    "Price/value": [r"\b(?:too expensive|overpriced|not worth|refund)\b"],
    "Short/low content": [r"\b(?:too short|very short|lack of content|not enough content)\b"],
}
PATTERNS = {k: re.compile("|".join(v), re.I) for k, v in {**TOPICS, **GENERIC}.items()}

# Secondary, sentence-level rule.  A review can naturally say “the map is
# empty” rather than one of our exact phrases.  We accept that only when the
# feature and a negative cue appear in the same sentence.  This is still much
# stricter than the old method, which counted a feature word anywhere in a
# negative review.
FEATURE_WORDS = {
    "Story & Characters": r"\b(?:story|plot|narrative|writing|dialogue|character(?:s)?)\b|เนื้อเรื่อง|บทสนทนา|ตัวละคร",
    "Progression & Pacing": r"\b(?:progress(?:ion)?|unlock(?:ing)?|upgrades?|grind(?:ing)?)\b|การปลดล็อก|ฟาร์มของ",
    "Building & Decoration": r"\b(?:build(?:ing)?|decorat(?:e|ion)|furniture|customi[sz](?:e|ation))\b|แต่งบ้าน|สร้างบ้าน",
    "Exploration & Discovery": r"\b(?:explor(?:e|ation)|map|world|discover(?:y)?)\b|สำรวจ|แผนที่",
    "Management & Tasks": r"\b(?:management|tasks?|chores?|customers?)\b|ภารกิจ|งาน",
    "Multiplayer & Social Play": r"\b(?:co-?op|multiplayer|online)\b|โคออป|มัลติ",
}
NEGATIVE_CUE = re.compile(r"\b(?:bad|poor|weak|boring|bland|flat|shallow|slow|grindy|tedious|repetitive|limited|missing|lack(?:s|ing)?|no|not enough|too (?:much|many|slow|small|short)|empty|awkward|clunky|frustrating|unbalanced|broken|annoying)\b|(?:แย่|น่าเบื่อ|ช้า|จำกัด|ไม่มี|น้อย|ยาก|ซ้ำ|ฝืด)", re.I)
FEATURE_PATTERNS = {topic: re.compile(words, re.I) for topic, words in FEATURE_WORDS.items()}


def request_json(url, params):
    for attempt in range(4):
        try:
            r = requests.get(url, params=params, timeout=45, headers={"User-Agent": "MADT7202-educational-research/2.0"})
            if r.status_code == 200:
                return r.json()
            if r.status_code not in (429, 500, 502, 503):
                return None
        except requests.RequestException:
            pass
        time.sleep(2 ** attempt)
    return None


def fetch_reviews(appid, lang):
    rows, seen, cursor = [], set(), "*"
    while len(rows) < N_PER_LANGUAGE:
        js = request_json(f"https://store.steampowered.com/appreviews/{appid}", {
            "json": 1, "filter": "recent", "language": lang, "review_type": "negative",
            "purchase_type": "all", "num_per_page": 100, "cursor": cursor,
        })
        if not js or not js.get("success"):
            break
        batch = js.get("reviews", [])
        if not batch:
            break
        for review in batch:
            rid = review.get("recommendationid")
            text = review.get("review", "").strip()
            if rid not in seen and text:
                seen.add(rid)
                rows.append({"review_id": str(rid), "language": lang, "timestamp": review.get("timestamp_created"), "text": text})
        nxt = js.get("cursor")
        if not nxt or nxt == cursor:
            break
        cursor = nxt
        time.sleep(1.05)  # respectful pacing: one public-endpoint page per second
    return rows[:N_PER_LANGUAGE]


def topic_hits(text):
    hits = [topic for topic, pattern in PATTERNS.items() if pattern.search(text)]
    # Preserve sentence boundaries before testing proximity.
    sentences = re.split(r"[.!?\n]+", text)
    for topic, pattern in FEATURE_PATTERNS.items():
        if topic not in hits:
            # Same sentence alone is too loose for long Steam reviews.  Require
            # the feature and negative cue to be within roughly ten words.
            for sentence in sentences:
                for feature in pattern.finditer(sentence):
                    for negative in NEGATIVE_CUE.finditer(sentence):
                        if abs(feature.start() - negative.start()) <= 70:
                            hits.append(topic)
                            break
                    if topic in hits:
                        break
                if topic in hits:
                    break
    return hits


def winner(edges):
    if edges.empty:
        return None
    ranked = edges.groupby("topic").agg(games=("game", "nunique"), matches=("n", "sum")).reset_index()
    return ranked.sort_values(["games", "matches", "topic"], ascending=[False, False, True]).iloc[0].to_dict()


def graph_for(reviews, share, minimum):
    rows = []
    for (game, topic), n in reviews.explode("topics").dropna(subset=["topics"]).query("topics in @TOPICS").groupby(["game", "topics"]).size().items():
        denom = int((reviews.game == game).sum())
        s = n / denom
        if n >= minimum and s >= share:
            rows.append({"game": game, "topic": topic, "n": int(n), "share": round(s, 4), "review_total": denom})
    return pd.DataFrame(rows, columns=["game", "topic", "n", "share", "review_total"])


def main():
    collected = []
    for game, appid in GAMES.items():
        for lang in LANGS:
            for item in fetch_reviews(appid, lang):
                item.update(game=game, appid=appid)
                collected.append(item)
    reviews = pd.DataFrame(collected)
    if reviews.empty:
        raise RuntimeError("Steam returned no reviews; rerun later.")
    reviews["topics"] = reviews.text.map(topic_hits)
    # De-identified frozen snapshot: raw text is omitted; reproducibility uses hash + coded topics.
    snap = reviews.assign(text_hash=reviews.text.map(lambda x: hashlib.sha256(x.encode()).hexdigest()))[["game", "appid", "review_id", "language", "timestamp", "text_hash", "topics"]]
    snap.to_json(DATA / "review_snapshot.jsonl", orient="records", lines=True, force_ascii=False)
    snap.to_csv(DATA / "review_snapshot.csv", index=False)
    edges = graph_for(reviews, LINK_SHARE, MIN_MATCHES)
    edges.to_csv(OUT / "edges.csv", index=False)
    ranked = (reviews.explode("topics").dropna(subset=["topics"]).query("topics in @TOPICS")
              .groupby("topics").size().rename("matches").reset_index().rename(columns={"topics": "topic"}))
    coverage = edges.groupby("topic").agg(games=("game", "nunique"), qualifying_matches=("n", "sum")).reset_index()
    topics = pd.DataFrame({"topic": list(TOPICS)}).merge(ranked, on="topic", how="left").merge(coverage, on="topic", how="left").fillna(0)
    topics[["matches", "games", "qualifying_matches"]] = topics[["matches", "games", "qualifying_matches"]].astype(int)
    topics = topics.sort_values(["games", "qualifying_matches", "topic"], ascending=[False, False, True])
    topics.to_csv(OUT / "topic_table.csv", index=False)
    win = winner(edges)
    # Robustness: predeclared cutoff matrix, no parameter selected after seeing the result.
    sweep = []
    for share in SWEEP_SHARE:
        for minimum in SWEEP_MIN:
            e = graph_for(reviews, share, minimum)
            w = winner(e)
            sweep.append({"share": share, "minimum": minimum, "winner": w["topic"] if w else "none", "coverage": int(w["games"]) if w else 0})
    pd.DataFrame(sweep).to_csv(OUT / "robustness_sweep.csv", index=False)
    # Audit manifest: reproducible random sample of all feature-topic matches.
    # Text stays local and is intentionally not added to the repository.
    hits = [(i, topic) for i, ts in enumerate(reviews.topics) for topic in ts if topic in TOPICS]
    pick = RNG.choice(len(hits), size=min(120, len(hits)), replace=False)
    audit = pd.DataFrame([{"game": reviews.iloc[i].game, "language": reviews.iloc[i].language, "topic": topic,
                           "review_id": reviews.iloc[i].review_id, "text_hash": hashlib.sha256(reviews.iloc[i].text.encode()).hexdigest(),
                           "correct": "", "reason": ""} for i, topic in (hits[j] for j in pick)])
    audit.to_csv(OUT / "audit_manifest.csv", index=False)
    generic_rates = {name: round(float(reviews.topics.map(lambda x: name in x).mean()), 4) for name in GENERIC}
    dates = pd.to_datetime(reviews.timestamp, unit="s", utc=True)
    stats = {
        "run_utc": datetime.now(timezone.utc).isoformat(), "question": "Which rival weakness should our new cozy game turn into its strength?",
        "sample": {"games": len(GAMES), "reviews": len(reviews), "languages": dict(Counter(reviews.language)), "period": [str(dates.min().date()), str(dates.max().date())], "per_language_cap": N_PER_LANGUAGE},
        "edge_definition": f"A game-topic edge requires at least {MIN_MATCHES} coded negative reviews and at least {LINK_SHARE:.0%} of that game's sampled negative reviews.",
        "winner": win, "generic_rates": generic_rates, "snapshot_sha256": hashlib.sha256((DATA / "review_snapshot.jsonl").read_bytes()).hexdigest(),
        "notes": ["Review text is not published; the snapshot keeps only de-identified IDs, timestamps, language, a text hash, and codes.", "A coding hit is a complaint phrase, not a bare feature mention. Hand-check audit still required before decision claim."],
    }
    (OUT / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
