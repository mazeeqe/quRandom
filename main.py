"""qrand demo for Qollab: quantum circuit -> bitstring -> random numbers.

Press Run, pick a QPU (built-in simulator or an IonQ remote simulator),
and set Shots / Qubits / Debias under Run settings.
"""
from qrand import QuantumRandom, EntropyExhausted

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
    print(f"Backend: {rep['backend']}  |  {qubits} qubits x {shots} shots (one job)\n")

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

    print("=== 4. Using the numbers ===")
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

    print("\nNote: simulators are classical programs, so on them the bits are "
          "simulated quantum randomness. Only real quantum hardware is "
          "physically random.")

    if plot and rolls:
        try:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
            ax[0].bar(range(qubits), rep["per_qubit_p1"], color="#5b6cff")
            ax[0].axhline(0.5, color="k", ls="--", lw=1)
            ax[0].set(title="P(1) per qubit (raw)", xlabel="qubit", ylim=(0, 1))
            ax[1].bar(range(1, 7), [rolls.count(f) for f in range(1, 7)], color="#ff7a59")
            ax[1].set(title=f"{len(rolls)} quantum dice rolls", xlabel="face")
            fig.tight_layout()
            plt.show()
        except ImportError:
            pass


# Qollab calls main() itself after the script finishes, so only call it when run locally.
if RUNNING_LOCALLY:
    main()
