"""Recipe 115 — Gambit 3-Player Game Theory.

Uses pygambit to find Nash equilibria in 3-player normal-form games.
Extends r110 (nashpy, 2-player) to 3-player competition — a qualitatively
different problem: each firm's optimal strategy now depends on what *two*
rivals do simultaneously.

Default game: 3-firm SaaS pricing (Bertrand triopoly).
  Premium ($200/mo) vs Standard ($120/mo).
  Nash: (Standard, Standard, Standard) — race to bottom.
  Cooperative: (Premium, Premium, Premium) — $80K/firm more, but unstable.

Install: pip install pygambit
"""

import json


_DEFAULT_3P_GAME = {
    "game_name": "3-Firm SaaS Pricing Triopoly",
    "description": (
        "Three SaaS firms (A, B, C) simultaneously choose a subscription tier: "
        "Premium ($200/mo) or Standard ($120/mo). "
        "Premium commands a higher margin but loses customers to any Standard rival. "
        "Standard captures share but compresses margins. "
        "Payoffs ($K/month per firm):\n"
        "  (P,P,P): each earns 200  — mutual premium pricing\n"
        "  (S,P,P): S-firm earns 300, each P-firm earns 120  — solo defector wins big\n"
        "  (S,S,P): each S-firm earns 260, P-firm earns 80   — solo holdout punished\n"
        "  (S,S,S): each earns 120  — race-to-bottom Nash equilibrium\n"
        "Standard dominates Premium for every firm regardless of rivals' choices."
    ),
    "players": ["Firm A", "Firm B", "Firm C"],
    "strategies": ["Premium", "Standard"],
    "payoffs": {
        "PPP": [200, 200, 200],
        "PPS": [120, 120, 300],
        "PSP": [120, 300, 120],
        "PSS": [ 80, 260, 260],
        "SPP": [300, 120, 120],
        "SPS": [260, 80,  260],
        "SSP": [260, 260,  80],
        "SSS": [120, 120, 120],
    },
    "cooperative_optimum": {
        "profile": ["Premium", "Premium", "Premium"],
        "payoffs": [200, 200, 200],
    },
    "nash_prediction": {
        "profile": ["Standard", "Standard", "Standard"],
        "payoffs": [120, 120, 120],
        "type": "Dominant strategy equilibrium (3-player Prisoner's Dilemma)",
    },
}


def get_default_game() -> str:
    return json.dumps(_DEFAULT_3P_GAME)


def find_nash_equilibria_3p(game_json: str) -> str:
    """Find pure Nash equilibria in a 3-player game using pygambit.

    Falls back to brute-force pure-strategy search if pygambit is unavailable,
    so the recipe always runs — it just logs which path was taken.

    Returns:
      {"game_name", "equilibria": [{profile, payoffs, type}],
       "cooperative", "pd_gap", "solver_used", "status"}
    """
    try:
        game = json.loads(game_json)
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": f"JSON parse: {e}"})

    payoffs = game["payoffs"]          # dict "PPP"->list[3]
    strategies = game["strategies"]    # ["Premium", "Standard"]
    players = game["players"]
    def profile_key(a, b, c):
        return ("P" if a == 0 else "S") + ("P" if b == 0 else "S") + ("P" if c == 0 else "S")

    def payoff(player_idx, a, b, c):
        return payoffs[profile_key(a, b, c)][player_idx]

    solver_used = "pygambit"
    equilibria = []

    try:
        import pygambit as gbt
        import numpy as np

        n = 2  # strategies per player
        # Build payoff arrays indexed [strat_A, strat_B, strat_C]
        A = np.array([[[payoff(0, a, b, c) for c in range(n)]
                        for b in range(n)] for a in range(n)], dtype=float)
        B = np.array([[[payoff(1, a, b, c) for c in range(n)]
                        for b in range(n)] for a in range(n)], dtype=float)
        C = np.array([[[payoff(2, a, b, c) for c in range(n)]
                        for b in range(n)] for a in range(n)], dtype=float)

        g = gbt.Game.from_arrays(A, B, C)
        for i, player in enumerate(g.players):
            player.label = players[i]
        for j, strat in enumerate(strategies):
            for player in g.players:
                player.strategies[j].label = strat

        solver = gbt.nash.ExternalEnumPureSolver()
        for eq in solver.solve(g):
            profile = []
            eq_payoffs = []
            for player in g.players:
                probs = [float(eq[player][s]) for s in player.strategies]
                chosen = strategies[probs.index(max(probs))]
                profile.append(chosen)
                eq_payoffs.append(round(float(eq.payoff(player)), 2))
            equilibria.append({"profile": profile, "payoffs": eq_payoffs,
                                "type": "pure"})

    except ImportError:
        solver_used = "brute-force (pygambit not installed)"
        # Pure-strategy brute-force: check all 2³=8 profiles
        for a in range(2):
            for b in range(2):
                for c in range(2):
                    # Check if (a,b,c) is a Nash equilibrium:
                    # no player can profitably deviate
                    pa = payoff(0, a, b, c)
                    pb = payoff(1, a, b, c)
                    pc = payoff(2, a, b, c)
                    is_nash = True
                    # Player A deviation
                    for a2 in range(2):
                        if a2 != a and payoff(0, a2, b, c) > pa:
                            is_nash = False; break
                    if not is_nash:
                        continue
                    # Player B deviation
                    for b2 in range(2):
                        if b2 != b and payoff(1, a, b2, c) > pb:
                            is_nash = False; break
                    if not is_nash:
                        continue
                    # Player C deviation
                    for c2 in range(2):
                        if c2 != c and payoff(2, a, b, c2) > pc:
                            is_nash = False; break
                    if is_nash:
                        profile = [strategies[a], strategies[b], strategies[c]]
                        eq_payoffs = [pa, pb, pc]
                        equilibria.append({"profile": profile, "payoffs": eq_payoffs,
                                           "type": "pure"})

    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e),
                           "solver_used": solver_used})

    coop = game["cooperative_optimum"]
    pd_gaps = []
    for eq in equilibria:
        gaps = [round(co - ne, 1) for co, ne in zip(coop["payoffs"], eq["payoffs"])]
        pd_gaps.append(
            f"Nash {eq['profile']} → each earns ${eq['payoffs'][0]}K; "
            f"cooperative {coop['profile']} → each earns ${coop['payoffs'][0]}K; "
            f"gap = ${gaps[0]}K/firm"
        )

    return json.dumps({
        "game_name":   game["game_name"],
        "n_players":   len(players),
        "players":     players,
        "n_equilibria": len(equilibria),
        "equilibria":  equilibria,
        "cooperative": coop,
        "pd_gap":      " | ".join(pd_gaps) if pd_gaps else "no equilibria found",
        "solver_used": solver_used,
        "status":      "OK",
    })


def nash_3p_found(result_json: str) -> bool:
    """ASSERT gate: at least one pure Nash equilibrium found."""
    try:
        data = json.loads(result_json)
        return data.get("status") == "OK" and data.get("n_equilibria", 0) > 0
    except Exception:
        return False


def format_gambit_report(result_json: str) -> str:
    """Markdown report of 3-player Nash equilibrium results."""
    try:
        data = json.loads(result_json)
        eqs = data.get("equilibria", [])
        coop = data.get("cooperative", {})
        players = data.get("players", ["A", "B", "C"])
        lines = [
            f"## 3-Player Nash Equilibrium Report — {data.get('game_name', 'Game')}",
            "",
            f"**Solver:** {data.get('solver_used', 'unknown')}  ",
            f"**Players:** {', '.join(players)}  ",
            f"**Nash equilibria found:** {data.get('n_equilibria', 0)}",
            "",
            "### Nash Equilibria",
            "",
            "| # | Firm A | Firm B | Firm C | Payoff A | Payoff B | Payoff C |",
            "|---|---|---|---|---|---|---|",
        ]
        for i, eq in enumerate(eqs, 1):
            p = eq["payoffs"]
            pf = eq["profile"]
            lines.append(
                f"| {i} | {pf[0]} | {pf[1]} | {pf[2]} "
                f"| ${p[0]}K | ${p[1]}K | ${p[2]}K |"
            )
        if coop:
            cp = coop["payoffs"]
            cf = coop["profile"]
            lines += [
                "",
                "### Cooperative Optimum (NOT a Nash equilibrium)",
                "",
                "| Firm A | Firm B | Firm C | Payoff A | Payoff B | Payoff C |",
                "|---|---|---|---|---|---|",
                f"| {cf[0]} | {cf[1]} | {cf[2]} | ${cp[0]}K | ${cp[1]}K | ${cp[2]}K |",
                "",
                "> *Collective optimum is unstable: every firm can unilaterally*",
                "> *gain by defecting to Standard, making Premium unsustainable.*",
            ]
        if data.get("pd_gap"):
            lines += ["", "### Prisoner's Dilemma Gap", "", data["pd_gap"]]
        return "\n".join(lines)
    except Exception as e:
        return f"(format error: {e})"


def json_get_field(data_json: str, field: str) -> str:
    try:
        v = json.loads(data_json).get(field)
        return str(v) if v is not None else ""
    except Exception:
        return ""
