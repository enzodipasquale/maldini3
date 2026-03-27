#!/usr/bin/env python3
import os
import requests


def main():
    server_url = os.getenv("SERVER_URL", "").strip()
    github_token = os.getenv("GAME_TOKEN", "").strip()
    player_name = os.getenv("PLAYER_NAME", "").strip()
    github_repo = os.getenv("GITHUB_REPOSITORY", os.getenv("GITHUB_REPO", "")).strip()

    print(f"[register] Config state: SERVER_URL={'set' if server_url else 'missing'}, "
          f"GAME_TOKEN={'set' if github_token else 'missing'}, "
          f"PLAYER_NAME={'set' if player_name else 'missing'}, "
          f"GITHUB_REPO={'set' if github_repo else 'missing'}", flush=True)

    for name, val in [("SERVER_URL", server_url), ("GAME_TOKEN", github_token),
                       ("PLAYER_NAME", player_name), ("GITHUB_REPO", github_repo)]:
        if not val:
            raise SystemExit(f"{name} environment variable not set")

    server_url = server_url.rstrip("/")
    print(f"[register] Using endpoint {server_url}/register", flush=True)

    response = requests.post(
        f"{server_url}/register",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {github_token}"},
        json={"player_name": player_name, "github_repo": github_repo},
        timeout=10,
    )
    if not response.ok:
        raise SystemExit(f"Registration failed: {response.status_code} {response.text}")

    payload = response.json()
    status = (payload.get("status") or "").lower()
    if status == "registered":
        print(f"Player '{payload.get('player_name')}' registered with id {payload.get('player_id')}.")
    elif status == "already_registered":
        print(f"Player '{payload.get('player_name')}' already registered. Id {payload.get('player_id')}.")
    else:
        print(f"Registration response: {payload}")


if __name__ == "__main__":
    main()

