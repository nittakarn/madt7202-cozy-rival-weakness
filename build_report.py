"""Create the submission-ready one-page A4 report from outputs/ only."""
import json
from pathlib import Path

import pandas as pd
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).resolve().parent
OUT, REPORT = ROOT / "outputs", ROOT / "report"
REPORT.mkdir(exist_ok=True)
stats = json.loads((OUT / "stats.json").read_text())
edges = pd.read_csv(OUT / "edges.csv")
topics = pd.read_csv(OUT / "topic_table.csv")
pdf = REPORT / "MADT7202_MidTerm_Rebuilt_Nittakarn.pdf"

W, H = A4
NAVY, ORANGE, INK, MUTED, PALE, BLUE = map(HexColor, ["#182544", "#E36B38", "#1F2937", "#5E6A7D", "#F4F6FA", "#2463A5"])
c = Canvas(str(pdf), pagesize=A4)

def text(x, y, s, size=9, color=INK, font="Helvetica"):
    c.setFont(font, size); c.setFillColor(color); c.drawString(x, y, s)

def wrap(x, y, s, width, size=8.5, leading=10.5, color=INK, font="Helvetica"):
    words, line = s.split(), ""
    for word in words:
        test = (line + " " + word).strip()
        if stringWidth(test, font, size) > width and line:
            text(x, y, line, size, color, font); y -= leading; line = word
        else: line = test
    if line: text(x, y, line, size, color, font); y -= leading
    return y

def pill(x, y, label, fill, fg=white):
    c.setFillColor(fill); c.roundRect(x, y-3, stringWidth(label, "Helvetica-Bold", 8)+12, 16, 8, fill=1, stroke=0)
    text(x+6, y+2, label, 8, fg, "Helvetica-Bold")

# Header
c.setFillColor(NAVY); c.rect(0, H-88, W, 88, fill=1, stroke=0)
text(38, H-35, "MADT 7202 · Mid-Term Applied Case", 9, white, "Helvetica-Bold")
text(38, H-58, "Which Rival Weakness Should Our New Cozy Game Turn Into Its Strength?", 15.2, white, "Helvetica-Bold")
text(38, H-76, "Rebuilt, reproducible analysis · Steam negative-review snapshot · 15 rival cozy games", 8.3, HexColor("#D8E1EF"))

# Decision box
top = H - 108
c.setFillColor(HexColor("#FFF4ED")); c.roundRect(34, top-65, W-68, 58, 8, fill=1, stroke=0)
pill(46, top-22, "DECISION", ORANGE)
text(46, top-43, "Make STORY & CHARACTERS our differentiating strength.", 12, NAVY, "Helvetica-Bold")
winner = stats["winner"]
runner = topics.loc[topics.topic == "Progression & Pacing"].iloc[0]
text(46, top-57, f"It is a qualified complaint in {int(winner['games'])}/15 rivals; Progression & Pacing is louder, but appears in only {int(runner.games)}/15.", 8.2, INK)

# Context two columns
left, right, colw = 38, 309, 248
y = top - 88
text(left, y, "1. The decision and why this is a network", 10.2, NAVY, "Helvetica-Bold")
y = wrap(left, y-14, "Before pre-production, the studio must choose one experience to do noticeably better. A table would choose the most frequent complaint, which can be driven by a few games. The bipartite network ranks market breadth: how many distinct rivals connect to each complaint.", colw, 8.25)
text(right, top-88, "2. Data and scope", 10.2, NAVY, "Helvetica-Bold")
sample = stats["sample"]
wrap(right, top-102, f"Frozen run: {sample['reviews']:,} recent negative Steam reviews from {sample['games']} fixed rivals; English {sample['languages'].get('english',0):,}, Thai {sample['languages'].get('thai',0)}; {sample['period'][0]}–{sample['period'][1]}. Max {sample['per_language_cap']} reviews/game/language.", colw, 8.25)

# Graph section
gy = 500
text(38, gy+18, "3. Network result — one line = a qualifying game × complaint relationship", 10.2, NAVY, "Helvetica-Bold")
text(38, gy+5, "Edge rule: ≥5 coded reviews AND ≥5% of that game’s sampled negative reviews. Orange = game; blue = complaint.", 7.8, MUTED)
c.setFillColor(PALE); c.roundRect(34, 282, W-68, 188, 8, fill=1, stroke=0)

# manually stable bipartite layout: complaint nodes left, games right
topic_order = list(topics.query("games > 0").topic)
glist = list(dict.fromkeys(edges.game))
topic_y = {t: 438 - i*34 for i,t in enumerate(topic_order)}
game_y = {g: 444 - i*21 for i,g in enumerate(glist)}
tx, gx = 186, 417
for row in edges.itertuples():
    c.setStrokeColor(ORANGE if row.topic == "Story & Characters" else HexColor("#B9C8DD"))
    c.setLineWidth(0.5 + 2.2*row.share/edges.share.max())
    c.line(tx+6, topic_y[row.topic], gx-6, game_y[row.game])
for topic in topic_order:
    hot = topic == "Story & Characters"
    c.setFillColor(ORANGE if hot else BLUE); c.circle(tx, topic_y[topic], 6 if hot else 5, fill=1, stroke=0)
    text(48, topic_y[topic]-3, topic, 8.4 if hot else 7.6, NAVY, "Helvetica-Bold" if hot else "Helvetica")
    val = topics.loc[topics.topic == topic].iloc[0]
    text(48, topic_y[topic]-14, f"{int(val.games)}/15 rivals · {int(val.qualifying_matches)} qualifying coded reviews", 6.7, MUTED)
for game in glist:
    c.setFillColor(ORANGE); c.circle(gx, game_y[game], 4, fill=1, stroke=0)
    label = game if len(game) <= 25 else game[:24] + "…"
    text(gx+8, game_y[game]-2.6, label, 6.5, INK)

# Bottom: method, action, limitation
by = 257
text(left, by, "4. Construction and robustness checks", 10.1, NAVY, "Helvetica-Bold")
wrap(left, by-14, "Each whole review belongs to one game. A line does NOT mean games are directly related: it means players in that one game raised the coded complaint often enough to pass the rule. A topic is coded only when a topic phrase or a topic word within about ten words of a negative cue appears in the same sentence—never from a bare feature word. Weight is conditional share, count(game, topic)/count(game), following Chapter 6 Scheme 4. The ranking excludes generic technical, price/value and short-content complaints. Unit tests verify that bare feature mentions are not coded as complaints.", colw, 7.55, 8.8)
text(right, by, "5. Action, comparison and limits", 10.1, NAVY, "Helvetica-Bold")
wrap(right, by-14, f"Action: budget a character-writing and dialogue loop: distinct character arcs, choices that affect relationships, and playtest narrative clarity before content scale. Comparison: Progression & Pacing has {int(runner.matches)} coded matches versus Story’s {int(topics.iloc[0].matches)}, but reaches {int(runner.games)} rather than {int(winner['games'])} rivals—why the network changes the decision. Robustness: Story wins 6 of 9 predeclared cutoff settings; at the strict 8% cutoff, Progression wins. Limit: recent, self-selected English-heavy negative reviews are not all players or causal proof.", colw, 7.7, 9.1)

# Footer
c.setStrokeColor(HexColor("#D6DDE8")); c.line(34, 42, W-34, 42)
text(38, 28, "Reproducibility: rebuild_analysis.py → outputs/ → build_report.py · raw text not published; de-identified snapshot SHA-256:", 6.8, MUTED)
text(38, 18, stats["snapshot_sha256"], 6.5, MUTED, "Courier")
text(375, 18, "Branch: codex/rebuild-validated-analysis", 6.5, MUTED)
c.save()
print(pdf)
