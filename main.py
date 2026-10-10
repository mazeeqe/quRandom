"""quRandom demo for Qollab: flip quantum coins, check them, make numbers, run a Bell test.

Press Run, pick a QPU (built-in simulator or an IonQ remote simulator),
and set Shots / Qubits / Debias under Run settings.
"""
import math
import textwrap

from qrand import EntropyExhausted, QuantumRandom, is_hardware, stats
from qrand import bell as bell_module

try:
    backend  # noqa: B018 - raises NameError unless Qollab pre-created it (Select QPU dialog)
    RUNNING_LOCALLY = False
except NameError:  # running locally: fall back to Qiskit's simulator
    from qiskit.providers.basic_provider import BasicSimulator
    backend = BasicSimulator()
    RUNNING_LOCALLY = True


HEALTH_TESTS = [  # (report key, NIST name, plain-language question)
    ("monobit_p", "frequency", "As many 0s as 1s overall?"),
    ("block_frequency_p", "block frequency", "As many 0s as 1s in every block of 32?"),
    ("runs_p", "runs", "Switches between 0 and 1 as often as coins?"),
    ("longest_run_p", "longest run of 1s", "No streaks of 1s that are too long?"),
    ("serial_p", "serial (3-bit)", "All 3-bit patterns equally common?"),
]
WIDTH = 76


def say(text, indent="  "):
    """Print a paragraph wrapped to the console width."""
    print(textwrap.fill(text, WIDTH, initial_indent=indent, subsequent_indent=indent))


def verdict(text):
    """Print a conclusion line: '  -> text', wrapped under itself."""
    print(textwrap.fill(text, WIDTH, initial_indent="  -> ", subsequent_indent="     "))


def heading(title):
    print(f"\n{title}\n{'-' * len(title)}")


def passes(p):
    return not math.isnan(p) and p >= 0.01


def tick(ok):
    return "✔ yes" if ok else "✘ NO"


def pass_fail(p):
    return "n/a" if math.isnan(p) else f"{p:.3f} {'pass' if p >= 0.01 else 'FAIL'}"


def checks(r):
    """Plain-language checks for one set of bits: list of (question, ok)."""
    rows = [(question, passes(r[key])) for key, _, question in HEALTH_TESTS]
    rows.append(("No hidden patterns between nearby bits?",
                 r["max_autocorr"] <= stats.autocorr_limit(r["bits"])))
    return rows


def unpredictability(r):
    """Min-entropy as a share of the best possible for this many bits."""
    return r["min_entropy"] / stats.ideal_min_entropy_per_bit(r["bits"])


def format_s(chsh):
    return "-" if not chsh or math.isnan(chsh["S"]) else f"{chsh['S']:.2f} ± {chsh['sigma']:.2f}"


def bar(p, width=30):
    return "#" * round(p * width) + "." * (width - round(p * width))


def s_scale(chsh, per_unit=16):
    """Text picture of S on a 0-3 scale with the classical limit and quantum prediction."""
    n = 3 * per_unit
    axis = "".join("|" if i % per_unit == 0 else "·" for i in range(n + 1))
    s_value = max(0.0, min(3.0, chsh["S"]))
    return [
        "    " + "".join(f"{u:<{per_unit}}" for u in range(3)) + "3",
        "    " + axis,
        "    " + "█" * round(s_value * per_unit) + f"  <- this run: S = {chsh['S']:.2f}",
        "    " + " " * round(chsh["classical_limit"] * per_unit) + "^ classical max: 2",
        "    " + " " * round(chsh["quantum_prediction"] * per_unit) + "^ quantum: 2.83",
    ]


def unflip_sigmas(u):
    """How many standard errors P(0) lies above the 0.5 of a coin flipped twice."""
    return (u["zeros"] - u["shots"] / 2) / math.sqrt(u["shots"] / 4)


def unflip_shows_interference(u):
    return unflip_sigmas(u) > 3


def explain_unflip(u, single_p0):
    """Step 1b: H twice shows that superposition is not hidden 0-or-1."""
    print("\n  Is the qubit secretly 0 or 1 already? Un-flipping a quantum coin")
    say("Flip a real coin, flip it again, and it is still 50/50. If a qubit in the mix were "
        "secretly 0 or 1 and we just didn't know which, a second H would act the same way. "
        "So one extra qubit gets H twice before it is measured:")
    print("\n      q: ─[H]─[H]─[M]─   ->   ?\n")
    print(f"    {'one H (coins above)':<22}{bar(single_p0)}  {single_p0:6.1%} zeros")
    print(f"    {'H then H (un-flipped)':<22}{bar(u['p0'])}  {u['p0']:6.1%} zeros"
          f"   ({u['zeros']} of {u['shots']} shots)")
    if u["p0"] == 1:
        verdict("Always 0. The two ways of reaching 1 cancel each other out, like waves "
                "(interference). A coin that was secretly heads or tails can't do that: the "
                "qubit really was in both states at once. That is superposition.")
    elif unflip_shows_interference(u):
        verdict(f"0 came up {u['p0']:.1%} of the time, far more than the 50% of a coin flipped "
                "twice: the two ways of reaching 1 cancel out (interference), so the qubit was "
                f"not secretly 0 or 1. The few 1s ({1 - u['p0']:.1%}) are noise: it disturbs "
                "the qubit while it is in superposition and washes out part of the interference "
                "(decoherence). That is why quantum computers are hard to build.")
    else:
        verdict(f"0 came up {u['p0']:.1%} of the time, close to the 50% of a coin flipped "
                "twice: here noise destroyed the interference (decoherence), or the backend "
                "is not quantum.")


def main(shots: int = 512, qubits: int = 8, debias: str = "xor", plot: bool = True, bell: bool = True, unflip: bool = True, hardware_checks: bool = False):
    # The Bell and un-flip qubits only check the randomness. They are free on simulators, but on
    # real hardware they cost credits, so there they run only when hardware_checks is on.
    checks_skipped = is_hardware(backend) and not hardware_checks and (bell or unflip)
    if checks_skipped:
        bell = unflip = False
    qr = QuantumRandom(backend, n_qubits=qubits, shots=shots, debias=debias, bell_test=bell,
                       unflip_test=unflip)
    rep = qr.report()
    raw, deb = rep["raw"], rep["debiased"]
    kind = "real quantum hardware" if rep["hardware"] else "a simulator"
    cleaned = "cleaned bits"
    steps = 4 if bell else 3

    print("=" * WIDTH)
    print("  quRandom: random numbers from quantum coin flips")
    print("=" * WIDTH)
    print("What this program does:")
    print("  STEP 1  Flip quantum coins   50/50 qubits"
          + (", then un-flip one (superposition)" if unflip else ""))
    print("  STEP 2  Check the coins      are the 0s and 1s fair and free of patterns?")
    print("  STEP 3  Make numbers         turn the bits into dice rolls, decimals, shuffles")
    if bell:
        print("  STEP 4  Prove it's quantum   a Bell test that no ordinary computer can pass")
    print("  Then a short summary, and technical details at the end for experts.\n")
    print(f"This run: {qubits} qubits x {shots} shots on {rep['backend']} ({kind})")
    print(f"          = {raw['bits']:,} random bits from a single run of the circuit")
    if checks_skipped:
        say("Real hardware: the Bell and un-flip checks are off to save credits. They only "
            "check the randomness and never become numbers. To test this device, turn on "
            "Hardware checks (best in a separate run).", "")

    # ---------------------------------------------------------------- step 1
    heading(f"STEP 1 of {steps}: Flip quantum coins" + (" (and un-flip one)" if unflip else ""))
    say("Every qubit starts at 0. A Hadamard gate (H) puts it in an equal mix of 0 and 1. "
        "Measuring it (M) then gives 0 or 1, each with a 50% chance, like a perfect coin. "
        "For one qubit the circuit is:")
    print("\n      q: ─[H]─[M]─   ->   0 or 1\n")
    say(f"We do this on {qubits} qubits at once and repeat it {shots} times (each repeat is a "
        f"'shot'), so we get {qubits} x {shots} = {raw['bits']:,} coin flips."
        + (" Four more qubits run the Bell test of step 4 in the same circuit." if bell else "")
        + (" One more qubit is un-flipped below." if unflip else "")
        + " The full circuit is drawn in the technical details at the end.")
    unflipped = rep["unflip"]
    if unflipped:
        explain_unflip(unflipped, 1 - raw["ones_fraction"])

    # ---------------------------------------------------------------- step 2
    heading(f"STEP 2 of {steps}: Check the coins")
    say("Real quantum chips are never perfect: noise can make a qubit land on 1 a little "
        "more often than on 0. So we check the coins before using them.")
    if debias == "none":
        say("Cleaning is off (Debias = none), so both columns below show the same raw bits.")
    else:
        say(f"Besides the raw bits we also check a cleaned copy (Debias = {debias}): "
            + ("each pair of qubits is combined with XOR, which cancels most of a lean and "
               "keeps half of the bits." if debias == "xor" else
               "the same qubit is compared in two shots and a bit is kept only when they "
               "differ, which removes a lean and keeps about a quarter of the bits."))

    limit = 3 * math.sqrt(0.25 / shots)
    print("\n  How often each qubit gave 1 (a fair coin gives 0.500):")
    leaning = []
    for q, p in enumerate(rep["per_qubit_p1"]):
        lean = abs(p - 0.5) > limit
        if lean:
            leaning.append(f"q{q}")
        print(f"    q{q:<3}{bar(p)} {p:.3f}" + ("  <- leans" if lean else ""))
    if leaning:
        verdict(f"{', '.join(leaning)} lean more than chance explains (more than ±{limit:.3f} "
                "from 0.500). That is noise; "
                + ("set Debias to xor to clean it." if debias == "none"
                   else "the cleaned bits remove it."))
    else:
        verdict(f"All qubits are within ±{limit:.3f} of 0.500, the normal wobble for {shots} "
            "flips: they look like fair coins.")

    raw_checks, deb_checks = checks(raw), checks(deb)
    col = 44
    print("\n  Six randomness checks (five come from NIST, the US standards agency):")
    print(f"    {'Check':<{col}}{'raw bits':<14}{cleaned}")
    for (question, ok_raw), (_, ok_deb) in zip(raw_checks, deb_checks):
        print(f"    {question:<{col}}{tick(ok_raw):<14}{tick(ok_deb)}")
    print(f"    {'Unpredictability (100% = perfect coin)':<{col}}"
          f"{unpredictability(raw):<14.0%}{unpredictability(deb):.0%}")
    n_raw, n_deb = sum(ok for _, ok in raw_checks), sum(ok for _, ok in deb_checks)
    verdict(f"Raw bits passed {n_raw}/6 checks, cleaned bits {n_deb}/6. Each check can fail by "
        "pure chance about 1 time in 100, so a single ✘ now and then is normal. Many ✘, or "
        "the same ✘ on every run, mean the bits are not fair.")

    print("\n  Seeing a lean: the random walk")
    say("Imagine walking along a line: one step up for every 1, one step down for every 0. "
        "Fair coins wander but stay near the start. Coins that lean toward 1 drift steadily "
        "upward, so even a small lean becomes easy to see.")
    raw_bits, deb_bits = qr.raw_bits, qr.pool_bits()
    walks = {"raw bits": stats.random_walk(raw_bits), cleaned: stats.random_walk(deb_bits)}
    for name, walk in walks.items():
        n_steps, end = len(walk) - 1, walk[-1]
        band = 2 * math.sqrt(n_steps)
        ok = abs(end) <= band
        print(f"    {name:<16}{n_steps:>5} steps, finished at {end:+5d}   "
              + (f"✔ within ±{band:.0f}, the fair range" if ok
                 else f"✘ beyond ±{band:.0f}: drift, so the coins lean"))
    say("(95% of fair walks finish inside that range. See the bottom of the first chart.)")

    # ---------------------------------------------------------------- step 3
    heading(f"STEP 3 of {steps}: Turn the bits into numbers")
    bits = qr.bitstring(16)
    say("Bits are read as a binary number. For example, the next 16 bits are:")
    print(f"\n      {bits}  ->  {int(bits, 2):,}   (16 bits give any whole number from 0 to 65,535)\n")
    say("A die roll takes 3 bits, a number from 0 to 7. 0-5 become faces 1-6; 6 and 7 are "
        "thrown away and redrawn, so every face stays equally likely. Every number below "
        "uses fresh bits.")
    rolls = []
    try:
        for _ in range(120):
            rolls.append(qr.randint(1, 6))
    except EntropyExhausted:
        say("(Ran out of bits early: raise Shots for more rolls.)")
    deck = list("ABCDEF")
    shuffled = qr.bits_remaining >= 30
    if shuffled:
        qr.shuffle(deck)
    decimal = qr.random() if qr.bits_remaining >= 53 else None
    print()
    first = f"{min(20, len(rolls))} dice rolls"
    print(f"    {first:<22}: {' '.join(map(str, rolls[:20]))}")
    print(f"    a decimal in [0, 1)   : {'n/a (out of bits)' if decimal is None else decimal}")
    print(f"    cards A-F shuffled    : {''.join(deck) if shuffled else 'n/a (out of bits)'}")
    print(f"    quantum bits left     : {qr.bits_remaining:,} of {deb['bits']:,} "
          "(raise Shots for more)")

    dice = {"raw bits": stats.dice_from_bits(raw_bits), cleaned: stats.dice_from_bits(deb_bits)}
    dice_p = {}
    print("\n  Are the dice fair? We turn all the bits into dice and count each face:")
    print(f"    {'':<16}" + "".join(f"{f:>7}" for f in range(1, 7)) + "    rolls")
    for name, d in dice.items():
        counts = [d.count(f) for f in range(1, 7)]
        dice_p[name] = stats.chi2_uniform_p(counts)
        print(f"    {name:<16}" + "".join(f"{100 * c / len(d):6.1f}%" for c in counts)
              + f"{len(d):>9}")
    print(f"    {'fair die':<16}" + f"{'16.7%':>7}" * 6)
    unfair = [name for name, p in dice_p.items() if p < 0.01]
    if not unfair:
        verdict("Both look like a fair die: small differences from 16.7% are normal luck.")
    else:
        verdict(f"The dice from {' and '.join(unfair)} are further from 16.7% than luck "
                "usually explains (this happens by chance about 1 time in 100). If it repeats "
                "on every run, the bits lean.")

    # ---------------------------------------------------------------- step 4
    chsh = rep["bell"]
    if chsh:
        heading(f"STEP 4 of {steps}: Prove it's quantum (Bell test)")
        say("Could an ordinary computer have made these bits? A Bell test checks for "
            "something only quantum physics can do. Two qubits are entangled: linked so "
            "that their results are connected even though each one alone is random. Two "
            "more quantum coins pick, at random, in which direction each of them is "
            "measured. From how often the pair agrees we compute a score S:")
        print()
        print("    any ordinary (classical) source:   S is at most 2.00")
        print("    quantum physics predicts:          S = 2.83")
        if math.isnan(chsh["S"]):
            say("Not enough shots for every combination of directions: raise Shots.")
        else:
            print(f"    this run:                          S = {chsh['S']:.2f} ± "
                  f"{chsh['sigma']:.2f}\n")
            print("\n".join(s_scale(chsh)))
            print()
            if chsh["S"] > chsh["classical_limit"]:
                verdict(f"S is above 2 by {chsh['sigmas_above_classical']:.1f} times its "
                    "uncertainty (±): no classical source can produce this, so the "
                    "correlations are quantum.")
            else:
                verdict("S is not above 2 this time, so these results could also come from a "
                    "classical source. Noise can wash out quantum correlations; try more "
                    "Shots.")
            if chsh["S"] > chsh["quantum_prediction"]:
                say("(S a bit above 2.83 is just luck in the sampling: the true value can't "
                    "exceed 2.83. More Shots narrow the ±.)")
        say("(This is a demonstration, not a certificate: a rigorous Bell test also needs the "
            "two qubits far apart, which one chip or a simulator can't provide.)")

    # ---------------------------------------------------------------- summary
    heading("SUMMARY")
    print(f"  ✔ Flipped {raw['bits']:,} quantum coins on {rep['backend']} in one run")
    print(f"  {'✔' if not leaning else '!'} " + ("Every qubit behaved like a fair coin"
          if not leaning else f"{', '.join(leaning)} leaned (noise); "
          + ("set Debias to xor to clean it" if debias == "none" else "cleaning fixes this")))
    print(f"  {'✔' if min(n_raw, n_deb) >= 5 else '!'} Raw bits passed {n_raw}/6 checks, cleaned bits "
          f"{n_deb}/6")
    made = [f"{len(rolls)} dice rolls"] + (["a decimal"] if decimal is not None else []) \
        + (["a shuffle"] if shuffled else [])
    print(f"  ✔ Made {', '.join(made[:-1]) + ' and ' + made[-1] if len(made) > 1 else made[0]}; "
          f"{qr.bits_remaining:,} bits left")
    if unflipped:
        print(f"  {'✔' if unflip_shows_interference(unflipped) else '!'} Un-flipped coin gave 0 "
              f"in {unflipped['p0']:.1%} of shots (a real coin: 50%)"
              + (": superposition" if unflip_shows_interference(unflipped) else ""))
    if chsh and not math.isnan(chsh["S"]):
        quantum = chsh["S"] > chsh["classical_limit"]
        print(f"  {'✔' if quantum else '!'} Bell test: S = {chsh['S']:.2f}, "
              + ("above the classical limit of 2: quantum" if quantum
                 else "not above the classical limit of 2 this time"))
    if checks_skipped:
        print("  - Bell and un-flip checks skipped on hardware (turn on Hardware checks)")
    if rep["hardware"]:
        say("Note: these bits come from measuring real qubits, so they are physically "
            "random. Any lean above is the hardware's own noise.")
    else:
        say("Note: a simulator is a classical program that imitates a quantum computer, so "
            "here the randomness is simulated. Only real quantum hardware is physically "
            "random.")
    for w in rep["warnings"]:
        say(f"Note: {w}")

    # ---------------------------------------------------------------- details
    heading("TECHNICAL DETAILS (for experts)")
    parts = [f"q0-q{qubits - 1}: random numbers"]
    if bell:
        parts += [f"q{qubits}-q{qubits + 1}: Bell setting coins",
                  f"q{qubits + 2}-q{qubits + 3}: entangled pair"]
    if unflip:
        parts.append(f"q{qr.circuit.num_qubits - 1}: un-flip test")
    print(f"Full circuit ({', '.join(parts)}):")
    print(qr.circuit.draw("text"))
    print(f"\n{'NIST SP 800-22 p-values':<26}{'raw':>14}{debias:>14}   (p >= 0.01 passes)")
    print(f"{'bits':<26}{raw['bits']:>14}{deb['bits']:>14}")
    print(f"{'share of 1s':<26}{raw['ones_fraction']:>14.4f}{deb['ones_fraction']:>14.4f}")
    for key, label, _ in HEALTH_TESTS:
        print(f"{label:<26}{pass_fail(raw[key]):>14}{pass_fail(deb[key]):>14}")
    print(f"{'min-entropy / bit (90B)':<26}{raw['min_entropy']:>14.3f}{deb['min_entropy']:>14.3f}"
          f"   (best possible {stats.ideal_min_entropy_per_bit(raw['bits']):.3f} / "
          f"{stats.ideal_min_entropy_per_bit(deb['bits']):.3f})")
    print(f"{'max |autocorr|, lag 1-16':<26}{raw['max_autocorr']:>14.3f}{deb['max_autocorr']:>14.3f}"
          f"   (limit 3/sqrt(n): {stats.autocorr_limit(raw['bits']):.3f} / "
          f"{stats.autocorr_limit(deb['bits']):.3f})")
    print(f"{'dice chi-square p':<26}" + "".join(f"{p:>14.3f}" for p in dice_p.values()))
    if chsh and not math.isnan(chsh["S"]):
        print("\nCHSH: S = E(0,0) + E(0,1) + E(1,0) - E(1,1), E = P(same) - P(different)")
        for (sa, sb), e in chsh["correlations"].items():
            print(f"  settings A{sa} B{sb}: E = {e:+.3f}  (prediction "
                  f"{bell_module.expected_correlation(sa, sb):+.3f}, "
                  f"{chsh['shots_per_setting'][(sa, sb)]} shots)")
        print(f"  S = {chsh['S']:.3f} ± {chsh['sigma']:.3f}  "
              f"({chsh['sigmas_above_classical']:+.1f} sigma relative to 2; Tsirelson bound "
              f"{chsh['quantum_prediction']:.3f})")
    if unflipped:
        print()
        say(f"Un-flip test (H, barrier, H, measure): P(0) = {unflipped['p0']:.4f} "
            f"({unflipped['zeros']}/{unflipped['shots']}), {unflip_sigmas(unflipped):+.1f} sigma "
            "from the 0.5 of a classical coin. The barrier stops Qiskit from cancelling H·H. A "
            "cloud compiler may still merge the two gates; then the 1s come only from "
            "measurement (readout) errors.", "")

    min_p = {name: min(r[key] for key, *_ in HEALTH_TESTS if not math.isnan(r[key]))
             for name, r in (("raw", raw), ("debiased", deb))}
    raw_walk_end, deb_walk_end = walks["raw bits"][-1], walks[cleaned][-1]
    print("\nResult line (copy into docs/DEVICE_RESULTS.md to compare devices):")
    print(f"| {rep['backend']} | {'hardware' if rep['hardware'] else 'simulator'} | {qubits} | "
          f"{shots} | {debias} | {max(rep['per_qubit_p1'], key=lambda p: abs(p - 0.5)):.3f} | "
          f"{raw['ones_fraction']:.4f} | {deb['ones_fraction']:.4f} | {raw_walk_end:+d} | "
          f"{deb_walk_end:+d} | {min_p['raw']:.3f} | {min_p['debiased']:.3f} | "
          f"{raw['min_entropy']:.3f} | {deb['min_entropy']:.3f} | "
          f"{format_s(chsh)} | {'-' if not unflipped else format(unflipped['p0'], '.3f')} |")
    if plot:
        charts = ["the coins, the dice and the random walk", "what the bits look like and the checks"]
        charts += ["the Bell test"] if chsh else []
        charts += ["the un-flipped coin"] if unflipped else []
        print()
        say(f"{len(charts)} charts follow: "
            + ", ".join(f"({i}) {c}" for i, c in enumerate(charts, 1)) + ".", "")

    if plot:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            return
        raw_c, deb_c = "#ff7a59", "#5b6cff"
        fig = plt.figure(figsize=(10, 7))

        ax = fig.add_subplot(2, 2, 1)
        ax.bar(range(qubits), rep["per_qubit_p1"], color=raw_c)
        ax.axhline(0.5, color="k", ls="--", lw=1)
        ax.set(title="Is each qubit a fair coin? (fair = 0.5)", xlabel="qubit",
               ylabel="share of 1s", ylim=(0, 1))

        ax = fig.add_subplot(2, 2, 2)
        width = 0.4
        for i, (name, d) in enumerate(dice.items()):
            pct = [100 * d.count(f) / len(d) for f in range(1, 7)]
            ax.bar([f - width / 2 + i * width for f in range(1, 7)], pct, width,
                   color=(raw_c, deb_c)[i], label=f"{name} ({len(d)} dice)")
        ax.axhline(100 / 6, color="k", ls="--", lw=1)
        ax.set(title="Are the dice fair? (dashed: fair die, 16.7%)", xlabel="face",
               ylabel="% of rolls", ylim=(0, 30))
        ax.legend(fontsize=8, loc="upper center", ncol=2)

        ax = fig.add_subplot(2, 1, 2)
        n = len(walks["raw bits"])
        band = [2 * math.sqrt(t) for t in range(n)]
        ax.fill_between(range(n), [-b for b in band], band, color="0.9",
                        label="95% of fair walks stay here")
        for i, (name, walk) in enumerate(walks.items()):
            ax.plot(walk, color=(raw_c, deb_c)[i], lw=1.2,
                    label=name if i == 0 else f"{name} ({debias})")
        ax.axhline(0, color="k", lw=0.8)
        ax.set(title="Random walk: 1 = step up, 0 = step down. Fair coins stay in the grey band",
               xlabel="step", ylabel="position")
        ax.legend(fontsize=8, loc="upper left")

        fig.tight_layout()
        plt.show()
        plot_randomness_report(plt, raw_bits, deb_bits, raw, deb, f"{cleaned} ({debias})", raw_c, deb_c)
        if chsh:
            plot_bell(plt, chsh)
        if unflipped:
            plot_unflip(plt, unflipped, 1 - raw["ones_fraction"])


def plot_randomness_report(plt, raw_bits, deb_bits, raw, deb, cleaned, raw_c, deb_c):
    """Second chart: what the bits look like, test p-values and patterns between bits."""
    fig = plt.figure(figsize=(10, 7))
    fig.suptitle("How random are the bits? Random bits look like TV static.\n"
                 "Unpredictability (100% = perfect coin): "
                 f"raw {unpredictability(raw):.0%}, {cleaned} {unpredictability(deb):.0%}",
                 fontsize=11)

    for i, (name, bits) in enumerate((("raw bits", raw_bits), (cleaned, deb_bits))):
        width = 64
        rows = [[int(b) for b in bits[r * width:(r + 1) * width]] for r in range(len(bits) // width)]
        ax = fig.add_subplot(2, 2, i + 1)
        ax.imshow(rows, cmap="gray_r", interpolation="nearest", aspect="auto")
        ax.set(title=f"{name}: every bit a pixel, black = 1", xticks=[], yticks=[])

    ax = fig.add_subplot(2, 2, 3)
    labels = [label for _, label, _ in HEALTH_TESTS]
    width = 0.4
    for i, (name, r, color) in enumerate((("raw", raw, raw_c), (cleaned, deb, deb_c))):
        ps = [0 if math.isnan(r[key]) else r[key] for key, *_ in HEALTH_TESTS]
        ax.bar([x - width / 2 + i * width for x in range(len(labels))], ps, width, color=color,
               label=name)
    ax.axhline(0.01, color="red", lw=1, ls="--", label="pass line (0.01)")
    ax.set_xticks(range(len(labels)), [lbl.replace(" ", "\n", 1) for lbl in labels], fontsize=7)
    ax.set(title="NIST tests: a bar above the red line passes", ylabel="p-value", ylim=(0, 1.3),
           yticks=[0, 0.2, 0.4, 0.6, 0.8, 1])
    ax.legend(fontsize=7, loc="upper center", ncol=3)

    ax = fig.add_subplot(2, 2, 4)
    for name, bits, r, color in (("raw", raw_bits, raw, raw_c), (cleaned, deb_bits, deb, deb_c)):
        corr = stats.autocorrelation(bits)
        lags = range(1, len(corr) + 1)
        ax.plot(lags, corr, "o-", color=color, ms=3, label=name)
        limit = stats.autocorr_limit(r["bits"])
        ax.axhline(limit, color=color, lw=0.8, ls="--")
        ax.axhline(-limit, color=color, lw=0.8, ls="--")
    ax.axhline(0, color="k", lw=0.8)
    ax.set(title="Hidden patterns? Fair bits stay between the dashed lines",
           xlabel="compared with the bit this many places later",
           ylabel="correlation")
    ax.legend(fontsize=7, loc="upper right", title="dashed: fair range", title_fontsize=7)

    fig.tight_layout()
    plt.show()


def plot_bell(plt, chsh):
    """Third chart: the four correlations and S against the classical limit."""
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    keys = list(chsh["correlations"])
    labels = [f"A{a} B{b}" for a, b in keys]
    ax[0].bar(range(4), [chsh["correlations"][k] for k in keys], color="#5b6cff",
              label="measured")
    ax[0].scatter(range(4), [bell_module.expected_correlation(*k) for k in keys], color="k",
                  marker="_", s=600, zorder=3, label="quantum prediction")
    ax[0].axhline(0, color="k", lw=0.8)
    ax[0].set_xticks(range(4), labels)
    ax[0].set(title="Agreement of the entangled pair\nfor each pair of directions", ylim=(-1, 1),
              ylabel="P(same) - P(different)")
    ax[0].legend(fontsize=8, loc="lower left")

    s_value, sigma = chsh["S"], chsh["sigma"]
    ax[1].axvspan(0, chsh["classical_limit"], color="red", alpha=0.08,
                  label="possible without quantum physics")
    ax[1].barh([0], [s_value], xerr=[sigma], color="#5b6cff", height=0.4, capsize=6,
               label="measured S")
    ax[1].axvline(chsh["classical_limit"], color="red", ls="--",
                  label=f"classical limit ({chsh['classical_limit']:.0f})")
    ax[1].axvline(chsh["quantum_prediction"], color="k", ls=":",
                  label=f"quantum prediction ({chsh['quantum_prediction']:.2f})")
    ax[1].set(title=f"Bell test score S = {s_value:.2f} ± {sigma:.2f}\nabove 2 = quantum", xlim=(min(0, s_value - 0.5), 3.2),
              ylim=(-0.5, 1.1), yticks=[])
    ax[1].legend(fontsize=7, loc="upper left", ncol=2)
    fig.tight_layout()
    plt.show()


def plot_unflip(plt, u, single_p0):
    """Fourth chart: share of 0s after one H vs after H then H."""
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.bar([0, 1], [single_p0, u["p0"]], color=["#ff7a59", "#5b6cff"], width=0.55)
    ax.axhline(0.5, color="k", ls="--", lw=1, label="a coin flipped twice: 50%")
    for x, p in enumerate((single_p0, u["p0"])):
        ax.text(x, p + 0.02, f"{p:.1%}", ha="center")
    ax.set_xticks([0, 1], ["one H\n(a quantum coin)", "H then H\n(un-flipped)"])
    ax.set(title="Un-flipping a quantum coin: interference", ylabel="share of 0s", ylim=(0, 1.15))
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    plt.show()


# Qollab calls main() itself after the script finishes, so only call it when run locally.
if RUNNING_LOCALLY:
    main()
