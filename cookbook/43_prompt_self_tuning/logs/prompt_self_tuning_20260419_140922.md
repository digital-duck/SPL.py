Registry: workflows=[prompt_self_tuning] prompts=[]
Running workflow: prompt_self_tuning(baseline_prompt, failed_case)
[SPL][INFO] Generating prompt variations for failed case: The document describes a complex quantum algorithm.
[SPL][INFO] Running mini A/B test on variants ...
[SPL][INFO] Winner: variant 1

Status:     complete
Output:     Summarize this technical document, focusing on explaining the core concepts and algorithm steps in a way understandable to someone with a basic understanding of computer science but no prior knowledge of quantum mechanics.
LLM calls:  4
Latency:    4530ms
Tokens:     338 in / 317 out
Est. Cost:  $0.0001
Log:        /home/papagame/.spl/logs/prompt_self_tuning-ollama-20260419-142958-ts.md
