"""Quantum random number generator for Qollab (and any Qiskit backend).

One circuit, one job: H on every qubit, measure everything. The per-shot
bitstrings fill an *entropy pool*; numbers are then carved out of the pool.
Using a single job matters on Qollab, where IonQ backends allow only one
job per run.
"""
from __future__ import annotations

import random
from collections.abc import Sequence
from typing import TypeVar

from qiskit import QuantumCircuit

from . import stats

T = TypeVar("T")
DEBIAS_MODES = ("none", "xor", "von_neumann")


class EntropyExhausted(RuntimeError):
    """The pool is empty. Use more shots/qubits (IonQ allows one job per run)."""


class QuantumRandom:
    """Random numbers from measuring qubits in superposition.

    Parameters
    ----------
    backend : Qiskit backend. On Qollab pass the pre-created ``backend``.
              ``None`` falls back to Qiskit's local BasicSimulator.
    n_qubits : qubits per shot; each shot yields an n_qubits-bit string.
    shots : number of shots. Raw pool size = n_qubits * shots bits.
    debias : "none" | "xor" | "von_neumann".
        Noisy hardware/noise models can make 1 slightly likelier than 0.
        "xor" XORs qubit pairs inside each shot (keeps 1/2 of the bits).
        "von_neumann" compares consecutive shots of the same qubit and
        keeps a bit only when they differ (keeps ~1/4, removes bias
        completely if shots are independent).
    auto_refill : run another job when the pool runs dry. Leave False on IonQ.
    """

    def __init__(self, backend=None, n_qubits: int = 8, shots: int = 512,
                 debias: str = "xor", auto_refill: bool = False):
        if debias not in DEBIAS_MODES:
            raise ValueError(f"debias must be one of {DEBIAS_MODES}")
        if n_qubits < 1 or shots < 2:
            raise ValueError("need n_qubits >= 1 and shots >= 2")
        if debias == "xor" and n_qubits % 2:
            raise ValueError("debias='xor' needs an even n_qubits")
        if backend is None:
            from qiskit.providers.basic_provider import BasicSimulator
            backend = BasicSimulator()
        self.backend, self.n_qubits, self.shots = backend, n_qubits, shots
        self.debias, self.auto_refill = debias, auto_refill
        self.warnings: list[str] = []
        self.circuit = self._build_circuit(n_qubits)
        self._pool, self._pos = "", 0
        self.raw_shots: list[str] = []
        self.raw_bits = ""
        self.refill()

    # ---------------------------------------------------------------- circuit
    @staticmethod
    def _build_circuit(n: int) -> QuantumCircuit:
        qc = QuantumCircuit(n, n)
        qc.h(range(n))                   # |0> -> (|0>+|1>)/sqrt(2)
        qc.measure(range(n), range(n))   # collapse: each qubit is a coin flip
        return qc

    # ------------------------------------------------------------------- pool
    def refill(self) -> None:
        """Run ONE job and replace the pool with the fresh bits."""
        job = self.backend.run(self.circuit, shots=self.shots, memory=True)
        result = job.result()
        try:
            shots = list(result.get_memory())
        except Exception:  # noqa: BLE001 - providers raise different errors when memory is off
            shots = None
        if not shots:  # backend gave only counts: order of shots is lost
            counts = result.get_counts()
            shots = [k.replace(" ", "") for k, v in counts.items() for _ in range(int(v))]
            # Expanded counts are grouped by outcome (all '0000' shots, then all '0001'...),
            # which makes the bit order anything but random. Restore a random order.
            random.SystemRandom().shuffle(shots)
            self.warnings.append(
                "Backend returned counts without per-shot memory, so shot order was "
                "restored with the OS random generator. Use a noise-model simulator "
                "for per-shot quantum results.")
        self.raw_shots = shots
        self.raw_bits = "".join(shots)
        self._pool, self._pos = self._extract(shots), 0

    def _extract(self, shots: list[str]) -> str:
        if self.debias == "none":
            return "".join(shots)
        if self.debias == "xor":
            return "".join(
                str(int(s[i]) ^ int(s[i + 1])) for s in shots for i in range(0, len(s), 2))
        # von Neumann, per qubit across consecutive shots (01 -> 0, 10 -> 1)
        out = []
        for a, b in zip(shots[0::2], shots[1::2]):
            for qa, qb in zip(a, b):
                if qa != qb:
                    out.append(qa)
        return "".join(out)

    @property
    def bits_remaining(self) -> int:
        return len(self._pool) - self._pos

    def pool_bits(self) -> str:
        """All debiased bits in the pool (for testing/plots)."""
        return self._pool

    def _take(self, k: int) -> str:
        if k < 1:
            raise ValueError("k must be >= 1")
        if self.bits_remaining < k:
            if not self.auto_refill:
                raise EntropyExhausted(
                    f"need {k} bits but only {self.bits_remaining} left; raise shots/n_qubits")
            self.refill()
            if self.bits_remaining < k:
                raise EntropyExhausted("a fresh job still has too few bits; raise shots")
        bits = self._pool[self._pos:self._pos + k]
        self._pos += k
        return bits

    # ---------------------------------------------- bitstring -> number API
    def bitstring(self, n_bits: int) -> str:
        """n_bits random bits, e.g. '01101001'."""
        return self._take(n_bits)

    def getrandbits(self, k: int) -> int:
        """k random bits converted to an integer: int('0110...', 2)."""
        return int(self._take(k), 2)

    def randbelow(self, n: int) -> int:
        """Uniform integer in [0, n) via rejection sampling (no modulo bias)."""
        if n < 1:
            raise ValueError("n must be >= 1")
        if n == 1:
            return 0
        k = (n - 1).bit_length()
        while True:
            r = self.getrandbits(k)
            if r < n:
                return r

    def randint(self, a: int, b: int) -> int:
        """Uniform integer in [a, b], inclusive."""
        if a > b:
            raise ValueError("a must be <= b")
        return a + self.randbelow(b - a + 1)

    def random(self) -> float:
        """Uniform float in [0, 1) with 53 bits of precision."""
        return self.getrandbits(53) / (1 << 53)

    def choice(self, seq: Sequence[T]) -> T:
        if not seq:
            raise IndexError("cannot choose from an empty sequence")
        return seq[self.randbelow(len(seq))]

    def shuffle(self, items: list) -> None:
        """In-place Fisher-Yates shuffle."""
        for i in range(len(items) - 1, 0, -1):
            j = self.randbelow(i + 1)
            items[i], items[j] = items[j], items[i]

    # ------------------------------------------------------------ diagnostics
    def report(self) -> dict:
        """Bias and health numbers for the raw and debiased bits."""
        return {
            "backend": _backend_name(self.backend),
            "hardware": is_hardware(self.backend),
            "qubits": self.n_qubits,
            "shots": self.shots,
            "per_qubit_p1": stats.per_qubit_p1(self.raw_shots),
            "raw": stats.health_report(self.raw_bits),
            "debiased": stats.health_report(self._pool),
            "debias": self.debias,
            "warnings": list(self.warnings),
        }


def is_hardware(backend) -> bool:
    """True for a real quantum computer, False for any simulator.

    IonQ's hardware backends are named ``ionq_qpu...`` (class ``IonQQPUBackend``);
    simulators, IBM noise models and Qiskit's BasicSimulator never contain "qpu".
    """
    return "qpu" in _backend_name(backend).lower() or "QPU" in type(backend).__name__


def _backend_name(backend) -> str:
    name = getattr(backend, "name", None)
    if callable(name):
        name = name()
    return str(name or type(backend).__name__)
