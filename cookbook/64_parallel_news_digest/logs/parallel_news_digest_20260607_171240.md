INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/64_parallel_news_digest/parallel_news_digest.spl
Registry: ['parallel_news_digest', 'summarise_single']
Running workflow: parallel_news_digest(['model'])
[INFO] [parallel_news_digest] digest_model=gemma3
[INFO] [parallel_news_digest] topics: "AI and large language models" | "space exploration and astronomy" | "global markets and energy transition"
INFO:spl.composer:CALL summarise_single(['topic', 'digest_model', 'log_dir']) INTO @tech_summary
INFO:spl.composer:CALL summarise_single(['topic', 'digest_model', 'log_dir']) INTO @sci_summary
INFO:spl.composer:CALL summarise_single(['topic', 'digest_model', 'log_dir']) INTO @biz_summary
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (summarise_topic) -> 90 tokens, 4710ms
INFO:spl.executor:GENERATE chain done -> @summary (564 chars total)
INFO:spl.executor:RETURN: 564 chars | none
INFO:spl.composer:CALL summarise_single completed: status=complete in 4710ms (1 LLM calls)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (summarise_topic) -> 114 tokens, 6825ms
INFO:spl.executor:GENERATE chain done -> @summary (660 chars total)
INFO:spl.executor:RETURN: 660 chars | none
INFO:spl.composer:CALL summarise_single completed: status=complete in 6826ms (1 LLM calls)
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (summarise_topic) -> 117 tokens, 8847ms
INFO:spl.executor:GENERATE chain done -> @summary (724 chars total)
INFO:spl.executor:RETURN: 724 chars | none
INFO:spl.composer:CALL summarise_single completed: status=complete in 8848ms (1 LLM calls)
[INFO] [parallel_news_digest] parallel summaries complete — merging into digest
INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
INFO:spl.executor:GENERATE segment 1 (morning_briefing) -> 250 tokens, 4807ms
INFO:spl.executor:GENERATE chain done -> @digest (1471 chars total)
[INFO] [parallel_news_digest] done | digest_len={len(@digest)}
INFO:spl.executor:RETURN: 1471 chars | none

Status:  complete
Output:  Good morning, [Senior Leader’s Name]. Here's a quick briefing on key developments across your areas of interest:

**AI & LLM Advancements**
The rapid evolution in artificial intelligence continues to accelerate. OpenAI’s GPT-4o is generating significant buzz with its multimodal capabilities – combining text, audio and image processing – while Google pushes forward with Gemini’s application development. While innovation remains robust, discussions surrounding responsible AI deployment and model refinement are paramount.

**Space Exploration & Astronomy**
NASA's James Webb Telescope continues to revolutionize our understanding of the universe, providing detailed data on exoplanets and early galaxy formation. Simultaneously, private companies like SpaceX are dramatically increasing space access through rapid launch cadence and development of Starship.  These advancements point toward a future with intensified lunar exploration and broader planetary investigations.

**Global Markets & Energy Transition**
Global equity markets remain volatile due to inflation concerns and central bank policies, alongside increased investment in renewable energy projects reaching record highs thanks to government incentives. Despite this shift, market uncertainty persists, coupled with ongoing pressure for accelerated decarbonization strategies. 

Watch today’s meeting regarding the revised Q3 projections – it will be crucial in addressing the evolving market landscape.
LLM calls: 4  Latency: 13657ms
Log:     /home/gongai/.spl/logs/parallel_news_digest-ollama-20260607-171406.md
