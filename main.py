"""qrand demo for Qollab: quantum circuit -> bitstring -> random numbers.

Press Run, pick a QPU (built-in simulator or an IonQ remote simulator),
and set Shots / Qubits / Debias under Run settings.
"""
import math

from qrand import EntropyExhausted, QuantumRandom, stats

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


def bar(p, width=30):
    return "#" * round(p * width) + "." * (width - round(p * width))


def main(shots: int = 512, qubits: int = 8, debias: str = "xor", plot: bool = True):
    qr = QuantumRandom(backend, n_qubits=qubits, shots=shots, debias=debias)
    rep = qr.report()

    print("=== 1. The circuit: Hadamard on every qubit, then measure ===")
    print(qr.circuit.draw("text"))
    kind = "real quantum hardware" if rep["hardware"] else "simulator"
    print(f"Backend: {rep['backend']} ({kind})  |  {qubits} qubits x {shots} shots (one job)\n")

    print("=== 2. Measured bitstring -> number ===")
    bits = qr.bitstring(16)
    print(f"bits   : {bits}")
    print(f"number : int('{bits}', 2) = {int(bits, 2)}\n")

    print("=== 3. Is each qubit a fair coin?  P(1) per qubit, raw ===")
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

    raw_walk_end, deb_walk_end = walks["raw"][-1], walks[debias][-1]
    min_p = {name: min(r[key] for key, _ in HEALTH_TESTS if not math.isnan(r[key]))
             for name, r in (("raw", raw), ("debiased", deb))}
    print("\nResult line (copy into docs/DEVICE_RESULTS.md to compare devices):")
    print(f"| {rep['backend']} | {'hardware' if rep['hardware'] else 'simulator'} | {qubits} | "
          f"{shots} | {debias} | {max(rep['per_qubit_p1'], key=lambda p: abs(p - 0.5)):.3f} | "
          f"{raw['ones_fraction']:.4f} | {deb['ones_fraction']:.4f} | {raw_walk_end:+d} | "
          f"{deb_walk_end:+d} | {min_p['raw']:.3f} | {min_p['debiased']:.3f} |")

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


# Qollab calls main() itself after the script finishes, so only call it when run locally.
if RUNNING_LOCALLY:
    main()
