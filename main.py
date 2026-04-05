import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pyrogram import Client

# Config
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

app = FastAPI()

# CORS Fix for GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

bot = Client("blitz_vault", api_id=int(API_ID), api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_event("startup")
async def startup():
    await bot.start()

@app.get("/")
def home():
    return {"status": "running"}

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        
        msg = await bot.send_document(chat_id=int(CHANNEL_ID), document=tmp_path, file_name=file.filename)
        os.remove(tmp_path)
        
        # URL check kar lena Render dashboard se
        link = f"https://blitz-backend-gxu4.onrender.com/download/{msg.id}"
        return {"link": link}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/download/{msg_id}")
async def download(msg_id: int):
    msg = await bot.get_messages(chat_id=int(CHANNEL_ID), message_ids=msg_id)
    async def stream():
        async for chunk in bot.stream_media(msg):
            yield chunk
    return StreamingResponse(stream(), media_type="application/octet-stream")
    
