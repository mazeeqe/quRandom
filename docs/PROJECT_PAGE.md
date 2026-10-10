# qrand: random numbers from a quantum circuit

**qrand** turns measured qubits into random numbers. Every qubit is put into
an equal superposition with a Hadamard gate and measured. The measured qubits
are joined into a binary string, and that string converts itself into a
number.

$$|0\rangle \xrightarrow{H} \tfrac{1}{\sqrt2}(|0\rangle+|1\rangle) \xrightarrow{\text{measure}} 0 \text{ or } 1 \quad(50/50)$$

```
bits "1001011011100011"  ->  int(bits, 2)  ->  38627
```

## What you get

- `bitstring(n)`, `getrandbits(k)`: raw quantum bits and integers
- `randint(a, b)`: unbiased integers, using rejection sampling (no modulo bias)
- `random()`, `choice()`, `shuffle()`: floats, picks and shuffles
- `report()`: per-qubit bias and NIST-style health tests (monobit, runs, entropy)

## What is new: noise-aware randomness

Real devices and their noise models are not perfect coins. A qubit can read
`1` a little more often than `0`. qrand measures that bias per qubit, shows
it, and can remove it with two debiasing modes:

| mode | idea | bits kept |
| --- | --- | --- |
| `xor` | XOR neighbouring qubits inside each shot | 1/2 |
| `von_neumann` | compare consecutive shots of one qubit, keep only `01`/`10` | ~1/4 |

The health report compares raw and debiased bits so you can see the effect.

## Built for Qollab's one-job-per-run IonQ rule

IonQ backends accept one job per run, so qrand runs **a single circuit job**
that fills an entropy pool. All later numbers are drawn from that pool. If the
pool runs dry, qrand raises a clear `EntropyExhausted` error: raise **Shots**
or **Qubits**.

## How to run

1. Open the project and press **Run**.
2. In **Select QPU**, choose the built-in simulator or an **IonQ remote
   simulator** (for example *IonQ Forte 1*). All are free.
3. Under **Run settings** set **Shots** (default 512), **Qubits** (8, even
   number) and **Debias** (`xor`, `von_neumann` or `none`).
4. Read the console: the circuit, a bitstring converted to a number, per-qubit
   bias, health tests, dice rolls, and a chart.

Use it in your own code:

```python
from qrand import QuantumRandom
qr = QuantumRandom(backend, n_qubits=8, shots=512, debias="xor")
qr.randint(1, 6)
```

## Honest notes

- Simulators are classical programs, so on them the bits are *simulated*
  quantum randomness. Only real quantum hardware is physically random.
  Run the same code on an IonQ QPU (credits) for that.
- IonQ's ideal simulators draw counts client-side with a classical RNG. The
  noise-model simulators return per-shot results, which is what qrand needs.
- Not for cryptographic use.

## Built during the hackathon

Everything here (library, bias analysis, debiasing, tests and demo) was built
during the Qollab Hackathon window (Oct 9-11, 2026). No pre-existing project
code was reused. The code was written with the help of AI tools (Claude).
It builds on Qiskit, and the health tests follow the ideas of NIST SP 800-22.

Source: https://github.com/mazeeqe/quRandom

License: MIT.

**Tags:** `qiskit`, `ionq`, `random-numbers`, `hadamard`, `noise`, `hackathon`
