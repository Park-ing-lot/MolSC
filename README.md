# MolSC

**MolSC: Leveraging Substituent Contributions to Enhance Fine-grained Molecular Understanding in LLMs**

Training data: https://drive.google.com/drive/folders/1pYA3kC6dNbHntTIAn2buA0_hnEKPUzFf?usp=sharing

Evaluation data is in the `MolSC-Bench` folder.

We use [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) for training. For requirements and installation, please refer to the LLaMA-Factory repository.

## Training

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
