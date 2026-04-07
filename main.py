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
        
        # 🔥 THE FIX: Number ke aage '/num ' lagakar bhejna 🔥
        command_message = f"/num {req.phone_number}"
        await client.send_message(target_bot, command_message)
        
        # 2. Wait karna taaki bot .txt file bhej sake (4 seconds)
        await asyncio.sleep(4)
        
        # 3. Latest messages padhna
        result_text = "Number not found in database" # Agar kuch na mile toh yeh dikhega
        
        async for message in client.get_chat_history(target_bot, limit=2):
            if message.document and message.document.file_name.endswith(".txt"):
                # File download karke read karna
                file_path = await client.download_media(message)
                with open(file_path, "r", encoding="utf-8") as f:
                    result_text = f.read()
                # Server se file delete kar dena
                os.remove(file_path)
                break
            elif message.text: 
                # Agar bot text mein hi bata de ki "Not found" ya result de de
                result_text = message.text
                break
                
        await client.disconnect()
        return {"status": "success", "result": result_text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
