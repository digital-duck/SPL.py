# 4. Experiment

4. Experiment
We evaluate our models on MMLU (Hendrycks et al., 2021), MMLU-Redux (Gema et al., 2025),
MMLU-Pro (Wang et al., 2024), C-Eval (Huang et al., 2023), and CMMLU (Li et al., 2024),
IFEval (Zhou et al., 2023b), FRAMES (Krishna et al., 2024), GPQA Diamond (Rein et al.,
2023), SimpleQA (OpenAI, 2024a), C-SimpleQA (He et al., 2024), SWE-Bench Verified (OpenAI,
2024b), Aider (Gauthier, 2025), LiveCodeBench (Jain et al., 2024) (2024-08 – 2025-01), Codeforces
(Mirzayanov, 2025), Chinese National High School Mathematics Olympiad (CNMO 2024) (CMS,
2024), and American Invitational Mathematics Examination 2024 (AIME 2024) (MAA, 2024).
The details of these benchmarks are listed in Supplementary D.
Table 3 summarizes the performance of DeepSeek-R1 across multiple developmental stages,
as outlined in Figure 2. A comparison between DeepSeek-R1-Zero and DeepSeek-R1 Dev1
reveals substantial improvements in instruction-following, as evidenced by higher scores on
the IF-Eval and ArenaHard benchmarks. However, due to the limited size of the cold-start
dataset, Dev1 exhibits a partial degradation in reasoning performance compared to DeepSeek-
R1-Zero, most notably on the AIME benchmark. In contrast, DeepSeek-R1 Dev2 demonstrates
8
Table 3|Experimental results at each stage of DeepSeek-R1. Numbers in bold denote the
performance is statistically significant (t−test with𝑝 <0.01).
Benchmark(Metric) R1-Zero R1-Dev1 R1-Dev2 R1-Dev3 R1
English
MMLU(EM) 88.8 89.191.291.0 90.8
MMLU-Redux(EM) 85.6 90.0 93.0 93.1 92.9
MMLU-Pro(EM) 68.9 74.1 83.8 83.1 84.0
DROP(3-shot F1) 89.1 89.8 91.1 88.7 92.2
IF-Eval(Prompt Strict) 46.6 71.7 72.0 78.1 83.3
GPQA Diamond(Pass@1) 75.866.1 70.7 71.2 71.5
SimpleQA(Correct) 30.3 17.8 28.2 24.9 30.1
FRAMES(Acc.) 82.3 78.5 81.8 81.9 82.5
AlpacaEval2.0(LC-winrate) 24.7 50.1 55.8 62.1 87.6
ArenaHard(GPT-4-1106) 53.6 77.0 73.2 75.6 92.3
Code
LiveCodeBench(Pass@1-COT) 50.0 57.5 63.5 64.6 65.9
Codeforces(Percentile) 80.4 84.5 90.5 92.1 96.3
Codeforces(Rating) 1444 1534 1687 1746 2029
SWE Verified(Resolved) 43.2 39.6 44.6 45.6 49.2
Aider-Polyglot(Acc.) 12.2 6.7 25.6 44.8 53.3
Math
AIME 2024(Pass@1) 77.9 59.0 74.0 78.1 79.8
MATH-500(Pass@1) 95.9 94.2 95.9 95.4 97.3
CNMO 2024(Pass@1) 88.158.0 73.9 77.3 78.8
Chinese
CLUEWSC(EM) 93.1 92.8 92.6 91.6 92.8
C-Eval(EM) 92.885.7 91.9 86.4 91.8
C-SimpleQA(Correct) 66.4 58.8 64.2 66.9 63.7
marked performance enhancements on benchmarks that require advanced reasoning skills,
including those focused on code generation, mathematical problem solving, and STEM-related
tasks. Benchmarks targeting general-purpose tasks, such as AlpacaEval 2.0, show marginal im-
provement. These results suggest that reasoning-oriented RL considerably enhances reasoning
capabilities while exerting limited influence on user preference-oriented benchmarks.
DeepSeek-R1 Dev3 integrates both reasoning and non-reasoning datasets into the SFT
pipeline, thereby enhancing the model’s proficiency in both reasoning and general language
generation tasks. Compared to Dev2, DeepSeek-R1 Dev3 achieves notable performance im-
provements on AlpacaEval 2.0 and Aider-Polyglot, attributable to the inclusion of large-scale
non-reasoning corpora and code engineering datasets. Finally, comprehensive RL training on
DeepSeek-R1 Dev3 using mixed reasoning-focused and general-purpose data produced the
final DeepSeek-R1. Marginal improvements occurred in code and mathematics benchmarks, as
substantial reasoning-specific RL was done in prior stages. The primary advancements in the
final DeepSeek-R1 were in general instruction-following and user-preference benchmarks, with
AlpacaEval 2.0 improving by 25% and ArenaHard by 17%.
In addition, we compare DeepSeek-R1 with other models in Supplementary D.2. Model
safety evaluations are provided in Supplementary D.3. A comprehensive analysis is provided in
Supplementary E, including a comparison with DeepSeek-V3, performance evaluations on both
fresh test sets, a breakdown of mathematical capabilities by category, and an investigation of
test-time scaling behavior. Supplementary F shows that the strong reasoning capability can be
transferred to smaller models.
9