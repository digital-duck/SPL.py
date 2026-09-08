INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/64_parallel_news_digest/parallel_news_digest.spl
Registry: ['parallel_news_digest', 'summarise_single']
Running workflow: parallel_news_digest(['model'])
[INFO] [parallel_news_digest] digest_model=gemma3
[INFO] [parallel_news_digest] topics: "AI and large language models" | "space exploration and astronomy" | "global markets and energy transition"
INFO:spl.composer:CALL summarise_single(['topic', 'digest_model', 'log_dir']) INTO @tech_summary
INFO:spl.composer:CALL summarise_single(['topic', 'digest_model', 'log_dir']) INTO @sci_summary
INFO:spl.composer:CALL summarise_single(['topic', 'digest_model', 'log_dir']) INTO @biz_summary
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (summarise_topic) -> 107 tokens, 2865ms
INFO:spl.executor:GENERATE chain done -> @summary (593 chars total)
INFO:spl.executor:RETURN: 593 chars | none
INFO:spl.composer:CALL summarise_single completed: status=complete in 2865ms (1 LLM calls)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (summarise_topic) -> 108 tokens, 4913ms
INFO:spl.executor:GENERATE chain done -> @summary (673 chars total)
INFO:spl.executor:RETURN: 673 chars | none
INFO:spl.composer:CALL summarise_single completed: status=complete in 4913ms (1 LLM calls)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (summarise_topic) -> 107 tokens, 6973ms
INFO:spl.executor:GENERATE chain done -> @summary (639 chars total)
INFO:spl.executor:RETURN: 639 chars | none
INFO:spl.composer:CALL summarise_single completed: status=complete in 6974ms (1 LLM calls)
[INFO] [parallel_news_digest] parallel summaries complete — merging into digest
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (morning_briefing) -> 257 tokens, 5196ms
INFO:spl.executor:GENERATE chain done -> @digest (1446 chars total)
[INFO] [parallel_news_digest] done | digest_len={len(@digest)}
INFO:spl.executor:RETURN: 1446 chars | none

Status:  complete
Output:  Good morning, [Senior Leader's Name], here’s your briefing for today:

**AI & Large Language Models** – The landscape of AI continues to shift dramatically with open-source models like Llama 2 challenging established proprietary systems and reducing costs.  Ongoing debates surround model safety and potential misuse, leading to increased regulatory scrutiny and demands for greater transparency. Expect further competition between open and closed models alongside efforts to manage the growing power of these technologies.

**Space Exploration & Astronomy** – NASA’s James Webb Telescope continues to revolutionize our understanding of the cosmos with detailed infrared images of exoplanets and early galaxies, while SpaceX's Starship launch represents a major step towards fully reusable space travel.  These advancements point toward an accelerated era of exploration and discovery driven by both governmental and private sector initiatives.

**Global Markets & Energy Transition** – Global equity markets remained volatile this week due to inflation concerns and interest rate anxieties, alongside rising Treasury yields. Notably, investment in renewable energy reached a record $92.3 billion, fueled by government incentives and declining technology costs - highlighting the continued growth within the energy transition sector.

Watch today for the release of updated inflation data at 9:00 AM EST; this will likely impact market sentiment.
LLM calls: 4  Latency: 12170ms
Log:     /home/papagame/.spl/logs/parallel_news_digest-ollama-gemma3-20260621-124131.md
