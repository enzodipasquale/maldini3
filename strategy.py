#!/usr/bin/env python3
# Bayesian Nash Equilibrium strategy for penalty shootout.
# Maintains Beta sufficient statistics in a local JSON file so we only
# process new turns each round.
import json
import os
import numpy as np
from scipy.optimize import linprog

STATS_FILE = os.path.join(os.path.dirname(__file__), "stats.json")
N = 3  # directions: 0=left, 1=center, 2=right

# ── Priors ──────────────────────────────────────────────────────────
# diagonal (keeper matches shooter): low scoring  -> Beta(1, 3), mean ~ 0.25
# off-diagonal (keeper misses):      high scoring -> Beta(3, 1), mean ~ 0.75
PRIOR_DIAG = (1.0, 3.0)
PRIOR_OFF  = (3.0, 1.0)


def _init_betas():
    """3x3 array of (a, b) pairs with structural priors."""
    return [
        [list(PRIOR_DIAG) if i == j else list(PRIOR_OFF) for j in range(N)]
        for i in range(N)
    ]


def _load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE) as f:
            return json.load(f)
    return {}


def _save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)


def _posterior_means(betas):
    """Return 3x3 matrix of posterior means from Beta parameters."""
    return [[a / (a + b) for a, b in row] for row in betas]


def _solve_zero_sum(M, role="shooter"):
    """
    Solve a 3x3 zero-sum game via LP.
    M[i][j] = P(goal | shoot=i, keep=j).
    role="shooter": maximize value  -> returns shooter mixed strategy.
    role="keeper":  minimize value   -> returns keeper mixed strategy.
    """
    M = np.array(M, dtype=float)

    if role == "shooter":
        # max v s.t. sum_i p_i * M[i][j] >= v for all j, sum p = 1, p >= 0
        c = [0, 0, 0, -1]
        A_ub = []
        b_ub = []
        for j in range(N):
            row = [-M[i][j] for i in range(N)] + [1]
            A_ub.append(row)
            b_ub.append(0)
        A_eq = [[1, 1, 1, 0]]
        b_eq = [1]
        bounds = [(0, None)] * N + [(None, None)]
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                      bounds=bounds, method="highs")
        return res.x[:N] if res.success else np.ones(N) / N
    else:
        # min v s.t. sum_j q_j * M[i][j] <= v for all i, sum q = 1, q >= 0
        c = [0, 0, 0, 1]
        A_ub = []
        b_ub = []
        for i in range(N):
            row = [-M[i][j] for j in range(N)] + [-1]
            A_ub.append(row)
            b_ub.append(0)
        A_eq = [[1, 1, 1, 0]]
        b_eq = [1]
        bounds = [(0, None)] * N + [(None, None)]
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                      bounds=bounds, method="highs")
        return res.x[:N] if res.success else np.ones(N) / N


def strategy(state):
    opponents = state.get("opponentsIds") or []
    if not opponents:
        return {"shoot": {}, "keep": {}}

    my_id = state.get("myPlayerId", "")
    history = state.get("state") or []

    # ── Load / initialise sufficient statistics ─────────────────────
    stats = _load_stats()
    last_turn = stats.get("last_turn", 0)

    for opp in opponents:
        if opp not in stats:
            stats[opp] = {
                "shoot_betas": _init_betas(),  # matrix when I shoot, opp keeps
                "keep_betas":  _init_betas(),  # matrix when opp shoots, I keep
            }

    # ── Update from new turns ───────────────────────────────────────
    for turn in history:
        turn_id = turn.get("_turnId", 0)
        if turn_id <= last_turn:
            continue

        my_data = turn.get(my_id, {})
        for opp in opponents:
            if opp not in stats:
                stats[opp] = {
                    "shoot_betas": _init_betas(),
                    "keep_betas":  _init_betas(),
                }

            # When I was shooter, opp was keeper
            # turn[me][opp] = {shoot: my_dir, keep: opp_keep_dir, outcome: goal?}
            my_vs_opp = my_data.get(opp, {})
            s = my_vs_opp.get("shoot")
            k = my_vs_opp.get("keep")
            outcome = my_vs_opp.get("outcome")
            if s is not None and k is not None and outcome is not None:
                si, ki = int(s), int(k)
                if outcome:
                    stats[opp]["shoot_betas"][si][ki][0] += 1  # a += 1
                else:
                    stats[opp]["shoot_betas"][si][ki][1] += 1  # b += 1

            # When opp was shooter, I was keeper
            # turn[opp][me] = {shoot: opp_dir, keep: my_keep_dir, outcome: goal?}
            opp_data = turn.get(opp, {})
            opp_vs_me = opp_data.get(my_id, {})
            s2 = opp_vs_me.get("shoot")
            k2 = opp_vs_me.get("keep")
            outcome2 = opp_vs_me.get("outcome")
            if s2 is not None and k2 is not None and outcome2 is not None:
                si2, ki2 = int(s2), int(k2)
                if outcome2:
                    stats[opp]["keep_betas"][si2][ki2][0] += 1
                else:
                    stats[opp]["keep_betas"][si2][ki2][1] += 1

        last_turn = max(last_turn, turn_id)

    stats["last_turn"] = last_turn
    _save_stats(stats)

    # ── Compute NE and sample actions ───────────────────────────────
    shoot_actions = {}
    keep_actions = {}

    for opp in opponents:
        opp_stats = stats.get(opp, {
            "shoot_betas": _init_betas(),
            "keep_betas":  _init_betas(),
        })

        # Shooting: I'm the row player maximising P(goal)
        shoot_matrix = _posterior_means(opp_stats["shoot_betas"])
        shoot_mix = _solve_zero_sum(shoot_matrix, role="shooter")
        shoot_mix = np.maximum(shoot_mix, 0)
        shoot_mix /= shoot_mix.sum()
        shoot_actions[opp] = int(np.random.choice(N, p=shoot_mix))

        # Keeping: opp is the row player, I'm the column player minimising
        keep_matrix = _posterior_means(opp_stats["keep_betas"])
        keep_mix = _solve_zero_sum(keep_matrix, role="keeper")
        keep_mix = np.maximum(keep_mix, 0)
        keep_mix /= keep_mix.sum()
        keep_actions[opp] = int(np.random.choice(N, p=keep_mix))

    return {"shoot": shoot_actions, "keep": keep_actions}
