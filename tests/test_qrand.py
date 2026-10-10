import random

import pytest

from qrand import EntropyExhausted, QuantumRandom, is_hardware, stats


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
    assert {qr.randint(1, 6) for _ in range(150)} == {1, 2, 3, 4, 5, 6}
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


def test_random_walk_and_dice_helpers():
    assert stats.random_walk("1101") == [0, 1, 2, 1, 2]
    # 3-bit chunks: 000 -> 1, 101 -> 6, 110 and 111 rejected
    assert stats.dice_from_bits("000101110111") == [1, 6]


def test_chi2_uniform_p():
    assert stats.chi2_uniform_p([100] * 6) == 1.0
    assert stats.chi2_uniform_p([200, 100, 100, 100, 100, 100]) < 0.01
    with pytest.raises(ValueError):
        stats.chi2_uniform_p([1, 2, 3])


def test_is_hardware():
    from qiskit.providers.basic_provider import BasicSimulator

    class IonQQPUBackend:  # same class and name as qiskit-ionq's hardware backend
        name = "ionq_qpu.forte-1"

    class IonQSimulatorBackend:
        name = "ionq_simulator"

    assert is_hardware(IonQQPUBackend())
    assert not is_hardware(IonQSimulatorBackend())
    assert not is_hardware(BasicSimulator())
    assert not QuantumRandom(shots=64).report()["hardware"]


def test_nist_worked_examples():
    # Examples from NIST SP 800-22 rev 1a, sections 2.1, 2.2, 2.3 and 2.4
    assert round(stats.monobit_p("1011010101"), 6) == 0.527089
    assert round(stats.block_frequency_p("0110011010", block=3), 6) == 0.801252
    assert round(stats.runs_p("1001101011"), 6) == 0.147232
    e128 = ("11001100000101010110110001001100111000000000001001001101010100010001001111010110"
            "100000001101011111001100111001101101100010110010")
    assert round(stats.longest_run_p(e128), 6) == 0.180609


def test_igamc_closed_forms():
    import math
    for x in (0.1, 1.0, 5.0, 30.0):
        assert math.isclose(stats.igamc(1, x), math.exp(-x), rel_tol=1e-12)
        assert math.isclose(stats.igamc(0.5, x), math.erfc(math.sqrt(x)), rel_tol=1e-12)


def test_serial_and_longest_run_catch_patterns():
    rng = random.Random(7)
    fair = "".join(rng.choice("01") for _ in range(4096))
    assert min(stats.serial_p(fair)) > 0.01
    assert stats.longest_run_p(fair) > 0.01
    pattern = "0011" * 1024  # balanced, so monobit passes, but far from random
    assert stats.monobit_p(pattern) == 1.0
    assert min(stats.serial_p(pattern)) < 0.01
    assert stats.longest_run_p(pattern) < 0.01
    with pytest.raises(ValueError):
        stats.serial_p("01" * 10)


def test_min_entropy_and_autocorrelation():
    assert stats.min_entropy_per_bit("1" * 100) == 0.0
    rng = random.Random(3)
    fair = "".join(rng.choice("01") for _ in range(4096))
    biased = "".join("1" if rng.random() < 0.6 else "0" for _ in range(4096))
    ideal = stats.ideal_min_entropy_per_bit(4096)
    assert 0.85 < stats.min_entropy_per_bit(fair) <= ideal < 1
    assert stats.min_entropy_per_bit(biased) < 0.75  # -log2(0.6) = 0.737
    assert stats.autocorrelation("01" * 50, 2) == [-1.0, 1.0]
    assert max(map(abs, stats.autocorrelation(fair))) <= stats.autocorr_limit(len(fair))
    report = QuantumRandom(shots=256).report()["raw"]
    assert {"min_entropy", "max_autocorr"} <= report.keys()
