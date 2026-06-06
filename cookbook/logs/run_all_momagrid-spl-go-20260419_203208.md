=== SPL Cookbook Batch Run — 2026-04-19 20:32:09 ===
    Adapter : momagrid  |  Model : gemma3
    Mode    : parallel  (workers=10)

Submitting 39 recipe(s) with 10 parallel worker(s)...

[01] Hello World  →  started
[02] Ollama Proxy  →  started
[03] Multilingual Greeting  →  started
[05] Self-Refine  →  started
[04] Model Showdown  →  started
[06] ReAct Agent  →  started
[07] Safe Generation  →  started
[08] RAG Query  →  started
[09] Chain of Thought  →  started
[10] Batch Test  →  started
[08] RAG Query  →  SUCCESS  (4.1s)
[11] Debate Arena  →  started
[02] Ollama Proxy  →  SUCCESS  (4.4s)
[12] Plan and Execute  →  started
[03] Multilingual Greeting  →  SUCCESS  (4.4s)
[14] Multi-Agent Collaboration  →  started
[01] Hello World  →  SUCCESS  (8.5s)
[15] Code Review  →  started
[07] Safe Generation  →  SUCCESS  (26.0s)
[16] Reflection Agent  →  started
[10] Batch Test  →  SUCCESS  (29.3s)
[17] Tree of Thought  →  started
[06] ReAct Agent  →  SUCCESS  (33.6s)
[18] Guardrails Pipeline  →  started
[09] Chain of Thought  →  SUCCESS  (39.6s)
[19] Memory Conversation  →  started
[04] Model Showdown  →  SUCCESS  (74.4s)
[20] Ensemble Voting  →  started
[19] Memory Conversation  →  SUCCESS  (61.6s)
[21] Multi-Model Pipeline  →  started
[16] Reflection Agent  →  SUCCESS  (75.5s)
[22] Text2SPL Demo  →  started
[22] Text2SPL Demo  →  SUCCESS  (18.8s)
[23] Structured Output  →  started
[23] Structured Output  →  SUCCESS  (14.3s)
[24] Few-Shot Prompting  →  started
[18] Guardrails Pipeline  →  SUCCESS  (118.7s)
[25] Nested Procedures  →  started
[05] Self-Refine  →  SUCCESS  (172.1s)
[26] Prompt A/B Test  →  started
[24] Few-Shot Prompting  →  SUCCESS  (45.1s)
[27] Data Extraction  →  started
[14] Multi-Agent Collaboration  →  SUCCESS  (176.2s)
[28] Customer Support Triage  →  started
[21] Multi-Model Pipeline  →  SUCCESS  (80.0s)
[29] Meeting Notes to Actions  →  started
[27] Data Extraction  →  SUCCESS  (22.3s)
[30] Code Generator + Tests  →  started
[11] Debate Arena  →  SUCCESS  (206.0s)
[31] Sentiment Pipeline  →  started
[28] Customer Support Triage  →  SUCCESS  (71.6s)
[32] Socratic Tutor  →  started
[12] Plan and Execute  →  SUCCESS  (269.3s)
[33] Interview Simulator  →  started
[15] Code Review  →  SUCCESS  (265.2s)
[34] Progressive Summarizer  →  started
[26] Prompt A/B Test  →  SUCCESS  (134.0s)
[35] Hypothesis Tester  →  started
[25] Nested Procedures  →  SUCCESS  (169.7s)
[45] Vision to Action  →  started
[45] Vision to Action  →  SUCCESS  (12.3s)
[05_v3] Self-Refine  →  started
[17] Tree of Thought  →  SUCCESS  (316.3s)
[50] Code Pipeline  →  started
[34] Progressive Summarizer  →  SUCCESS  (93.2s)
[63] Parallel Code Review  →  started
[50] Code Pipeline  →  SUCCESS  (32.7s)
[64] Parallel News Digest  →  started
[63] Parallel Code Review  →  SUCCESS  (34.7s)
[31] Sentiment Pipeline  →  SUCCESS  (198.5s)
[29] Meeting Notes to Actions  →  SUCCESS  (234.8s)
[64] Parallel News Digest  →  SUCCESS  (38.9s)
[20] Ensemble Voting  →  SUCCESS  (342.8s)
[32] Socratic Tutor  →  SUCCESS  (177.6s)
[35] Hypothesis Tester  →  SUCCESS  (136.6s)
[30] Code Generator + Tests  →  SUCCESS  (247.6s)
[05_v3] Self-Refine  →  SUCCESS  (155.3s)
[33] Interview Simulator  →  FAILED  (277.0s)

=== Summary: 38/39 Success  (total 550.8s) ===

ID     Recipe                       Status    Elapsed
--------------------------------------------------------
01     Hello World                  OK           8.5s
02     Ollama Proxy                 OK           4.4s
03     Multilingual Greeting        OK           4.4s
04     Model Showdown               OK          74.4s
05     Self-Refine                  OK         172.1s
05_v3  Self-Refine                  OK         155.3s
06     ReAct Agent                  OK          33.6s
07     Safe Generation              OK          26.0s
08     RAG Query                    OK           4.1s
09     Chain of Thought             OK          39.6s
10     Batch Test                   OK          29.3s
11     Debate Arena                 OK         206.0s
12     Plan and Execute             OK         269.3s
14     Multi-Agent Collaboration    OK         176.2s
15     Code Review                  OK         265.2s
16     Reflection Agent             OK          75.5s
17     Tree of Thought              OK         316.3s
18     Guardrails Pipeline          OK         118.7s
19     Memory Conversation          OK          61.6s
20     Ensemble Voting              OK         342.8s
21     Multi-Model Pipeline         OK          80.0s
22     Text2SPL Demo                OK          18.8s
23     Structured Output            OK          14.3s
24     Few-Shot Prompting           OK          45.1s
25     Nested Procedures            OK         169.7s
26     Prompt A/B Test              OK         134.0s
27     Data Extraction              OK          22.3s
28     Customer Support Triage      OK          71.6s
29     Meeting Notes to Actions     OK         234.8s
30     Code Generator + Tests       OK         247.6s
31     Sentiment Pipeline           OK         198.5s
32     Socratic Tutor               OK         177.6s
33     Interview Simulator          FAILED     277.0s
34     Progressive Summarizer       OK          93.2s
35     Hypothesis Tester            OK         136.6s
45     Vision to Action             OK          12.3s
50     Code Pipeline                OK          32.7s
63     Parallel Code Review         OK          34.7s
64     Parallel News Digest         OK          38.9s

