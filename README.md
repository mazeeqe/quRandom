# quRandom

![quRandom: noise-aware random numbers from a quantum circuit](docs/images/thumbnail.png)

**qrand**: noise-aware random numbers from a quantum circuit. Submission for the Qollab Hackathon.

Every qubit gets a Hadamard gate and is measured, so each one is a 50/50 coin flip. A single
circuit job fills an *entropy pool*, and numbers are carved out of it. qrand measures each qubit's
bias (noisy hardware often reads `1` a little more than `0`) and can remove it with `xor` or
`von_neumann` debiasing.

New here? Start with the tutorial notebook,
[notebooks/qrand_tutorial.ipynb](notebooks/qrand_tutorial.ipynb). See [docs/USAGE.md](docs/USAGE.md) for the full API: ranges, bit costs and how many numbers a
job gives you. [docs/PROJECT_PAGE.md](docs/PROJECT_PAGE.md) has the project write-up,
[docs/PROJECT_CARD.md](docs/PROJECT_CARD.md) explains how to fill in the Qollab Project Card, and
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

### What the demo shows

One run sends a single circuit job. The console is written for newcomers: it opens with a
four-step overview, explains each step in plain words, and marks every check with ✔ or ✘.

1. **Flip quantum coins (and un-flip one):** a Hadamard gate and a measurement turn each qubit
   into a fair coin. One extra qubit gets H twice and reads 0 every time: the two paths to 1
   cancel (interference), so superposition is not a coin that is secretly heads or tails. On a
   noisy device a few 1s slip in, which is decoherence.
2. **Check the coins:** how often each qubit gave 1, six yes/no checks (five NIST SP 800-22
   tests plus a hidden-pattern check), an unpredictability score (NIST SP 800-90B min-entropy
   as a share of the best possible) and a **random walk**: every bit is a step, `1` up and `0`
   down. A fair walk of `n` steps ends within `±2√n` about 95% of the time; a bias toward `1`
   makes it drift out. Raw bits are compared with cleaned (debiased) bits throughout.
3. **Make numbers:** 16 bits turned into an integer, dice rolls, a float in `[0, 1)`, a shuffle,
   and a table of dice faces from raw vs cleaned bits.
4. **Prove it's quantum (Bell test, CHSH):** the Bell score S on a text scale, against the
   classical limit of 2 and the quantum prediction of 2.83.

Then a **summary** of ✔ / ! lines and a **technical details** section for experts: the full
circuit, p-values, min-entropy, autocorrelation, chi-square, the four CHSH correlations and a
result line for [docs/DEVICE_RESULTS.md](docs/DEVICE_RESULTS.md).

With **Plot** on it also draws this chart:

![Demo chart: per-qubit bias, dice raw vs debiased, and two random walks](docs/images/demo_chart.png)

*This example comes from a test backend with a simulated 3% bias toward `1`: the raw walk
(orange) ends at +206, outside the ±128 band, while the debiased walk (blue) stays inside. On an
unbiased simulator both walks stay inside the band.*

A second chart, the **randomness report**, shows each run at a glance:

![Randomness report: bit images, test p-values and correlations](docs/images/randomness_report.png)

- **Bit images:** every bit as a pixel (black = 1). Random bits look like TV static; a bias shows
  as more black, and a pattern shows as stripes or bands.
- **Health tests:** the p-value of each test, raw vs debiased, with the 0.01 pass line.
- **Patterns:** the correlation between each bit and the bit 1 to 16 places later. Fair bits stay
  inside the dashed range of `±3/√n`.
- **Min-entropy** in the title: how many truly random bits each bit is worth (NIST SP 800-90B
  estimate at 99% confidence), next to the best score possible for that many bits.

*This example is a run on Qiskit's built-in simulator.*

The walk and dice comparison only read the bits the job already produced; they don't use up the
pool or send extra jobs.

The run ends with a **result line**. Collect lines from different backends in
[docs/DEVICE_RESULTS.md](docs/DEVICE_RESULTS.md) to compare how fair each device's qubits are.

### The Bell test

Random numbers from a simulator could in principle come from a hidden classical program. A
**Bell test** checks for something no classical source can do. Every run adds four qubits to the
same circuit (still one job):

- two **setting coins**: qubits in superposition whose measurement picks, at random, the direction
  in which each side is measured
- an **entangled pair** `(|00⟩ + |11⟩)/√2`, measured along 0° or 90° on one side and 45° or −45° on
  the other, as the coins decide

For each of the four setting pairs, qrand computes the correlation `E = P(same) − P(different)`,
then `S = E(0,0) + E(0,1) + E(1,0) − E(1,1)`. Any classical source gives `S ≤ 2`; quantum
mechanics predicts `2√2 ≈ 2.83`. The demo prints S with its standard error and how many standard
errors it lies above 2.

This is a demonstration, not a certificate of randomness: a rigorous Bell test also needs the two
sides far apart and other loopholes closed, which a single chip or a simulator can't provide.

![Bell test: correlations per setting pair and S against the classical limit](docs/images/bell_test.png)

*A 512-shot run on Qiskit's built-in simulator: S = 2.84 ± 0.13, about 7 standard errors above
the classical limit. A value above 2.83 is sampling noise; more shots narrow the error.*

### Run settings

On Qollab, these appear under **Run settings** in the Select QPU dialog. Locally,
`python main.py` uses the defaults; to try other values, change them in the `def main(...)` line.

| Setting | Default | Notes |
| --- | --- | --- |
| `shots` | 512 | more shots give more numbers and make a bias easier to see in the walk |
| `qubits` | 8 | must be even with `xor` |
| `debias` | `xor` | `xor`, `von_neumann` or `none` |
| `plot` | on | draw the charts |
| `bell` | on | add the Bell test: 4 extra qubits in the same circuit and job |
| `unflip` | on | add the un-flip test: 1 extra qubit with H, H, measure |

| `hardware_checks` | off | on real hardware, also run the Bell and un-flip checks (costs more) |

The Bell and un-flip qubits only check the randomness; they never become numbers. On simulators
they run alongside the numbers because they are free. On real hardware they are skipped unless
`hardware_checks` is on, so a normal run pays only for the random-number qubits. In your own
code, `QuantumRandom` leaves them out by default and `check_hardware(backend)` runs them as a
separate test.

### Run on real quantum hardware

No login or API key is needed. On Qollab, the IonQ account and key belong to Qollab, which
creates the `backend` for whatever you pick in **Select QPU**. The same code runs on simulators
and hardware; only quantum computers cost credits.

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

Keep API keys out of the code: published Qollab code is public.

**Not yet tested on hardware:** we had no Qollab credits during the hackathon, so this path
has been checked against IonQ's Qiskit backend objects and the IonQ remote simulators, but
not run on a real quantum computer.

### In your own code

```python
from qrand import QuantumRandom

qr = QuantumRandom(backend, n_qubits=8, shots=512, debias="xor")  # backend=None uses a local simulator
qr.randint(1, 6)
qr.random()
qr.report()  # per-qubit bias and NIST-style health tests
```

The helpers behind the demo work on any bitstring:

```python
from qrand import stats

walk = stats.random_walk(qr.raw_bits)          # positions, starting at 0
rolls = stats.dice_from_bits(qr.pool_bits())   # die rolls 1-6
counts = [rolls.count(f) for f in range(1, 7)]
stats.chi2_uniform_p(counts)                   # >= 0.01: consistent with a fair die
```

## Tests

```bash
pytest
```

## Project layout

```
qrand/       library: generator (entropy pool, debiasing) and stats (health tests,
             random walk, dice, chi-square)
main.py      Qollab demo: console sections and chart
tests/       pytest tests
docs/        usage guide, project page and card, demo script, device results
docs/images/ pictures for the README and Project Card
scripts/     make_figures.py regenerates docs/images/
notebooks/   tutorial notebook (qrand_tutorial.ipynb)
```

## Team

- [@mazeeqe](https://github.com/mazeeqe)

## License

MIT, see [LICENSE](LICENSE).
