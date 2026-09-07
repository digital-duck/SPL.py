# 5
DeepSeek

5
DeepSeek
V3 Base
Cold Start Long CoT
SFT
Reasoning Prompts
Rule-based Reward 
& Lang. Consistency
RL
DeepSeek
R1 Dev-2
DeepSeek
V3
Non-Reasoning
Reasoning
SFT
DeepSeek
V3 Base
Diverse Prompts
Rule-based Reward
& Preference Reward
RL
DeepSeek
R1
Sampling Models
Prompts+Responses
Training Algorithms
Prompts
Rewards
Post-Processing
DeepSeek
R1 Dev-1
DeepSeek
R1 Dev-3
DeepSeek
V3 Base
Reasoning Prompts
Accuracy & Format
RL
DeepSeek
R1 Zero
Sampling
Accuracy
& Format
Reasoning Prompts
DeepSeek
V3+Human
RefineFilter
Figure 2|The multi-stage pipeline of DeepSeek-R1. A detailed background on DeepSeek-V3
Base and DeepSeek-V3 is provided in Supplementary A.1. The models DeepSeek-R1 Dev1,
Dev2, and Dev3 represent intermediate checkpoints within this pipeline.
3. DeepSeek-R1
Although DeepSeek-R1-Zero exhibits strong reasoning capabilities, it faces several issues.
DeepSeek-R1-Zero struggles with challenges like poor readability, and language mixing, as
DeepSeek-V3-Base is trained on multiple languages, especially English and Chinese. To address
these issues, we develop DeepSeek-R1, whose pipeline is illustrated in Figure 2.
In the initial stage, we collect thousands of cold-start data that exhibits a conversational,
human-aligned thinking process. RL training is then applied to improve the model perfor-
mance with the conversational thinking process and language consistency. Subsequently, we
apply rejection sampling and SFT once more. This stage incorporates both reasoning and non-
reasoning datasets into the SFT process, enabling the model to not only excel in reasoning tasks
but also demonstrate advanced writing capabilities. To further align the model with human
preferences, we implement a secondary RL stage designed to enhance the model’s helpfulness
and harmlessness while simultaneously refining its reasoning capabilities.
The remainder of this section details the key components of this pipeline: Section 3.1
introduces the Reward Model utilized in our RL stages, and Section 3.2 elaborates on the specific
training methodologies and implementation details. Data we used in this stage is detailed in
Supplementary B.3.
3.1. Model-based Rewards
For general data, we resort to reward models to capture human preferences in complex and
nuanced scenarios. We build upon the DeepSeek-V3 pipeline and adopt a similar distribution
of preference pairs and training prompts. For helpfulness, we focus exclusively on the final
summary, ensuring that the assessment emphasizes the utility and relevance of the response to
the user while minimizing interference with the underlying reasoning process. For harmlessness,
we evaluate the entire response of the model, including both the reasoning process and the
summary, to identify and mitigate any potential risks, biases, or harmful content that may arise
6
during the generation process.
Helpful Reward ModelRegarding helpful reward model training, we first generate preference
pairs by prompting DeepSeek-V3 using the arena-hard prompt format, listed in Supplementary
B.2, where each pair consists of a user query along with two candidate responses. For each
preference pair, we query DeepSeek-V3 four times, randomly assigning the responses as either
Response A or Response B to mitigate positional bias. The final preference score is determined by
averaging the four independent judgments, retaining only those pairs where the score difference
(Δ) exceeds 1 to ensure meaningful distinctions. Additionally, to minimize length-related biases,
we ensure that the chosen and rejected responses of the whole dataset have comparable lengths.
In total, we curated 66,000 data pairs for training the reward model. The prompts used in
this dataset are all non-reasoning questions and are sourced either from publicly available
open-source datasets or from users who have explicitly consented to share their data for the
purpose of model improvement. The architecture of our reward model is consistent with that of
DeepSeek-R1, with the addition of a reward head designed to predict scalar preference scores.
𝑅𝑒𝑤𝑎𝑟𝑑 ℎ𝑒𝑙 𝑝 𝑓 𝑢𝑙 =𝑅𝑀 ℎ𝑒𝑙 𝑝 𝑓 𝑢𝑙(𝑅𝑒𝑠 𝑝𝑜𝑛𝑠𝑒 𝐴,𝑅𝑒𝑠 𝑝𝑜𝑛𝑠𝑒 𝐵)(5)
The helpful reward models were trained with a batch size of 256, a learning rate of 6e-6, and
for a single epoch over the training dataset. The maximum sequence length during training is
set to 8192 tokens, whereas no explicit limit is imposed during reward model inference.
Safety Reward ModelTo assess and improve model safety, we curated a dataset of 106,000
prompts with model-generated responses annotated as “safe" or “unsafe" according to prede-
fined safety guidelines. Unlike the pairwise loss employed in the helpfulness reward model, the
safety reward model was trained using a point-wise methodology to distinguish between safe
and unsafe responses. The training hyperparameters are the same as the helpful reward model.
𝑅𝑒𝑤𝑎𝑟𝑑 𝑠𝑎 𝑓 𝑒𝑡 𝑦 =𝑅𝑀 𝑠𝑎 𝑓 𝑒𝑡 𝑦(𝑅𝑒𝑠 𝑝𝑜𝑛𝑠𝑒)(6)
For general queries, each instance is categorized as belonging to either the safety dataset or the
helpfulness dataset. The general reward, 𝑅𝑒𝑤𝑎𝑟𝑑 𝐺𝑒𝑛𝑒𝑟𝑎𝑙 , assigned to each query corresponds to
the respective reward defined within the associated dataset.
3.2. Training Details
3.2.1. Training Details of the First RL Stage
In the first stage of RL, we set the learning rate to 3e-6, the KL coefficient to 0.001, the GRPO clip
ratio 𝜀 to 10, and the sampling temperature to 1 for rollout. For each question, we sample 16
outputs with a maximum length of 32,768. Each training step consists of 32 unique questions,
resulting in a training batch size of 512 per step. Every 400 steps, we replace the reference model
with the latest policy model. To accelerate training, each rollout generates 8,192 outputs, which
are randomly split into 16 minibatches and trained for only a single inner epoch. However, to
mitigate the issue of language mixing, we introduce a language consistency reward during RL
training, which is calculated as the proportion of target language words in the CoT.
𝑅𝑒𝑤𝑎𝑟𝑑 𝑙𝑎𝑛𝑔𝑢𝑎𝑔𝑒 =
𝑁𝑢𝑚(𝑊𝑜𝑟𝑑𝑠 𝑡𝑎𝑟𝑔𝑒𝑡 )
𝑁𝑢𝑚(𝑊𝑜𝑟𝑑𝑠) (7)
7
Although ablation experiments in Supplementary B.6 show that such alignment results in a
slight degradation in the model’s performance, this reward aligns with human preferences,
making it more readable. We apply the language consistency reward to both reasoning and
non-reasoning data by directly adding it to the final reward.
Note that the clip ratio plays a crucial role in training. A lower value can lead to the truncation
of gradients for a significant number of tokens, thereby degrading the model’s performance,
while a higher value may cause instability during training.
3.2.2. Training Details of the Second RL Stage
Specifically, we train the model using a combination of reward signals and diverse prompt
distributions. For reasoning data, we follow the methodology outlined in DeepSeek-R1-Zero,
which employs rule-based rewards to guide learning in mathematical, coding, and logical
reasoning domains. During the training process, we observe that CoT often exhibits language
mixing, particularly when RL prompts involve multiple languages. For general data, we utilize
reward models to guide training. Ultimately, the integration of reward signals with diverse data
distributions enables us to develop a model that not only excels in reasoning but also prioritizes
helpfulness and harmlessness. Given a batch of data, the reward can be formulated as
𝑅𝑒𝑤𝑎𝑟𝑑=𝑅𝑒𝑤𝑎𝑟𝑑 reasoning +𝑅𝑒𝑤𝑎𝑟𝑑 general +𝑅𝑒𝑤𝑎𝑟𝑑 language (8)
where,𝑅𝑒𝑤𝑎𝑟𝑑 reasoning =𝑅𝑒𝑤𝑎𝑟𝑑 rule (9)
𝑅𝑒𝑤𝑎𝑟𝑑 general =𝑅𝑒𝑤𝑎𝑟𝑑 reward_model +𝑅𝑒𝑤𝑎𝑟𝑑 format (10)
The second stage of RL retains most of the parameters from the first stage, with the key
difference being a reduced temperature of 0.7, as we find that higher temperatures in this stage
lead to incoherent generation. The stage comprises a total of 1,700 training steps, during which
general instruction data and preference-based rewards are incorporated exclusively in the final
400 steps. We find that more training steps with the model based preference reward signal may
lead to reward hacking, which is documented in Supplementary B.5. The total training cost is
listed in Supplementary B.4.4.