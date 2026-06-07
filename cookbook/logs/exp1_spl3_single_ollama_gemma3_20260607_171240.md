=== SPL Cookbook Batch Run — 2026-06-07 17:12:40 ===
    Adapter : ollama  |  Model : gemma3

[51] Image Caption  (Ollama only)
     cmd : python cookbook/51_image_caption/run.py --image cookbook/51_image_caption/sample/photo.jpg --model gemma4:12b
     log : /home/gongai/projects/digital-duck/SPL.py/cookbook/51_image_caption/logs/image_caption_20260607_171240.md
     | [image_caption] encoded image/jpeg ~18 KB (10 ms)
     | [image_caption] → ollama/gemma4:12b (mode=caption) ...
     | [image_caption] ✓ 297 in / 388 out (20122 ms)
     | 
     | ── Result ───────────────────────────────────────────────────────────
     | This image is a stylized, flat illustration of a landscape featuring:
     | 
     | *   **Sky:** A solid blue background.
     | *   **Sun:** A large yellow circle in the upper right corner.
     | *   **Mountains:** Three dark gray triangular mountains with white-capped peaks in the center. The middle mountain is slightly taller than the two flanking it.
     | *   **Water:** A horizontal blue oval at the bottom, representing a lake or body of water.
     | *   **Text:** A black rectangle in the top left corner contains the white text "SPL-3.0 Multimodal Test Image".
     | ─────────────────────────────────────────────────────────────────────
     result: SUCCESS  (20.4s)

[54] Text to Image  (OpenAI key)
     cmd : python cookbook/54_text_to_image/run.py --prompt A serene mountain lake at golden hour, photorealistic
     log : /home/gongai/projects/digital-duck/SPL.py/cookbook/54_text_to_image/logs/text_to_image_20260607_171240.md
     | [text_to_image] → gpt-image-1 (1024x1024, quality=auto) ...
     | [text_to_image] ✓ saved generated_1780866799.png (1508 KB, 17738 ms)
     | 
     | ── Output ───────────────────────────────────────────────────────────
     | Image saved: cookbook/54_text_to_image/outputs/generated_1780866799.png
     | ─────────────────────────────────────────────────────────────────────
     result: SUCCESS  (18.1s)

[58] Image Restyle  (OpenAI + OpenRouter + Ollama)
     cmd : python cookbook/58_image_restyle/run.py --image cookbook/58_image_restyle/sample/photo.jpg --style watercolor painting, soft edges, pastel tones
     log : /home/gongai/projects/digital-duck/SPL.py/cookbook/58_image_restyle/logs/image_restyle_20260607_171240.md
     | [image_restyle] encoded image/jpeg ~23 KB (11 ms)
     | [image_restyle] → Gemma4 vision analysis (gemma4:12b) ...
     | [image_restyle] vision ✓ (32126 ms)
     | [image_restyle] → gpt-image-1 (1024x1024, quality=auto) ...
     | [image_restyle] ✓ saved restyled_1780866831.png (1523 KB, 14752 ms)
     | 
     | ── Text output (vision analysis) ────────────────────────────────────
     | Description:   A minimalist graphic illustration featuring three stylized mountains with snow-capped peaks, a yellow sun in the upper right corner, and an oval-shaped body of water at the base.
     | DALL-E prompt: A delicate watercolor painting of a serene mountain landscape. The composition features three majestic mountains with snow-covered peaks centered in the frame, rendered in soft gray tones. In the upper right corner, a large sun glows in a pale yellow hue against a pastel blue sky. At the base of the mountains lies a calm lake depicted as an elongated oval of soft blue. The style is characterized by soft edges, wet-on-wet watercolor techniques where colors blend gently, and a dreamy, muted pastel color palette.
     | 
     | ── Image output ─────────────────────────────────────────────────────
     | Restyled image: cookbook/58_image_restyle/outputs/restyled_1780866831.png
     | ─────────────────────────────────────────────────────────────────────
     result: SUCCESS  (47.2s)

[64] Parallel News Digest  (Ollama only)
     cmd : spl3 run --model gemma3 --adapter ollama cookbook/64_parallel_news_digest/parallel_news_digest.spl
     log : /home/gongai/projects/digital-duck/SPL.py/cookbook/64_parallel_news_digest/logs/parallel_news_digest_20260607_171240.md
     | INFO:spl.registry:Registry: loaded 2 workflow(s) from cookbook/64_parallel_news_digest/parallel_news_digest.spl
     | Registry: ['parallel_news_digest', 'summarise_single']
     | Running workflow: parallel_news_digest(['model'])
     | [INFO] [parallel_news_digest] digest_model=gemma3
     | [INFO] [parallel_news_digest] topics: "AI and large language models" | "space exploration and astronomy" | "global markets and energy transition"
     | INFO:spl.composer:CALL summarise_single(['topic', 'digest_model', 'log_dir']) INTO @tech_summary
     | INFO:spl.composer:CALL summarise_single(['topic', 'digest_model', 'log_dir']) INTO @sci_summary
     | INFO:spl.composer:CALL summarise_single(['topic', 'digest_model', 'log_dir']) INTO @biz_summary
     | INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
     | INFO:spl.executor:GENERATE segment 1 (summarise_topic) -> 90 tokens, 4710ms
     | INFO:spl.executor:GENERATE chain done -> @summary (564 chars total)
     | INFO:spl.executor:RETURN: 564 chars | none
     | INFO:spl.composer:CALL summarise_single completed: status=complete in 4710ms (1 LLM calls)
     | INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
     | INFO:spl.executor:GENERATE segment 1 (summarise_topic) -> 114 tokens, 6825ms
     | INFO:spl.executor:GENERATE chain done -> @summary (660 chars total)
     | INFO:spl.executor:RETURN: 660 chars | none
     | INFO:spl.composer:CALL summarise_single completed: status=complete in 6826ms (1 LLM calls)
     | INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
     | INFO:spl.executor:GENERATE segment 1 (summarise_topic) -> 117 tokens, 8847ms
     | INFO:spl.executor:GENERATE chain done -> @summary (724 chars total)
     | INFO:spl.executor:RETURN: 724 chars | none
     | INFO:spl.composer:CALL summarise_single completed: status=complete in 8848ms (1 LLM calls)
     | [INFO] [parallel_news_digest] parallel summaries complete — merging into digest
     | INFO:httpx:HTTP Request: POST http://localhost:11434/v1/chat/completions "HTTP/1.1 200 OK"
     | INFO:spl.executor:GENERATE segment 1 (morning_briefing) -> 250 tokens, 4807ms
     | INFO:spl.executor:GENERATE chain done -> @digest (1471 chars total)
     | [INFO] [parallel_news_digest] done | digest_len={len(@digest)}
     | INFO:spl.executor:RETURN: 1471 chars | none
     | 
     | Status:  complete
     | Output:  Good morning, [Senior Leader’s Name]. Here's a quick briefing on key developments across your areas of interest:
     | 
     | **AI & LLM Advancements**
     | The rapid evolution in artificial intelligence continues to accelerate. OpenAI’s GPT-4o is generating significant buzz with its multimodal capabilities – combining text, audio and image processing – while Google pushes forward with Gemini’s application development. While innovation remains robust, discussions surrounding responsible AI deployment and model refinement are paramount.
     | 
     | **Space Exploration & Astronomy**
     | NASA's James Webb Telescope continues to revolutionize our understanding of the universe, providing detailed data on exoplanets and early galaxy formation. Simultaneously, private companies like SpaceX are dramatically increasing space access through rapid launch cadence and development of Starship.  These advancements point toward a future with intensified lunar exploration and broader planetary investigations.
     | 
     | **Global Markets & Energy Transition**
     | Global equity markets remain volatile due to inflation concerns and central bank policies, alongside increased investment in renewable energy projects reaching record highs thanks to government incentives. Despite this shift, market uncertainty persists, coupled with ongoing pressure for accelerated decarbonization strategies. 
     | 
     | Watch today’s meeting regarding the revised Q3 projections – it will be crucial in addressing the evolving market landscape.
     | LLM calls: 4  Latency: 13657ms
     | Log:     /home/gongai/.spl/logs/parallel_news_digest-ollama-20260607-171406.md
     result: SUCCESS  (14.0s)


=== Summary: 4/4 Success  (total 99.7s) ===

ID     Recipe                       Status    Elapsed
--------------------------------------------------------
51     Image Caption                OK          20.4s
54     Text to Image                OK          18.1s
58     Image Restyle                OK          47.2s
64     Parallel News Digest         OK          14.0s

