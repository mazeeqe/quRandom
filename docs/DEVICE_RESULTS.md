# Which device is the fairest coin?

Each Qollab run ends with a **result line**. Running the demo on different backends and
collecting those lines shows how fair each device's qubits are. Qollab doesn't keep anything
between runs, so copy each line into the table below by hand.

## How to add a row

1. Run the demo on Qollab with the same settings each time (recommended: Shots 512, Qubits 8,
   Debias `xor`), picking a different backend in **Select QPU**.
2. Copy the line under *Result line* at the end of the console output.
3. Paste it as a new row at the bottom of the table.

All simulators are free, including the IBM noise models and the IonQ remote simulators.

## Columns

| Column | Meaning |
| --- | --- |
| backend | backend name the run reported |
| type | `simulator` or `hardware` |
| qubits, shots, debias | run settings |
| worst qubit P(1) | the qubit furthest from a fair 0.5 |
| raw / debiased share of 1s | share of 1s over all bits; fair is 0.5 |
| raw / debiased walk end | where the random walk ended; a fair walk of `n` steps ends within `±2√n` about 95% of the time (±128 for 4096 raw steps, ±91 for 2048 `xor` steps) |
| raw / debiased lowest p | lowest p-value of the five health tests; `>= 0.01` passes |
| raw / debiased min-entropy | min-entropy per bit; best possible is 0.943 for 4096 raw bits and 0.920 for 2048 `xor` bits |
| Bell S | Bell test value with its standard error; above 2 is impossible classically, 2.83 is the quantum prediction; noise pulls it down |
| certified bits/round | random bits per Bell round that S guarantees, using S minus 3 standard errors (Pironio et al. 2010); 0 at S ≤ 2, 1 at S = 2.83 |
| un-flip P(0) | share of 0s after H, H, measure; 1.0 is perfect interference, 0.5 is a classical coin; noise (decoherence) pulls it down |

## Results

| backend | type | qubits | shots | debias | worst qubit P(1) | raw share of 1s | debiased share of 1s | raw walk end | debiased walk end | raw lowest p | debiased lowest p | raw min-entropy | debiased min-entropy | Bell S | certified bits/round | un-flip P(0) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
