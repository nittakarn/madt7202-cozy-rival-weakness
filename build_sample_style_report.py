"""A compact, Sample-C-style one-page A4 report using this project's own data."""
import json
from pathlib import Path
import pandas as pd
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).resolve().parent
OUT, REPORT = ROOT / "outputs", ROOT / "report"
stats = json.loads((OUT / "stats.json").read_text())
edges = pd.read_csv(OUT / "edges.csv")
topics = pd.read_csv(OUT / "topic_table.csv")
pdf = REPORT / "MADT7202_MidTerm_SampleStyle_Nittakarn.pdf"
W, H = A4
BLUE, ORANGE, INK, GRID, FADE = map(HexColor, ["#30339A", "#F26B21", "#313746", "#C8CDDA", "#E9ECF4"])
c = Canvas(str(pdf), pagesize=A4)
L, R = 58, W-58

def tx(x, y, s, size=9, color=INK, font="Helvetica"):
    c.setFillColor(color); c.setFont(font, size); c.drawString(x, y, s)

def para(x, y, s, width, size=8.5, lead=10):
    words, line = s.split(), ""
    for w in words:
        trial = (line + " " + w).strip()
        if stringWidth(trial, "Helvetica", size) > width and line:
            tx(x, y, line, size); y -= lead; line = w
        else: line = trial
    if line: tx(x, y, line, size); y -= lead
    return y

def head(y, n, title):
    tx(L, y, str(n), 9.5, ORANGE, "Helvetica-Bold")
    tx(L+14, y, title, 9.5, BLUE, "Helvetica")
    return y - 14

def table(y, rows, leftw=116):
    height = 0
    for _, v in rows:
        lines = max(1, int(stringWidth(v, "Helvetica", 8.1)/(R-L-leftw-12)) + 1)
        height += max(17, lines*9+6)
    top = y
    for label, value in rows:
        rowh = max(17, (int(stringWidth(value, "Helvetica", 8.1)/(R-L-leftw-12)) + 1)*9+6)
        c.setFillColor(FADE); c.rect(L, y-rowh, leftw, rowh, fill=1, stroke=0)
        c.setStrokeColor(GRID); c.rect(L, y-rowh, R-L, rowh, fill=0, stroke=1)
        c.line(L+leftw, y-rowh, L+leftw, y)
        tx(L+6, y-12, label, 8.1)
        para(L+leftw+6, y-11, value, R-L-leftw-12, 8.1, 9)
        y -= rowh
    return y-8

# Heading - matches the sample's restrained hierarchy, not its exact artwork.
tx(L, H-40, "MADT 7202 · Mid-Term Applied Case", 8.3, ORANGE)
tx(L, H-59, "Which Rival Weakness Should Our New Cozy Game Turn Into Its Strength?", 13.3, BLUE)
c.setStrokeColor(ORANGE); c.line(L, H-66, R, H-66)
y = H-84

y = head(y, 1, "The decision")
tx(L, y, "Which weakness should a new cozy-game studio turn into its differentiating strength?", 8.4)
y -= 17

y = head(y, 2, "Why a network")
y = para(L, y, "A frequency table selects the loudest complaint. The decision needs the complaint shared by the most distinct rivals, which is a relationship pattern between game and complaint nodes.", R-L, 8.35, 9.6) - 3

y = head(y, 3, "Data")
s = stats["sample"]
y = table(y, [
    ("Source", "Recent negative reviews from Steam's public appreviews endpoint; 15 fixed rival games."),
    ("Access / privacy", "Educational use; paced public requests. No account login, usernames, profiles or Steam IDs retained."),
    ("Period / volume", f"{s['period'][0]} - {s['period'][1]} · {s['reviews']:,} reviews · English {s['languages'].get('english',0):,}; Thai {s['languages'].get('thai',0)}."),
    ("Sampling bias", "Recent, self-selected and English-heavy negative reviews; not all players and not causal evidence."),
])

y = head(y, 4, "Graph construction")
y = table(y, [
    ("Node / edge", "A rival game or complaint topic; an edge asserts a qualifying coded complaint relationship in that game's reviews."),
    ("Weighting", "Conditional share: coded complaints for a game-topic pair divided by that game's sampled negative reviews (Chapter 6 Scheme 4)."),
    ("Pruning", "At least 5 coded reviews and 5% of a game's sample. Generic technical, price/value and short-content complaints excluded."),
    ("Result", f"{len(set(edges.game)) + len(set(edges.topic))} nodes, {len(edges)} edges. A topic is coded only with a complaint phrase or nearby negative cue, never a bare feature word."),
])

y = head(y, 5, "The graph")
# Compact bipartite graph, central like Sample C.
box_top, box_bottom = y, y-174
topic_order = list(topics.query("games > 0").topic)
games = list(dict.fromkeys(edges.game))
ty = {t: box_top-22-i*31 for i,t in enumerate(topic_order)}
gy = {g: box_top-15-i*19 for i,g in enumerate(games)}
lx, rx = 224, 354
for row in edges.itertuples():
    c.setStrokeColor(ORANGE if row.topic == stats["winner"]["topic"] else GRID)
    c.setLineWidth(.45 + 1.5*row.share/edges.share.max())
    c.line(lx, ty[row.topic], rx, gy[row.game])
for topic in topic_order:
    c.setFillColor(ORANGE if topic == stats["winner"]["topic"] else BLUE); c.circle(lx, ty[topic], 4.6, fill=1, stroke=0)
    tx(lx-8-stringWidth(topic, "Helvetica", 6.6), ty[topic]-2, topic, 6.6, INK)
for game in games:
    c.setFillColor(ORANGE); c.circle(rx, gy[game], 3.9, fill=1, stroke=0)
    label = game if len(game)<22 else game[:21]+"…"
    tx(rx+6, gy[game]-2, label, 6.2)
y = box_bottom-3

y = head(y, 6, "Findings")
w = stats["winner"]
runner = topics.loc[topics.topic == "Progression & Pacing"].iloc[0]
y = para(L+12, y, f"• Story & Characters is the broadest shared weakness: {int(w['games'])} rival games, {int(w['matches'])} coded matches. Progression & Pacing is louder ({int(runner.matches)} matches) but reaches only {int(runner.games)} rivals.", R-L-12, 8.2, 9.5)
y = para(L+12, y, "• Robustness: Story wins 6 of 9 predeclared cutoff settings; at the strict 8% share cutoff, Progression wins. The decision is robust but not absolute.", R-L-12, 8.2, 9.5) - 2

y = head(y, 7, "Recommended action")
y = para(L+12, y, "• Build character arcs, meaningful relationship choices and dialogue playtests before scaling content. • Track narrative clarity in playtests; do not make a generic price or bug claim the game’s differentiator.", R-L-12, 8.2, 9.5) - 2

y = head(y, 8, "What would change my mind")
para(L, y, "If a stratified player survey or playtest shows that players value progression pain points more than narrative weakness, shift investment to pacing. Re-run the analysis after a meaningful change in review volume or game mix.", R-L, 8.2, 9.5)
c.save(); print(pdf)
