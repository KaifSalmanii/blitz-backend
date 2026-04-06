import os
import tempfile
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
class FolderReq(BaseModel): session_string: str; folder_id: str

@app.get("/")
def home(): return {"message": "🚀 UnlimGram Pro Engine Live!"}

# --- AUTH ---
@app.post("/send-otp")
async def send_otp(req: PhoneReq):
    try:
        client = Client(f"temp_{req.phone_number}", api_id=int(API_ID), api_hash=API_HASH, in_memory=True)
        await client.connect()
        code = await client.send_code(req.phone_number)
        login_sessions[req.phone_number] = {"hash": code.phone_code_hash, "client": client}
        return {"status": "success"}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@app.post("/verify-otp")
async def verify_otp(req: OTPReq):
    if req.phone_number not in login_sessions: raise HTTPException(status_code=400, detail="Timeout")
    data = login_sessions[req.phone_number]
    try:
        await data["client"].sign_in(req.phone_number, data["hash"], req.otp)
        session_str = await data["client"].export_session_string()
        await data["client"].disconnect()
        del login_sessions[req.phone_number]
        return {"session_string": session_str}
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

# --- FOLDERS (With Secret Filter) ---
@app.post("/create-folder")
async def create_folder(req: ActionReq):
    try:
        client = Client("user", session_string=req.session_string, in_memory=True)
        await client.connect()
        # '\u200b' ek zero-width space hai. Yeh UI mein nahi dikhega par backend pehchan lega
        chat = await client.create_channel(title=req.folder_name + "\u200b", description="UnlimGram Vault")
        await client.disconnect()
        return {"status": "success", "folder_id": str(chat.id), "folder_name": req.folder_name}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/get-folders")
async def get_folders(req: ActionReq):
    try:
        client = Client("user", session_string=req.session_string, in_memory=True)
        await client.connect()
        folders = []
        async for dialog in client.get_dialogs():
            # Sirf wo channel uthayega jiske aakhir mein hamara secret code hai
            if dialog.chat.type == ChatType.CHANNEL and dialog.chat.is_creator:
                if dialog.chat.title and dialog.chat.title.endswith("\u200b"):
                    clean_name = dialog.chat.title.replace("\u200b", "")
                    folders.append({"id": str(dialog.chat.id), "name": clean_name})
        await client.disconnect()
        return {"folders": folders}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# --- FILES & STREAMING ---
@app.post("/get-files")
async def get_files(req: FolderReq):
    try:
        client = Client("user", session_string=req.session_string, in_memory=True)
        await client.connect()
        target = int(req.folder_id) if req.folder_id != "root" else "me"
        
        files = []
        async for msg in client.get_chat_history(target, limit=50): # Last 50 files
            if msg.document or msg.video or msg.photo or msg.audio:
                media = msg.document or msg.video or msg.photo or msg.audio
                
                # Metadata nikalna
                is_photo = True if msg.photo else False
                file_name = getattr(media, "file_name", f"Image_{msg.id}.jpg" if is_photo else f"File_{msg.id}")
                mime = getattr(media, "mime_type", "image/jpeg" if is_photo else "unknown")
                size = getattr(media, "file_size", 0)
                
                files.append({
                    "msg_id": msg.id, "name": file_name, "mime": mime, "size": size
                })
        
        await client.disconnect()
        return {"files": files}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/stream")
async def stream_media(session: str, folder_id: str, msg_id: int):
    # Yeh API video aur images ko direct website par play karegi
    client = Client("streamer", session_string=session, in_memory=True)
    await client.connect()
    target = int(folder_id) if folder_id != "root" else "me"
    msg = await client.get_messages(target, msg_id)
    
    async def generate():
        async for chunk in client.stream_media(msg):
            yield chunk
        await client.disconnect()

    return StreamingResponse(generate(), media_type="application/octet-stream")

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
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
