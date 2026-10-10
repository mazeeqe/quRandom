"""Random bit generation from measuring qubits in superposition.

Each qubit gets a Hadamard gate, putting it in an equal superposition of |0> and |1>.
Measuring it yields 0 or 1 with probability 1/2 each. On a simulator this is only
pseudo-random; run it on real quantum hardware for true randomness.

If Qiskit is not installed, the OS random source (``secrets``) is used instead.
"""

from __future__ import annotations

import secrets

try:
    from qiskit import QuantumCircuit
    from qiskit.primitives import StatevectorSampler

    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False


class QuantumRandom:
    def __init__(self, num_qubits: int = 8, use_quantum: bool | None = None):
        if num_qubits < 1:
            raise ValueError("num_qubits must be at least 1")
        self.num_qubits = num_qubits
        self.use_quantum = HAS_QISKIT if use_quantum is None else use_quantum
        if self.use_quantum and not HAS_QISKIT:
            raise RuntimeError("Qiskit is not installed: pip install -e '.[quantum]'")
        self._sampler = StatevectorSampler() if self.use_quantum else None

    def _circuit(self) -> QuantumCircuit:
        qc = QuantumCircuit(self.num_qubits)
        qc.h(range(self.num_qubits))
        qc.measure_all()
        return qc

    def bits(self, n: int) -> list[int]:
        """Return ``n`` random bits."""
        if n < 0:
            raise ValueError("n must be non-negative")
        if not self.use_quantum:
            return [secrets.randbits(1) for _ in range(n)]

        shots = -(-n // self.num_qubits)  # ceil division
        if shots == 0:
            return []
        result = self._sampler.run([self._circuit()], shots=shots).result()
        bitstrings = result[0].data.meas.get_bitstrings()
        return [int(b) for s in bitstrings for b in s][:n]

    def randint(self, low: int, high: int) -> int:
        """Return a uniform random integer in ``[low, high]`` using rejection sampling."""
        if low > high:
            raise ValueError("low must be <= high")
        span = high - low + 1
        k = (span - 1).bit_length()
        if k == 0:
            return low
        while True:
            value = int("".join(map(str, self.bits(k))), 2)
            if value < span:
                return low + value

    def random(self, precision: int = 32) -> float:
        """Return a random float in ``[0, 1)``."""
        return int("".join(map(str, self.bits(precision))), 2) / (1 << precision)
