"""Recipe 110 — Nash Equilibrium Game Theory.

Uses nashpy to find Nash equilibria in 2-player normal-form games.
Demonstrates that the rational equilibrium (Nash) often differs from
the cooperative optimum — Prisoner's Dilemma structure in pricing games.

Install: pip install nashpy
"""

import json


_DEFAULT_PRICING_GAME = {
    "game_name": "SaaS Pricing Duopoly",
    "description": (
        "Two SaaS firms A and B simultaneously choose a monthly subscription price: "
        "High ($100/mo) or Low ($70/mo). "
        "If both choose High: each earns $40K/mo profit (40% market share × $100 margin). "
        "If both choose Low: each earns $25K/mo profit (50% share × $50 margin). "
        "If A chooses High and B chooses Low: A earns $10K (loses share) and B earns $55K. "
        "If A chooses Low and B chooses High: A earns $55K and B earns $10K."
    ),
    "players": ["Firm A", "Firm B"],
    "strategies": {
        "Firm A": ["High", "Low"],
        "Firm B": ["High", "Low"],
    },
    "payoff_matrix_A": [[40, 10], [55, 25]],
    "payoff_matrix_B": [[40, 55], [10, 25]],
    "joint_optimal": {"strategies": ["High", "High"], "payoffs": [40, 40]},
    "known_nash": {"strategies": ["Low", "Low"], "payoffs": [25, 25]},
    "known_nash_type": "Dominant strategy equilibrium (Prisoner's Dilemma)",
}


def get_default_game() -> str:
    """Return default pricing duopoly game JSON."""
    return json.dumps(_DEFAULT_PRICING_GAME)


def find_nash_equilibria(game_json: str) -> str:
    """Find all Nash equilibria using nashpy support enumeration.

    Returns:
      {"game_name": str, "n_equilibria": int, "equilibria": [{sigma_A, sigma_B, payoffs}],
       "joint_optimal": {...}, "gap": str, "status": "OK"|"ERROR"}
    """
    try:
        import nashpy as nash  # type: ignore[import-untyped]
        import numpy as np
    except ImportError:
        return json.dumps({"status": "ERROR",
                           "error": "nashpy not installed — run: pip install nashpy"})

    try:
        game = json.loads(game_json)
        A = np.array(game["payoff_matrix_A"], dtype=float)
        B = np.array(game["payoff_matrix_B"], dtype=float)

        g = nash.Game(A, B)
        equilibria = []
        for eq in g.support_enumeration():
            sigma_A, sigma_B = eq
            payoff_A = float(sigma_A @ A @ sigma_B)
            payoff_B = float(sigma_A @ B @ sigma_B)

            strats_A = game["strategies"]["Firm A"]
            strats_B = game["strategies"]["Firm B"]

            # Interpret the mixed strategy as a pure or mixed label
            def label_strategy(sigma, strats):
                for i, p in enumerate(sigma):
                    if abs(p - 1.0) < 1e-6:
                        return strats[i]
                parts = [f"{p:.2f}×{s}" for p, s in zip(sigma, strats) if p > 1e-6]
                return " + ".join(parts)

            equilibria.append({
                "sigma_A": sigma_A.tolist(),
                "sigma_B": sigma_B.tolist(),
                "label_A": label_strategy(sigma_A, strats_A),
                "label_B": label_strategy(sigma_B, strats_B),
                "payoff_A": round(payoff_A, 2),
                "payoff_B": round(payoff_B, 2),
            })

        opt = game.get("joint_optimal", {})
        opt_payoffs = opt.get("payoffs", [0, 0])

        # Compute Prisoner's Dilemma gap
        gap_lines = []
        for eq in equilibria:
            gap_A = round(opt_payoffs[0] - eq["payoff_A"], 2)
            gap_B = round(opt_payoffs[1] - eq["payoff_B"], 2)
            gap_lines.append(
                f"Nash ({eq['label_A']}, {eq['label_B']}): "
                f"Firm A earns ${eq['payoff_A']}K vs optimal ${opt_payoffs[0]}K "
                f"(gap=${gap_A}K); "
                f"Firm B earns ${eq['payoff_B']}K vs optimal ${opt_payoffs[1]}K "
                f"(gap=${gap_B}K)"
            )

        return json.dumps({
            "game_name":     game.get("game_name", "Game"),
            "n_equilibria":  len(equilibria),
            "equilibria":    equilibria,
            "joint_optimal": opt,
            "pd_gap":        " | ".join(gap_lines),
            "status":        "OK",
        })

    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def nash_found(result_json: str) -> bool:
    """ASSERT gate: at least one Nash equilibrium was found."""
    try:
        data = json.loads(result_json)
        return data.get("status") == "OK" and data.get("n_equilibria", 0) > 0
    except Exception:
        return False


def format_nash_report(result_json: str) -> str:
    """Markdown report of Nash equilibrium results."""
    try:
        data  = json.loads(result_json)
        eqs   = data.get("equilibria", [])
        opt   = data.get("joint_optimal", {})
        lines = [
            f"## Nash Equilibrium Report — {data.get('game_name', 'Game')}",
            "",
            f"**Nash equilibria found:** {data.get('n_equilibria', 0)}",
            "",
            "### Equilibria",
            "",
            "| # | Firm A plays | Firm B plays | Payoff A | Payoff B |",
            "|---|---|---|---|---|",
        ]
        for i, eq in enumerate(eqs, 1):
            lines.append(
                f"| {i} | {eq['label_A']} | {eq['label_B']} "
                f"| ${eq['payoff_A']}K | ${eq['payoff_B']}K |"
            )
        if opt:
            lines += [
                "",
                "### Joint Optimum (cooperative — NOT a Nash equilibrium)",
                "",
                f"| Firm A plays | Firm B plays | Payoff A | Payoff B |",
                "|---|---|---|---|",
                f"| {opt['strategies'][0]} | {opt['strategies'][1]} "
                f"| ${opt['payoffs'][0]}K | ${opt['payoffs'][1]}K |",
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
