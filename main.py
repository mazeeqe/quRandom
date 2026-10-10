"""qrand demo for Qollab: quantum circuit -> bitstring -> random numbers.

Press Run, pick a QPU (built-in simulator or an IonQ remote simulator),
and set Shots / Qubits / Debias under Run settings.
"""
import math

from qrand import EntropyExhausted, QuantumRandom, stats
from qrand import bell as bell_module

try:
    backend  # noqa: B018 - raises NameError unless Qollab pre-created it (Select QPU dialog)
    RUNNING_LOCALLY = False
except NameError:  # running locally: fall back to Qiskit's simulator
    from qiskit.providers.basic_provider import BasicSimulator
    backend = BasicSimulator()
    RUNNING_LOCALLY = True


HEALTH_TESTS = [
    ("monobit_p", "frequency"),
    ("block_frequency_p", "block frequency"),
    ("runs_p", "runs"),
    ("longest_run_p", "longest run of 1s"),
    ("serial_p", "serial (3-bit)"),
]


def pass_fail(p):
    return "n/a" if math.isnan(p) else f"{p:.3f} {'pass' if p >= 0.01 else 'FAIL'}"


def randomness_score(r):
    """Summary strings for one column of the randomness score table."""
    passed = sum(1 for key, _ in HEALTH_TESTS if not math.isnan(r[key]) and r[key] >= 0.01)
    limit = stats.autocorr_limit(r["bits"])
    return {
        "passed": f"{passed}/{len(HEALTH_TESTS)}",
        "entropy": f"{r['min_entropy']:.3f} / {stats.ideal_min_entropy_per_bit(r['bits']):.3f}",
        "pattern": "none found" if r["max_autocorr"] <= limit else "FOUND",
    }


def chsh_verdict(chsh):
    if math.isnan(chsh["S"]):
        return "Not enough shots for every setting pair: raise Shots."
    if chsh["S"] > chsh["classical_limit"]:
        return (f"S is {chsh['sigmas_above_classical']:.1f} standard errors above 2: no classical "
                "source of correlated bits can produce this.")
    return ("S is not above 2 here, so these results could also come from a classical source. "
            "Noise can wash out quantum correlations.")


def format_s(chsh):
    return "-" if not chsh or math.isnan(chsh["S"]) else f"{chsh['S']:.2f} ± {chsh['sigma']:.2f}"


def bar(p, width=30):
    return "#" * round(p * width) + "." * (width - round(p * width))


def main(shots: int = 512, qubits: int = 8, debias: str = "xor", plot: bool = True, bell: bool = True):
    qr = QuantumRandom(backend, n_qubits=qubits, shots=shots, debias=debias, bell_test=bell)
    rep = qr.report()

    print("=== 1. The circuit: Hadamard on every qubit, then measure ===")
    print(qr.circuit.draw("text"))
    if bell:
        print(f"Qubits 0-{qubits - 1}: random numbers. Qubits {qubits}-{qubits + 3}: Bell test "
              "(two setting coins and an entangled pair), in the same circuit and job.")
    kind = "real quantum hardware" if rep["hardware"] else "simulator"
    print(f"Backend: {rep['backend']} ({kind})  |  {qubits} qubits x {shots} shots (one job)\n")

    print("=== 2. Measured bitstring -> number ===")
    bits = qr.bitstring(16)
    print(f"bits   : {bits}")
    print(f"number : int('{bits}', 2) = {int(bits, 2)}\n")

    print("=== 3. How random is this run? ===")
    print("Is each qubit a fair coin?  P(1) per qubit, raw:")
    for q, p in enumerate(rep["per_qubit_p1"]):
        print(f"q{q}: {bar(p)} {p:.3f}")
    raw, deb = rep["raw"], rep["debiased"]
    print(f"\n{'health test':<20}{'raw':>14}{debias:>14}")
    print(f"{'bits':<20}{raw['bits']:>14}{deb['bits']:>14}")
    print(f"{'share of 1s':<20}{raw['ones_fraction']:>14.4f}{deb['ones_fraction']:>14.4f}")
    for key, label in HEALTH_TESTS:
        print(f"{label:<20}{pass_fail(raw[key]):>14}{pass_fail(deb[key]):>14}")
    print("(NIST SP 800-22 style p-values: p >= 0.01 passes. With 10 checks, a single FAIL turns "
          "up by chance in about 1 run in 10. Noise models can tilt raw bits toward 1; "
          "debiasing evens them out.)\n")

    score = {name: randomness_score(r) for name, r in (("raw", raw), (debias, deb))}
    print(f"{'randomness score':<24}{'raw':>16}{debias:>16}")
    print(f"{'tests passed':<24}" + "".join(f"{sc['passed']:>16}" for sc in score.values()))
    print(f"{'min-entropy per bit':<24}" + "".join(f"{sc['entropy']:>16}" for sc in score.values()))
    print(f"{'patterns between bits':<24}" + "".join(f"{sc['pattern']:>16}" for sc in score.values()))
    print("min-entropy: how many truly random bits each bit is worth, as 'measured / best "
          "possible for this many bits' (NIST SP 800-90B, 99% confidence). Patterns: "
          "correlation between each bit and the next 16 bits, fair if all stay within "
          "+/-3/sqrt(n).\n")

    print("=== 4. Random walk: each bit is a step, 1 = up, 0 = down ===")
    raw_bits, deb_bits = qr.raw_bits, qr.pool_bits()
    walks = {"raw": stats.random_walk(raw_bits), debias: stats.random_walk(deb_bits)}
    for name, walk in walks.items():
        steps, end = len(walk) - 1, walk[-1]
        band = 2 * math.sqrt(steps)
        verdict = "inside, looks fair" if abs(end) <= band else "OUTSIDE, drift = bias"
        print(f"{name:<11}: {steps:>6} steps, ends at {end:+5d}  "
              f"(fair walks end within +/-{band:.0f} 95% of the time: {verdict})")
    print("A tiny bias toward 1 makes the walk drift upward; debiasing should remove the drift.\n")

    print("=== 5. Dice from raw vs debiased bits (3 bits per roll, 6 and 7 rejected) ===")
    dice = {"raw": stats.dice_from_bits(raw_bits), debias: stats.dice_from_bits(deb_bits)}
    for name, d in dice.items():
        counts = [d.count(f) for f in range(1, 7)]
        pct = "  ".join(f"{f}:{100 * c / len(d):4.1f}%" for f, c in zip(range(1, 7), counts))
        print(f"{name:<11}: {len(d):>5} rolls  {pct}  chi-square p={stats.chi2_uniform_p(counts):.3f}")
    print("(A fair die gives 16.7% per face. p >= 0.01 means consistent with a fair die.)\n")

    print("=== 6. Using the numbers ===")
    rolls = []
    try:
        for _ in range(120):
            rolls.append(qr.randint(1, 6))
    except EntropyExhausted:
        print("Ran out of entropy early - raise Shots for more rolls.")
    print("d6 rolls (first 20):", rolls[:20])
    print("float in [0,1)      :", qr.random() if qr.bits_remaining >= 53 else "n/a")
    deck = list("ABCDEF")
    if qr.bits_remaining >= 30:
        qr.shuffle(deck)
    print("shuffled A-F        :", "".join(deck))
    print(f"entropy left in pool: {qr.bits_remaining} bits")
    for w in rep["warnings"]:
        print("WARNING:", w)

    chsh = rep["bell"]
    if chsh:
        print("\n=== 7. Is it really quantum? A Bell test (CHSH) ===")
        print("Two entangled qubits are measured along directions picked by two quantum coin flips.")
        for (sa, sb), e in chsh["correlations"].items():
            print(f"settings A{sa} B{sb}: correlation {e:+.3f}  (quantum prediction "
                  f"{bell_module.expected_correlation(sa, sb):+.3f}, "
                  f"{chsh['shots_per_setting'][(sa, sb)]} shots)")
        print(f"S = {chsh['S']:.3f} +/- {chsh['sigma']:.3f}   "
              f"(classical limit {chsh['classical_limit']:.0f}, "
              f"quantum prediction {chsh['quantum_prediction']:.3f})")
        print(f"{chsh_verdict(chsh)}")
        if chsh["S"] > chsh["quantum_prediction"]:
            print("(S above 2.83 is sampling noise: the true value can't exceed 2*sqrt(2). "
                  "More shots narrow the error.)")
        print("(A demonstration, not a certificate: a real Bell test also needs the two sides far "
              "apart and other loopholes closed.)")

    raw_walk_end, deb_walk_end = walks["raw"][-1], walks[debias][-1]
    min_p = {name: min(r[key] for key, _ in HEALTH_TESTS if not math.isnan(r[key]))
             for name, r in (("raw", raw), ("debiased", deb))}
    print("\nResult line (copy into docs/DEVICE_RESULTS.md to compare devices):")
    print(f"| {rep['backend']} | {'hardware' if rep['hardware'] else 'simulator'} | {qubits} | "
          f"{shots} | {debias} | {max(rep['per_qubit_p1'], key=lambda p: abs(p - 0.5)):.3f} | "
          f"{raw['ones_fraction']:.4f} | {deb['ones_fraction']:.4f} | {raw_walk_end:+d} | "
          f"{deb_walk_end:+d} | {min_p['raw']:.3f} | {min_p['debiased']:.3f} | "
          f"{raw['min_entropy']:.3f} | {deb['min_entropy']:.3f} | "
          f"{format_s(chsh)} |")

    if rep["hardware"]:
        print("\nNote: these bits come from measuring real qubits, so they are physically "
              "random. Any bias above is the hardware's own noise.")
    else:
        print("\nNote: simulators are classical programs, so on them the bits are "
              "simulated quantum randomness. Only real quantum hardware is "
              "physically random.")

    if plot:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            return
        raw_c, deb_c = "#ff7a59", "#5b6cff"
        fig = plt.figure(figsize=(10, 7))

        ax = fig.add_subplot(2, 2, 1)
        ax.bar(range(qubits), rep["per_qubit_p1"], color=raw_c)
        ax.axhline(0.5, color="k", ls="--", lw=1)
        ax.set(title="P(1) per qubit (raw)", xlabel="qubit", ylim=(0, 1))

        ax = fig.add_subplot(2, 2, 2)
        width = 0.4
        for i, (name, d) in enumerate(dice.items()):
            pct = [100 * d.count(f) / len(d) for f in range(1, 7)]
            ax.bar([f - width / 2 + i * width for f in range(1, 7)], pct, width,
                   color=(raw_c, deb_c)[i], label=f"{name} ({len(d)} rolls)")
        ax.axhline(100 / 6, color="k", ls="--", lw=1)
        ax.set(title="Dice: raw vs debiased", xlabel="face", ylabel="% of rolls", ylim=(0, 30))
        ax.legend(fontsize=8, loc="upper center", ncol=2)

        ax = fig.add_subplot(2, 1, 2)
        n = len(walks["raw"])
        band = [2 * math.sqrt(t) for t in range(n)]
        ax.fill_between(range(n), [-b for b in band], band, color="0.9",
                        label="95% of fair walks stay here")
        for i, (name, walk) in enumerate(walks.items()):
            ax.plot(walk, color=(raw_c, deb_c)[i], lw=1.2, label=name)
        ax.axhline(0, color="k", lw=0.8)
        ax.set(title="Random walk: 1 = step up, 0 = step down", xlabel="step",
               ylabel="position")
        ax.legend(fontsize=8, loc="upper left")

        fig.tight_layout()
        plt.show()
        plot_randomness_report(plt, raw_bits, deb_bits, raw, deb, debias, raw_c, deb_c)
        if chsh:
            plot_bell(plt, chsh)


def plot_randomness_report(plt, raw_bits, deb_bits, raw, deb, debias, raw_c, deb_c):
    """Second chart: what the bits look like, test p-values and patterns between bits."""
    fig = plt.figure(figsize=(10, 7))
    fig.suptitle("Randomness report: min-entropy per bit "
                 f"raw {raw['min_entropy']:.3f}, {debias} {deb['min_entropy']:.3f} "
                 f"(best possible {stats.ideal_min_entropy_per_bit(raw['bits']):.3f} / "
                 f"{stats.ideal_min_entropy_per_bit(deb['bits']):.3f})", fontsize=11)

    for i, (name, bits) in enumerate((("raw", raw_bits), (debias, deb_bits))):
        width = 64
        rows = [[int(b) for b in bits[r * width:(r + 1) * width]] for r in range(len(bits) // width)]
        ax = fig.add_subplot(2, 2, i + 1)
        ax.imshow(rows, cmap="gray_r", interpolation="nearest", aspect="auto")
        ax.set(title=f"{name} bits ({len(rows) * width}), black = 1", xticks=[], yticks=[])

    ax = fig.add_subplot(2, 2, 3)
    labels = [label for _, label in HEALTH_TESTS]
    width = 0.4
    for i, (name, r, color) in enumerate((("raw", raw, raw_c), (debias, deb, deb_c))):
        ps = [0 if math.isnan(r[key]) else r[key] for key, _ in HEALTH_TESTS]
        ax.bar([x - width / 2 + i * width for x in range(len(labels))], ps, width, color=color,
               label=name)
    ax.axhline(0.01, color="red", lw=1, ls="--", label="pass line (0.01)")
    ax.set_xticks(range(len(labels)), [lbl.replace(" ", "\n", 1) for lbl in labels], fontsize=7)
    ax.set(title="Health tests: p-values (higher bar = passes more easily)", ylim=(0, 1))
    ax.legend(fontsize=7, loc="upper right")

    ax = fig.add_subplot(2, 2, 4)
    for name, bits, r, color in (("raw", raw_bits, raw, raw_c), (debias, deb_bits, deb, deb_c)):
        corr = stats.autocorrelation(bits)
        lags = range(1, len(corr) + 1)
        ax.plot(lags, corr, "o-", color=color, ms=3, label=name)
        limit = stats.autocorr_limit(r["bits"])
        ax.axhline(limit, color=color, lw=0.8, ls="--")
        ax.axhline(-limit, color=color, lw=0.8, ls="--")
    ax.axhline(0, color="k", lw=0.8)
    ax.set(title="Patterns: correlation with the bit k places later", xlabel="k (lag)",
           ylabel="correlation")
    ax.legend(fontsize=7, loc="upper right", title="dashed: fair range", title_fontsize=7)

    fig.tight_layout()
    plt.show()


def plot_bell(plt, chsh):
    """Third chart: the four correlations and S against the classical limit."""
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    keys = list(chsh["correlations"])
    labels = [f"A{a} B{b}" for a, b in keys]
    ax[0].bar(range(4), [chsh["correlations"][k] for k in keys], color="#5b6cff",
              label="measured")
    ax[0].scatter(range(4), [bell_module.expected_correlation(*k) for k in keys], color="k",
                  marker="_", s=600, zorder=3, label="quantum prediction")
    ax[0].axhline(0, color="k", lw=0.8)
    ax[0].set_xticks(range(4), labels)
    ax[0].set(title="Correlation per setting pair", ylim=(-1, 1), ylabel="P(same) - P(different)")
    ax[0].legend(fontsize=8, loc="lower left")

    s_value, sigma = chsh["S"], chsh["sigma"]
    ax[1].axvspan(0, chsh["classical_limit"], color="red", alpha=0.08,
                  label="possible without quantum physics")
    ax[1].barh([0], [s_value], xerr=[sigma], color="#5b6cff", height=0.4, capsize=6,
               label="measured S")
    ax[1].axvline(chsh["classical_limit"], color="red", ls="--",
                  label=f"classical limit ({chsh['classical_limit']:.0f})")
    ax[1].axvline(chsh["quantum_prediction"], color="k", ls=":",
                  label=f"quantum prediction ({chsh['quantum_prediction']:.2f})")
    ax[1].set(title=f"Bell test: S = {s_value:.3f} ± {sigma:.3f}", xlim=(min(0, s_value - 0.5), 3.2),
              ylim=(-0.5, 1.1), yticks=[])
    ax[1].legend(fontsize=7, loc="upper left", ncol=2)
    fig.tight_layout()
    plt.show()


# Qollab calls main() itself after the script finishes, so only call it when run locally.
if RUNNING_LOCALLY:
    main()
