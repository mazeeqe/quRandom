# quRandom

Quantum random number generation. Submission for the Qollab Hackathon.

## How it works

Each qubit goes through a Hadamard gate, which puts it in an equal superposition of `|0⟩` and `|1⟩`.
Measuring it gives `0` or `1` with probability ½ each. quRandom builds bits, integers and floats from
those measurements.

> On a simulator the output is only pseudo-random. Run it on real quantum hardware for true randomness.

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[quantum,dev]"
```

## Usage

```bash
qurandom              # random float in [0, 1)
qurandom --bits 16    # 16 random bits
qurandom --int 1 6    # roll a die
qurandom --classical  # skip Qiskit and use the OS random source
```

```python
from qurandom import QuantumRandom

qr = QuantumRandom(num_qubits=8)
qr.bits(16)
qr.randint(1, 6)
qr.random()
```

## Tests

```bash
pytest
```

## Project layout

```
src/qurandom/   package source (generator, CLI)
tests/          pytest tests
notebooks/      experiments and demos
docs/           docs and presentation material
```

## Team

- [@mazeeqe](https://github.com/mazeeqe)

## License

MIT, see [LICENSE](LICENSE).
