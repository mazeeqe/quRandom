"""Regenerate the pictures in docs/images/ (Project Card, README).

Run from the repository root:  python scripts/make_figures.py

- thumbnail.png: Project Card thumbnail
- how_it_works.png: one circuit -> bits -> pool -> numbers, plus the Bell test
- circuit.png: the circuit (4 random-number qubits + 4 Bell-test qubits, for readability)
- demo_chart.png: demo chart on a test backend with a simulated 3% bias toward 1
- randomness_report.png, bell_test.png: demo charts from Qiskit's built-in simulator
"""
import math
import pathlib
import random
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
OUT = ROOT / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)

from qiskit.providers.basic_provider import BasicSimulator
from test_qrand import BiasedBackend

from qrand import QuantumRandom, stats

ORANGE, BLUE, INK, PAPER = "#ff7a59", "#5b6cff", "#1d2333", "#f6f7fb"


def demo_charts(backend, names):
    """Run main.py's demo on `backend` and save its charts under `names` (None = skip)."""
    namespace = {"__name__": "__main__", "backend": backend}
    exec((ROOT / "main.py").read_text(), namespace)  # noqa: S102 - runs our own main.py like Qollab does
    queue = list(names)

    def save():
        name = queue.pop(0)
        if name:
            plt.savefig(OUT / name, dpi=110, bbox_inches="tight")
        plt.close()

    plt.show = save
    namespace["main"]()


def circuit():
    qr = QuantumRandom(n_qubits=4, shots=64, debias="none", bell_test=True)
    fig = qr.circuit.draw("mpl", fold=-1, style={"backgroundcolor": "#ffffff"})
    fig.savefig(OUT / "circuit.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def box(ax, x, y, w, h, title, body, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.04",
                                fc="white", ec=color, lw=2))
    ax.text(x + w / 2, y + h - 0.09, title, ha="center", va="top", fontsize=11,
            fontweight="bold", color=INK)
    ax.text(x + w / 2, y + h - 0.24, body, ha="center", va="top", fontsize=8.5, color="#444",
            linespacing=1.4)


def arrow(ax, x0, y0, x1, y1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops={"arrowstyle": "-|>", "color": INK, "lw": 1.6})


def how_it_works():
    fig, ax = plt.subplots(figsize=(12, 4.6))
    fig.patch.set_facecolor(PAPER)
    ax.set(xlim=(0, 6.1), ylim=(0.15, 2.25))
    ax.axis("off")
    w, h, y = 1.05, 0.95, 1.2
    steps = [
        ("1. One circuit", "Hadamard on every qubit,\nthen measure:\neach qubit is a\n50/50 coin flip", BLUE),
        ("2. One job", "8 qubits x 512 shots\n= 4096 raw bits.\nIonQ allows one job\nper run", BLUE),
        ("3. Check & debias", "P(1) per qubit, NIST tests,\nmin-entropy, random walk.\nxor / von Neumann\nremove bias", ORANGE),
        ("4. Numbers", "randint, random, choice,\nshuffle from the pool.\nRejection sampling:\nno modulo bias", BLUE),
    ]
    xs = [0.1 + i * 1.5 for i in range(4)]
    for x, (title, body, color) in zip(xs, steps):
        box(ax, x, y, w, h, title, body, color)
    for x in xs[:-1]:
        arrow(ax, x + w + 0.03, y + h / 2, x + 1.5 - 0.03, y + h / 2)
    box(ax, 1.25, 0.25, 3.3, 0.7, "Same circuit and job: Bell test on 4 extra qubits",
        "Two quantum coins pick the measurement directions of an entangled pair.\n"
        "Classical sources give S <= 2; quantum mechanics predicts S = 2.83.", "#2a9d8f")
    arrow(ax, xs[0] + w / 2, y - 0.02, 1.25 + 0.15, 0.95 - 0.03)
    fig.savefig(OUT / "how_it_works.png", dpi=110, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)


def thumbnail():
    rng = random.Random(42)
    fig = plt.figure(figsize=(12, 6.3))
    fig.patch.set_facecolor(INK)
    # background: random bits as "TV static"
    bg = fig.add_axes((0, 0, 1, 1))
    bits = [[rng.random() < 0.5 for _ in range(96)] for _ in range(50)]
    bg.imshow(bits, cmap=matplotlib.colors.ListedColormap([INK, "#2b3350"]),
              interpolation="nearest", aspect="auto")
    bg.axis("off")
    # random walk across the card
    walk_ax = fig.add_axes((0.05, 0.08, 0.9, 0.42))
    walk_ax.patch.set_alpha(0)
    steps = "".join(rng.choice("01") for _ in range(1500))
    n = len(steps) + 1
    band = [2 * math.sqrt(t) for t in range(n)]
    walk_ax.fill_between(range(n), [-b for b in band], band, color="white", alpha=0.08)
    walk_ax.plot(stats.random_walk(steps), color=ORANGE, lw=2.2)
    walk_ax.axhline(0, color="white", lw=0.6, alpha=0.4)
    walk_ax.set(xlim=(0, n), ylim=(-95, 95))
    walk_ax.axis("off")
    fig.text(0.06, 0.80, "quRandom", fontsize=64, fontweight="bold", color="white")
    fig.text(0.065, 0.70, "Noise-aware random numbers from a quantum circuit",
             fontsize=22, color="#c9d1ff")
    fig.text(0.065, 0.625, "Qiskit  ·  IonQ  ·  NIST health tests  ·  Bell test (CHSH)",
             fontsize=15, color="#9aa5c8")
    fig.text(0.94, 0.82, "|0⟩ → H → measure → 0 / 1", fontsize=16, color=ORANGE,
             ha="right", family="DejaVu Sans Mono")
    fig.savefig(OUT / "thumbnail.png", dpi=100, facecolor=INK)
    plt.close(fig)


if __name__ == "__main__":
    thumbnail()
    how_it_works()
    circuit()
    demo_charts(BiasedBackend(0.53), ["demo_chart.png", None, None])
    seeded = BasicSimulator()
    seeded.set_options(seed_simulator=2026)  # same pictures on every run
    demo_charts(seeded, [None, "randomness_report.png", "bell_test.png"])
    for p in sorted(OUT.glob("*.png")):
        print(p.relative_to(ROOT), f"{p.stat().st_size // 1024} KB")
