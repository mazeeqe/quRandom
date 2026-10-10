"""Command-line interface: ``qurandom --bits 16`` or ``qurandom --int 1 6``."""

import argparse

from qurandom.generator import QuantumRandom


def main() -> None:
    parser = argparse.ArgumentParser(description="Quantum random number generator")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--bits", type=int, metavar="N", help="print N random bits")
    group.add_argument("--int", type=int, nargs=2, metavar=("LOW", "HIGH"),
                       help="print a random integer in [LOW, HIGH]")
    parser.add_argument("--classical", action="store_true",
                        help="use the OS random source instead of Qiskit")
    args = parser.parse_args()

    qr = QuantumRandom(use_quantum=False if args.classical else None)
    if args.bits is not None:
        print("".join(map(str, qr.bits(args.bits))))
    elif args.int is not None:
        print(qr.randint(*args.int))
    else:
        print(qr.random())


if __name__ == "__main__":
    main()
