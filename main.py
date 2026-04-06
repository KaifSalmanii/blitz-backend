import os
import tempfile
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pyrogram import Client
from pyrogram.enums import ChatType

API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")

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
class ActionReq(BaseModel): session_string: str; folder_name: str = ""

@app.get("/")
def home(): 
    return {"message": "🚀 UnlimGram REAL Engine is Live!"}

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

@app.post("/create-folder")
async def create_folder(req: ActionReq):
    try:
        client = Client("user", session_string=req.session_string, in_memory=True)
        await client.connect()
        chat = await client.create_channel(title=req.folder_name, description="Created via UnlimGram")
        await client.disconnect()
        return {"status": "success", "folder_id": chat.id, "folder_name": chat.title}
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-folders")
async def get_folders(req: ActionReq):
    try:
        client = Client("user", session_string=req.session_string, in_memory=True)
        await client.connect()
        folders = []
        async for dialog in client.get_dialogs():
            if dialog.chat.type == ChatType.CHANNEL and dialog.chat.is_creator:
                folders.append({"id": dialog.chat.id, "name": dialog.chat.title})
        await client.disconnect()
        return {"folders": folders}
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_file(session_string: str = Form(...), folder_id: str = Form(...), file: UploadFile = File(...)):
    try:
        client = Client("user", session_string=session_string, in_memory=True)
        await client.connect()
        
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(await file.read())
            temp_path = temp.name
            
        target_chat = int(folder_id) if folder_id != "root" else "me"
        
        await client.send_document(chat_id=target_chat, document=temp_path, file_name=file.filename)
        os.remove(temp_path)
        await client.disconnect()
        return {"status": "success", "message": "File Uploaded to Telegram!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🔥 YEH SABSE ZAROORI HAI SERVER START HONE KE LIYE 🔥
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
