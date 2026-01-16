from pydoc import doc
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends , BackgroundTasks , Request , status
from app.core.auth import get_current_user
from app.db.client import mongo_client
from app.services.ai_service import rag_service
from app.utils.uploads import extract_text_from_pdf
import pdfplumber
from app.core.logging import logger
from uuid import uuid4
from typing import List
from datetime import datetime
from pathlib import Path
from bson import ObjectId
from app.services.redis import redis_client
import json

PROJECT_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_DIR = PROJECT_ROOT / "uploads" / "pdfs"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()

@router.post("/")
async def upload_new_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    # 1. Enforce PDF
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    try:
        # 2. Calculate file size (MB)
        file.file.seek(0, 2)  # move cursor to end
        file_size_bytes = file.file.tell()
        file.file.seek(0)

        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

        # 3. Count pages using pdfplumber
        with pdfplumber.open(file.file) as pdf:
            total_pages = len(pdf.pages)

        # reset cursor again (VERY IMPORTANT)
        file.file.seek(0)
        logger.info(f"Got ingestion request of file of size ${file_size_mb} and ${total_pages} pages")
        # 5. Build DB document (matches schema exactly)
        document = {
            "owner_id": user_id,
            "filename": file.filename,
            "upload_date": datetime.utcnow(),
            "status": "processing",
            "percent_complete" : 0,
            "number_of_chunk_processed" : 0 ,
            "number_of_parent_chunks" : 0 ,
            "metadata": {
                "total_pages": total_pages,
                "file_size_mb": file_size_mb
            }
        }

        # Save to disk
        unique_id = uuid4()
        file_path = UPLOAD_DIR / f"{unique_id}.pdf"
        with open(file_path, "wb") as f:
          f.write(await file.read())

        # 6. Insert into MongoDB
        linux_file_path = f"/mnt/c/Users/Lenovo/OneDrive/Desktop/DE Shaw/Risk-sent/Backend/app/uploads/pdfs/{unique_id}.pdf"
        await mongo_client.db.document.insert_one(document)
        document["_id"] = str(document["_id"])
        job_id = str(uuid4())
        job_payload = {
            "job_id" : job_id ,
            "doc_id" : document["_id"] ,
            "file_path" : str(linux_file_path) ,
            "user_id" : user_id
        }
        await redis_client.lpush("parse_queue" , json.dumps(job_payload))
        # background_tasks.add_task(
        # rag_service.ingest_pdf ,
        # str(file_path),
        # user_id,
        # document["_id"] 
        # )
        return {
            "status": "success",
            "document_id": document["_id"],
            "message": "File uploaded successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF upload failed: {str(e.with_traceback())}"
        )

@router.get("/")
async def get_doc(request : Request , user_id: str = Depends(get_current_user)) : 
    data = await request.json()
    logger.info(f"Got the query {data["query"]} for document {data["doc_id"]}")
    docs = await rag_service.search_risks(query=data["query"] , doc_id=data["doc_id"])
    for doc in docs :
        doc["_id"] = str(doc["_id"])
    return docs

@router.get("/me")
async def get_my_document(user_id: str = Depends(get_current_user)) :
      try :
        cursor = mongo_client.db.document.find({"owner_id" : user_id})
        documents = await cursor.to_list()
        response = []

        for doc in documents :
            response.append({"id" : str(doc["_id"]) , "status" : doc["status"] , "percent_complete" : doc["percent_complete"] ,  "filename" : doc["filename"]})
        return response 
      except Exception as e :
        logger.error(f"Error occured while fetching document {str(e)}")     

@router.get("/is-processed/{doc_id}")
async def check_document(doc_id : str) :
    try :
        doc = await mongo_client.db.document.find_one({"_id" : ObjectId(doc_id)})
        if not doc :
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return { "id" : str(doc["_id"]) , "status" : doc["status"] , "percent_complete" : doc["percent_complete"] , "filename" : doc["filename"]}
    except Exception as e :
        logger.error(f"Error occured while checking the document status {str(e)}")         

@router.get("/debug")
async def get_doc_debug(request : Request , user_id: str = Depends(get_current_user)) : 
    data = await request.json()
    print(data)
    docs = await rag_service.debug_search(query=data["query"] , doc_id=data["doc_id"] , user_id=user_id)
    for doc in docs :
        doc["_id"] = str(doc["_id"])
    print(docs)
    return docs
