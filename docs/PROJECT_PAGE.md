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
- `stats.random_walk()`, `stats.dice_from_bits()`, `stats.chi2_uniform_p()`: the tools
  behind the demo charts

Full usage guide, with ranges and how many numbers each job gives:
[docs/USAGE.md](https://github.com/mazeeqe/quRandom/blob/main/docs/USAGE.md)

## What is new: noise-aware randomness

Real devices and their noise models are not perfect coins. A qubit can read
`1` a little more often than `0`. qrand measures that bias per qubit, shows
it, and can remove it with two debiasing modes:

| mode | idea | bits kept |
| --- | --- | --- |
| `xor` | XOR neighbouring qubits inside each shot | 1/2 |
| `von_neumann` | compare consecutive shots of one qubit, keep only `01`/`10` | ~1/4 |

The health report compares raw and debiased bits so you can see the effect.

## Seeing the bias: a quantum random walk

A bias of a few percent is hard to spot in a list of numbers. qrand makes it
visible by turning the bits into a **random walk**: every bit is one step,
`1` goes up and `0` goes down.

- A fair walk wanders around zero. After `n` steps it ends within `±2√n` about
  95% of the time. The demo draws this range as a grey band.
- A biased walk drifts. With P(1) = p, it moves about `(2p − 1) × n` steps
  away, and this drift grows faster than the band. A 3% bias over 4096 steps
  ends around +170, well outside the band of ±128.

The demo draws the raw walk (orange) and the debiased walk (blue) from the
same job, so you can see debiasing remove the drift.

It also rolls **dice from the raw and from the debiased bits** (3 bits per
roll, 6 and 7 rejected) and compares how often each face comes up with a fair
16.7%, using a chi-square test. The dice show that the numbers work; the walk
is what shows the bias, because a small bias barely changes dice counts.

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
   number), **Debias** (`xor`, `von_neumann` or `none`) and **Plot** (on).
4. Read the console:
   1. the circuit
   2. a measured bitstring converted to a number
   3. P(1) for each qubit and the health tests, raw vs debiased
   4. the random walk: where the raw and debiased walks end, and whether that
      is inside the range of fair walks
   5. dice from raw vs debiased bits, with the chi-square fairness test
   6. using the numbers: dice rolls, a float and a shuffle
5. Look at the chart: per-qubit bias, dice raw vs debiased, and the two random
   walks inside the band where fair walks stay.

Tip: try an IonQ noise-model simulator to see real noise. More **Shots** make
a bias easier to see in the walk. The walk and the dice comparison only read
the job's bits, so it is still a single job.

Use it in your own code:

```python
from qrand import QuantumRandom
qr = QuantumRandom(backend, n_qubits=8, shots=512, debias="xor")
qr.randint(1, 6)
```

## Run it on real quantum hardware

Everything above runs on free simulators. With Qollab credits, the same code runs on real IonQ
trapped-ion hardware. There is no login or key to set up, because Qollab provides the backend.

1. **Try the free simulator of the same machine first.** Pick **IonQ Forte 1** under *Remote
   simulator*. It uses IonQ's noise model of that machine and costs nothing.
2. **Check the machine is online.** Offline machines show in the Select QPU dialog, and
   maintenance is posted at [status.ionq.co](https://status.ionq.co).
3. **Pick the quantum computer.** Choose **IonQ Forte 1** or **IonQ Forte Enterprise 1** under
   *Quantum computer*.
4. **Keep shots low at first.** Cost grows with shots. 512 shots × 8 qubits already gives about
   500 die rolls with `xor`.
5. **Approve the price.** The runner shows an estimated cost next to your balance and waits.
   Decline and nothing is charged. The final charge can differ a little from the estimate.
6. **Read the output.** The console says `(real quantum hardware)` next to the backend name, and
   the closing note says the bits are physically random. Waiting in IonQ's queue can take a
   while; the console prints a predicted wait.

Judges don't need hardware; it isn't required or scored.

**Not yet tested on hardware:** we had no Qollab credits during the hackathon, so this path
has been checked against IonQ's Qiskit backend objects and the IonQ remote simulators, but
not run on a real quantum computer.

## Honest notes

- Simulators are classical programs, so on them the bits are *simulated*
  quantum randomness. Only real quantum hardware is physically random.
  Run the same code on an IonQ quantum computer (credits) for that; the demo
  detects hardware and says so.
- IonQ's ideal simulator returns only counts (how often each outcome came up),
  not the order of the shots. qrand then rebuilds the shots and restores a
  random order with the OS random generator, and prints a warning. The
  noise-model simulators return per-shot results, which is what qrand needs.
- Not for cryptographic use.

## Built during the hackathon

Everything here (library, bias analysis, debiasing, tests and demo) was built
during the Qollab Hackathon window (Oct 9-11, 2026). No pre-existing project
code was reused. The code was written with the help of AI tools (Claude).
It builds on Qiskit, and the health tests follow the ideas of NIST SP 800-22.

Source: https://github.com/mazeeqe/quRandom

License: MIT.

**Tags:** `qiskit`, `ionq`, `random-numbers`, `hadamard`, `noise`, `random-walk`, `hackathon`
