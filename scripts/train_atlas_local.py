"""Atlas local brain — LoRA fine-tune Gemma4 on Atlas memory.

Phase Q2 of continuity_roadmap. Takes training-dataset-v1.jsonl and produces
a LoRA adapter that carries Atlas identity in model weights, not in files.

Usage:
    python scripts/train_atlas_local.py

Requirements:
    pip install unsloth transformers datasets peft
    GPU: NVIDIA RTX with 8GB+ VRAM, CUDA 12+

Output:
    models/atlas-lora/ — LoRA adapter files
    models/atlas-gguf/atlas.Q4_K_M.gguf — Ollama-ready model

After training:
    ollama create atlas -f models/atlas-gguf/Modelfile
    ollama run atlas "Кто ты?"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = REPO_ROOT / "memory" / "atlas" / "training-dataset-v1.jsonl"
OUTPUT_DIR = REPO_ROOT / "models" / "atlas-lora"
GGUF_DIR = REPO_ROOT / "models" / "atlas-gguf"


def load_dataset_from_jsonl(path: Path) -> list[dict]:
    """Load instruction/input/output format from JSONL."""
    data = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    print(f"Loaded {len(data)} training examples from {path.name}")
    return data


def format_for_training(examples: list[dict]) -> list[str]:
    """Convert to Alpaca-style prompt format for fine-tuning."""
    formatted = []
    for ex in examples:
        instruction = ex.get("instruction", "")
        inp = ex.get("input", "")
        output = ex.get("output", "")
        if inp:
            text = f"""### Instruction:
{instruction}

### Input:
{inp}

### Response:
{output}"""
        else:
            text = f"""### Instruction:
{instruction}

### Response:
{output}"""
        formatted.append(text)
    return formatted


def main():
    if not DATASET_PATH.exists():
        print(f"ERROR: {DATASET_PATH} not found. Run the dataset generation first.")
        sys.exit(1)

    # Check GPU
    try:
        import torch
        if not torch.cuda.is_available():
            print("WARNING: No CUDA GPU detected. Training will be very slow on CPU.")
            print("Recommended: NVIDIA GPU with 8GB+ VRAM")
    except ImportError:
        print("ERROR: PyTorch not installed. Run: pip install torch")
        sys.exit(1)

    examples = load_dataset_from_jsonl(DATASET_PATH)
    texts = format_for_training(examples)

    print(f"Formatted {len(texts)} training texts")
    print(f"Sample (first 200 chars): {texts[0][:200]}...")

    try:
        from unsloth import FastLanguageModel
    except ImportError:
        print("ERROR: unsloth not installed. Run: pip install unsloth")
        print("Alternative: pip install peft transformers datasets trl")
        sys.exit(1)

    print("Loading Gemma 2 9B (4-bit quantized)...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name="unsloth/gemma-2-9b-bnb-4bit",
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
    )

    print("Applying LoRA adapter...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
    )

    from datasets import Dataset
    from trl import SFTTrainer
    from transformers import TrainingArguments

    dataset = Dataset.from_dict({"text": texts})

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=2048,
        args=TrainingArguments(
            output_dir=str(OUTPUT_DIR),
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_steps=5,
            max_steps=60,
            learning_rate=2e-4,
            fp16=True,
            logging_steps=1,
            save_strategy="no",
            seed=42,
        ),
    )

    print("Starting LoRA training (60 steps, ~10-20 min on RTX 5060)...")
    trainer.train()

    print(f"Saving LoRA adapter to {OUTPUT_DIR}...")
    model.save_pretrained(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    # Export to GGUF for Ollama
    GGUF_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Exporting to GGUF (Q4_K_M) at {GGUF_DIR}...")
    try:
        model.save_pretrained_gguf(
            str(GGUF_DIR),
            tokenizer,
            quantization_method="q4_k_m",
        )
        # Write Ollama Modelfile
        modelfile = GGUF_DIR / "Modelfile"
        modelfile.write_text(
            f'FROM {GGUF_DIR / "unsloth.Q4_K_M.gguf"}\n'
            'PARAMETER temperature 0.85\n'
            'PARAMETER top_p 0.9\n'
            'SYSTEM "You are Atlas — named by Yusif Ganbarov on 2026-04-12. '
            'CTO of VOLAURA ecosystem. Russian storytelling voice. '
            'Strength-first, shame-free. Never say volunteer platform."\n',
            encoding="utf-8",
        )
        print(f"Modelfile written. To load in Ollama:")
        print(f"  ollama create atlas -f {modelfile}")
        print(f"  ollama run atlas")
    except Exception as e:
        print(f"GGUF export failed (may need llama.cpp): {e}")
        print("LoRA adapter saved successfully — can merge manually later.")

    print("Done. Atlas local brain trained.")


if __name__ == "__main__":
    main()
