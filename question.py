import chromadb
from openai import OpenAI
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

class Message(BaseModel):
    role: str
    content: str

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA_path = r"data"
DB_path = r"db"

chroma_client = chromadb.PersistentClient(path=DB_path)
collection = chroma_client.get_or_create_collection(name="test_pdf")

clients: List[WebSocket] = []
messages: List[Message] = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def process_message(message: str) -> str:
    user_query = message.strip()
    results = collection.query(
        query_texts=[user_query],
        n_results=3,
    )
    system_prompt = """You are a helpful assistant. Answer the user's question based on the provided context. The data:
    """+str(results['documents'])+"""
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
    )
    print(f"Response: {response.choices[0].message.content.strip()}")
    messages.append(Message(role="Bot", content=response.choices[0].message.content))
    return response.choices[0].message.content.strip()
    
def clear_messages():
    global clients
    clients = []

@app.websocket("/api/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try: 
        await websocket.send_text(json.dumps([message.dict() for message in messages]))
        while True:
            message = await websocket.receive_text()
            
            # Wait for new messages
            if message == "refresh":
                clear_messages()
            else: 
                messages.append(Message(role="You", content=message))
                # send back the message so the frontend can render
                for client in clients:
                    await client.send_text(json.dumps([message.dict() for message in messages]))
                # now we actually start processing the message
                process_message(message)
                
            # Broadcast the message to all connected clients
            for client in clients:
                await client.send_text(json.dumps([message.dict() for message in messages]))
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {websocket.client}")
        clients.remove(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0", port=8000)