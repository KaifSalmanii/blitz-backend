from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pyrogram import Client
import os
import tempfile
import asyncio

# Environment Variables
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

app = FastAPI()

# 🔥 CORS SETTINGS - Iske bina website connect nahi hogi 🔥
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Sabhi websites ko allow karein
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bot Client Setup
bot = Client(
    "blitz_vault_bot",
    api_id=int(API_ID) if API_ID else 0,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_event("startup")
async def startup():
    if not bot.is_connected:
        await bot.start()

@app.on_event("shutdown")
async def shutdown():
    if bot.is_connected:
        await bot.stop()

@app.get("/")
async def root():
    return {"status": "online", "message": "🚀 BlitzVault Engine is Running!"}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    try:
        # 1. File ko temporarily save karein
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            content = await file.read()
            temp.write(content)
            temp_path = temp.name
        
        # 2. Telegram par bhejein
        sent_msg = await bot.send_document(
            chat_id=int(CHANNEL_ID),
            document=temp_path,
            file_name=file.filename,
            caption=f"Uploaded from BlitzVault\nFile: {file.filename}"
        )
        
        # 3. Temp file delete karein
        os.remove(temp_path)
        
        # 4. Download Link banayein
        # Yahan apna Render wala asli URL check kar lena
        download_url = f"https://blitz-backend-gxu4.onrender.com/download/{sent_msg.id}"
        
        return {
            "status": "success",
            "link": download_url,
            "file_id": sent_msg.id
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/download/{msg_id}")
async def download_video(msg_id: int):
    try:
        msg = await bot.get_messages(chat_id=int(CHANNEL_ID), message_ids=msg_id)
        
        if not msg or not (msg.document or msg.video):
            raise HTTPException(status_code=404, detail="File not found in Vault")

        file_name = msg.document.file_name if msg.document else "video.mp4"

        async def stream_file():
            async for chunk in bot.stream_media(msg):
                yield chunk

        return StreamingResponse(
            stream_file(),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'}
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
