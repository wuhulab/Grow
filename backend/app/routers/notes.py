from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import json

router = APIRouter()

NOTES_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "notes.json")
os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)


def _load():
    if not os.path.exists(NOTES_FILE):
        return {"content": ""}
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"content": ""}


def _save(data):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class NoteUpdate(BaseModel):
    content: str


@router.get("/")
async def get_notes():
    return _load()


@router.post("/")
async def update_notes(req: NoteUpdate):
    data = {"content": req.content}
    try:
        _save(data)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))