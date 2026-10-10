"""Tiny statistical health checks (NIST SP 800-22 style), pure Python."""
from __future__ import annotations

import math
from collections import Counter


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


def per_qubit_p1(shots: list[str]) -> list[float]:
    """P(measure 1) for each qubit. Qiskit strings are MSB-left, so qubit 0 is last."""
    n = len(shots[0])
    return [sum(s[n - 1 - q] == "1" for s in shots) / len(shots) for q in range(n)]


def igamc(a: float, x: float) -> float:
    """Regularized upper incomplete gamma function Q(a, x), as used by NIST SP 800-22."""
    if x <= 0:
        return 1.0
    log_prefix = a * math.log(x) - x - math.lgamma(a)
    if x < a + 1:  # series for P(a, x), then Q = 1 - P
        term = total = 1.0 / a
        n = a
        while abs(term) > abs(total) * 1e-15:
            n += 1
            term *= x / n
            total += term
        return max(0.0, 1.0 - total * math.exp(log_prefix))
    # continued fraction for Q(a, x) (modified Lentz)
    tiny = 1e-300
    b = x + 1 - a
    c, d = 1 / tiny, 1 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = tiny if abs(d) < tiny else d
        c = b + an / c
        c = tiny if abs(c) < tiny else c
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-15:
            break
    return math.exp(log_prefix) * h


def block_frequency_p(bits: str, block: int = 32) -> float:
    """Block frequency test: is the share of 1s about 1/2 inside every block of `block` bits?"""
    n_blocks = len(bits) // block
    if n_blocks == 0:
        return float("nan")
    chi2 = 4 * block * sum(
        (bits[i * block:(i + 1) * block].count("1") / block - 0.5) ** 2 for i in range(n_blocks))
    return igamc(n_blocks / 2, chi2 / 2)


# (block size, longest-run categories (lowest, highest), category probabilities) from NIST SP 800-22
_LONGEST_RUN_TABLES = [
    (750000, 10000, (10, 16), [0.0882, 0.2092, 0.2483, 0.1933, 0.1208, 0.0675, 0.0727]),
    (6272, 128, (4, 9), [0.1174, 0.2430, 0.2493, 0.1752, 0.1027, 0.1124]),
    (128, 8, (1, 4), [55 / 256, 94 / 256, 59 / 256, 48 / 256]),  # exact for 8-bit blocks
]


def longest_run_p(bits: str) -> float:
    """Longest-run-of-ones test: are the longest runs of 1s per block as long as chance predicts?

    Needs at least 128 bits; returns nan for shorter input.
    """
    n = len(bits)
    for min_n, block, (low, high), probs in _LONGEST_RUN_TABLES:
        if n >= min_n:
            break
    else:
        return float("nan")
    n_blocks = n // block
    counts = [0] * len(probs)
    for i in range(n_blocks):
        longest = max(len(r) for r in bits[i * block:(i + 1) * block].split("0"))
        counts[min(max(longest, low), high) - low] += 1
    chi2 = sum((c - n_blocks * p) ** 2 / (n_blocks * p) for c, p in zip(counts, probs))
    return igamc((len(probs) - 1) / 2, chi2 / 2)


def serial_p(bits: str, m: int = 3) -> tuple[float, float]:
    """Serial test: are all overlapping m-bit patterns equally common? Returns two p-values."""
    n = len(bits)
    if m < 3 or m >= int(math.log2(n)) - 2:
        raise ValueError("serial_p needs 3 <= m < log2(len(bits)) - 2")

    def psi2(k: int) -> float:
        if k <= 0:
            return 0.0
        wrapped = bits + bits[:k - 1]
        counts = Counter(wrapped[i:i + k] for i in range(n))
        return 2 ** k / n * sum(c * c for c in counts.values()) - n

    d1 = psi2(m) - psi2(m - 1)
    d2 = psi2(m) - 2 * psi2(m - 1) + psi2(m - 2)
    return igamc(2 ** (m - 2), d1 / 2), igamc(2 ** (m - 3), d2 / 2)


def health_report(bits: str) -> dict[str, float]:
    if len(bits) < 100:
        raise ValueError("need at least 100 bits for a meaningful report")
    return {
        "bits": len(bits),
        "ones_fraction": ones_fraction(bits),
        "monobit_p": monobit_p(bits),
        "runs_p": runs_p(bits),
        "block_frequency_p": block_frequency_p(bits),
        "longest_run_p": longest_run_p(bits),
        "serial_p": min(serial_p(bits)),
        "nibble_entropy": nibble_entropy(bits),
    }


def random_walk(bits: str) -> list[int]:
    """Position after each step: '1' steps up, '0' steps down. Starts at 0."""
    pos, path = 0, [0]
    for b in bits:
        pos += 1 if b == "1" else -1
        path.append(pos)
    return path


def dice_from_bits(bits: str) -> list[int]:
    """Die rolls (1-6) from 3-bit chunks; values 6 and 7 are rejected (no modulo bias)."""
    rolls = []
    for i in range(0, len(bits) - 2, 3):
        v = int(bits[i:i + 3], 2)
        if v < 6:
            rolls.append(v + 1)
    return rolls


def chi2_uniform_p(counts: list[int]) -> float:
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
