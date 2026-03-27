#!/usr/bin/env python3
import argparse
from pathlib import Path
from cryptography.fernet import Fernet


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="strategy.py", type=Path)
    parser.add_argument("--output", default="strategy.py.encrypted", type=Path)
    parser.add_argument("--key", help="Reuse an existing key instead of generating a new one.")
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"{args.source} not found.")

    key = args.key or Fernet.generate_key().decode("ascii")
    encrypted = Fernet(key.encode("ascii")).encrypt(args.source.read_bytes())
    args.output.write_bytes(encrypted)

    print(f"Encrypted {args.source} -> {args.output}")
    print(f"\nAdd to GitHub Secrets as ENCRYPTION_KEY:\n  {key}")
    print(f"\nCommit only {args.output} — do NOT commit {args.source}")


if __name__ == "__main__":
    main()
