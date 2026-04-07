import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pyrogram import Client

# Render ke Environment Variables se API keys aayengi
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
SESSION_STRING = os.environ.get("SESSION_STRING")

# 🔥 YEH WALI LINE MISSING THI JISKI WAJAH SE ERROR AAYA 🔥
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

login_sessions = {}

class PhoneReq(BaseModel): phone_number: str
class OTPReq(BaseModel): phone_number: str; otp: str
class SearchReq(BaseModel): phone_number: str

@app.get("/")
def home(): 
    return {"message": "🚀 TrueSearch Engine is Live!"}

# --- 1. ADMIN LOGIN (Sirf ek baar use hoga Session String nikalne ke liye) ---
@app.post("/send-otp")
async def send_otp(req: PhoneReq):
    try:
        client = Client(f"temp_{req.phone_number}", api_id=int(API_ID), api_hash=API_HASH, in_memory=True)
        await client.connect()
        code = await client.send_code(req.phone_number)
        login_sessions[req.phone_number] = {"hash": code.phone_code_hash, "client": client}
        return {"status": "success"}
    except Exception as e: 
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/verify-otp")
async def verify_otp(req: OTPReq):
    if req.phone_number not in login_sessions: 
        raise HTTPException(status_code=400, detail="Timeout")
    data = login_sessions[req.phone_number]
    try:
        await data["client"].sign_in(req.phone_number, data["hash"], req.otp)
        session_str = await data["client"].export_session_string()
        await data["client"].disconnect()
        del login_sessions[req.phone_number]
        return {"session_string": session_str}
    except Exception as e: 
        raise HTTPException(status_code=400, detail=str(e))

# --- 2. MAIN SEARCH API (Website yahan number bhejegi) ---
@app.post("/search")
async def search_number(req: SearchReq):
    if not SESSION_STRING:
         raise HTTPException(status_code=500, detail="Server Not Configured: SESSION_STRING is missing in Render.")
         
    # ⚠️ YAHAN US BOT KA USERNAME DAALO (quotes ke andar)
    target_bot = "@Randominsight69_bot" 
    
    try:
        client = Client("searcher", api_id=int(API_ID), api_hash=API_HASH, session_string=SESSION_STRING, in_memory=True)
        await client.connect()
        
        # Number ke aage '/num ' lagakar bhejna
        command_message = f"/num {req.phone_number}"
        await client.send_message(target_bot, command_message)
        
        # Wait karna taaki bot .txt file bhej sake (4 seconds)
        await asyncio.sleep(4)
        
        result_text = "Number not found in database"
        
        async for message in client.get_chat_history(target_bot, limit=2):
            if message.document and message.document.file_name.endswith(".txt"):
                file_path = await client.download_media(message)
                with open(file_path, "r", encoding="utf-8") as f:
                    result_text = f.read()
                os.remove(file_path)
                break
            elif message.text: 
                result_text = message.text
                break
                
        await client.disconnect()
        return {"status": "success", "result": result_text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
    
