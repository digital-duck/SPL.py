nohup: ignoring input
=== SPL Cookbook Batch Run — 2026-04-19 20:03:46 ===
    Adapter : momagrid  |  Model : gemma3
    Mode    : parallel  (workers=10)

Submitting 39 recipe(s) with 10 parallel worker(s)...

[01] Hello World  →  started
[02] Ollama Proxy  →  started
[03] Multilingual Greeting  →  started
[06] ReAct Agent  →  started
[05] Self-Refine  →  started
[04] Model Showdown  →  started
[07] Safe Generation  →  started
[08] RAG Query  →  started
[10] Batch Test  →  started
[09] Chain of Thought  →  started
[08] RAG Query  →  FAILED  (300.5s)
[11] Debate Arena  →  started
[02] Ollama Proxy  →  FAILED  (300.5s)
[12] Plan and Execute  →  started
[03] Multilingual Greeting  →  FAILED  (300.5s)
[14] Multi-Agent Collaboration  →  started
[05] Self-Refine  →  FAILED  (300.5s)
[15] Code Review  →  started
[06] ReAct Agent  →  FAILED  (300.5s)
[16] Reflection Agent  →  started
[04] Model Showdown  →  FAILED  (300.5s)
[17] Tree of Thought  →  started
[07] Safe Generation  →  FAILED  (300.5s)
[18] Guardrails Pipeline  →  started
[01] Hello World  →  FAILED  (300.8s)
[10] Batch Test  →  FAILED  (300.8s)
[19] Memory Conversation  →  started
[20] Ensemble Voting  →  started
[09] Chain of Thought  →  FAILED  (301.6s)
[21] Multi-Model Pipeline  →  started
[15] Code Review  →  FAILED  (300.5s)
[22] Text2SPL Demo  →  started
[18] Guardrails Pipeline  →  FAILED  (300.6s)
[23] Structured Output  →  started
[11] Debate Arena  →  FAILED  (300.6s)
[24] Few-Shot Prompting  →  started
[19] Memory Conversation  →  FAILED  (300.4s)
[25] Nested Procedures  →  started
[17] Tree of Thought  →  FAILED  (300.7s)
[26] Prompt A/B Test  →  started
[16] Reflection Agent  →  FAILED  (300.7s)
[27] Data Extraction  →  started
[20] Ensemble Voting  →  FAILED  (300.4s)
[28] Customer Support Triage  →  started
[14] Multi-Agent Collaboration  →  FAILED  (300.7s)
[29] Meeting Notes to Actions  →  started
[12] Plan and Execute  →  FAILED  (300.8s)
[30] Code Generator + Tests  →  started
[21] Multi-Model Pipeline  →  FAILED  (301.6s)
[31] Sentiment Pipeline  →  started
[22] Text2SPL Demo  →  SUCCESS  (14.8s)
[32] Socratic Tutor  →  started
[27] Data Extraction  →  FAILED  (301.2s)
[33] Interview Simulator  →  started
[28] Customer Support Triage  →  FAILED  (301.2s)
[34] Progressive Summarizer  →  started
[24] Few-Shot Prompting  →  FAILED  (301.5s)
[35] Hypothesis Tester  →  started
[29] Meeting Notes to Actions  →  FAILED  (301.4s)
[45] Vision to Action  →  started
[23] Structured Output  →  FAILED  (301.8s)
[05_v3] Self-Refine  →  started
[30] Code Generator + Tests  →  FAILED  (301.6s)
[50] Code Pipeline  →  started
[25] Nested Procedures  →  FAILED  (301.8s)
[63] Parallel Code Review  →  started
[26] Prompt A/B Test  →  FAILED  (302.0s)
[64] Parallel News Digest  →  started
[31] Sentiment Pipeline  →  FAILED  (301.4s)
[32] Socratic Tutor  →  FAILED  (301.4s)
[34] Progressive Summarizer  →  FAILED  (300.6s)
[33] Interview Simulator  →  FAILED  (300.6s)
[05_v3] Self-Refine  →  FAILED  (300.3s)
[63] Parallel Code Review  →  FAILED  (300.6s)
[45] Vision to Action  →  SUCCESS  (301.1s)
[35] Hypothesis Tester  →  SUCCESS  (301.1s)
[64] Parallel News Digest  →  FAILED  (300.8s)
[50] Code Pipeline  →  SUCCESS  (301.6s)

=== Summary: 4/39 Success  (total 1204.5s) ===

ID     Recipe                       Status    Elapsed
--------------------------------------------------------
01     Hello World                  FAILED     300.8s
02     Ollama Proxy                 FAILED     300.5s
03     Multilingual Greeting        FAILED     300.5s
04     Model Showdown               FAILED     300.5s
05     Self-Refine                  FAILED     300.5s
05_v3  Self-Refine                  FAILED     300.3s
06     ReAct Agent                  FAILED     300.5s
07     Safe Generation              FAILED     300.5s
08     RAG Query                    FAILED     300.5s
09     Chain of Thought             FAILED     301.6s
10     Batch Test                   FAILED     300.8s
11     Debate Arena                 FAILED     300.6s
12     Plan and Execute             FAILED     300.8s
14     Multi-Agent Collaboration    FAILED     300.7s
15     Code Review                  FAILED     300.5s
16     Reflection Agent             FAILED     300.7s
17     Tree of Thought              FAILED     300.7s
18     Guardrails Pipeline          FAILED     300.6s
19     Memory Conversation          FAILED     300.4s
20     Ensemble Voting              FAILED     300.4s
21     Multi-Model Pipeline         FAILED     301.6s
22     Text2SPL Demo                OK          14.8s
23     Structured Output            FAILED     301.8s
24     Few-Shot Prompting           FAILED     301.5s
25     Nested Procedures            FAILED     301.8s
26     Prompt A/B Test              FAILED     302.0s
27     Data Extraction              FAILED     301.2s
28     Customer Support Triage      FAILED     301.2s
29     Meeting Notes to Actions     FAILED     301.4s
30     Code Generator + Tests       FAILED     301.6s
31     Sentiment Pipeline           FAILED     301.4s
32     Socratic Tutor               FAILED     301.4s
33     Interview Simulator          FAILED     300.6s
34     Progressive Summarizer       FAILED     300.6s
35     Hypothesis Tester            OK         301.1s
45     Vision to Action             OK         301.1s
50     Code Pipeline                OK         301.6s
63     Parallel Code Review         FAILED     300.6s
64     Parallel News Digest         FAILED     300.8s

