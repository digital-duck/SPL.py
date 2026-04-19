Registry: workflows=[parallel_code_review, security_audit, style_review, test_generator] prompts=[]
Running workflow: parallel_code_review(code)
[SPL][INFO] [parallel_code_review] starting 3-way parallel review | lang=python review_model=gemma4
Error: Ollama error 404: {"error":"model 'gemma4' not found"}
    at OllamaAdapter.generate (file:///home/papagame/projects/digital-duck/SPL.ts/dist/adapters/ollama.js:35:19)
    at process.processTicksAndRejections (node:internal/process/task_queues:95:5)
    at async Executor.runGenerateChain (file:///home/papagame/projects/digital-duck/SPL.ts/dist/executor.js:241:22)
    at async Executor.execGenerateInto (file:///home/papagame/projects/digital-duck/SPL.ts/dist/executor.js:229:24)
    at async Executor.execBody (file:///home/papagame/projects/digital-duck/SPL.ts/dist/executor.js:180:13)
    at async Executor.executeWorkflow (file:///home/papagame/projects/digital-duck/SPL.ts/dist/executor.js:150:13)
    at async file:///home/papagame/projects/digital-duck/SPL.ts/dist/executor.js:378:28
    at async Promise.all (index 0)
    at async Executor.execCallParallel (file:///home/papagame/projects/digital-duck/SPL.ts/dist/executor.js:381:25)
    at async Executor.execBody (file:///home/papagame/projects/digital-duck/SPL.ts/dist/executor.js:180:13)
