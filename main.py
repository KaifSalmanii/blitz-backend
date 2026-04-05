from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pyrogram import Client
import os
import tempfile

# Keys Render se automatically uthayega
api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
bot_token = os.environ.get("BOT_TOKEN")
channel_id = int(os.environ.get("CHANNEL_ID"))

app = FastAPI()

# Frontend ko connect hone ki permission dena
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bot = Client("blitz_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@app.on_event("startup")
async def startup():
    await bot.start()

@app.on_event("shutdown")
async def shutdown():
    await bot.stop()

@app.get("/")
def home():
    return {"message": "🚀 BlitzVault Engine is Running!"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # File ko temporarily server par save karna
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            content = await file.read()
            temp.write(content)
            temp_path = temp.name
        
        # File ko Telegram Channel (Vault) mein bhejna
        msg = await bot.send_document(
            chat_id=channel_id,
            document=temp_path,
            file_name=file.filename
        )
        os.remove(temp_path) # Temp file delete karna (Storage bachane ke liye)
        
        # Link Generate karna
        file_id = msg.id
        download_link = f"https://blitz-backend-gxu4.onrender.com/download/{file_id}"
        
        return {"status": "success", "message": "Uploaded to Vault!", "link": download_link}
    
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/download/{message_id}")
async def download_file(message_id: int):
    try:
        # Telegram Channel se file dhoondhna
        msg = await bot.get_messages(chat_id=channel_id, message_ids=message_id)
        if not msg or (not msg.document and not msg.video):
            return {"error": "File not found or deleted from vault."}
        
        # File ka naam pata lagana
        file_name = msg.document.file_name if msg.document else "blitzvault_video.mp4"

        # File ko seedha browser mein stream karna (chunk by chunk)
        async def file_generator():
            async for chunk in bot.stream_media(msg):
                yield chunk

        headers = {
            "Content-Disposition": f'attachment; filename="{file_name}"'
        }
        return StreamingResponse(file_generator(), media_type="application/octet-stream", headers=headers)
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
        
