# MolSC

**MolSC: Leveraging Substituent Contributions to Enhance Fine-grained Molecular Understanding in LLMs**

<p align="left">
  <a href="https://2026.emnlp.org/"><img src="https://img.shields.io/badge/EMNLP%202026-Main-blue.svg" alt="EMNLP 2026 Main"></a>
  <a href="https://drive.google.com/drive/folders/1pYA3kC6dNbHntTIAn2buA0_hnEKPUzFf?usp=sharing"><img src="https://img.shields.io/badge/Data-Google%20Drive-4285F4.svg" alt="Data"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-green.svg" alt="License"></a>
</p>

> Official code and data for our paper accepted to **EMNLP 2026 (Main Conference)**.

## Data

Training and evaluation data are available here:
[Google Drive](https://drive.google.com/drive/folders/1pYA3kC6dNbHntTIAn2buA0_hnEKPUzFf?usp=sharing)

## Training

We use [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) for training.
For requirements and installation, please refer to the LLaMA-Factory repository.

`mol_sft.yaml`:

```yaml
### model
model_name_or_path: meta-llama/Llama-3.2-1B-Instruct
trust_remote_code: true

### method
stage: sft
do_train: true
finetuning_type: lora
lora_rank: 64
lora_alpha: 128
lora_target: all

### dataset
dataset: mol_sft_full
template: llama3
cutoff_len: 4096
max_samples: 9999999999
overwrite_cache: true
preprocessing_num_workers: 16
dataloader_num_workers: 4

### output
output_dir: saves/llama3-1b/lora/mol_sft
logging_steps: 10
save_steps: 1000
plot_loss: true
overwrite_output_dir: true
save_only_model: false
report_to: wandb

### train
per_device_train_batch_size: 1
gradient_accumulation_steps: 8
learning_rate: 1.0e-4
num_train_epochs: 6.0
lr_scheduler_type: cosine
warmup_ratio: 0.1
bf16: true
ddp_timeout: 180000000
resume_from_checkpoint: null

flash_attn: fa2
packing: true
neat_packing: true
```

```bash
llamafactory-cli train mol_sft.yaml
```

## Evaluation

Inference examples and the evaluation code are in the `MolSC-Bench` folder.

```
MolSC-Bench/
├── eval_molsc_bench.py                 # evaluation script
├── task1_with_gpt_responses.json       # inference examples (GPT-5.2)
├── task2_with_gpt_responses.json
├── task1_with_gemini_responses.json    # inference examples (Gemini-3-Flash)
└── task2_with_gemini_responses.json
```

Each entry keeps the benchmark fields (`prompt`, `gt`, ...) together with the
model output in `response`. To evaluate your own outputs, save them in the same
format and run:

```bash
python MolSC-Bench/eval_molsc_bench.py \
    task1_with_your_model_responses.json \
    task2_with_your_model_responses.json
```

Files whose names contain `task1` are scored with the Task 1 metrics, and all
others with the Task 2 metrics:

| Task | Metrics |
| --- | --- |
| Task 1: Property Profiling | SR (%), propMAE ↓, alertAcc ↑, bioMAE ↓ |
| Task 2: Substituent Contribution Prediction | SR (%), ΔpropMAE ↓, ΔalertAcc ↑, ΔbioMAE ↓, dirAcc ↑ |
