## Summary

This implementation defines an asynchronous three-stage order-fulfillment pipeline — Payment, Inventory, and Shipping — where each stage is a self-contained sub-workflow composed in sequence. The payment stage includes conditional retry logic: if payment processing fails, control routes back to the validation step rather than aborting. A companion visualization tool renders any PocketFlow graph as an interactive D3.js diagram grouped by sub-workflow, helping developers inspect and debug multi-flow compositions without reading code.

---

## Detailed Specification

### 1. Purpose

Orchestrate a sequential order fulfillment pipeline across three autonomous sub-workflows (payment processing with retry, inventory management, and shipping logistics), writing status results into shared state at each step, while providing an interactive graph visualization for any composed PocketFlow workflow.

---

### 2. High-level Description

The implementation declares three `WORKFLOW` units — PaymentFlow, InventoryFlow, and ShippingFlow — each containing three `GENERATE`-equivalent nodes that produce status strings stored in the shared `@var` dictionary. PaymentFlow sequences ValidatePayment → ProcessPayment → PaymentConfirmation, but with non-trivial branching: an `EVALUATE`-driven WHILE loop re-routes ProcessPayment back to ValidatePayment on a `"something fail"` signal, and ValidatePayment retries itself on `"out_of_stock"`, advancing only when ProcessPayment signals `"pass"`. The master pipeline composes all three sub-workflows sequentially via `CALL`: PaymentFlow → InventoryFlow → ShippingFlow, with InventoryFlow and ShippingFlow running as purely linear chains. A separate visualization workflow acts as a `CALL`-style side-effect tool: it traverses the composed graph structure, emits a Mermaid diagram to stdout, serializes nodes, intra-group links, and inter-group links to JSON, then serves an interactive D3.js HTML page with force-directed layout where dashed group boundaries represent sub-flow containment and dashed inter-boundary arrows represent the `CALL` connections between flows.

---

### 3. SPL ↔ Python Construct Mapping

| SPL Construct | Python Equivalent | Notes |
|---|---|---|
| `WORKFLOW <name>` | `class OrderFlow(AsyncFlow)` | Top-level master workflow |
| `PROCEDURE <name>` | `payment_flow`, `inventory_flow`, `shipping_flow` (`AsyncFlow` instances) | Named sub-workflows composed into the master |
| `GENERATE fn(...) INTO @var` | `AsyncNode.exec_async()` + `shared[key] = exec_res` in `post_async` | Each node produces a result written to the shared dict |
| `CALL workflow INTO @var` | `payment_flow >> inventory_flow >> shipping_flow` | Sequential sub-workflow composition |
| `WHILE condition DO ... END` | `validate_payment - "out_of_stock" >> validate_payment` (self-loop) | Retry until stock is available |
| `EVALUATE @var WHEN ... THEN ... ELSE ...` | `process_payment - 'something fail' >> validate_payment` / `- 'pass' >> payment_confirmation` | Conditional branch on payment step outcome |
| `RETURN @var WITH status='pass'` | `return "pass"` from `post_async` | Non-default token that exits the payment retry loop |
| `RETURN @var WITH status='retry'` | `return "something fail"` / `return "out_of_stock"` | Non-default tokens that drive retry routing |
| SPL `@var` shared state | `shared` dict threaded through all `post_async` calls | Single mutable context passed across all nodes and sub-flows |
| `CALL tool(...) INTO @var` | `visualize_flow(...)` / `create_d3_visualization(...)` | Side-effect tool calls producing files and starting HTTP server |
| `EXCEPTION WHEN ... THEN ...` | _(absent — retry loops absorb failure cases)_ | No explicit exception handler; retry routing substitutes |

---

### 4. Logical Functions / Prompts

**ValidatePayment**
- Role: Entry gate for PaymentFlow; verifies payment authorization before charging
- Key convention: Returns `"out_of_stock"` to self-loop (WHILE retry), `"default"` to advance to ProcessPayment; in a real LLM deployment, prompts a payment-validation agent

**ProcessPayment**
- Role: Executes the financial transaction against a payment provider
- Key convention: Returns `"something fail"` to route back to ValidatePayment (full retry from top of payment loop), `"pass"` to advance to PaymentConfirmation — these are the only non-default tokens in the system

**PaymentConfirmation**
- Role: Issues the final payment receipt and writes `payment_confirmation` into shared state; terminal node of PaymentFlow

**CheckStock**
- Role: Queries inventory availability; writes `stock_status` into shared state; entry node of InventoryFlow

**ReserveItems**
- Role: Places a hold on requested items; writes `reservation_status` into shared state

**UpdateInventory**
- Role: Commits the inventory deduction; writes `inventory_update` into shared state; terminal node of InventoryFlow

**CreateLabel**
- Role: Generates a shipping label; writes `shipping_label` into shared state; entry node of ShippingFlow

**AssignCarrier**
- Role: Selects and assigns a logistics carrier; writes `carrier` into shared state

**SchedulePickup**
- Role: Books the carrier pickup window; writes `pickup_status` into shared state; terminal node of ShippingFlow and the entire pipeline

**visualize_flow (meta side-effect tool)**
- Role: Introspection utility invoked after pipeline definition; not an LLM step
- Key conventions: `build_mermaid` emits a `graph LR` Mermaid diagram to stdout; `flow_to_json` serializes the graph topology into `{nodes, links, group_links, flows}`; `create_d3_visualization` writes `.html` + `.json` to `./viz/`; `serve_and_open_visualization` launches a daemon HTTP server thread and opens the browser

---

### 5. Control Flow

The master `order_pipeline` starts by delegating to **PaymentFlow**. Inside PaymentFlow (as defined in `async_loop_flow.py`):

1. **ValidatePayment** runs. If it returns `"out_of_stock"`, it loops back to itself — a WHILE retry on stock availability.
2. **ProcessPayment** runs. If it returns `"something fail"`, control returns to **ValidatePayment** (full retry from top of PaymentFlow). If it returns `"pass"`, it advances.
3. **PaymentConfirmation** completes PaymentFlow with no further branching.

PaymentFlow then transfers to **InventoryFlow** (CheckStock → ReserveItems → UpdateInventory, linear). InventoryFlow transfers to **ShippingFlow** (CreateLabel → AssignCarrier → SchedulePickup, linear).

**Termination:** SchedulePickup has no successors; `order_pipeline.run_async(shared_data)` resolves and prints the three terminal status values (`payment_confirmation`, `inventory_update`, `pickup_status`).

---

### 6. How to Regenerate as SPL

```bash
# Step 1 — generate SPL from this spec (Section 1 above as text2spl input)
spl3 text2spl --description "Orchestrate a sequential order fulfillment pipeline across three
sub-workflows. PaymentFlow chains ValidatePayment → ProcessPayment → PaymentConfirmation:
ProcessPayment loops back to ValidatePayment on failure ('something fail'), ValidatePayment
retries itself on out-of-stock, and only a 'pass' result from ProcessPayment advances to
PaymentConfirmation. InventoryFlow chains CheckStock → ReserveItems → UpdateInventory.
ShippingFlow chains CreateLabel → AssignCarrier → SchedulePickup. The three sub-workflows
are called sequentially: PaymentFlow then InventoryFlow then ShippingFlow. Each node writes
its status string into shared state under a named key." --mode workflow

# Step 2 — compile to any target
spl3 splc compile order_pipeline.spl --lang python/pocketflow
spl3 splc compile order_pipeline.spl --lang python/langgraph
spl3 splc compile order_pipeline.spl --lang go
```