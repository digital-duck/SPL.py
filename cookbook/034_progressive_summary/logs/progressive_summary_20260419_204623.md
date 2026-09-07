INFO:spl.registry:Registry: loaded 1 workflow(s) from cookbook/34_progressive_summary/progressive_summary.spl
Registry: ['progressive_summarizer']
Running workflow: progressive_summarizer(['text', 'audience'])
[INFO] Progressive summary | audience=executive layers=3
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task c60e6f8b-ee89-488c-a268-841f1fc41759 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/c60e6f8b-ee89-488c-a268-841f1fc41759 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/c60e6f8b-ee89-488c-a268-841f1fc41759 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/c60e6f8b-ee89-488c-a268-841f1fc41759 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/c60e6f8b-ee89-488c-a268-841f1fc41759 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/c60e6f8b-ee89-488c-a268-841f1fc41759 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/c60e6f8b-ee89-488c-a268-841f1fc41759 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/c60e6f8b-ee89-488c-a268-841f1fc41759 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task c60e6f8b-ee89-488c-a268-841f1fc41759 completed by agent wengong in 8864ms (132 tokens)
INFO:spl.executor:GENERATE segment 1 (summarize) -> 132 tokens, 12390ms
INFO:spl.executor:GENERATE chain done -> @sentence_summary (698 chars total)
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task f30269a4-23ef-4c42-ae3e-589b022bc1d0 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/f30269a4-23ef-4c42-ae3e-589b022bc1d0 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/f30269a4-23ef-4c42-ae3e-589b022bc1d0 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/f30269a4-23ef-4c42-ae3e-589b022bc1d0 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task f30269a4-23ef-4c42-ae3e-589b022bc1d0 completed by agent gong2 in 2711ms (185 tokens)
INFO:spl.executor:GENERATE segment 1 (expand_summary) -> 185 tokens, 4048ms
INFO:spl.executor:GENERATE chain done -> @paragraph_summary (1018 chars total)
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 936644df-2411-4648-a134-f42b2d20a731 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/936644df-2411-4648-a134-f42b2d20a731 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/936644df-2411-4648-a134-f42b2d20a731 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/936644df-2411-4648-a134-f42b2d20a731 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/936644df-2411-4648-a134-f42b2d20a731 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/936644df-2411-4648-a134-f42b2d20a731 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/936644df-2411-4648-a134-f42b2d20a731 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/936644df-2411-4648-a134-f42b2d20a731 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/936644df-2411-4648-a134-f42b2d20a731 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/936644df-2411-4648-a134-f42b2d20a731 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/936644df-2411-4648-a134-f42b2d20a731 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/936644df-2411-4648-a134-f42b2d20a731 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/936644df-2411-4648-a134-f42b2d20a731 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/936644df-2411-4648-a134-f42b2d20a731 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 936644df-2411-4648-a134-f42b2d20a731 completed by agent papa-game in 23236ms (584 tokens)
INFO:spl.executor:GENERATE segment 1 (expand_summary) -> 584 tokens, 24926ms
INFO:spl.executor:GENERATE chain done -> @page_summary (3047 chars total)
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task cf3cb4ea-cf95-4ee3-8daa-05eabfb71beb submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/cf3cb4ea-cf95-4ee3-8daa-05eabfb71beb "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/cf3cb4ea-cf95-4ee3-8daa-05eabfb71beb "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/cf3cb4ea-cf95-4ee3-8daa-05eabfb71beb "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/cf3cb4ea-cf95-4ee3-8daa-05eabfb71beb "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/cf3cb4ea-cf95-4ee3-8daa-05eabfb71beb "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/cf3cb4ea-cf95-4ee3-8daa-05eabfb71beb "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/cf3cb4ea-cf95-4ee3-8daa-05eabfb71beb "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task cf3cb4ea-cf95-4ee3-8daa-05eabfb71beb completed by agent papa-game in 11535ms (339 tokens)
INFO:spl.executor:GENERATE segment 1 (verify_summary_fidelity) -> 339 tokens, 12287ms
INFO:spl.executor:GENERATE chain done -> @fidelity_score (1695 chars total)
[INFO] Fidelity score: It looks like we've got a good starting point!

To verify the `summary_fidelity` of our summaries, I'll provide some feedback on each input. Feel free to adjust the constraints or provide more guidance if needed.

**Input 1:**
The summary is concise and captures the main idea of artificial intelligence transforming industries. However, it's quite brief and doesn't fully explore the implications of AI on industries like healthcare and finance. To improve its `summary_fidelity`, consider expanding on the benefits and challenges of AI in these fields.

**Input 2:**
This summary is a good attempt at condensing the original text into a shorter form while maintaining some of the key points. However, it's still somewhat vague and could benefit from more specific examples or details to make it more informative.

**Input 3:**
The expanded summary meets the specified constraints (50 words) and incorporates relevant keywords like "machine learning" and "deep learning." It also provides a clearer overview of AI's impact on industries, including its benefits (e.g., automating complex tasks) and challenges (e.g., bias, accountability). Well done!

To further improve our summaries, I'd like to suggest the following constraints:

1. **Word Count:** Expand the summary to exactly 75 words.
2. **Tone:** Maintain a neutral and informative tone throughout the summary.
3. **Keywords:** Include specific keywords related to artificial intelligence, such as "machine learning," "deep learning," or "natural language processing."

Please let me know if you'd like to adjust these constraints or provide additional guidance on what aspects of AI in healthcare and finance you'd like us to focus on.
INFO:httpx:HTTP Request: POST http://192.168.0.184:9000/tasks "HTTP/1.1 202 Accepted"
INFO:spl.adapters.momagrid:Task 9697ed07-9787-47fa-8304-bc1b700fc964 submitted to Momagrid hub
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/9697ed07-9787-47fa-8304-bc1b700fc964 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/9697ed07-9787-47fa-8304-bc1b700fc964 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/9697ed07-9787-47fa-8304-bc1b700fc964 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/9697ed07-9787-47fa-8304-bc1b700fc964 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/9697ed07-9787-47fa-8304-bc1b700fc964 "HTTP/1.1 200 OK"
INFO:httpx:HTTP Request: GET http://192.168.0.184:9000/tasks/9697ed07-9787-47fa-8304-bc1b700fc964 "HTTP/1.1 200 OK"
INFO:spl.adapters.momagrid:Task 9697ed07-9787-47fa-8304-bc1b700fc964 completed by agent papa-game in 7884ms (212 tokens)
INFO:spl.executor:GENERATE segment 1 (assemble_summary_package) -> 212 tokens, 10342ms
INFO:spl.executor:GENERATE chain done -> @summary_package (1125 chars total)
INFO:spl.executor:RETURN: 1125 chars | status=complete, layers_generated=3, audience=executive, fidelity=It looks like we've got a good starting point!

To verify the `summary_fidelity` of our summaries, I'll provide some feedback on each input. Feel free to adjust the constraints or provide more guidance if needed.

**Input 1:**
The summary is concise and captures the main idea of artificial intelligence transforming industries. However, it's quite brief and doesn't fully explore the implications of AI on industries like healthcare and finance. To improve its `summary_fidelity`, consider expanding on the benefits and challenges of AI in these fields.

**Input 2:**
This summary is a good attempt at condensing the original text into a shorter form while maintaining some of the key points. However, it's still somewhat vague and could benefit from more specific examples or details to make it more informative.

**Input 3:**
The expanded summary meets the specified constraints (50 words) and incorporates relevant keywords like "machine learning" and "deep learning." It also provides a clearer overview of AI's impact on industries, including its benefits (e.g., automating complex tasks) and challenges (e.g., bias, accountability). Well done!

To further improve our summaries, I'd like to suggest the following constraints:

1. **Word Count:** Expand the summary to exactly 75 words.
2. **Tone:** Maintain a neutral and informative tone throughout the summary.
3. **Keywords:** Include specific keywords related to artificial intelligence, such as "machine learning," "deep learning," or "natural language processing."

Please let me know if you'd like to adjust these constraints or provide additional guidance on what aspects of AI in healthcare and finance you'd like us to focus on.

Status:  complete
Output:  Based on the input provided, I can create a summary that meets certain constraints.

Here's a possible summary:

"Artificial intelligence has revolutionized various industries by automating complex tasks, enabling machine learning models to diagnose diseases from medical images and detect fraud in financial transactions. However, AI raises important questions about bias, accountability, and the future of work, highlighting the need for responsible innovation and regulation. As AI continues to advance, it's essential to prioritize transparency, explainability, and fairness in its development and deployment."

If you'd like me to adjust this summary to meet specific constraints or provide additional guidance on what aspects of AI in healthcare and finance I should focus on, please let me know.

Alternatively, if you'd like to use the `expand_summary` function from Input 3, here's an updated version with the new constraints:

input5_constraints = {'word_count': 75, 'tone': 'neutral', 'keywords': ['machine learning', 'deep learning']}
expanded_summary = expand_summary(input5_constraints)

print(expanded_summary)
LLM calls: 5  Latency: 63995ms
Log:     /home/papagame/.spl/logs/progressive_summary-momagrid-20260419-204958.md
