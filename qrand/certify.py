"""Bell-certified randomness: how many random bits a CHSH score S guarantees.

Pironio et al., "Random numbers certified by Bell's theorem", Nature 464, 1021 (2010), eq. (6):
for ANY quantum devices that reach a CHSH value S, Alice's output in each round has min-entropy

    H_min(A|X) >= 1 - log2(1 + sqrt(2 - S^2 / 4))

S <= 2 certifies nothing (a classical program could have written the outputs in advance);
S = 2*sqrt(2) ~ 2.83 certifies a full random bit per round. The bound does not depend on what
is inside the devices ("device-independent"), but it assumes the two sides cannot signal to each
other and that the setting coins are independent of the devices. One chip, or a simulator,
cannot guarantee that, so in quRandom this is a lesson in how certification works, not a
certificate. The bound is asymptotic: we use S minus a few standard errors as a stand-in for the
paper's finite-statistics correction.

It also does not *expand* randomness: every round spends two setting coins (2 bits) to certify
at most 1 bit. Real protocols pick the test rounds rarely so that the output exceeds the input.
"""
from __future__ import annotations

import math

from .bell import CLASSICAL_LIMIT, QUANTUM_PREDICTION

SAFETY_SIGMAS = 3.0
SETTING_BITS_PER_ROUND = 2


def min_entropy_bound(s: float) -> float:
    """Certified min-entropy of Alice's output bit per round, for CHSH value s (0 to 1)."""
    if math.isnan(s) or s <= CLASSICAL_LIMIT:
        return 0.0
    s = min(s, QUANTUM_PREDICTION)            # sampling noise can push S past Tsirelson's bound
    return 1 - math.log2(1 + math.sqrt(max(0.0, 2 - s * s / 4)))


def certify(chsh: dict, sigmas: float = SAFETY_SIGMAS) -> dict:
    """Certified randomness for a ``bell.chsh_from_shots`` result.

    ``per_round`` uses the measured S; ``per_round_safe`` uses S - sigmas * standard error, so a
    lucky sample does not overstate it. ``certified_bits`` = rounds * per_round_safe.
    """
    s_value, sigma = chsh["S"], chsh["sigma"]
    rounds = sum(chsh["shots_per_setting"].values())
    s_safe = s_value - sigmas * sigma if not math.isnan(sigma) else float("nan")
    per_round_safe = min_entropy_bound(s_safe)
    return {
        "per_round": min_entropy_bound(s_value),
        "per_round_safe": per_round_safe,
        "s_safe": s_safe,
        "sigmas": sigmas,
        "rounds": rounds,
        "certified_bits": per_round_safe * rounds,
        "setting_bits_spent": SETTING_BITS_PER_ROUND * rounds,
    }
