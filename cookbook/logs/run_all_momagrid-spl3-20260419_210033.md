nohup: ignoring input
=== SPL Cookbook Batch Run — 2026-04-19 21:00:33 ===
    Adapter : momagrid  |  Model : gemma3
    Mode    : parallel  (workers=10)

Submitting 50 recipe(s) with 10 parallel worker(s)...

[01] Hello World  →  started
[02] Ollama Proxy  →  started
[03] Multilingual Greeting  →  started
[04] Model Showdown  →  started
[05] Self-Refine  →  started
[06] ReAct Agent  →  started
[07] Safe Generation  →  started
[08] RAG Query  →  started
[10] Batch Test  →  started
[09] Chain of Thought  →  started
[03] Multilingual Greeting  →  SUCCESS  (2.8s)
[11] Debate Arena  →  started
[01] Hello World  →  SUCCESS  (4.7s)
[12] Plan and Execute  →  started
[08] RAG Query  →  SUCCESS  (6.9s)
[13] Map-Reduce Summarizer  →  started
[02] Ollama Proxy  →  SUCCESS  (14.9s)
[14] Multi-Agent Collaboration  →  started
[06] ReAct Agent  →  FAILED  (19.1s)
[15] Code Review  →  started
[10] Batch Test  →  SUCCESS  (37.4s)
[16] Reflection Agent  →  started
[09] Chain of Thought  →  SUCCESS  (37.4s)
[17] Tree of Thought  →  started
[07] Safe Generation  →  SUCCESS  (45.6s)
[18] Guardrails Pipeline  →  started
[04] Model Showdown  →  SUCCESS  (66.1s)
[19] Memory Conversation  →  started
[14] Multi-Agent Collaboration  →  SUCCESS  (57.9s)
[20] Ensemble Voting  →  started
[11] Debate Arena  →  SUCCESS  (72.0s)
[21] Multi-Model Pipeline  →  started
[18] Guardrails Pipeline  →  SUCCESS  (29.3s)
[22] Text2SPL Demo  →  started
[19] Memory Conversation  →  SUCCESS  (9.4s)
[23] Structured Output  →  started
[23] Structured Output  →  SUCCESS  (4.6s)
[24] Few-Shot Prompting  →  started
[15] Code Review  →  SUCCESS  (61.9s)
[25] Nested Procedures  →  started
[24] Few-Shot Prompting  →  SUCCESS  (6.8s)
[26] Prompt A/B Test  →  started
[13] Map-Reduce Summarizer  →  SUCCESS  (100.6s)
[27] Data Extraction  →  started
[27] Data Extraction  →  SUCCESS  (12.9s)
[28] Customer Support Triage  →  started
[05] Self-Refine  →  SUCCESS  (121.4s)
[29] Meeting Notes to Actions  →  started
[26] Prompt A/B Test  →  SUCCESS  (65.6s)
[30] Code Generator + Tests  →  started
[22] Text2SPL Demo  →  SUCCESS  (111.2s)
[31] Sentiment Pipeline  →  started
[29] Meeting Notes to Actions  →  SUCCESS  (68.2s)
[32] Socratic Tutor  →  started
[21] Multi-Model Pipeline  →  SUCCESS  (122.8s)
[33] Interview Simulator  →  started
[25] Nested Procedures  →  SUCCESS  (128.0s)
[34] Progressive Summarizer  →  started
[28] Customer Support Triage  →  SUCCESS  (99.0s)
[35] Hypothesis Tester  →  started
[31] Sentiment Pipeline  →  SUCCESS  (39.4s)
[36] Tool-Use / Function-Call  →  started
[36] Tool-Use / Function-Call  →  SUCCESS  (12.6s)
[37] Headline News Aggregator  →  started
[16] Reflection Agent  →  SUCCESS  (237.3s)
[41] Human Steering  →  started
[34] Progressive Summarizer  →  SUCCESS  (66.2s)
[42] Knowledge Synthesis  →  started
[42] Knowledge Synthesis  →  SUCCESS  (4.6s)
[43] Prompt Self-Tuning  →  started
[41] Human Steering  →  FAILED  (6.7s)
[44] Adaptive Failover  →  started
[32] Socratic Tutor  →  SUCCESS  (92.3s)
[45] Vision to Action  →  started
[45] Vision to Action  →  SUCCESS  (2.6s)
[47] arXiv Morning Brief  →  started
[37] Headline News Aggregator  →  SUCCESS  (57.8s)
[48] Credit Risk Assessment  →  started
[35] Hypothesis Tester  →  SUCCESS  (77.9s)
[12] Plan and Execute  →  SUCCESS  (292.6s)
[49] Regulatory News Audit  →  started
[50] Code Pipeline  →  started
[47] arXiv Morning Brief  →  SUCCESS  (19.0s)
[51] Image Caption  →  started
[48] Credit Risk Assessment  →  SUCCESS  (15.0s)
[57] Image Format Conversion  →  started
[57] Image Format Conversion  →  SUCCESS  (0.1s)
[63] Parallel Code Review  →  started
[50] Code Pipeline  →  SUCCESS  (15.0s)
[64] Parallel News Digest  →  started
[51] Image Caption  →  SUCCESS  (19.2s)
[44] Adaptive Failover  →  SUCCESS  (43.2s)
[64] Parallel News Digest  →  SUCCESS  (17.0s)
[33] Interview Simulator  →  SUCCESS  (149.4s)
[63] Parallel Code Review  →  SUCCESS  (39.2s)
[49] Regulatory News Audit  →  SUCCESS  (55.8s)
[43] Prompt Self-Tuning  →  SUCCESS  (73.9s)
[30] Code Generator + Tests  →  SUCCESS  (210.7s)
[20] Ensemble Voting  →  SUCCESS  (346.1s)
[17] Tree of Thought  →  SUCCESS  (386.6s)

=== Summary: 48/50 Success  (total 424.0s) ===

ID     Recipe                       Status    Elapsed
--------------------------------------------------------
01     Hello World                  OK           4.7s
02     Ollama Proxy                 OK          14.9s
03     Multilingual Greeting        OK           2.8s
04     Model Showdown               OK          66.1s
05     Self-Refine                  OK         121.4s
06     ReAct Agent                  FAILED      19.1s
07     Safe Generation              OK          45.6s
08     RAG Query                    OK           6.9s
09     Chain of Thought             OK          37.4s
10     Batch Test                   OK          37.4s
11     Debate Arena                 OK          72.0s
12     Plan and Execute             OK         292.6s
13     Map-Reduce Summarizer        OK         100.6s
14     Multi-Agent Collaboration    OK          57.9s
15     Code Review                  OK          61.9s
16     Reflection Agent             OK         237.3s
17     Tree of Thought              OK         386.6s
18     Guardrails Pipeline          OK          29.3s
19     Memory Conversation          OK           9.4s
20     Ensemble Voting              OK         346.1s
21     Multi-Model Pipeline         OK         122.8s
22     Text2SPL Demo                OK         111.2s
23     Structured Output            OK           4.6s
24     Few-Shot Prompting           OK           6.8s
25     Nested Procedures            OK         128.0s
26     Prompt A/B Test              OK          65.6s
27     Data Extraction              OK          12.9s
28     Customer Support Triage      OK          99.0s
29     Meeting Notes to Actions     OK          68.2s
30     Code Generator + Tests       OK         210.7s
31     Sentiment Pipeline           OK          39.4s
32     Socratic Tutor               OK          92.3s
33     Interview Simulator          OK         149.4s
34     Progressive Summarizer       OK          66.2s
35     Hypothesis Tester            OK          77.9s
36     Tool-Use / Function-Call     OK          12.6s
37     Headline News Aggregator     OK          57.8s
41     Human Steering               FAILED       6.7s
42     Knowledge Synthesis          OK           4.6s
43     Prompt Self-Tuning           OK          73.9s
44     Adaptive Failover            OK          43.2s
45     Vision to Action             OK           2.6s
47     arXiv Morning Brief          OK          19.0s
48     Credit Risk Assessment       OK          15.0s
49     Regulatory News Audit        OK          55.8s
50     Code Pipeline                OK          15.0s
51     Image Caption                OK          19.2s
57     Image Format Conversion      OK           0.1s
63     Parallel Code Review         OK          39.2s
64     Parallel News Digest         OK          17.0s

