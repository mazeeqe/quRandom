# Demo video script (target 2:30)

Record in a browser, upload to YouTube **Unlisted** (or Loom/Vimeo with public
link and no login). Open the link in a private window to confirm no sign-in.

| Time | Show | Say |
| --- | --- | --- |
| 0:00-0:15 | Project page | "qrand makes random numbers by measuring qubits. Let me show how." |
| 0:15-0:45 | Press Run, pick built-in simulator, show the circuit in the console | "Hadamard puts each qubit in superposition. Measuring gives a fair coin flip. Eight qubits give eight bits." |
| 0:45-1:10 | Bitstring -> number lines | "The measured qubits are joined into a binary string, which converts itself into a number." |
| 1:10-1:50 | Run again on an IonQ noise-model simulator. Point at the per-qubit bars, then the random walk chart | "On a noisy device the qubits are not perfect coins. Every bit is a step: 1 up, 0 down. A small bias toward 1 makes the raw walk drift out of the grey band where fair walks stay. The debiased walk stays inside." |
| 1:50-2:15 | Dice: raw vs debiased chart and the chi-square lines | "Here are dice rolled from the same bits. Each face should get 16.7%. Now `randint(1, 6)` is a fair quantum die, with no modulo bias." |
| 2:15-2:30 | Honest note + license | "On simulators it is simulated randomness; on real IonQ hardware it is physically random. MIT licensed, runnable on Qollab." |

Tip: use `shots=512`, `qubits=8`. More shots make a bias easier to see in the walk (the drift
grows with the number of steps, the spread only with its square root). If the noise-model run
shows no drift, say so: both walks inside the band means the device looks fair.
