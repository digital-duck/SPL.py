[persistence] workflow-id: 02d92e3a-067a-48a5-90f7-5018786fa29b
[persistence] backend=sqlite  workflow-id=02d92e3a-067a-48a5-90f7-5018786fa29b
[kernel-store] db=~/.spl/workflows.db
INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook-solver/109_synthetic_problems/synthetic_problem_gen.spl
Registry: ['synthetic_problem_gen']
INFO:spl.executor:HITL tools registered: wait_for_approval / send_approval
Auto-loaded 96 tool(s) from cookbook-solver/109_synthetic_problems/tools.py
Running workflow: synthetic_problem_gen(['domain', 'n_variants', 'n_size', 'model'])
[INFO] [r109] start  domain=LP  n_variants=5  n_size=5
INFO:spl.executor:GENERATE segment 1 (generate_variants_prompt) -> 1828 tokens, 256073ms
INFO:spl.executor:GENERATE chain done -> @variants_raw (7315 chars total)
INFO:spl.executor:ASSERT (kernel-store) has_valid_variants('{"status": "OK", "n_valid": 5, "n_errors": 0, "errors": [], "variants": [{"id": "v001", "domain": "lp", "problem_text": "A beverage company produces five drinks: Lemonade (x1), Orange Juice (x2), Apple Cider (x3), Grape Juice (x4), and Iced Tea (x5). Lemonade earns $24 profit per case and requires 3 labor-hours and 2 kg of fruit. Orange Juice earns $6 profit per case and requires 2 labor-hours and 4 kg of fruit. Apple Cider earns $5 profit per case and requires 1 labor-hour and 3 kg of fruit. Grape Juice earns $4 profit per case and requires 3 labor-hours and 2 kg of fruit. Iced Tea earns $3 profit per case and requires 2 labor-hours and 3 kg of fruit. The plant has 60 labor-hours and 40 kg of fruit available per day. All production quantities must be non-negative. Maximize total daily profit.", "variables": [{"name": "x1", "type": "continuous", "lb": 0}, {"name": "x2", "type": "continuous", "lb": 0}, {"name": "x3", "type": "continuous", "lb": 0}, {"name": "x4", "type": "continuous", "lb": 0}, {"name": "x5", "type": "continuous", "lb": 0}], "objective": {"sense": "maximize", "coefficients": {"x1": 24, "x2": 6, "x3": 5, "x4": 4, "x5": 3}}, "constraints": [{"name": "labor", "lhs": {"x1": 3, "x2": 2, "x3": 1, "x4": 3, "x5": 2}, "op": "<=", "rhs": 60}, {"name": "fruit", "lhs": {"x1": 2, "x2": 4, "x3": 3, "x4": 2, "x5": 3}, "op": "<=", "rhs": 40}]}, {"id": "v002", "domain": "lp", "problem_text": "A furniture maker produces five items: Armchairs (x1), Benches (x2), Coffee Tables (x3), Dining Sets (x4), and End Tables (x5). Armchairs earn $20 profit and require 2 labor-hours and 5 board-feet of wood. Benches earn $8 profit and require 1 labor-hour and 2 board-feet. Coffee Tables earn $15 profit and require 4 labor-hours and 2 board-feet. Dining Sets earn $6 profit and require 1 labor-hour and 3 board-feet. End Tables earn $4 profit and require 1 labor-hour and 1 board-foot. Available daily resources: 20 labor-hours and 30 board-feet of wood. All quantities must be non-negative. Maximize total daily profit.", "variables": [{"name": "x1", "type": "continuous", "lb": 0}, {"name": "x2", "type": "continuous", "lb": 0}, {"name": "x3", "type": "continuous", "lb": 0}, {"name": "x4", "type": "continuous", "lb": 0}, {"name": "x5", "type": "continuous", "lb": 0}], "objective": {"sense": "maximize", "coefficients": {"x1": 20, "x2": 8, "x3": 15, "x4": 6, "x5": 4}}, "constraints": [{"name": "labor", "lhs": {"x1": 2, "x2": 1, "x3": 4, "x4": 1, "x5": 1}, "op": "<=", "rhs": 20}, {"name": "wood", "lhs": {"x1": 5, "x2": 2, "x3": 2, "x4": 3, "x5": 1}, "op": "<=", "rhs": 30}]}, {"id": "v003", "domain": "lp", "problem_text": "An electronics firm assembles five circuit-board types: Alpha (x1), Beta (x2), Gamma (x3), Delta (x4), and Epsilon (x5). Alpha boards earn $15 profit and consume 2 assembly-hours, 3 kg of solder, and 1 machine-hour. Beta boards earn $12 profit and consume 3 assembly-hours, 2 kg of solder, and 2 machine-hours. Gamma boards earn $10 profit and consume 1 assembly-hour, 2 kg of solder, and 1 machine-hour. Delta boards earn $8 profit and consume 2 assembly-hours, 1 kg of solder, and 2 machine-hours. Epsilon boards earn $6 profit and consume 1 assembly-hour, 2 kg of solder, and 1 machine-hour. Daily capacity: 25 assembly-hours, 30 kg of solder, and 20 machine-hours. All quantities must be non-negative. Maximize total daily profit.", "variables": [{"name": "x1", "type": "continuous", "lb": 0}, {"name": "x2", "type": "continuous", "lb": 0}, {"name": "x3", "type": "continuous", "lb": 0}, {"name": "x4", "type": "continuous", "lb": 0}, {"name": "x5", "type": "continuous", "lb": 0}], "objective": {"sense": "maximize", "coefficients": {"x1": 15, "x2": 12, "x3": 10, "x4": 8, "x5": 6}}, "constraints": [{"name": "assembly_hours", "lhs": {"x1": 2, "x2": 3, "x3": 1, "x4": 2, "x5": 1}, "op": "<=", "rhs": 25}, {"name": "solder_kg", "lhs": {"x1": 3, "x2": 2, "x3": 2, "x4": 1, "x5": 2}, "op": "<=", "rhs": 30}, {"name": "machine_hours", "lhs": {"x1": 1, "x2": 2, "x3": 1, "x4": 2, "x5": 1}, "op": "<=", "rhs": 20}]}, {"id": "v004", "domain": "lp", "problem_text": "A pharmaceutical company manufactures five drug formulations: P1 (x1), P2 (x2), P3 (x3), P4 (x4), and P5 (x5). P1 earns $25 profit per batch and requires 4 chemist-hours, 3 kg of active ingredient, and 2 reactor-hours. P2 earns $20 profit per batch and requires 3 chemist-hours, 4 kg of active ingredient, and 3 reactor-hours. P3 earns $18 profit per batch and requires 5 chemist-hours, 2 kg of active ingredient, and 2 reactor-hours. P4 earns $15 profit per batch and requires 2 chemist-hours, 5 kg of active ingredient, and 3 reactor-hours. P5 earns $12 profit per batch and requires 3 chemist-hours, 3 kg of active ingredient, and 4 reactor-hours. Daily limits: 40 chemist-hours, 35 kg of active ingredient, and 30 reactor-hours. All batch quantities must be non-negative. Maximize total daily profit.", "variables": [{"name": "x1", "type": "continuous", "lb": 0}, {"name": "x2", "type": "continuous", "lb": 0}, {"name": "x3", "type": "continuous", "lb": 0}, {"name": "x4", "type": "continuous", "lb": 0}, {"name": "x5", "type": "continuous", "lb": 0}], "objective": {"sense": "maximize", "coefficients": {"x1": 25, "x2": 20, "x3": 18, "x4": 15, "x5": 12}}, "constraints": [{"name": "chemist_hours", "lhs": {"x1": 4, "x2": 3, "x3": 5, "x4": 2, "x5": 3}, "op": "<=", "rhs": 40}, {"name": "active_ingredient", "lhs": {"x1": 3, "x2": 4, "x3": 2, "x4": 5, "x5": 3}, "op": "<=", "rhs": 35}, {"name": "reactor_hours", "lhs": {"x1": 2, "x2": 3, "x3": 2, "x4": 3, "x5": 4}, "op": "<=", "rhs": 30}]}, {"id": "v005", "domain": "lp", "problem_text": "An apparel factory produces five garment styles: Jackets (x1), Trousers (x2), Shirts (x3), Dresses (x4), and Skirts (x5). Jackets earn $30 profit and require 5 labor-hours and 4 m\\u00b2 of fabric. Trousers earn $25 profit and require 4 labor-hours and 5 m\\u00b2 of fabric. Shirts earn $20 profit and require 6 labor-hours and 3 m\\u00b2 of fabric. Dresses earn $18 profit and require 3 labor-hours and 6 m\\u00b2 of fabric. Skirts earn $15 profit and require 5 labor-hours and 5 m\\u00b2 of fabric. The factory has exactly 30 labor-hours and 30 m\\u00b2 of fabric available per day. All quantities must be non-negative. Maximize total daily profit.", "variables": [{"name": "x1", "type": "continuous", "lb": 0}, {"name": "x2", "type": "continuous", "lb": 0}, {"name": "x3", "type": "continuous", "lb": 0}, {"name": "x4", "type": "continuous", "lb": 0}, {"name": "x5", "type": "continuous", "lb": 0}], "objective": {"sense": "maximize", "coefficients": {"x1": 30, "x2": 25, "x3": 20, "x4": 18, "x5": 15}}, "constraints": [{"name": "labor", "lhs": {"x1": 5, "x2": 4, "x3": 6, "x4": 3, "x5": 5}, "op": "<=", "rhs": 30}, {"name": "fabric", "lhs": {"x1": 4, "x2": 5, "x3": 3, "x4": 6, "x5": 5}, "op": "<=", "rhs": 30}]}]}') -> True
[INFO] [r109] 5 valid variants after 0 repair(s)
[INFO] [r109] solved 5/5 optimally
ERROR:spl.executor:Unhandled SPL exception [ModelOverloaded]: Claude CLI limit reached: You've hit your session limit · resets 11:10pm (America/New_York) — no EXCEPTION WHEN handler matched; propagating to caller. Add 'WHEN OTHERS THEN' to catch all exceptions.
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/cli.py", line 5353, in <module>
    main()
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1524, in __call__
    return self.main(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1445, in main
    rv = self.invoke(ctx)
         ^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1912, in invoke
    return _process_result(sub_ctx.command.invoke(sub_ctx))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 1308, in invoke
    return ctx.invoke(self.callback, **ctx.params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/core.py", line 877, in invoke
    return callback(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/cli.py", line 63, in wrapper
    return fn(*args, adapter=adapter, model=model, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/site-packages/click/decorators.py", line 34, in new_func
    return f(get_current_context(), *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/cli.py", line 778, in run
    asyncio.run(_run_workflow(path, adapter, model, params, hub_url, log_prompts,
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/asyncio/runners.py", line 190, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/anaconda3/envs/spl123/lib/python3.11/asyncio/base_events.py", line 654, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/cli.py", line 946, in _run_workflow
    result = await executor.execute_workflow(target.ast_node, params=params)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/executor.py", line 888, in execute_workflow
    result = await super().execute_workflow(stmt, params=params)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 688, in execute_workflow
    await self._execute_body(stmt.body, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 724, in _execute_body
    await self._execute_statement(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/executor.py", line 191, in _execute_statement
    await super()._execute_statement(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 750, in _execute_statement
    await self._exec_generate_into(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/executor.py", line 534, in _exec_generate_into
    await self._exec_generate_into_impl(stmt, state)
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/executor.py", line 557, in _exec_generate_into_impl
    return await super()._exec_generate_into(stmt, state)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl/executor.py", line 959, in _exec_generate_into
    gen_result = await self.adapter.generate(
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl3/cli.py", line 92, in generate
    return await self._inner.generate(prompt, model=model, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/papagame/projects/digital-duck/SPL.py/spl/adapters/claude_cli.py", line 117, in generate
    raise ModelOverloaded(f"Claude CLI limit reached: {error_detail}")
spl.executor.ModelOverloaded: Claude CLI limit reached: You've hit your session limit · resets 11:10pm (America/New_York)
