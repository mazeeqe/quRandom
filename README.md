# quRandom

**qrand**: noise-aware random numbers from a quantum circuit. Submission for the Qollab Hackathon.

Every qubit gets a Hadamard gate and is measured, so each one is a 50/50 coin flip. A single
circuit job fills an *entropy pool*, and numbers are carved out of it. qrand measures each qubit's
bias (noisy hardware often reads `1` a little more than `0`) and can remove it with `xor` or
`von_neumann` debiasing.

See [docs/USAGE.md](docs/USAGE.md) for the full API: ranges, bit costs and how many numbers a
job gives you. [docs/PROJECT_PAGE.md](docs/PROJECT_PAGE.md) has the project write-up, and
[docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) has the demo video plan.

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[plot,dev]"
```

## Usage

On Qollab, open the project and press **Run**. `main.py` uses the `backend` Qollab provides.

Locally, run the demo on Qiskit's built-in simulator:

```bash
python main.py
```

In your own code:

```python
from qrand import QuantumRandom

qr = QuantumRandom(backend, n_qubits=8, shots=512, debias="xor")  # backend=None uses a local simulator
qr.randint(1, 6)
qr.random()
qr.report()  # per-qubit bias and NIST-style health tests
```

## Tests

```bash
pytest
```

## Project layout

```
qrand/       library: generator (entropy pool, debiasing) and stats (health tests)
main.py      Qollab demo entry point
tests/       pytest tests
docs/        project page and demo script
notebooks/   experiments
```

## Team

- [@mazeeqe](https://github.com/mazeeqe)

## License

MIT, see [LICENSE](LICENSE).
