from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

notes_db = []
counter = 1


class NoteItem(BaseModel):
    id: int
    title: str
    content: str


class NoteCreate(BaseModel):
    title: str
    content: str


class NoteUpdate(BaseModel):
    title: str
    content: str


@router.get("/list", response_model=List[NoteItem])
def list_notes():
    return [
        NoteItem(id=n["id"], title=n["title"], content=n["content"]) for n in notes_db
    ]


@router.post("/create", response_model=NoteItem)
def create_note(body: NoteCreate):
    global counter
    note = {"id": counter, "title": body.title, "content": body.content}
    counter += 1
    notes_db.append(note)
    return NoteItem(id=note["id"], title=note["title"], content=note["content"])


@router.put("/{nid}", response_model=NoteItem)
def update_note(nid: int, body: NoteUpdate):
    for n in notes_db:
        if n["id"] == nid:
            n["title"] = body.title
            n["content"] = body.content
            return NoteItem(id=n["id"], title=n["title"], content=n["content"])
    raise HTTPException(status_code=404, detail="Note not found")


@router.delete("/{nid}")
def delete_note(nid: int):
    global notes_db
    notes_db = [n for n in notes_db if n["id"] != nid]
    return {"ok": True}
