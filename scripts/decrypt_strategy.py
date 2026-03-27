#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
from cryptography.fernet import Fernet


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--encrypted", default="strategy.py.encrypted", type=Path)
    parser.add_argument("--output", default="strategy.py", type=Path)
    parser.add_argument("--key")
    args = parser.parse_args()

    key = args.key or os.getenv("ENCRYPTION_KEY")
    if not key:
        raise SystemExit("Encryption key required. Set ENCRYPTION_KEY or pass --key.")

    if not args.encrypted.exists():
        raise SystemExit(f"{args.encrypted} not found.")

    decrypted = Fernet(key.encode("ascii")).decrypt(args.encrypted.read_bytes())
    args.output.write_bytes(decrypted)
    print(f"Decrypted {args.encrypted} -> {args.output}", flush=True)


if __name__ == "__main__":
    main()

