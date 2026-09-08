"""Recipe 111 — Stackelberg Sequential Game (Backward Induction).

Pure-Python backward induction solver for extensive-form games.
Demonstrates Stackelberg leader-follower pricing: the leader commits
to a price BEFORE the follower responds. Backward induction determines
the subgame-perfect Nash equilibrium (SPNE).

No external dependencies required.
"""

import json


# ── Backward induction solver ─────────────────────────────────────────────────

def _backward_induct(node: dict) -> dict:
    """Recursively solve a game tree node by backward induction.

    Node format:
      Terminal: {"type": "terminal", "payoff_leader": float, "payoff_follower": float, "label": str}
      Decision: {"type": "decision", "player": "leader"|"follower",
                 "choices": [{"action": str, "node": {...}}]}

    Returns the node annotated with {"best_action": str, "value_leader": float, "value_follower": float}
    """
    if node["type"] == "terminal":
        return {**node, "value_leader": node["payoff_leader"],
                "value_follower": node["payoff_follower"]}

    player   = node["player"]
    solved   = [{"action": c["action"], "node": _backward_induct(c["node"])}
                for c in node["choices"]]

    # Player maximizes their own payoff
    key = "value_leader" if player == "leader" else "value_follower"
    best = max(solved, key=lambda c: c["node"][key])

    return {
        **node,
        "choices":        solved,
        "best_action":    best["action"],
        "value_leader":   best["node"]["value_leader"],
        "value_follower": best["node"]["value_follower"],
    }


def _extract_path(solved_node: dict, path: list | None = None) -> list:
    """Extract the equilibrium action path from a solved game tree."""
    if path is None:
        path = []
    if solved_node["type"] == "terminal":
        return path + [{"label": solved_node.get("label", "end"),
                        "payoff_leader": solved_node["payoff_leader"],
                        "payoff_follower": solved_node["payoff_follower"]}]
    best_action = solved_node.get("best_action")
    for c in solved_node.get("choices", []):
        if c["action"] == best_action:
            return _extract_path(c["node"], path + [{"player": solved_node["player"],
                                                       "action": best_action}])
    return path


# ── Default Stackelberg pricing game ─────────────────────────────────────────

_DEFAULT_GAME = {
    "game_name":   "Stackelberg Pricing Duopoly",
    "description": (
        "A market leader (Firm A) sets price FIRST. "
        "The follower (Firm B) observes A's price and responds. "
        "Both can choose High ($100/mo) or Low ($70/mo). "
        "If both High: Leader=$38K, Follower=$38K (share split, slight leader premium). "
        "If Leader High, Follower Low: Leader=$12K (loses share), Follower=$52K. "
        "If Leader Low, Follower High: Leader=$50K (follower loses share), Follower=$14K. "
        "If both Low: Leader=$28K, Follower=$22K (leader has slight scale advantage). "
        "LLM says leader should price High to signal quality. "
        "Backward induction: follower always undercutting makes Low the leader's SPNE choice."
    ),
    "game_tree": {
        "type": "decision",
        "player": "leader",
        "choices": [
            {
                "action": "High ($100)",
                "node": {
                    "type": "decision",
                    "player": "follower",
                    "choices": [
                        {
                            "action": "High ($100)",
                            "node": {"type": "terminal",
                                     "payoff_leader": 38, "payoff_follower": 38,
                                     "label": "(High, High) -> Leader=$38K, Follower=$38K"},
                        },
                        {
                            "action": "Low ($70)",
                            "node": {"type": "terminal",
                                     "payoff_leader": 12, "payoff_follower": 52,
                                     "label": "(High, Low) -> Leader=$12K, Follower=$52K"},
                        },
                    ],
                },
            },
            {
                "action": "Low ($70)",
                "node": {
                    "type": "decision",
                    "player": "follower",
                    "choices": [
                        {
                            "action": "High ($100)",
                            "node": {"type": "terminal",
                                     "payoff_leader": 50, "payoff_follower": 14,
                                     "label": "(Low, High) -> Leader=$50K, Follower=$14K"},
                        },
                        {
                            "action": "Low ($70)",
                            "node": {"type": "terminal",
                                     "payoff_leader": 28, "payoff_follower": 22,
                                     "label": "(Low, Low) -> Leader=$28K, Follower=$22K"},
                        },
                    ],
                },
            },
        ],
    },
    "llm_prediction":  "Leader should price High ($100) to signal quality",
    "spne_prediction":  "Leader: Low ($70); Follower: Low ($70) if leader played Low, Low ($70) if leader played High",
}


def get_default_game() -> str:
    return json.dumps(_DEFAULT_GAME)


def solve_stackelberg(game_json: str) -> str:
    """Solve the extensive-form game by backward induction.

    Returns:
      {"game_name": str, "spne_path": [{player, action}], "spne_payoffs": {leader, follower},
       "llm_prediction": str, "spne_vs_llm": str, "status": "OK"}
    """
    try:
        game   = json.loads(game_json)
        solved = _backward_induct(game["game_tree"])
        path   = _extract_path(solved)

        terminal = next((p for p in path if "payoff_leader" in p), {})
        actions  = [p for p in path if "player" in p]

        spne_payoffs = {
            "leader":   terminal.get("payoff_leader", 0),
            "follower": terminal.get("payoff_follower", 0),
        }

        return json.dumps({
            "game_name":    game.get("game_name", "Game"),
            "spne_path":    actions,
            "spne_outcome": terminal.get("label", ""),
            "spne_payoffs": spne_payoffs,
            "llm_prediction": game.get("llm_prediction", ""),
            "spne_vs_llm":  (
                f"SPNE: Leader plays '{actions[0]['action'] if actions else '?'}' "
                f"(earns ${spne_payoffs['leader']}K) vs LLM: '{game.get('llm_prediction', '')}'"
            ),
            "status": "OK",
        })

    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e)})


def spne_solved(result_json: str) -> bool:
    """ASSERT gate: backward induction completed successfully."""
    try:
        return json.loads(result_json).get("status") == "OK"
    except Exception:
        return False


def format_stackelberg_report(result_json: str) -> str:
    """Markdown report of the Stackelberg SPNE."""
    try:
        data    = json.loads(result_json)
        actions = data.get("spne_path", [])
        payoffs = data.get("spne_payoffs", {})
        lines   = [
            f"## Stackelberg Game Report — {data.get('game_name', 'Game')}",
            "",
            "### Subgame-Perfect Nash Equilibrium (backward induction)",
            "",
            "| Step | Player | Action |",
            "|---|---|---|",
        ]
        for i, a in enumerate(actions, 1):
            lines.append(f"| {i} | {a['player'].title()} | {a['action']} |")

        lines += [
            "",
            f"**Outcome:** {data.get('spne_outcome', '—')}",
            f"**Leader payoff (SPNE):** ${payoffs.get('leader', '?')}K/mo",
            f"**Follower payoff (SPNE):** ${payoffs.get('follower', '?')}K/mo",
            "",
            "### LLM Prediction vs SPNE",
            "",
            f"- **LLM:** {data.get('llm_prediction', '—')}",
            f"- **SPNE:** {data.get('spne_vs_llm', '—')}",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"(format error: {e})"


def json_get_field(data_json: str, field: str) -> str:
    try:
        v = json.loads(data_json).get(field)
        return str(v) if v is not None else ""
    except Exception:
        return ""
