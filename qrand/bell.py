"""CHSH Bell test that rides along in the same circuit as the random number generator.

Four extra qubits, measured in the same job (IonQ allows one job per run):

- ``a``, ``b``: Hadamard + measure, so each shot picks Alice's and Bob's measurement setting
  with a quantum coin flip.
- ``A``, ``B``: an entangled Bell pair (|00> + |11>)/sqrt(2). Alice measures A along angle 0 or 90
  degrees, Bob measures B along 45 or -45 degrees (in the X-Z plane), chosen by ``a`` and ``b``.

For each setting pair the correlation is E = P(same) - P(different). Then

    S = E(0,0) + E(0,1) + E(1,0) - E(1,1)

Any classical (local hidden variable) source gives |S| <= 2. Quantum mechanics predicts
2 * sqrt(2) ~ 2.83 for these angles.
"""
from __future__ import annotations

import math

from qiskit import QuantumCircuit

CLASSICAL_LIMIT = 2.0
QUANTUM_PREDICTION = 2 * math.sqrt(2)
BELL_QUBITS = 4

# Measurement angles in the X-Z plane: (setting 0, setting 1)
ALICE_ANGLES = (0.0, math.pi / 2)
BOB_ANGLES = (math.pi / 4, -math.pi / 4)


def _controlled_ry(qc: QuantumCircuit, theta: float, control: int, target: int) -> None:
    """Controlled RY built from RY and CX only, so every backend can run it."""
    qc.ry(theta / 2, target)
    qc.cx(control, target)
    qc.ry(-theta / 2, target)
    qc.cx(control, target)


def add_chsh(qc: QuantumCircuit, qubits: list[int], clbits: list[int]) -> None:
    """Append the CHSH test on qubits/clbits ordered as [a, b, A, B]."""
    a, b, qa, qb = qubits
    qc.h(a)                      # Alice's setting: quantum coin flip
    qc.h(b)                      # Bob's setting: quantum coin flip
    qc.h(qa)
    qc.cx(qa, qb)                # Bell pair (|00> + |11>) / sqrt(2)
    # Measuring along angle t equals RY(-t) followed by a Z measurement.
    for setting, target, angles in ((a, qa, ALICE_ANGLES), (b, qb, BOB_ANGLES)):
        if angles[0]:
            qc.ry(-angles[0], target)
        _controlled_ry(qc, -(angles[1] - angles[0]), setting, target)
    qc.measure(qubits, clbits)


def chsh_from_shots(shots: list[str]) -> dict:
    """CHSH result from 4-character shot strings ordered 'B A b a' (Qiskit, MSB-left).

    Returns S, its standard error, the correlation and shot count per setting pair, and how many
    standard errors S lies above the classical limit.
    """
    counts = {(x, y): [0, 0] for x in (0, 1) for y in (0, 1)}  # [same, different]
    for s in shots:
        out_b, out_a, set_b, set_a = (int(c) for c in s)
        counts[(set_a, set_b)][out_a != out_b] += 1

    correlations, n_per_setting, variance = {}, {}, 0.0
    for key, (same, diff) in counts.items():
        n = same + diff
        e = (same - diff) / n if n else float("nan")
        correlations[key], n_per_setting[key] = e, n
        if n:
            variance += (1 - e * e) / n
    if any(n == 0 for n in n_per_setting.values()):
        s_value = sigma = float("nan")
    else:
        s_value = (correlations[(0, 0)] + correlations[(0, 1)]
                   + correlations[(1, 0)] - correlations[(1, 1)])
        sigma = math.sqrt(variance)
    sigmas_above = ((s_value - CLASSICAL_LIMIT) / sigma
                    if sigma and not math.isnan(sigma) else float("nan"))
    return {
        "S": s_value,
        "sigma": sigma,
        "sigmas_above_classical": sigmas_above,
        "correlations": correlations,
        "shots_per_setting": n_per_setting,
        "quantum_prediction": QUANTUM_PREDICTION,
        "classical_limit": CLASSICAL_LIMIT,
    }


def expected_correlation(set_a: int, set_b: int) -> float:
    """Quantum prediction for E at a setting pair: cos(angle_A - angle_B)."""
    return math.cos(ALICE_ANGLES[set_a] - BOB_ANGLES[set_b])
