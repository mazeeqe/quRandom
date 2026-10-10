import random
import pytest
from qrand import QuantumRandom, EntropyExhausted, stats


class FakeResult:
    def __init__(self, mem, counts=False): self.mem, self.counts = mem, counts
    def get_memory(self):
        if self.counts: raise RuntimeError("no memory")
        return self.mem
    def get_counts(self):
        out = {}
        for m in self.mem: out[m] = out.get(m, 0) + 1
        return out

class FakeJob:
    def __init__(self, r): self.r = r
    def result(self): return self.r

class BiasedBackend:
    """Every qubit reads 1 with probability p (mimics readout bias)."""
    name = "biased"
    def __init__(self, p, counts=False): self.p, self.counts, self.jobs = p, counts, 0
    def run(self, circuit, shots, memory):
        self.jobs += 1
        n = circuit.num_qubits
        rng = random.Random(1)
        mem = ["".join("1" if rng.random() < self.p else "0" for _ in range(n)) for _ in range(shots)]
        return FakeJob(FakeResult(mem, self.counts))


def test_default_backend_bits_and_numbers():
    qr = QuantumRandom(shots=256, n_qubits=8, debias="none")
    s = qr.bitstring(40)
    assert len(s) == 40 and set(s) <= {"0", "1"}
    assert set(qr.randint(1, 6) for _ in range(150)) == {1, 2, 3, 4, 5, 6}
    assert 0 <= qr.random() < 1


def test_single_job_only():
    be = BiasedBackend(0.5)
    qr = QuantumRandom(be, shots=256)
    for _ in range(50): qr.randint(1, 100)
    assert be.jobs == 1


@pytest.mark.parametrize("mode", ["xor", "von_neumann"])
def test_debias_reduces_bias(mode):
    qr = QuantumRandom(BiasedBackend(0.62), n_qubits=8, shots=2000, debias=mode)
    raw = stats.ones_fraction(qr.raw_bits)
    out = stats.ones_fraction(qr.pool_bits())
    assert abs(raw - 0.5) > 0.1
    assert abs(out - 0.5) < abs(raw - 0.5) / 2
    assert stats.monobit_p(qr.raw_bits) < 0.01   # bias is detected


def test_exhaustion_and_refill():
    qr = QuantumRandom(BiasedBackend(0.5), n_qubits=2, shots=4, debias="none")
    qr.bitstring(8)
    with pytest.raises(EntropyExhausted): qr.bitstring(1)
    be = BiasedBackend(0.5)
    qr = QuantumRandom(be, n_qubits=2, shots=4, debias="none", auto_refill=True)
    qr.bitstring(8); qr.bitstring(8)
    assert be.jobs == 2


def test_counts_fallback_warns():
    qr = QuantumRandom(BiasedBackend(0.5, counts=True), shots=64)
    assert qr.warnings


def test_counts_fallback_is_not_grouped_by_outcome():
    qr = QuantumRandom(BiasedBackend(0.5, counts=True), n_qubits=4, shots=512, debias="none")
    # Grouped shots change outcome at most 15 times (16 possible outcomes);
    # a random order changes outcome on almost every shot.
    changes = sum(a != b for a, b in zip(qr.raw_shots, qr.raw_shots[1:]))
    assert changes > 400


def test_invalid_args():
    with pytest.raises(ValueError): QuantumRandom(n_qubits=3, debias="xor")
    with pytest.raises(ValueError): QuantumRandom(debias="nope")


def test_report_and_shuffle():
    qr = QuantumRandom(shots=256)
    assert qr.report()["debiased"]["bits"] == 8 * 256 // 2
    x = list(range(10)); qr.shuffle(x); assert sorted(x) == list(range(10))
