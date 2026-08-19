# 5 Training

5 Training
This section describes the training regime for our models.
5.1 Training Data and Batching
We trained on the standard WMT 2014 English-German dataset consisting of about 4.5 million
sentence pairs. Sentences were encoded using byte-pair encoding [ 3], which has a shared source-
target vocabulary of about 37000 tokens. For English-French, we used the significantly larger WMT
2014 English-French dataset consisting of 36M sentences and split tokens into a 32000 word-piece
vocabulary [38]. Sentence pairs were batched together by approximate sequence length. Each training
batch contained a set of sentence pairs containing approximately 25000 source tokens and 25000
target tokens.
5.2 Hardware and Schedule
We trained our models on one machine with 8 NVIDIA P100 GPUs. For our base models using
the hyperparameters described throughout the paper, each training step took about 0.4 seconds. We
trained the base models for a total of 100,000 steps or 12 hours. For our big models,(described on the
bottom line of table 3), step time was 1.0 seconds. The big models were trained for 300,000 steps
(3.5 days).
5.3 Optimizer
We used the Adam optimizer [20] with β1 = 0.9, β2 = 0.98 and ϵ = 10 −9. We varied the learning
rate over the course of training, according to the formula:
lrate = d−0.5
model · min(step_num−0.5, step_num · warmup_steps−1.5) (3)
This corresponds to increasing the learning rate linearly for the first warmup_steps training steps,
and decreasing it thereafter proportionally to the inverse square root of the step number. We used
warmup_steps = 4000.
5.4 Regularization
We employ three types of regularization during training:
7
Table 2: The Transformer achieves better BLEU scores than previous state-of-the-art models on the
English-to-German and English-to-French newstest2014 tests at a fraction of the training cost.
Model
BLEU Training Cost (FLOPs)
EN-DE EN-FR EN-DE EN-FR
ByteNet [18] 23.75
Deep-Att + PosUnk [39] 39.2 1.0 · 1020
GNMT + RL [38] 24.6 39.92 2.3 · 1019 1.4 · 1020
ConvS2S [9] 25.16 40.46 9.6 · 1018 1.5 · 1020
MoE [32] 26.03 40.56 2.0 · 1019 1.2 · 1020
Deep-Att + PosUnk Ensemble [39] 40.4 8.0 · 1020
GNMT + RL Ensemble [38] 26.30 41.16 1.8 · 1020 1.1 · 1021
ConvS2S Ensemble [9] 26.36 41.29 7.7 · 1019 1.2 · 1021
Transformer (base model) 27.3 38.1 3.3 · 1018
Transformer (big) 28.4 41.8 2.3 · 1019
Residual Dropout We apply dropout [33] to the output of each sub-layer, before it is added to the
sub-layer input and normalized. In addition, we apply dropout to the sums of the embeddings and the
positional encodings in both the encoder and decoder stacks. For the base model, we use a rate of
Pdrop = 0.1.
Label Smoothing During training, we employed label smoothing of value ϵls = 0 .1 [36]. This
hurts perplexity, as the model learns to be more unsure, but improves accuracy and BLEU score.