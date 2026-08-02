from fastapi import APIRouter, File, UploadFile 
 
router = APIRouter(tags=["Upload"], prefix="/upload") 
 
@router.post("/") 
async def upload_image(file: UploadFile = File(...)): 
    return {"filename": file.filename, "status": "uploaded"} 
