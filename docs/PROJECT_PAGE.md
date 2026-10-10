**quRandom** turns measured qubits into random numbers, checks how fair the quantum coins really
are, removes bias, and runs a Bell test to show the randomness comes from quantum physics. All of
it runs in **one circuit and one job**, so it works within IonQ's one-job-per-run limit on Qollab.

![How quRandom works: one circuit, one job, check and debias, numbers, plus a Bell test](https://raw.githubusercontent.com/mazeeqe/quRandom/main/docs/images/how_it_works.png)

## How it works

Every qubit is put into an equal superposition with a Hadamard gate and measured, so each one is a
fair coin flip:

$$|0\rangle \xrightarrow{H} \tfrac{1}{\sqrt2}(|0\rangle+|1\rangle) \xrightarrow{\text{measure}} 0 \text{ or } 1 \quad(50/50)$$

The measured bits fill an *entropy pool*, and numbers are carved out of it:

```
bits "1001011011100011"  ->  int(bits, 2)  ->  38627
```

The circuit below has 4 random-number qubits (q0–q3) and the 4 Bell-test qubits (q4–q7). The demo
uses 8 random-number qubits by default.

![The circuit: Hadamard and measure on the random-number qubits, then the Bell test on four more](https://raw.githubusercontent.com/mazeeqe/quRandom/main/docs/images/circuit.png)

**What the library gives you:**

- `bitstring(n)`, `getrandbits(k)`, `randint(a, b)`, `random()`, `choice()`, `shuffle()`.
  Integers use rejection sampling, so there is no modulo bias.
- `report()`: per-qubit bias, five NIST SP 800-22 health tests, min-entropy and the Bell test.
- Full guide with ranges and how many numbers each job gives:
  [docs/USAGE.md](https://github.com/mazeeqe/quRandom/blob/main/docs/USAGE.md). Step-by-step
  tutorial: [notebooks/qrand_tutorial.ipynb](https://github.com/mazeeqe/quRandom/blob/main/notebooks/qrand_tutorial.ipynb).

## Noise-aware: seeing and removing bias

Real devices and their noise models are not perfect coins: a qubit can read `1` a little more
often than `0`. quRandom measures that bias per qubit and can remove it:

| mode | idea | bits kept |
| --- | --- | --- |
| `xor` | XOR neighbouring qubits inside each shot | 1/2 |
| `von_neumann` | compare consecutive shots of one qubit, keep only `01` / `10` | ~1/4 |

A bias of a few percent is hard to spot in a list of numbers, so quRandom turns the bits into a
**random walk**: every `1` is a step up, every `0` a step down. A fair walk of `n` steps ends within
`±2√n` about 95% of the time (the grey band). A biased walk drifts out of it.

![Demo chart: per-qubit bias, dice from raw vs debiased bits, and the two random walks](https://raw.githubusercontent.com/mazeeqe/quRandom/main/docs/images/demo_chart.png)

*Example on a test backend with a simulated 3% bias toward `1`: the raw walk (orange) drifts out of
the band, the debiased walk (blue) stays inside. The dice from both sets of bits come up about one
time in six per face.*

## How random is each run?

Every run gets a **randomness score** for its raw and its debiased bits:

- **Tests passed:** five NIST SP 800-22 tests (frequency, block frequency, runs, longest run of 1s,
  serial). They reproduce NIST's own worked examples.
- **Min-entropy per bit:** how many truly random bits each bit is worth (NIST SP 800-90B
  most-common-value estimate, 99% confidence), shown next to the best score possible for that
  many bits.
- **Patterns between bits:** the correlation between each bit and the bit 1 to 16 places later.

![Randomness report: every bit as a pixel, test p-values, and correlations between bits](https://raw.githubusercontent.com/mazeeqe/quRandom/main/docs/images/randomness_report.png)

*A run on the built-in simulator: random bits look like TV static, every test passes, and no
pattern links nearby bits.*

## Is it really quantum? A built-in Bell test

Bits from a simulator could in principle come from a hidden classical program. A **Bell test**
checks for something no classical source can do. Four extra qubits in the same circuit form two
**setting coins** and an **entangled pair** `(|00⟩ + |11⟩)/√2`. The coins pick, at random, the
direction each side of the pair is measured in.

From the correlations `E = P(same) − P(different)` of the four setting pairs:

$$S = E(0,0) + E(0,1) + E(1,0) - E(1,1)$$

Any classical source gives `S ≤ 2`. Quantum mechanics predicts `2√2 ≈ 2.83`.

![Bell test: correlation per setting pair against the quantum prediction, and S against the classical limit](https://raw.githubusercontent.com/mazeeqe/quRandom/main/docs/images/bell_test.png)

*A 512-shot run on the built-in simulator: S is many standard errors above the classical limit
of 2. This is a demonstration, not a certificate of randomness: a rigorous Bell test also needs
the two sides far apart, which one chip or a simulator can't provide.*

## How to run

1. Press **Run**.
2. In **Select QPU**, choose the built-in simulator or an **IonQ remote simulator** such as
   *IonQ Forte 1*. All simulators are free.
3. Under **Run settings** keep the defaults or change them: **Shots** 512, **Qubits** 8 (even),
   **Debias** `xor` / `von_neumann` / `none`, **Plot** on, **Bell** on.
4. Read the console, in order: the circuit; a bitstring turned into a number; how random the run
   is (per-qubit bias, health tests, randomness score); the random walk; dice from raw vs
   debiased bits; dice rolls, a float and a shuffle; the Bell test; and a result line for
   comparing devices.
5. Look at the three charts shown above.

Tip: an IonQ noise-model simulator shows real noise. More **Shots** make a bias easier to see in
the walk and narrow the error on S. Everything still runs as a single job.

In your own code:

```python
from qrand import QuantumRandom
qr = QuantumRandom(backend, n_qubits=8, shots=512, debias="xor", bell_test=True)
qr.randint(1, 6)
qr.report()["bell"]["S"]
```

## Real quantum hardware

The same code runs on IonQ's trapped-ion computers (**IonQ Forte 1**, **IonQ Forte Enterprise 1**
under *Quantum computer*) with Qollab credits. No login or API key is needed: Qollab provides the
backend. Try the matching free remote simulator first, keep shots low, and approve the credit
estimate. The console then labels the backend `(real quantum hardware)`. Hardware isn't required
or scored, and **this path is not yet tested on a real device**: we had no credits during the
hackathon.

## Honest notes

- On simulators, the bits are *simulated* quantum randomness. Only real quantum hardware is
  physically random.
- IonQ's ideal simulator returns counts only, not the order of the shots. quRandom then restores
  a random order with the OS random generator and prints a warning. The noise-model simulators
  return per-shot results.
- Not for cryptographic use.

## Built during the hackathon

Everything here (library, bias analysis, debiasing, health tests, Bell test, demo, docs and
pictures) was built during the Qollab Hackathon window (Oct 9–11, 2026). No pre-existing project
code was reused. The code was written with the help of AI tools (Claude). It builds on Qiskit;
the health tests follow NIST SP 800-22 and the min-entropy estimate follows NIST SP 800-90B.

Source code, tests and docs: [github.com/mazeeqe/quRandom](https://github.com/mazeeqe/quRandom).
License: MIT.
