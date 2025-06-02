![Under Construction](https://img.shields.io/badge/status-under--construction-orange?logo=semantic-release&logoColor=white)
* There may be certain files missing as we are building out this repo in the next week. Plesae be patient with us!
  
# MedCaseReasoning

**An open-access benchmark and pipeline for evaluating and improving clinical diagnostic reasoning in large language models.**

[![HuggingFace](https://img.shields.io/badge/Dataset-HuggingFace-blue)](https://huggingface.co/datasets/zou-lab/MedCaseReasoning)
[![Paper](https://arxiv.org/abs/2505.11733)
[![License](https://img.shields.io/badge/License-CC--BY_4.0-green)](#license)

---

## ✨ What’s inside?

| Split | # Cases | Purpose |
|-------|--------:|---------|
| **train** | 13,092 | Supervised fine-tuning & analysis |
| **test**  |   897 | Model-agnostic evaluation (diagnostic accuracy & reasoning recall) |

*Total*: **14,489 clinician-authored diagnostic cases** spanning 30+ medical specialties.

Each example contains

* `case_prompt` – the patient presentation **before** a differential is made  
* `diagnostic_reasoning` – numbered reasoning statements (with quotes from the article)  
* `final_diagnosis` – single gold-standard diagnosis label  

Prompts are ~2.5× longer than typical short-vignette datasets (e.g. MedQA, MMLU), mimicking real ward notes.

---

## 🔧 Repository structure
<pre>
.
├── prompts.py               # all prompt templates used in the paper
├── download_pmc.py          # ① bulk PMC OA downloader
├── get_case_report_pmcids.py# ② fetch case-report PMCIDs
├── process_pmc.py           # ③ parallel extractor for candidate XML
├── extract_metadata.py      # ④ structured metadata
├── extract_text.py          # ⑤ clean XML → text
├── stitch_reasoning.py      # bullets → fluent reasoning trace
├── evaluate.py              # diagnostic accuracy & reasoning-recall runner
└── finetune/
    ├── train_sft.py         # supervised fine-tuning recipe
    └── configs/
</pre>

---

## 🚀 Quick start

### 1. Install

```bash
git clone https://github.com/kevinwu23/MedCaseReasoning.git
cd MedCaseReasoning
conda env create -f environment.yml
conda activate medcase
```

### 2. Load the dataset
```python
from datasets import load_dataset
ds = load_dataset("zou-lab/MedCaseReasoning", "all")  # or "train" / "test"
```
### 3. Evaluate an LLM
```bash
python evaluate.py \
    --model deepseek-ai/deepseek-llm-7b-chat \
    --shots 10 \
    --save results.json
```
evaluate.py reports:
	•	Diagnostic accuracy (1/5/10-shot, LLM-as-judge)
	•	Reasoning recall – percentage of ground-truth reasoning points covered by the model trace

### 4. Fine-tune
```bash
python finetune/train_sft.py \
    --base_model "Qwen/Qwen2-7B-Instruct" \
    --train_file data/medcase_reasoning_train.jsonl \
    --eval_file  data/medcase_reasoning_test.jsonl \
    --config finetune/configs/sft_default.yaml
```

### 🧑‍🔬 Reproducing the dataset

Run the pipeline end-to-end for full provenance:
#### 1.	Download bulk PMC XML
```bash
python download_pmc.py --year-from 2024
```

#### 2.	Identify case-report PMCIDs
```bash
python get_case_report_pmcids.py \
    --start-date 2015/01/01 \
    --email you@domain.com
```

#### 3.	Extract matching XML
```bash
python process_pmc.py
```

#### 4. Build JSONL dataset
```bash
python extract_metadata.py
python extract_text.py
python stitch_reasoning.py
```

### 📄 Citation

```bibtex
@inproceedings{wu2025medcase,
  title     = {MedCaseReasoning: Evaluating and Learning Diagnostic Reasoning from Clinical Case Reports},
  author    = {Wu, Kevin and Wu, Eric and Thapa, Rahul and others},
  booktitle = {NeurIPS},
  year      = {2025},
  url       = {https://github.com/kevinwu23/MedCaseReasoning}
}
```

🔒 License
	•	Code — MIT
	•	Dataset — CC-BY 4.0 (derived from the PMC Open Access Subset)
	•	Model checkpoints — see individual model cards

For questions, open an issue or email stanfordmedeval@gmail.com.
