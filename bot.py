#!/usr/bin/env python3
import os
import requests


def load_strategy():
    try:
        from strategy import strategy as private_strategy
        return private_strategy
    except ModuleNotFoundError as exc:
        raise RuntimeError("strategy.py is missing. Decrypt before running bot.py.") from exc


def submit_once():
    server_url = os.getenv("SERVER_URL")
    github_token = os.getenv("GAME_TOKEN")
    player_name = os.getenv("PLAYER_NAME")

    if not server_url:
        raise SystemExit("SERVER_URL env var required")
    if not player_name:
        raise SystemExit("PLAYER_NAME env var required")
    if not github_token:
        raise SystemExit("GAME_TOKEN env var required")

    strategy_func = load_strategy()
    headers = {"Authorization": f"Bearer {github_token}"}

    status = requests.get(f"{server_url}/status", headers=headers, params={"player_name": player_name}, timeout=10)
    if not status.ok:
        raise SystemExit(f"Failed to get status: {status.status_code} {status.text or status.reason}")

    action = strategy_func(status.json())

    response = requests.post(
        f"{server_url}/action",
        headers={**headers, "Content-Type": "application/json"},
        json={"action": action, "player_name": player_name},
        timeout=10,
    )
    if not response.ok:
        raise SystemExit(f"Submission failed: {response.status_code} {response.text or response.reason}")


if __name__ == "__main__":
    submit_once()

