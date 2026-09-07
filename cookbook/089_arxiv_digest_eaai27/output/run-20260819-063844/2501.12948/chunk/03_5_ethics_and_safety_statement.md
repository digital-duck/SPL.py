# 5. Ethics and Safety Statement

5. Ethics and Safety Statement
With the advancement in the reasoning capabilities of DeepSeek-R1, we deeply recognize
the potential ethical risks. For example, R1 can be subject to jailbreak attacks, leading to the
generation of dangerous content such as explosive manufacturing plans, while the enhanced
reasoning capabilities enable the model to provide plans with better operational feasibility
and executability. Besides, a public model is also vulnerable to further fine-tuning that could
compromise inherent safety protections.
In Supplementary D.3, we present a comprehensive safety report from multiple perspectives,
including performance on open-source and in-house safety evaluation benchmarks, and safety
levels across multiple languages and against jailbreak attacks. These comprehensive safety
analyses conclude that the inherent safety level of the DeepSeek-R1 model, compared to other
state-of-the-art models, is generally at a moderate level (comparable to GPT-4o (2024-05-13)).
Besides, when coupled with the risk control system, the model’s safety level is elevated to a
superior standard.
6. Conclusion, Limitation, and Future Work
We present DeepSeek-R1-Zero and DeepSeek-R1, which rely on large-scale RL to incentivize
model reasoning behaviors. Our results demonstrate that pre-trained checkpoints inherently
possess substantial potential for complex reasoning tasks. We believe that the key to unlocking
this potential lies not in large-scale human annotation but in the provision of hard reasoning
questions, a reliable verifier, and sufficient computational resources for reinforcement learning.
Sophisticated reasoning behaviors, such as self-verification and reflection, appeared to emerge
organically during the reinforcement learning process.
Even if DeepSeek-R1 achieves frontier results on reasoning benchmarks, it still faces several
capability limitations, as outlined below:
Structure Output and Tool Use:Currently, the structural output capabilities of DeepSeek-R1
remain suboptimal compared to existing models. Moreover, DeepSeek-R1 cannot leverage tools,
such as search engines and calculators, to improve the performance of output. However, as it is
not hard to build an RL environment for structure output and tool use, we believe the issue will
be addressed in the next version.
Token efficiency:Unlike conventional test-time computation scaling approaches, such
as majority voting or Monte Carlo Tree Search (MCTS), DeepSeek-R1 dynamically allocates
computational resources during inference according to the complexity of the problem at hand.
Specifically, it uses fewer tokens to solve simple tasks, while generating more tokens for complex
tasks. Nevertheless, there remains room for further optimization in terms of token efficiency, as
instances of excessive reasoning—manifested as overthinking—are still observed in response to
simpler questions.
Language Mixing:DeepSeek-R1 is currently optimized for Chinese and English, which
may result in language mixing issues when handling queries in other languages. For instance,
DeepSeek-R1 might use English for reasoning and responses, even if the query is in a language
other than English or Chinese. We aim to address this limitation in future updates. The limitation
may be related to the base checkpoint, DeepSeek-V3-Base, mainly utilizes Chinese and English,
so that it can achieve better results with the two languages in reasoning.
Prompting Engineering:When evaluating DeepSeek-R1, we observe that it is sensitive to
10
prompts. Few-shot prompting consistently degrades its performance. Therefore, we recommend
users directly describe the problem and specify the output format using a zero-shot setting for
optimal results.
Software Engineering Tasks:Due to the long evaluation times, which impact the efficiency
of the RL process, large-scale RL has not been applied extensively in software engineering tasks.
As a result, DeepSeek-R1 has not demonstrated a huge improvement over DeepSeek-V3 on
software engineering benchmarks. Future versions will address this by implementing rejection
sampling on software engineering data or incorporating asynchronous evaluations during the
RL process to improve efficiency.
Beyond specific capability limitations, the pure RL methodology itself also presents inherent
challenges:
Reward Hacking:The success of pure RL depends on reliable reward signals. In this
study, we ensure reward reliability through a reasoning-domain rule-based reward model (RM).
However, such dependable RMs are difficult to construct for certain tasks, such as writing. If the
reward signal is assigned by a model instead of predefined rules, it becomes more susceptible to
exploitation as training progresses, which means the policy model may find shortcuts to hack
the reward model. Consequently, for complex tasks that cannot be effectively evaluated by a
reliable reward model, scaling up pure RL methods remains an open challenge.
In this work, for tasks that cannot obtain a reliable signal, DeepSeek-R1 uses human anno-
tation to create supervised data, and only conduct RL for hundreds of steps. We hope in the
future, a robust reward model can be obtained to address such issues.
With the advent of pure RL methods like DeepSeek-R1, the future holds immense potential
for solving any task that can be effectively evaluated by a verifier, regardless of its complexity
for humans. Machines equipped with such advanced RL techniques are poised to surpass
human capabilities in these domains, driven by their ability to optimize performance iteratively
through trial and error. However, challenges remain for tasks where constructing a reliable
reward model is inherently difficult. In such cases, the lack of a robust feedback mechanism
may hinder progress, suggesting that future research should focus on developing innovative
approaches to define and refine reward structures for these complex, less verifiable problems.
Furthermore, leveraging tools during the reasoning process holds significant promise.
Whether it’s utilizing tools like compilers or search engines to retrieve or compute necessary
information, or employing external tools—such as biological or chemical reagents, to validate
final results in the real world, this integration of tool-augmented reasoning could dramatically
enhance the scope and accuracy of machine-driven solutions.