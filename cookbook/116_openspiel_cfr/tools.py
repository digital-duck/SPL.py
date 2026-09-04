"""Recipe 116 — OpenSpiel CFR (Counterfactual Regret Minimization).

Uses DeepMind OpenSpiel to solve imperfect-information extensive-form
games via CFR. Demonstrates the key step beyond r110 (Nash in normal form)
and r111 (Stackelberg backward induction): here neither player knows the
other's private information, so optimal play requires a *mixed strategy*
that balances bluffing and value betting.

Default game: Kuhn Poker — the smallest non-trivial poker variant.
  2 players, 3 cards (J < Q < K), 1 chip ante, 1 chip bet.
  Each player receives one private card. Player 1 acts first (bet/pass).
  CFR converges to the Nash equilibrium mixed strategy in ~1000 iterations.
  Known Nash: Player 1 bluffs with J at frequency 1/3, bets K always;
  Player 2 calls with K always, calls with Q at frequency 1/3.

ASSERT: exploitability < 0.05 after n_iterations (measures distance from
  Nash — 0 means perfectly optimal; LLM naive strategy is ~0.25).

Install: pip install open_spiel
"""

import json


_KUHN_POKER_DESCRIPTION = {
    "game_name": "Kuhn Poker",
    "n_players": 2,
    "cards": ["Jack (J)", "Queen (Q)", "King (K)"],
    "card_ranking": "J < Q < K",
    "rules": (
        "Each player antes 1 chip and receives one private card (J, Q, or K). "
        "Player 1 acts first: Pass or Bet (1 chip). "
        "After Player 1 acts, Player 2 responds: Pass or Call/Bet. "
        "Showdown if needed — higher card wins the pot. "
        "Key tension: betting signals a strong card but also enables bluffing. "
        "Since neither player sees the other's card, optimal play requires "
        "a mixed (randomized) strategy to remain unexploitable."
    ),
    "llm_naive_strategy": (
        "Bet with K (strong), Pass with J (weak), mix with Q — "
        "this is close but not perfectly unexploitable; "
        "an opponent can exploit the pure bet-K-only strategy."
    ),
    "known_nash_summary": (
        "Player 1: Bet with K always (1.0), Bet with J at probability 1/3 (bluff), "
        "Pass with Q always. "
        "Player 2: Call with K always, Call with Q at probability 1/3, "
        "Pass with J always."
    ),
}


def get_game_description() -> str:
    return json.dumps(_KUHN_POKER_DESCRIPTION)


def solve_with_cfr(n_iterations: int = 1000) -> str:
    """Run CFR on Kuhn Poker for n_iterations and return exploitability.

    Exploitability measures how far the average policy is from Nash:
      0.0 = perfect Nash equilibrium
      ~0.25 = LLM-naive always-bet-K strategy

    Returns:
      {"game", "n_iterations", "exploitability", "converged",
       "nash_summary", "player_strategies", "status"}
    """
    try:
        import pyspiel  # type: ignore[import-untyped]
        from open_spiel.python.algorithms import cfr  # type: ignore[import-untyped]
        from open_spiel.python.algorithms import exploitability as exp_lib  # type: ignore[import-untyped]
    except ImportError:
        return json.dumps({
            "status": "ERROR",
            "error": "OpenSpiel not installed — run: pip install open_spiel",
        })

    try:
        game = pyspiel.load_game("kuhn_poker")
        cfr_solver = cfr.CFRSolver(game)

        for _ in range(n_iterations):
            cfr_solver.evaluate_and_update_policy()

        avg_policy = cfr_solver.average_policy()
        exploit = exp_lib.exploitability(game, avg_policy)
        exploit = round(float(exploit), 6)

        converged = exploit < 0.05

        # Extract readable strategy summary from average policy
        player_strategies = _extract_strategy_summary(game, avg_policy)

        return json.dumps({
            "game":              "Kuhn Poker",
            "n_iterations":      n_iterations,
            "exploitability":    exploit,
            "converged":         converged,
            "threshold":         0.05,
            "nash_summary":      _KUHN_POKER_DESCRIPTION["known_nash_summary"],
            "player_strategies": player_strategies,
            "status":            "OK",
        })

    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def _extract_strategy_summary(game, avg_policy) -> dict:
    """Walk the game tree and collect action probabilities at each info set."""
    info_set_probs = {}
    state = game.new_initial_state()

    def traverse(state):
        if state.is_terminal():
            return
        if state.is_chance_node():
            for action, _prob in state.chance_outcomes():
                traverse(state.child(action))
            return

        player = state.current_player()
        info_str = state.information_state_string(player)
        if info_str not in info_set_probs:
            policy_at_state = avg_policy.action_probabilities(state)
            action_labels = {
                0: "Pass/Check",
                1: "Bet/Call",
            }
            probs = {action_labels.get(a, str(a)): round(p, 3)
                     for a, p in policy_at_state.items()}
            info_set_probs[f"P{player+1}:{info_str}"] = probs

        for action in state.legal_actions():
            traverse(state.child(action))

    traverse(state)
    return info_set_probs


def cfr_converged(result_json: str) -> bool:
    """ASSERT gate: exploitability below threshold (close to Nash equilibrium)."""
    try:
        data = json.loads(result_json)
        return data.get("status") == "OK" and data.get("converged", False)
    except Exception:
        return False


def format_cfr_report(result_json: str) -> str:
    """Markdown report of CFR convergence and strategy."""
    try:
        data = json.loads(result_json)
        exploit = data.get("exploitability", "N/A")
        converged = data.get("converged", False)
        strategies = data.get("player_strategies", {})

        lines = [
            f"## CFR Report — {data.get('game', 'Game')}",
            "",
            f"**Iterations:** {data.get('n_iterations', 0)}  ",
            f"**Exploitability:** {exploit:.4f} (threshold: {data.get('threshold', 0.05)})  ",
            f"**Converged to Nash:** {'Yes ✓' if converged else 'No — run more iterations'}",
            "",
            "### Average Policy at Key Information Sets",
            "",
            "| Info set | Pass / Check | Bet / Call |",
            "|---|---|---|",
        ]
        for info_str, probs in sorted(strategies.items()):
            p_pass = probs.get("Pass/Check", 0.0)
            p_bet  = probs.get("Bet/Call",   0.0)
            lines.append(f"| {info_str} | {p_pass:.3f} | {p_bet:.3f} |")

        lines += [
            "",
            "### Known Nash Equilibrium (Kuhn Poker)",
            "",
            f"> {data.get('nash_summary', '')}",
            "",
            "### Exploitability Interpretation",
            "",
            "| Policy | Exploitability | Meaning |",
            "|---|---|---|",
            "| Perfect Nash | 0.000 | Unexploitable — best response cannot gain |",
            f"| CFR avg (this run) | {exploit:.3f} | {'Near-Nash ✓' if converged else 'Still converging'} |",
            "| LLM naive (bet-K-only) | ~0.250 | Exploitable — opponent folds J/Q, always calls K |",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"(format error: {e})"


def solver_enabled(use_solver: str) -> str:
    """Return 'run_solver' or 'run_llm' so the SPL EVALUATE has distinctive
    condition strings that the LLM can match unambiguously."""
    if use_solver.strip().lower() in ("true", "1", "yes", "on"):
        return "run_solver"
    return "run_llm"


def json_get_field(data_json: str, field: str) -> str:
    try:
        v = json.loads(data_json).get(field)
        return str(v) if v is not None else ""
    except Exception:
        return ""
