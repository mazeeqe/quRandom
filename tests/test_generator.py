import pytest

from qurandom.generator import HAS_QISKIT, QuantumRandom

MODES = [False] + ([True] if HAS_QISKIT else [])


@pytest.mark.parametrize("quantum", MODES)
def test_bits_length_and_values(quantum):
    bits = QuantumRandom(num_qubits=4, use_quantum=quantum).bits(10)
    assert len(bits) == 10
    assert set(bits) <= {0, 1}


@pytest.mark.parametrize("quantum", MODES)
def test_randint_in_range(quantum):
    qr = QuantumRandom(use_quantum=quantum)
    for _ in range(20):
        assert 1 <= qr.randint(1, 6) <= 6


@pytest.mark.parametrize("quantum", MODES)
def test_random_in_unit_interval(quantum):
    assert 0.0 <= QuantumRandom(use_quantum=quantum).random() < 1.0


def test_invalid_args():
    with pytest.raises(ValueError):
        QuantumRandom(num_qubits=0)
    with pytest.raises(ValueError):
        QuantumRandom(use_quantum=False).randint(5, 1)
