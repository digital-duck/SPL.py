=== SPL Cookbook Batch Run — 2026-04-19 20:08:30 ===
    Adapter : momagrid  |  Model : gemma3
    Mode    : parallel  (workers=10)

Submitting 44 recipe(s) with 10 parallel worker(s)...

[01] Hello World  →  started
[02] Ollama Proxy  →  started
[03] Multilingual Greeting  →  started
[04] Model Showdown  →  started
[05] Self-Refine  →  started
[06] ReAct Agent  →  started
[07] Safe Generation  →  started
[09] Chain of Thought  →  started
[10] Batch Test  →  started
[11] Debate Arena  →  started
[06] ReAct Agent  →  SUCCESS  (4.5s)
[12] Plan and Execute  →  started
[02] Ollama Proxy  →  SUCCESS  (4.5s)
[13] Map-Reduce Summarizer  →  started
[03] Multilingual Greeting  →  SUCCESS  (4.7s)
[14] Multi-Agent Collaboration  →  started
[01] Hello World  →  SUCCESS  (8.5s)
[15] Code Review  →  started
[07] Safe Generation  →  SUCCESS  (52.6s)
[16] Reflection Agent  →  started
[13] Map-Reduce Summarizer  →  SUCCESS  (56.5s)
[17] Tree of Thought  →  started
[09] Chain of Thought  →  SUCCESS  (67.2s)
[18] Guardrails Pipeline  →  started
[18] Guardrails Pipeline  →  SUCCESS  (14.8s)
[20] Ensemble Voting  →  started
[10] Batch Test  →  SUCCESS  (82.5s)
[21] Multi-Model Pipeline  →  started
[14] Multi-Agent Collaboration  →  SUCCESS  (87.2s)
[23] Structured Output  →  started
[04] Model Showdown  →  SUCCESS  (102.3s)
[24] Few-Shot Prompting  →  started
[24] Few-Shot Prompting  →  SUCCESS  (15.1s)
[25] Nested Procedures  →  started
[23] Structured Output  →  SUCCESS  (25.5s)
[26] Prompt A/B Test  →  started
[16] Reflection Agent  →  SUCCESS  (74.7s)
[27] Data Extraction  →  started
[17] Tree of Thought  →  SUCCESS  (70.9s)
[28] Customer Support Triage  →  started
[27] Data Extraction  →  SUCCESS  (6.4s)
[29] Meeting Notes to Actions  →  started
[25] Nested Procedures  →  SUCCESS  (35.1s)
[30] Code Generator + Tests  →  started
[21] Multi-Model Pipeline  →  SUCCESS  (77.0s)
[31] Sentiment Pipeline  →  started
[29] Meeting Notes to Actions  →  SUCCESS  (40.0s)
[32] Socratic Tutor  →  started
[31] Sentiment Pipeline  →  SUCCESS  (29.1s)
[33] Interview Simulator  →  started
[05] Self-Refine  →  SUCCESS  (211.5s)
[34] Progressive Summarizer  →  started
[26] Prompt A/B Test  →  SUCCESS  (96.2s)
[35] Hypothesis Tester  →  started
[11] Debate Arena  →  SUCCESS  (237.1s)
[36] Tool-Use / Function-Call  →  started
[20] Ensemble Voting  →  SUCCESS  (165.1s)
[37] Headline News Aggregator  →  started
[28] Customer Support Triage  →  SUCCESS  (125.7s)
[42] Knowledge Synthesis  →  started
[36] Tool-Use / Function-Call  →  SUCCESS  (24.8s)
[43] Prompt Self-Tuning  →  started
[42] Knowledge Synthesis  →  SUCCESS  (4.2s)
[44] Adaptive Failover  →  started
[34] Progressive Summarizer  →  SUCCESS  (65.3s)
[45] Vision to Action  →  started
[32] Socratic Tutor  →  SUCCESS  (105.2s)
[48] Credit Risk Assessment  →  started
[33] Interview Simulator  →  SUCCESS  (96.4s)
[49] Regulatory News Audit  →  started
[45] Vision to Action  →  SUCCESS  (20.8s)
[05_v3] Self-Refine  →  started
[48] Credit Risk Assessment  →  SUCCESS  (20.8s)
[50] Code Pipeline  →  started
[37] Headline News Aggregator  →  SUCCESS  (63.2s)
[63] Parallel Code Review  →  started
[50] Code Pipeline  →  SUCCESS  (12.8s)
[64] Parallel News Digest  →  started
[30] Code Generator + Tests  →  SUCCESS  (180.7s)
[44] Adaptive Failover  →  SUCCESS  (87.8s)
[43] Prompt Self-Tuning  →  SUCCESS  (92.2s)
[64] Parallel News Digest  →  SUCCESS  (43.4s)
[63] Parallel Code Review  →  SUCCESS  (56.2s)
[49] Regulatory News Audit  →  SUCCESS  (83.7s)
[15] Code Review  →  SUCCESS  (385.2s)
[35] Hypothesis Tester  →  SUCCESS  (196.5s)
[05_v3] Self-Refine  →  SUCCESS  (127.7s)
[12] Plan and Execute  →  SUCCESS  (572.5s)

=== Summary: 44/44 Success  (total 577.0s) ===

ID     Recipe                       Status    Elapsed
--------------------------------------------------------
01     Hello World                  OK           8.5s
02     Ollama Proxy                 OK           4.5s
03     Multilingual Greeting        OK           4.7s
04     Model Showdown               OK         102.3s
05     Self-Refine                  OK         211.5s
05_v3  Self-Refine                  OK         127.7s
06     ReAct Agent                  OK           4.5s
07     Safe Generation              OK          52.6s
09     Chain of Thought             OK          67.2s
10     Batch Test                   OK          82.5s
11     Debate Arena                 OK         237.1s
12     Plan and Execute             OK         572.5s
13     Map-Reduce Summarizer        OK          56.5s
14     Multi-Agent Collaboration    OK          87.2s
15     Code Review                  OK         385.2s
16     Reflection Agent             OK          74.7s
17     Tree of Thought              OK          70.9s
18     Guardrails Pipeline          OK          14.8s
20     Ensemble Voting              OK         165.1s
21     Multi-Model Pipeline         OK          77.0s
23     Structured Output            OK          25.5s
24     Few-Shot Prompting           OK          15.1s
25     Nested Procedures            OK          35.1s
26     Prompt A/B Test              OK          96.2s
27     Data Extraction              OK           6.4s
28     Customer Support Triage      OK         125.7s
29     Meeting Notes to Actions     OK          40.0s
30     Code Generator + Tests       OK         180.7s
31     Sentiment Pipeline           OK          29.1s
32     Socratic Tutor               OK         105.2s
33     Interview Simulator          OK          96.4s
34     Progressive Summarizer       OK          65.3s
35     Hypothesis Tester            OK         196.5s
36     Tool-Use / Function-Call     OK          24.8s
37     Headline News Aggregator     OK          63.2s
42     Knowledge Synthesis          OK           4.2s
43     Prompt Self-Tuning           OK          92.2s
44     Adaptive Failover            OK          87.8s
45     Vision to Action             OK          20.8s
48     Credit Risk Assessment       OK          20.8s
49     Regulatory News Audit        OK          83.7s
50     Code Pipeline                OK          12.8s
63     Parallel Code Review         OK          56.2s
64     Parallel News Digest         OK          43.4s

