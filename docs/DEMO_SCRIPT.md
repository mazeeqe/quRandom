# Demo video script (target 2:40)

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
5. Settings for both runs: **Shots 512, Qubits 8, Debias xor, Plot on, Bell on**.

## Script

About 290 words of voiceover (about 2:15 at a calm pace). With clicking and pauses it comes to
about 2:40, inside the 3-minute limit; trim scene 3 if you run long.

### 1. Hook (0:00–0:15)

**Show:** the Qollab project page.

**Say:** "This is quRandom. It makes random numbers by measuring qubits, and it checks whether
the quantum hardware is actually a fair coin."

### 2. The idea (0:15–0:45)

**Show:** press **Run**, choose the **built-in simulator**, press Run. Show the overview at the
top of the console, then step 1.

**Say:** "Every qubit gets a Hadamard gate, which puts it halfway between zero and one. When we
measure it, it collapses to zero or one, fifty-fifty. Eight qubits give eight random bits per
shot, and 512 shots fill a pool of bits in a single job."

### 3. Bits become numbers (0:45–1:05)

**Show:** step 3 (bitstring → number, dice rolls, decimal, shuffle) and the dice chart.

**Say:** "The measured bits form a binary string, and that string becomes a number. From the
pool we draw dice rolls, decimals and shuffles. Rejection sampling keeps every result equally
likely, and the dice chart shows each face coming up about one time in six."

### 4. Noise and the random walk (1:05–1:50)

**Show:** run again on the **IonQ noise-model simulator**. Point at the per-qubit bars and
the ✔/✘ checks in step 2, then at the random-walk chart.

**Say (both versions):** "Real devices are noisy, so a qubit can lean slightly toward one. A
lean of a few percent is hard to see in a list of numbers, so we turn the bits into a random
walk: every one is a step up, every zero a step down. A fair walk stays inside this grey band."

**Script A, the raw walk drifts out:** "The raw walk, in orange, drifts out of the band: that's
the bias. Debiasing combines pairs of qubits, and the blue walk stays inside."

**Script B, both walks stay inside:** "Here both walks stay inside the band, so this device
looks fair. If it leaned toward one, the orange walk would drift out, and debiasing would bring
it back."

### 5. Is it really quantum? (1:50–2:15)

**Show:** step 4 (the S scale) and the Bell test chart, from either run.

**Say:** "But could a classical program fake all this? Each run also includes a Bell test: two
entangled qubits, measured in directions picked by quantum coin flips. No classical source can
push the score S above two. We get about 2.8, many standard errors above the limit, just as
quantum mechanics predicts."

If noise pulls S below 2 on the noise-model run, show the built-in simulator run for this scene.

### 6. Honest close (2:15–2:30)

**Show:** the "Honest notes" section of the project page, then the license.

**Say:** "On simulators this is simulated quantum randomness; on real quantum hardware it is
physically random. Random numbers and the Bell test share one circuit and one job, so it works
within IonQ's limit. It's MIT
licensed and runs on Qollab. Thanks for watching."

## Optional: a real hardware run

If you have Qollab credits, a short hardware run makes a strong last scene. Record it separately,
since IonQ's queue can take a while, and keep shots low to limit the cost.

**Show:** pick **IonQ Forte 1** under *Quantum computer*, approve the credit estimate, then point
at `(real quantum hardware)` in the output and at the random walk.

**Say:** "And this is the same code on IonQ's real trapped-ion computer. No code changes: these
bits come from real qubits, so they're physically random."

To keep the video under 3 minutes, shorten scene 3 or 5.

## After recording

- Check the length: 2:00 to 3:00.
- Upload to YouTube as **Unlisted** (or Loom, Vimeo or Google Drive, viewable by anyone with the
  link).
- Open the link in a private window to confirm it plays without signing in.
- Add the link to your submission before **Oct 11, 19:00 ET**.
