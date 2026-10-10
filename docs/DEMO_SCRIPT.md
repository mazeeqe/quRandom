# Demo video script (target 2:30)

The rules ask for 2 to 3 minutes showing the project working. A screen recording with voiceover
is enough.

## Before recording

1. Upload the latest code to the Qollab project and make sure the project page is up to date.
2. Do a test run on an **IonQ noise-model simulator** and look at the random walk:
   - **Raw walk leaves the grey band:** use script **A** in scene 4.
   - **Both walks stay inside:** use script **B** in scene 4. That is an honest result too.
3. IonQ jobs can take a while. Record the run, then cut out the waiting. Qollab allows one IonQ
   job per run, so press **Stop** and **Run** again to repeat.
4. Use Chrome, Edge, Brave, Opera or Firefox 153+ (Safari can't run projects yet). Zoom the
   browser so the console text is readable in the recording.
5. Settings for both runs: **Shots 512, Qubits 8, Debias xor, Plot on**.

## Script

About 250 words of voiceover (about 2 minutes at a calm pace), leaving time for clicking and
pauses to reach 2:30.

### 1. Hook (0:00–0:15)

**Show:** the Qollab project page.

**Say:** "This is quRandom. It makes random numbers by measuring qubits, and it checks whether
the quantum hardware is actually a fair coin."

### 2. The idea (0:15–0:45)

**Show:** press **Run**, choose the **built-in simulator**, press Run. Scroll to section 1, the
circuit.

**Say:** "Every qubit gets a Hadamard gate, which puts it halfway between zero and one. When we
measure it, it collapses to zero or one, fifty-fifty. Eight qubits give eight random bits per
shot, and 512 shots fill a pool of bits in a single job."

### 3. Bits become numbers (0:45–1:05)

**Show:** section 2 (bitstring → number), then section 6 (dice rolls, float, shuffle).

**Say:** "The measured bits form a binary string, and that string becomes a number. From the
pool we draw dice rolls, decimals and shuffles. Rejection sampling keeps every result equally
likely."

### 4. Noise and the random walk (1:05–1:50)

**Show:** run again on the **IonQ noise-model simulator**. Point at the per-qubit bars in
section 3, then at the random-walk chart.

**Say (both versions):** "Real devices are noisy, so a qubit can lean slightly toward one. A
lean of a few percent is hard to see in a list of numbers, so we turn the bits into a random
walk: every one is a step up, every zero a step down. A fair walk stays inside this grey band."

**Script A, the raw walk drifts out:** "The raw walk, in orange, drifts out of the band: that's
the bias. Debiasing combines pairs of qubits, and the blue walk stays inside."

**Script B, both walks stay inside:** "Here both walks stay inside the band, so this device
looks fair. If it leaned toward one, the orange walk would drift out, and debiasing would bring
it back."

### 5. Fair dice (1:50–2:15)

**Show:** the dice chart and the chi-square lines in section 5.

**Say:** "We also roll dice from the raw and the debiased bits. Every face should come up about
one time in six, and the chi-square test confirms that these dice are consistent with fair
ones."

### 6. Honest close (2:15–2:30)

**Show:** the "Honest notes" section of the project page, then the license.

**Say:** "On simulators this is simulated quantum randomness; on real quantum hardware it is
physically random. Everything runs in one job, so it works within IonQ's limit. It's MIT
licensed and runs on Qollab. Thanks for watching."

## After recording

- Check the length: 2:00 to 3:00.
- Upload to YouTube as **Unlisted** (or Loom, Vimeo or Google Drive, viewable by anyone with the
  link).
- Open the link in a private window to confirm it plays without signing in.
- Add the link to your submission before **Oct 11, 19:00 ET**.
