"""Recipe 105 — Prolog-style Inference Engine (pure Python).

Implements backward-chaining inference over a set of facts and rules.
The engine resolves queries by recursively matching rule heads to goals,
substituting known facts, and backtracking on failure.

This demonstrates the Prolog reasoning model without requiring SWI-Prolog
or pyswip — useful for contract/compliance satisfiability where
rules have multiple levels of indirection.
"""

import json


# ── Mini backward-chaining inference engine ──────────────────────────────────

class KnowledgeBase:
    """Holds facts (ground atoms) and rules (head :- body)."""

    def __init__(self):
        self.facts: list[tuple] = []          # [(pred, *args)]
        self.rules: list[dict]  = []          # [{head, body}]

    def add_fact(self, predicate: str, *args):
        self.facts.append((predicate, *args))

    def add_rule(self, head: dict, body: list[dict]):
        self.rules.append({"head": head, "body": body})

    def query(self, goal: dict, bindings: dict | None = None) -> list[dict]:
        """Find all binding sets that satisfy the goal (backward chaining)."""
        if bindings is None:
            bindings = {}

        pred = goal["pred"]
        args = [bindings.get(a, a) for a in goal.get("args", [])]

        results: list[dict] = []

        # Try facts first
        for fact in self.facts:
            if fact[0] != pred or len(fact) - 1 != len(args):
                continue
            new_b = dict(bindings)
            match  = True
            for got, want in zip(fact[1:], args):
                if want.startswith("?"):        # unbound variable
                    new_b[want] = got
                elif got != want:
                    match = False
                    break
            if match:
                results.append(new_b)

        # Try rules (head unification → prove body)
        for rule in self.rules:
            head = rule["head"]
            if head["pred"] != pred or len(head.get("args", [])) != len(args):
                continue
            new_b = dict(bindings)
            match  = True
            for got, want in zip(head.get("args", []), args):
                if got.startswith("?"):         # head variable
                    new_b[got] = want
                elif got != want:
                    match = False
                    break
            if not match:
                continue
            # Prove all body goals with the new bindings
            body_solutions = [new_b]
            for body_goal in rule["body"]:
                next_solutions: list[dict] = []
                for sol in body_solutions:
                    next_solutions.extend(self.query(body_goal, sol))
                body_solutions = next_solutions
                if not body_solutions:
                    break
            results.extend(body_solutions)

        return results


# ── Default insurance policy knowledge base ──────────────────────────────────

def _build_default_kb() -> KnowledgeBase:
    kb = KnowledgeBase()

    # Facts: customer "alice" profile
    kb.add_fact("has_policy",          "alice", "comprehensive")
    kb.add_fact("policy_active",       "alice")
    kb.add_fact("deductible_met",      "alice")
    kb.add_fact("claim_type",          "alice", "emergency_repair")
    kb.add_fact("emergency_event",     "alice")

    # Facts: customer "bob" profile (lapsed policy)
    kb.add_fact("has_policy",          "bob", "basic")
    kb.add_fact("claim_type",          "bob", "emergency_repair")
    # bob does NOT have policy_active (lapsed)

    # Facts: customer "carol" profile (comprehensive, catastrophic)
    kb.add_fact("has_policy",          "carol", "comprehensive")
    kb.add_fact("policy_active",       "carol")
    kb.add_fact("catastrophic_event",  "carol")
    kb.add_fact("claim_type",          "carol", "emergency_repair")

    # Rules:
    # eligible_claim(X, Type) :- has_policy(X, comprehensive), policy_active(X), claim_covered(X, Type)
    kb.add_rule(
        head={"pred": "eligible_claim", "args": ["?X", "?Type"]},
        body=[
            {"pred": "has_policy",    "args": ["?X", "comprehensive"]},
            {"pred": "policy_active", "args": ["?X"]},
            {"pred": "claim_covered", "args": ["?X", "?Type"]},
        ],
    )

    # claim_covered(X, emergency_repair) :- deductible_met(X)
    kb.add_rule(
        head={"pred": "claim_covered", "args": ["?X", "emergency_repair"]},
        body=[{"pred": "deductible_met", "args": ["?X"]}],
    )

    # claim_covered(X, emergency_repair) :- catastrophic_event(X)
    kb.add_rule(
        head={"pred": "claim_covered", "args": ["?X", "emergency_repair"]},
        body=[{"pred": "catastrophic_event", "args": ["?X"]}],
    )

    # emergency_claim(X) :- eligible_claim(X, emergency_repair), emergency_event(X)
    kb.add_rule(
        head={"pred": "emergency_claim", "args": ["?X"]},
        body=[
            {"pred": "eligible_claim", "args": ["?X", "emergency_repair"]},
            {"pred": "emergency_event", "args": ["?X"]},
        ],
    )

    return kb


_DEFAULT_POLICY = {
    "policy_name": "ComprehensiveAuto_v3",
    "customers": ["alice", "bob", "carol"],
    "query": "emergency_claim",
    "description": (
        "Insurance eligibility: a customer can file an emergency claim if "
        "they have a comprehensive policy, the policy is active (not lapsed), "
        "and either the deductible is met OR the event is catastrophic. "
        "Alice: comprehensive, active, deductible met, emergency event. "
        "Bob: basic policy only (lapsed — policy_active missing). "
        "Carol: comprehensive, active, catastrophic event (no deductible needed)."
    ),
}


def get_default_policy() -> str:
    return json.dumps(_DEFAULT_POLICY)


def run_inference(policy_json: str) -> str:
    """Run backward-chaining inference for all customers in the policy.

    Returns:
      {"policy_name": str, "n_customers": int, "n_eligible": int,
       "results": [{customer, eligible, proof_chain}]}
    """
    try:
        policy = json.loads(policy_json)
        kb     = _build_default_kb()
        query_pred = policy.get("query", "emergency_claim")
        results = []

        for customer in policy.get("customers", []):
            solutions = kb.query({"pred": query_pred, "args": [customer]})
            eligible  = len(solutions) > 0
            results.append({
                "customer":    customer,
                "eligible":    eligible,
                "n_solutions": len(solutions),
                "verdict":     f"{customer}: {'ELIGIBLE' if eligible else 'NOT ELIGIBLE'} for {query_pred}",
            })

        n_eligible = sum(1 for r in results if r["eligible"])
        return json.dumps({
            "policy_name": policy.get("policy_name", "Policy"),
            "query":       query_pred,
            "n_customers": len(results),
            "n_eligible":  n_eligible,
            "status":      "OK",
            "results":     results,
        })
    except Exception as e:
        return json.dumps({"status": "ERROR", "error": str(e), "n_eligible": 0})


def inference_succeeded(result_json: str) -> bool:
    """ASSERT gate: inference ran without error and at least one result exists."""
    try:
        data = json.loads(result_json)
        return data.get("status") == "OK" and data.get("n_customers", 0) > 0
    except Exception:
        return False


def format_inference_report(result_json: str) -> str:
    """Markdown report of inference results."""
    try:
        data    = json.loads(result_json)
        results = data.get("results", [])
        lines   = [
            f"## Prolog Inference Report — {data.get('policy_name', 'Policy')}",
            "",
            f"**Query:** `{data.get('query', '?')}`  ",
            f"**Customers:** {data.get('n_customers', '?')}  ",
            f"**Eligible:** {data.get('n_eligible', '?')}",
            "",
            "| Customer | Eligible | Verdict |",
            "|---|---|---|",
        ]
        for r in results:
            mark = "✓" if r["eligible"] else "✗"
            lines.append(f"| {r['customer']} | {mark} | {r['verdict']} |")
        return "\n".join(lines)
    except Exception as e:
        return f"(format error: {e})"


def json_get_field(data_json: str, field: str) -> str:
    try:
        v = json.loads(data_json).get(field)
        return str(v) if v is not None else ""
    except Exception:
        return ""
