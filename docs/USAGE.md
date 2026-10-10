# qrand usage guide

This guide covers how to create a generator, what range each function returns, and how many
numbers one quantum job gives you.

## How it works in one paragraph

`QuantumRandom` runs **one** circuit job when you create it: a Hadamard gate on every qubit,
then a measurement. Every shot gives one bit per qubit. All those bits go into an **entropy pool**
(optionally debiased first). Every function below takes bits out of that pool, so the pool size
decides how many numbers you can draw. When the pool is empty, qrand raises `EntropyExhausted`.

```python
from qrand import QuantumRandom, EntropyExhausted

qr = QuantumRandom(backend, n_qubits=8, shots=512, debias="xor")
qr.randint(1, 6)       # a die roll
qr.bits_remaining      # bits left in the pool
```

## Creating a generator

```python
QuantumRandom(backend=None, n_qubits=8, shots=512, debias="xor", auto_refill=False)
```

| Parameter | Default | Allowed values | Meaning |
| --- | --- | --- | --- |
| `backend` | `None` | any Qiskit backend | On Qollab pass the `backend` it creates. `None` uses Qiskit's local `BasicSimulator`. |
| `n_qubits` | `8` | `>= 1`; even when `debias="xor"` | Qubits per shot, so bits per shot. |
| `shots` | `512` | `>= 2` | Number of shots in the job. |
| `debias` | `"xor"` | `"none"`, `"xor"`, `"von_neumann"` | How to remove measurement bias (see below). |
| `auto_refill` | `False` | `True` / `False` | Run another job when the pool runs out. **Keep `False` on IonQ**, which allows one job per run. |

Invalid values raise `ValueError`.

## Pool size: how many bits you get

| `debias` | Pool size | Default settings (8 qubits × 512 shots) |
| --- | --- | --- |
| `"none"` | `n_qubits × shots` | 4096 bits |
| `"xor"` | `n_qubits × shots / 2` | 2048 bits |
| `"von_neumann"` | about `n_qubits × shots / 4` (varies run to run) | about 1024 bits |

- `"xor"` XORs neighbouring qubits inside each shot (q0⊕q1, q2⊕q3, ...).
- `"von_neumann"` compares the same qubit in two consecutive shots and keeps a bit only when they
  differ (`01` → 0, `10` → 1). It removes bias completely but keeps fewer bits.

Check `qr.bits_remaining` at any time.

## Functions, ranges and bit cost

| Function | Returns | Range | Bits used per call |
| --- | --- | --- | --- |
| `bitstring(n)` | `str` of `'0'`/`'1'` | exactly `n` characters | `n` |
| `getrandbits(k)` | `int` | `0` to `2**k - 1` | `k` |
| `randbelow(n)` | `int` | `0` to `n - 1` | about `k × 2**k / n`, where `k = (n-1).bit_length()` |
| `randint(a, b)` | `int` | `a` to `b`, **both included** | same as `randbelow(b - a + 1)` |
| `random()` | `float` | `0.0 <= x < 1.0`, steps of 2⁻⁵³ | `53` |
| `choice(seq)` | an item of `seq` | any item, equally likely | same as `randbelow(len(seq))` |
| `shuffle(items)` | `None` (shuffles the list in place) | every order equally likely | sum of `randbelow(i + 1)` for `i = 1 … len - 1` |

Notes:

- **No size limit on ranges.** `randint(1, 10**12)` works; it only uses more bits (40 per try).
  The only limit is how many bits are left in the pool.
- **No modulo bias.** `randbelow`, `randint`, `choice` and `shuffle` use rejection sampling: they
  draw `k` bits and retry if the value is too large. That is why their cost is an average. A
  range whose size is a power of two (2, 4, 8, ..., 256) never retries, so it costs exactly `k`.
- `randint(a, b)` raises `ValueError` if `a > b`. `choice([])` raises `IndexError`.
- `randbelow(1)` and `randint(a, a)` return without using any bits.

## How many numbers you get

Average numbers per pool, from the formulas above. The default column has been checked against
real runs (for example 527 die rolls and 38 floats from a 2048-bit pool).

| What you draw | Bits per number (average) | Default pool, `xor` (2048 bits) | `none` (4096 bits) | `von_neumann` (~1024 bits) |
| --- | --- | --- | --- | --- |
| Coin flip, `randint(0, 1)` | 1 | 2048 | 4096 | ~1024 |
| Die, `randint(1, 6)` | 4 | ~512 | ~1024 | ~256 |
| `randint(1, 10)` | 6.4 | ~320 | ~640 | ~160 |
| `randint(1, 100)` | 8.96 | ~229 | ~457 | ~114 |
| Byte, `randint(0, 255)` | 8 | 256 | 512 | ~128 |
| `randint(1, 1000)` | 10.24 | ~200 | ~400 | ~100 |
| `randint(1, 1_000_000)` | 20.97 | ~98 | ~195 | ~49 |
| `random()` float | 53 | 38 | 77 | ~19 |
| Shuffle a 52-card deck | ~356 | ~5 | ~11 | ~2 |

To get more numbers, raise `shots` or `n_qubits`. The pool grows in proportion to
`n_qubits × shots`; for example 8 qubits × 2048 shots with `xor` gives 8192 bits (about 2048 die
rolls).

### Plan the shots you need

```
shots ≈ numbers × bits_per_number / (n_qubits × keep)
```

with `keep = 1` for `none`, `1/2` for `xor`, `1/4` for `von_neumann`. For 1000 die rolls with
8 qubits and `xor`: `1000 × 4 / (8 × 0.5) = 1000` shots. Add a margin of 10–20 %, because
rejection sampling sometimes needs extra tries.

## When the pool runs out

```python
try:
    rolls = [qr.randint(1, 6) for _ in range(5000)]
except EntropyExhausted:
    print("Out of quantum bits: raise shots or qubits")
```

With `auto_refill=True` qrand runs a new job instead of raising. Use it only on local
simulators: IonQ backends on Qollab accept one job per run.

## Checking quality: `report()`

`qr.report()` returns a dict describing the bits from the job:

| Key | Contents |
| --- | --- |
| `backend`, `qubits`, `shots`, `debias` | the settings used |
| `hardware` | `True` on a real quantum computer, `False` on any simulator |
| `per_qubit_p1` | list with P(measure 1) for each qubit; a fair qubit is near 0.5 |
| `raw`, `debiased` | health tests for the raw and the debiased bits (below) |
| `warnings` | list of warnings, for example when a backend returned counts only |

Each of `raw` and `debiased` contains:

| Key | Meaning | Ideal |
| --- | --- | --- |
| `bits` | number of bits tested | – |
| `ones_fraction` | share of 1s | 0.5 |
| `monobit_p` | frequency test p-value | `>= 0.01` passes |
| `block_frequency_p` | block frequency test: is the share of 1s about ½ inside every 32-bit block? | `>= 0.01` passes |
| `runs_p` | runs test p-value (are flips between 0 and 1 as frequent as chance predicts?) | `>= 0.01` passes |
| `longest_run_p` | longest run of 1s per block, compared with chance (needs 128+ bits, else `nan`) | `>= 0.01` passes |
| `serial_p` | serial test: are all overlapping 3-bit patterns equally common? (lower of its two p-values) | `>= 0.01` passes |
| `min_entropy` | min-entropy per bit: how many truly random bits each bit is worth (NIST SP 800-90B most-common-value estimate, 99% confidence) | as close as possible to `ideal_min_entropy_per_bit(bits)` |
| `max_autocorr` | largest correlation between a bit and the bit 1–16 places later | `<= autocorr_limit(bits)` |
| `nibble_entropy` | Shannon entropy of 4-bit blocks | 4.0 |

`report()` needs at least 100 bits in both the raw and the debiased pool, so use a job of at
least 512 raw bits with `von_neumann` (for example 8 qubits × 64 shots).

The same tests are available on their own in `qrand.stats`:
`ones_fraction`, `monobit_p`, `block_frequency_p(bits, block=32)`, `runs_p`, `longest_run_p`,
`serial_p(bits, m=3)` (returns both p-values), `nibble_entropy`, `per_qubit_p1`, `health_report`
and `igamc` (the incomplete gamma function the tests use).

Measures of how random a run is:

| Function | Returns |
| --- | --- |
| `min_entropy_per_bit(bits)` | min-entropy per bit, between 0 (always the same value) and just under 1 |
| `ideal_min_entropy_per_bit(n)` | the best `min_entropy_per_bit` can give for `n` perfectly balanced bits; the 99% confidence bound keeps it below 1 (0.943 for 4096 bits, 0.920 for 2048) |
| `autocorrelation(bits, max_lag=16)` | correlation between each bit and the bit `k` places later, for `k = 1 … max_lag`; `+1` means bits repeat, `-1` means they alternate |
| `autocorr_limit(n)` | fair range `3/√n`; fair bits keep all 16 lags inside it about 96% of the time |

The five p-value tests follow NIST SP 800-22 and reproduce the worked examples in that document
(checked in `tests/test_qrand.py`). With 10 checks per run (5 tests × raw and debiased), a single
fail at the 0.01 level turns up by chance in about 1 run in 10, even for perfect bits.

`qrand.stats` also has the helpers behind the demo charts:

| Function | Returns |
| --- | --- |
| `random_walk(bits)` | list of positions, starting at 0; `'1'` steps up, `'0'` steps down |
| `dice_from_bits(bits)` | die rolls 1–6 from 3-bit chunks; chunks worth 6 or 7 are skipped |
| `chi2_uniform_p(counts)` | chi-square p-value against equal counts (needs an even number of categories, e.g. 6 faces); `>= 0.01` means consistent with fair |

A fair random walk of `n` steps ends within `±2√n` about 95% of the time. If bits are biased
toward 1 with P(1) = p, the walk drifts by about `(2p − 1) × n`, so the drift grows faster than
the spread and becomes visible with enough steps.

## Simulator or real hardware?

`is_hardware(backend)` returns `True` for a real quantum computer and `False` for any simulator:

```python
from qrand import is_hardware
is_hardware(backend)
```

It recognises IonQ's hardware backends (named `ionq_qpu...`). The IonQ simulators, IBM noise
models and Qiskit's `BasicSimulator` count as simulators.

On Qollab, running on hardware needs no code change and no API key: pick an IonQ quantum computer
in **Select QPU** and approve the credit cost. Both IonQ simulators and hardware accept one job
per run, which is what qrand sends.

## Other attributes

| Attribute | Meaning |
| --- | --- |
| `qr.circuit` | the Qiskit circuit that was run (`print(qr.circuit)` draws it) |
| `qr.raw_shots` | list of per-shot bitstrings from the job |
| `qr.raw_bits` | all raw bits joined into one string |
| `qr.pool_bits()` | the whole debiased pool, including bits already used |
| `qr.bits_remaining` | bits left to draw |
| `qr.refill()` | run a new job and replace the pool (counts as another job on IonQ) |

## Qollab demo settings

`main.py` exposes these as **Run settings** in Qollab's Select QPU dialog:

| Setting | Default | Notes |
| --- | --- | --- |
| Shots | 512 | more shots, more numbers |
| Qubits | 8 | must be even with `xor` |
| Debias | `xor` | `xor`, `von_neumann` or `none` |
| Plot | on | draws two charts: per-qubit bias, dice and random walks; then the randomness report (bit images, test p-values, correlations) |

The demo draws 16 bits, up to 120 die rolls, one float and a 6-letter shuffle (about 600 bits in
total), so the defaults leave plenty to spare. The random walk and the raw vs debiased dice
only read the job's bits for the charts; they do not use up the pool. With `von_neumann` and few shots, it may run out of
bits early and print a message instead of crashing.

## Limits to keep in mind

- On simulators, the bits are simulated quantum randomness. Only real quantum hardware is
  physically random.
- IonQ's ideal simulator returns counts only. qrand then restores the shot order with the OS
  random generator and adds a warning. The noise-model simulators return per-shot results.
- Not for cryptographic use.
