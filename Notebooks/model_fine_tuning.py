import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from unsloth.chat_templates import get_chat_template
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments


model_name = "unsloth/Phi-3-mini-4k-instruct-bnb-4bit"
max_seq_length = 2048
dtype = None


model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=model_name,
    max_seq_length=max_seq_length,
    dtype=dtype,
    load_in_4bit=True,
)

# 1. Load our perfectly cleaned resume dataset
dataset = load_dataset('json', data_files='cleaned_resume_finetune_data.jsonl', split="train")

# 2. Tell Unsloth to use Phi-3's native chat format
tokenizer = get_chat_template(
    tokenizer,
    chat_template = "phi-3",
    mapping = {"role" : "role", "content" : "content", "user" : "user", "assistant" : "assistant"}
)


def formatting_prompts_func(examples):
    convos = examples["messages"]
    texts = [tokenizer.apply_chat_template(convo, tokenize = False, add_generation_prompt = False) for convo in convos]
    return { "text" : texts }

# Map the function across the dataset
dataset = dataset.map(formatting_prompts_func, batched = True)

print(f"Loaded and formatted {len(dataset)} resumes!")
print(dataset['text'][0]) # Peek at the formatting

# Attach the LoRA adapters to the 4-bit model
model = FastLanguageModel.get_peft_model(
    model,
    r=16, # Rank 16 is perfect for JSON extraction (saves memory over 64)
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_alpha=32,
    lora_dropout=0, # Unsloth optimization
    bias="none",    # Unsloth optimization
    use_gradient_checkpointing="unsloth", # True or "unsloth" for very long context
    random_state=3407,
    use_rslora=False,
    loftq_config=None,
)

print("LoRA adapters successfully attached! Ready for Trainer.")


trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text", # <--- This tells it to use our formatted strings
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=10, # Dropped to 10 so you see updates faster
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="outputs",
        save_strategy="epoch",
        save_total_limit=2,
        dataloader_pin_memory=False,
        report_to="none",
    ),
)

model.save_pretrained_gguf("gguf_model", tokenizer, quantization_method="q4_k_m")