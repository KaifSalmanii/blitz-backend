from fastapi import FastAPI, File, UploadFile
from pyrogram import Client
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Yeh aapki website ko is server se baat karne ki permission deta hai
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secrets jo hum Render par set karenge (Code mein nahi dikhenge)
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID") # Aapka Telegram ID jahan video aayegi

# Pyrogram Bot Setup
bot = Client(
    "blitz_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@app.on_event("startup")
async def startup():
    await bot.start()

@app.on_event("shutdown")
async def shutdown():
    await bot.stop()

@app.get("/")
def home():
    return {"message": "🚀 Blitz Backend is Running!"}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    try:
        # Video ko server par temporarily save karna
        file_location = f"temp_{file.filename}"
        with open(file_location, "wb") as f:
            f.write(await file.read())

        # Telegram par upload karna (Pyrogram ki power se)
        await bot.send_video(
            chat_id=int(CHAT_ID),
            video=file_location,
            caption=f"🎥 Uploaded via Blitz Web: {file.filename}"
        )
        
        # Upload hone ke baad server se delete kar dena taaki memory full na ho
        os.remove(file_location)
        
        return {"status": "success", "message": "✅ Video Telegram par chali gayi!"}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}
