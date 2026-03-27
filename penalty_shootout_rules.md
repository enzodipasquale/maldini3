# Penalty Shootout Game Rule

Let N denote the finite set of active players. Server time evolves in discrete turns $(t = 1, 2, …)$. During each turn the platform inspects every unordered pair $(i, j)$ with $i ≠ j$. For the pair $(i, j)$ we read the event as “player i shoots on player j”; note that the reverse pairing $(j, i)$ is also evaluated in the same turn, hence every player $i$ shoots $N-1$ penalties and keeps $N-1$ penalties in each turn.

## State space

The state at turn $t$ is the set $H(t) = \{h_1, …, h_t\}$. Each $h_r$ contains one entry per player identifier, and each player entry is a mapping of opponents to mini-records:

```
player_id → {
    opponent_id → {
        "shoot": direction ($0$, $1$, or $2$),
        "keep": opponent's defence direction ($0$, $1$, or $2$),
        "outcome": True if the shot scored, False otherwise
    }
}
```

Until a duel resolves, the `outcome` field is omitted (or `null`). The `keep` field always reports the keeper’s choice (the opponent listed in the key).

## Action space

At the start of turn t each player i submits an action consisting of two maps:

- shoot map: opponents → ${0, 1, 2}$
- keep map: opponents → ${0, 1, 2}$

The labels $0, 1, 2$ correspond respectively to left, centre, and right.

## Penalty mechanism

For each ordered pair $(i, j)$ with $i \neq j$, there exists a 3 × 3 success-probability matrix $P^{ij}$ whose rows index shooting directions and columns index keeping directions. Matrices are drawn independently for every ordered pair, so in general $P^{ij} \neq P^{ji}$. Each matrix satisfies the dominance property $P^{ij}[d, d] < P^{ij}[u, v]$ for every direction $d$ and any pair $(u, v)$ with $u \neq v$. Intuitively, a shot aimed away from the keeper’s chosen direction strictly improves the conversion probability relative to a shot that matches it. Players do not observe the matrices.

During round $t$ a duel between shooter $i$ and keeper $j$ is determined by their chosen directions. Let $d$ be the shooter’s direction against $j$ and $u$ the keeper’s defence against $i$. The shot succeeds with probability $P^{ij}[d, u]$; success yields a goal for $i$, otherwise $i$ is denied and $j$ records a save. If a goal happens the shooter gets reward $1$ and the keeper $0$, otherwise the shooter gets $0$ and the keeper $1.$