from fastapi import FastAPI, UploadFile, File
from llama_cpp import Llama
import pypdf
import io

app = FastAPI()

# Load the model
llm = Llama(
    model_path="../models/phi-3-mini-4k-instruct.Q4_K_M.gguf",
    n_ctx=2048
)

@app.post("/parse")
async def parse_resume(file: UploadFile = File(...)):
    
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
    response = llm(
        prompt,
        max_tokens=1500, 
        temperature=0.0,  # <--- ADD THIS LINE to stop hallucinations
        stop=["<|end|>"],
        echo=False
    )
    
    return {"result": response['choices'][0]['text']}
