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
