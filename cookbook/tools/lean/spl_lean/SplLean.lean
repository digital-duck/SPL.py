/-- Minimal root module for the SPL Lean project.  Checks live in the
REPL's transient environments, not in this library — it exists so that
`lake env` has a project to resolve dependencies (e.g. mathlib) in. -/
def splLeanReady : Bool := true
