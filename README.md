# Resume Info Extraction System

![image](assets/Resume_storage.jpg)

# 📄 Local AI Resume Parser

## 🚀 Overview
A privacy-first, end-to-end Machine Learning pipeline for extracting structured candidate data from unstructured PDF resumes. 

This project replaces expensive, cloud-dependent APIs (like OpenAI) with a completely local, highly compressed Large Language Model (LLM). The model was meticulously cleaned, fine-tuned, and quantized to run strictly on consumer hardware and free-tier/low-cost cloud servers while guaranteeing strict JSON schema adherence.

## 🏗️ Architecture & Tech Stack

The application uses a decoupled Client-Server architecture:

* **Frontend (UI):** `Streamlit` - A reactive web interface for seamless PDF ingestion and human-readable data rendering.
* **Backend (API):** `FastAPI` - A high-performance ASGI server handling document orchestration and LLM prompt formatting.
* **Inference Engine:** `llama-cpp-python` - Executes the AI locally on the CPU/RAM, bypassing the need for expensive datacenter GPUs.
* **Model Engine:** Microsoft `Phi-3-Mini-4k-Instruct`
* **Fine-Tuning Framework:** `Unsloth` + `TRL` + `LoRA`

## 🧠 The Machine Learning Pipeline

### 1. Data Sanitization ("The Core Fix")
Trained on a dataset of human resumes, heavily filtered via a custom Python script to remove 65% of the original "poisoned" data (mismatched labels/names). This guaranteed the model only learned from pristine, accurate examples.

### 2. Parameter-Efficient Fine-Tuning (PEFT)
The base Phi-3 model was fine-tuned using **Unsloth** and **LoRA** (Low-Rank Adaptation). By targeting the Attention and MLP layers with a rank of 16 (`r=16`), the model was strictly conditioned to stop acting like a conversational chatbot and behave exclusively as an HR data extraction agent.

### 3. 4-bit Quantization (GGUF)
To ensure the model could be deployed cheaply, the massive 15GB model was mathematically compressed into a 4-bit `.gguf` file (`Q4_K_M`). The final model footprint is just **2.4 GB**, allowing it to run smoothly on servers with as little as 8GB of RAM.

---

## 💻 Local Installation & Usage

### Prerequisites
* Python 3.10+
* 8GB RAM Minimum

### Setup Instructions
1. **Clone the repository:**
   ```bash
   git clone [https://github.com/omar24524/NLU-Project.git](https://github.com/omar24524/NLU-Project.git)
   cd NLU-Project
