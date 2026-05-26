from fastapi import FastAPI, UploadFile, File, Query
import pypdf
import io
import sqlite3
import json
from datetime import datetime

app = FastAPI()

# Global model variable
llm = None

# Initialize database
def init_db():
    conn = sqlite3.connect('resumes.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parsed_resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp TEXT,
            filename TEXT,
            json_data TEXT
        )
    ''')
    # Add index for faster user lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON parsed_resumes(user_id)')
    conn.commit()
    conn.close()

def get_llm():
    global llm
    if llm is None:
        import os
        os.environ['LLAMA_CPP_DISABLE_PREFETCH'] = '1'  # Fix for Windows PrefetchVirtualMemory issue
        try:
            from llama_cpp import Llama
            llm = Llama(
                model_path="../models/phi-3-mini-4k-instruct.Q4_K_M.gguf",
                n_ctx=2048,
                # n_gpu_layers=0,  # Force CPU mode for Windows compatibility
                verbose=True
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load the AI model: {str(e)}. Please check the model file and llama-cpp-python installation.")
    return llm

init_db()

@app.post("/parse")
async def parse_resume(file: UploadFile = File(...), user_id: str = Query(...)):
    
    # 1. Read the PDF
    pdf_content = await file.read()
    pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_content))
    
    resume_text = ""
    for page in pdf_reader.pages:
        extracted = page.extract_text()
        if extracted:
            resume_text += extracted + "\n"

# 2. Strict, Iron-Clad Extraction Prompt
    system_instruction = """
    You are an expert IT technical recruiter and data extraction system. 
    Analyze the provided resume and extract ALL available information into the exact JSON structure below.
    
    CRITICAL RULES:
    1. Output ONLY a valid, raw JSON object. 
    2. DO NOT output any markdown tags (like ```json).
    3. DO NOT output any SQL scripts, Python code, or conversational text.
    4. If a piece of information is missing, leave it as an empty string "" or empty list [].
    5. Close all brackets and braces properly.
    
    {
        "personal_info": {
            "name": "string",
            "email": "string",
            "phone": "string",
            "location": "string",
            "links": ["string"]
        },
        "professional_summary": "string",
        "skills": ["string", "string"],
        "work_experience": [
            {
                "job_title": "string",
                "company": "string",
                "dates": "string",
                "responsibilities": ["string", "string"]
            }
        ],
        "education": [
            {
                "degree": "string",
                "institution": "string",
                "graduation_date": "string"
            }
        ],
        "projects": [
            {
                "project_name": "string",
                "description": "string"
            }
        ]
    }
    """

    prompt = f"<|system|>\n{system_instruction}<|end|>\n<|user|>\n{resume_text}<|end|>\n<|assistant|>\n"
    
    # 3. Increased max_tokens to accommodate the larger JSON output
    # 3. Increased max_tokens and set temperature to ZERO
    llm_instance = get_llm()
    response = llm_instance(
        prompt,
        max_tokens=1500, 
        temperature=0.0,  # <--- ADD THIS LINE to stop hallucinations
        stop=["<|end|>"],
        echo=False
    )
    
    result_text = response['choices'][0]['text']
    
    # Save to database with user_id
    conn = sqlite3.connect('resumes.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO parsed_resumes (user_id, timestamp, filename, json_data)
        VALUES (?, ?, ?, ?)
    ''', (user_id, datetime.now().isoformat(), file.filename, result_text))
    conn.commit()
    conn.close()
    
    return {"result": result_text}

@app.get("/stored")
async def get_stored_resumes(user_id: str = Query(...)):
    conn = sqlite3.connect('resumes.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, timestamp, filename, json_data FROM parsed_resumes WHERE user_id = ? ORDER BY timestamp DESC', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    resumes = []
    for row in rows:
        resumes.append({
            "id": row[0],
            "timestamp": row[1],
            "filename": row[2],
            "json_data": row[3]
        })
    
    return {"resumes": resumes}