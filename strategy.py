#!/usr/bin/env python3
# Edit this file with your strategy, then encrypt with: python scripts/setup_encryption.py
import numpy as np


def strategy(state):
    opponents = state.get("opponentsIds") or []
    if not opponents:
        return {"shoot": {}, "keep": {}}

    # Random baseline — replace with your logic
    shoot = np.random.randint(0, 3, len(opponents)).tolist()
    keep = np.random.randint(0, 3, len(opponents)).tolist()

    return {
        "shoot": {pid: d for pid, d in zip(opponents, shoot)},
        "keep": {pid: d for pid, d in zip(opponents, keep)},
    }

