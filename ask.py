from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
import re
import os
from openai import OpenAI
from dotenv import load_dotenv
import aiofiles

load_dotenv()

# setting the environment
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionTypeModel(BaseModel):
    choose_many: int = Field(..., alias="choose-many")
    fill_in: int = Field(..., alias="fill-in")
    match_word: int = Field(..., alias="match-word")
    multiple_choice: int = Field(..., alias="multiple-choice")
    open: int

class Payload(BaseModel):
    amount: int
    documentID: str
    gptModel: str
    grade: int
    note: Optional[str]
    questionType: QuestionTypeModel
    subject: str
    topic: List[str]
    

client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

@app.post("/api/generate-quiz")
async def generate_quiz(payload: Payload):
    """
    Endpoint to generate a quiz based on the provided payload.
    """
    try:
        async with aiofiles.open(f"data/{payload.documentID}.md", "r", encoding="utf-8") as f:
            text = await f.read()
            
        sections = re.split(r'\n(?=#)', text)  

        matched_sections = []
            
        for section in sections:
            lines = section.strip().splitlines()
            if not lines:
                continue
            heading = lines[0].lower()
            for topic in payload.topic:
                if topic.lower() in heading:
                    matched_sections.append(section.strip())

        for idx, sec in enumerate(matched_sections):
            res = (f"\n--- Section {idx+1} ---\n{sec}\n")
        
        system_prompt = f"""
You are an assessment designer. Your task is to create a quiz in English for {payload.grade} grade students.

**Strict adherence to the specified question types and counts is crucial.**

The total number of questions must be {payload.amount}. The exact distribution of question types must be as follows:
- Multiple Choice: {payload.questionType.multiple_choice} questions
- Choose Many: {payload.questionType.choose_many} questions
- Fill In: {payload.questionType.fill_in} questions
- Match Word: {payload.questionType.match_word} questions
- Open: {payload.questionType.open} questions

Use easy, age-appropriate language.

The quiz must be based **only** on the provided data. Do not use any outside information.
---
**Data to use:**
{res}
---
**Quiz Topic:** {', '.join(payload.topic)}

Your response must be in **exactly** the following JSON format:
{{
  "name": "Quiz on {', '.join(payload.topic)}",
  "questions": [
    {{
      "correct_answers": ["..."],
      "explanation": "...",
      "incorrect_answers": ["..."],
      "level": "...",
      "question": "...",
      "type": "..."
    }}
    // Repeat according to questionType, level of difficulty (easy, medium, hard), and question type (multiple-choice, choose-many, fill-in, match-word, open)
  ]
}}

""" 
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
            ]
        )
        quiz_content = response.choices[0].message.content
        return json.loads(quiz_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/health")
async def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return {"status": "ok", "message": "Service is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0", port=8000)
    