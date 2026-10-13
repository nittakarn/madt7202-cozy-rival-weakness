"""Sample-C style network: small dots, tiny labels, thin lavender lines, orange highlight.
usage: fig_c.py <outputs_dir> <out.png> [width_in height_in]"""
import sys, json, re
import numpy as np, pandas as pd, networkx as nx
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.patheffects as pe

D, OUTF = sys.argv[1], sys.argv[2]
W = float(sys.argv[3]) if len(sys.argv) > 3 else 5.2
HGT = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0
FS = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
MIN = float(sys.argv[6]) if len(sys.argv) > 6 else 0.21
plt.rcParams["font.family"] = "Inter"

st = json.load(open(f"{D}/stats.json"))
E = pd.read_csv(f"{D}/edges.csv"); TT = pd.read_csv(f"{D}/topic_table.csv"); games = pd.read_csv(f"{D}/games.csv")
T_ = TT.set_index("topic"); WIN = st["winner"]["topic"]; w = T_.loc[WIN]
NG = len(games)

def short(n):
    n = re.split(r" - | \(|: |,", n)[0]
    return n if len(n) <= 16 else n[:15] + "…"

H = nx.Graph()
for r in E.itertuples():
    H.add_node(r.game, kind="game"); H.add_node(r.topic, kind="topic")
    H.add_edge(r.game, r.topic, share=r.share)

pos = nx.kamada_kawai_layout(H, weight=None)
P = np.array([pos[k] for k in H]); P = (P - P.min(0)) / np.ptp(P, 0)
P[:, 0] *= W / HGT
for _ in range(800):
    moved = False
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            d = P[j] - P[i]; dist = np.hypot(*d)
            if dist < MIN:
                push = d / (dist + 1e-9) * (MIN - dist) / 2; P[i] -= push; P[j] += push; moved = True
    if not moved: break
pos = {k: tuple(v) for k, v in zip(H, P)}

ORANGE, NAVY, LINE, INK2 = "#f26b21", "#2e2f86", "#c7c9e0", "#4a4d5c"
vol = T_.reviews.to_dict(); pop = games.set_index("game").reviews.to_dict()
size = {v: FS**2*(14 + 46 * pop[v] / max(pop.values())) if H.nodes[v]["kind"] == "game"
        else FS**2*(16 + 70 * vol[v] / max(vol.values())) for v in H}
smax = E.share.max()

fig, ax = plt.subplots(figsize=(W, HGT), dpi=300)
for u, v, d in H.edges(data=True):
    hot = WIN in (u, v)
    ax.plot(*zip(pos[u], pos[v]), color=ORANGE if hot else LINE, lw=(0.5 + 1.6 * d["share"] / smax),
            alpha=0.95 if hot else 0.85, zorder=2 if hot else 1, solid_capstyle="round")
for v in H:
    ax.scatter(*pos[v], s=size[v], color=NAVY if H.nodes[v]["kind"] == "topic" else ORANGE,
               edgecolors="none", zorder=3)
halo = [pe.withStroke(linewidth=1.6*FS, foreground="white")]
for v, (x, y) in pos.items():
    is_t = H.nodes[v]["kind"] == "topic"
    ax.annotate(v if is_t else short(v), (x, y), xytext=(0, -(size[v] ** 0.5) / 2 - 0.8), textcoords="offset points",
                ha="center", va="top", fontsize=(4.6 if is_t else 4.1)*FS, fontweight="bold" if is_t else "normal",
                color=NAVY if is_t else INK2, path_effects=halo, zorder=4)

# one orange note, like Sample C: placed in the emptiest spot near the winner
pts = np.array(list(pos.values()) + [tuple(np.array(pos[a]) * f + np.array(pos[b]) * (1 - f))
                                     for a, b in H.edges() for f in (0.25, 0.5, 0.75)])
x, y = pos[WIN]; best, bd = None, -1
for a in np.linspace(0, 2 * np.pi, 32, endpoint=False):
    for r in (0.18, 0.24, 0.30):
        tx, ty = x + r * np.cos(a), y + r * np.sin(a)
        if not (P[:, 0].min() <= tx <= P[:, 0].max() and P[:, 1].min() <= ty <= P[:, 1].max() + 0.05): continue
        dd = np.min(np.hypot(pts[:, 0] - tx, pts[:, 1] - ty))
        if dd > bd: best, bd = (tx, ty), dd
ax.annotate(f"criticised in {int(w.games)} of {NG} rival games", (x, y), xytext=best, textcoords="data",
            ha="center", va="center", fontsize=4.4*FS, color=ORANGE, path_effects=halo, zorder=5,
            arrowprops=dict(arrowstyle="-", color=ORANGE, lw=0.5, shrinkA=1, shrinkB=2))

ax.margins(0.06); ax.axis("off"); ax.set_aspect("equal")
fig.tight_layout(pad=0.05)
fig.savefig(OUTF, dpi=300, bbox_inches="tight", facecolor="white")
print("saved", OUTF)
