import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import create_document, get_documents, db
from schemas import Note

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# ================= Notes API ==================

class NoteOut(BaseModel):
    id: str
    text: str
    author: Optional[str] = None
    created_at: Optional[str] = None

@app.post("/notes", response_model=dict)
async def create_note(note: Note):
    try:
        note_id = create_document("note", note)
        return {"id": note_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notes", response_model=List[NoteOut])
async def list_notes(limit: int = 100):
    try:
        docs = get_documents("note", {}, limit=limit)
        results: List[NoteOut] = []
        for d in docs:
            _id = str(d.get("_id"))
            created = d.get("created_at")
            created_str = None
            if isinstance(created, datetime):
                created_str = created.isoformat()
            results.append(NoteOut(
                id=_id,
                text=d.get("text", ""),
                author=d.get("author"),
                created_at=created_str
            ))
        # Show newest first
        results.sort(key=lambda x: x.created_at or "", reverse=True)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
