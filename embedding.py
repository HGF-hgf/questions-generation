
from google.api_core import exceptions
from google.genai import types
from google import genai
from pymongo import MongoClient
import openai
import chromadb
import time
import os
import re
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key= os.getenv("GOOGLE_API_KEY"))
chroma_client = chromadb.PersistentClient(path="db")
collection = chroma_client.get_or_create_collection(name="embedding_sections")
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_embeddings(text, model= "gemini-embedding-exp-03-07"):
    for attempt in range(5):
        try:
            result = client.models.embed_content(
                model=model,
                contents=text,
                config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"))
            time.sleep(20)  # Đợi 1 giây giữa các lần thử
            return result.embeddings[0].values
        except exceptions.ResourceExhausted as e:
            if attempt < 5 - 1:
                print(f"Quota vượt quá, thử lại sau {2 ** attempt} giây...")
                time.sleep(20)  # Đợi 1s, 2s, 4s,...
            else:
                raise e
            
            
with open("data/output.md", "r", encoding="utf-8") as f:
    text = f.read()
 
    
headings = re.findall(r"^(#{1,6})\s+(.*)", text, flags=re.MULTILINE)

for level, title in headings:
    print(f"{level} {title}")

# for idx, sec in enumerate(sections):
#     lines = sec.splitlines()
#     title = lines[0].strip()
#     body = "\n".join(lines[1:]).strip()

#     print(f"📄 Đang xử lý: {title}")

#     embedding = get_embeddings(body)

#     collection.upsert(
#         documents=[body],
#         metadatas=[{"title": title}],
#         ids=[f"section-{idx}"]
#     )


