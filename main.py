"""qrand demo for Qollab: quantum circuit -> bitstring -> random numbers.

Press Run, pick a QPU (built-in simulator or an IonQ remote simulator),
and set Shots / Qubits / Debias under Run settings.
"""
import math

from qrand import QuantumRandom, EntropyExhausted, stats

try:
    backend  # pre-created by Qollab from the Select QPU dialog
    RUNNING_LOCALLY = False
except NameError:  # running locally: fall back to Qiskit's simulator
    from qiskit.providers.basic_provider import BasicSimulator
    backend = BasicSimulator()
    RUNNING_LOCALLY = True


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
    print(f"\nraw      : {raw['bits']:>6} bits, ones={raw['ones_fraction']:.4f}, "
          f"monobit p={raw['monobit_p']:.3f}, runs p={raw['runs_p']:.3f}")
    print(f"{debias:<9}: {deb['bits']:>6} bits, ones={deb['ones_fraction']:.4f}, "
          f"monobit p={deb['monobit_p']:.3f}, runs p={deb['runs_p']:.3f}")
    print("(p >= 0.01 passes. Noise models can tilt raw bits toward 1; debiasing evens them out.)\n")

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
