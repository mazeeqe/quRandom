# Demo video script (target 2:30)

Record in a browser, upload to YouTube **Unlisted** (or Loom/Vimeo with public
link and no login). Open the link in a private window to confirm no sign-in.

| Time | Show | Say |
| --- | --- | --- |
| 0:00-0:15 | Project page | "qrand makes random numbers by measuring qubits. Let me show how." |
| 0:15-0:45 | Press Run, pick built-in simulator, show the circuit in the console | "Hadamard puts each qubit in superposition. Measuring gives a fair coin flip. Eight qubits give eight bits." |
| 0:45-1:10 | Bitstring -> number lines | "The measured qubits are joined into a binary string, which converts itself into a number." |
| 1:10-1:50 | Run again on **IonQ Forte 1** remote simulator | "On IonQ's noise model the qubits are no longer perfect coins. See the per-qubit bias." Point at the raw vs `xor` lines. |
| 1:50-2:15 | Dice rolls and chart | "Debiasing evens it out. Now `randint(1, 6)` is a fair quantum die, with no modulo bias." |
| 2:15-2:30 | Honest note + license | "On simulators it is simulated randomness; on real IonQ hardware it is physically random. MIT licensed, runnable on Qollab." |

Tip: use `shots=512`, `qubits=8`. Try `von_neumann` once to show it removing bias fully.
