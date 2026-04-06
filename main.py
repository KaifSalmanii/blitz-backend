import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pyrogram import Client

# Render se API credentials uthayenge
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")

app = FastAPI()

# CORS Fix taaki frontend website connect ho sake
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OTP process ke time data temporarily store karne ke liye
login_sessions = {}

class PhoneRequest(BaseModel):
    phone_number: str

class OTPRequest(BaseModel):
    phone_number: str
    otp: str

@app.get("/")
def home():
    return {"message": "🚀 UnlimGram Auth Engine is Running!"}

# Endpoint 1: Phone Number par OTP bhejna
@app.post("/send-otp")
async def send_otp(req: PhoneRequest):
    if not API_ID or not API_HASH:
        raise HTTPException(status_code=500, detail="Server par API Keys missing hain!")
        
    try:
        # In-memory client banayenge (Server ki storage use nahi karenge)
        client = Client(f"temp_{req.phone_number}", api_id=int(API_ID), api_hash=API_HASH, in_memory=True)
        await client.connect()
        
        # Telegram se OTP send karne ko bolenge
        sent_code = await client.send_code(req.phone_number)
        
        # Hash aur Client ko save kar lenge taaki verify karte time kaam aaye
        login_sessions[req.phone_number] = {
            "hash": sent_code.phone_code_hash,
            "client": client
        }
        return {"status": "success", "message": "OTP Sent Successfully!"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Telegram Error: {str(e)}")

# Endpoint 2: OTP Verify karna aur Session String generate karna
@app.post("/verify-otp")
async def verify_otp(req: OTPRequest):
    if req.phone_number not in login_sessions:
        raise HTTPException(status_code=400, detail="Time out ya invalid number. Wapas try karein.")
        
    session_data = login_sessions[req.phone_number]
    client = session_data["client"]
    phone_code_hash = session_data["hash"]
    
    try:
        # OTP verify karke user ko login karwana
        await client.sign_in(req.phone_number, phone_code_hash, req.otp)
        
        # 🌟 MAGIC: User ka "Session String" nikalna 🌟
        session_string = await client.export_session_string()
        await client.disconnect()
        
        # Temporary data delete karna (Security ke liye)
        del login_sessions[req.phone_number]
        
        return {"status": "success", "session_string": session_string}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid OTP ya Error: {str(e)}")
