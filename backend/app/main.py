from fastapi import FastAPI 
 
app = FastAPI(title="Forensic Image Sanitizer", version="0.1.0") 
 
@app.get("/") 
async def root(): 
    return {"message": "Forensic Image Sanitizer API"} 
 
@app.get("/health") 
async def health(): 
    return {"status": "healthy"} 
