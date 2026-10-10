"""Tiny statistical health checks (NIST SP 800-22 style), pure Python."""
from __future__ import annotations

import math
from collections import Counter
from typing import Dict, List


def ones_fraction(bits: str) -> float:
    return bits.count("1") / len(bits) if bits else float("nan")


def monobit_p(bits: str) -> float:
    """Frequency test: are 0s and 1s equally likely? p >= 0.01 passes."""
    n = len(bits)
    s = abs(2 * bits.count("1") - n)
    return math.erfc(s / math.sqrt(2 * n))


def runs_p(bits: str) -> float:
    """Runs test: is the number of 0->1 / 1->0 flips what chance predicts?"""
    n = len(bits)
    pi = bits.count("1") / n
    if abs(pi - 0.5) >= 2 / math.sqrt(n):
        return 0.0
    v = 1 + sum(bits[i] != bits[i + 1] for i in range(n - 1))
    return math.erfc(abs(v - 2 * n * pi * (1 - pi)) / (2 * math.sqrt(2 * n) * pi * (1 - pi)))


def nibble_entropy(bits: str) -> float:
    """Shannon entropy of 4-bit symbols, in bits (ideal = 4.0)."""
    chunks = [bits[i:i + 4] for i in range(0, len(bits) - 3, 4)]
    if not chunks:
        return float("nan")
    total = len(chunks)
    return -sum(c / total * math.log2(c / total) for c in Counter(chunks).values())


def per_qubit_p1(shots: List[str]) -> List[float]:
    """P(measure 1) for each qubit. Qiskit strings are MSB-left, so qubit 0 is last."""
    n = len(shots[0])
    return [sum(s[n - 1 - q] == "1" for s in shots) / len(shots) for q in range(n)]


def health_report(bits: str) -> Dict[str, float]:
    if len(bits) < 100:
        raise ValueError("need at least 100 bits for a meaningful report")
    return {
        "bits": len(bits),
        "ones_fraction": ones_fraction(bits),
        "monobit_p": monobit_p(bits),
        "runs_p": runs_p(bits),
        "nibble_entropy": nibble_entropy(bits),
    }


def random_walk(bits: str) -> List[int]:
    """Position after each step: '1' steps up, '0' steps down. Starts at 0."""
    pos, path = 0, [0]
    for b in bits:
        pos += 1 if b == "1" else -1
        path.append(pos)
    return path


def dice_from_bits(bits: str) -> List[int]:
    """Die rolls (1-6) from 3-bit chunks; values 6 and 7 are rejected (no modulo bias)."""
    rolls = []
    for i in range(0, len(bits) - 2, 3):
        v = int(bits[i:i + 3], 2)
        if v < 6:
            rolls.append(v + 1)
    return rolls


def chi2_uniform_p(counts: List[int]) -> float:
    """Chi-square goodness-of-fit p-value against a uniform distribution.

    Exact for an odd number of degrees of freedom (e.g. 6 dice faces -> 5).
    p >= 0.01 means the counts are consistent with a fair distribution.
    """
    k, n = len(counts), sum(counts)
    df = k - 1
    if df % 2 == 0:
        raise ValueError("chi2_uniform_p supports an even number of categories only")
    expected = n / k
    x = sum((c - expected) ** 2 / expected for c in counts)
    # Q(x; 1) = erfc(sqrt(x/2)); Q(x; d+2) = Q(x; d) + (x/2)^(d/2) e^(-x/2) / Gamma(d/2 + 1)
    q = math.erfc(math.sqrt(x / 2))
    for d in range(1, df, 2):
        q += (x / 2) ** (d / 2) * math.exp(-x / 2) / math.gamma(d / 2 + 1)
    return q
