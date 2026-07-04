import os
import shutil
import mimetypes
from pathlib import Path
from fastapi import APIRouter, UploadFile, File as APIFile, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List

router = APIRouter()

# Default root directory is全盘根目录(Windows), or /
if os.name == "nt":
    DEFAULT_ROOT = "C:\\"
else:
    DEFAULT_ROOT = "/"


class FileItem(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int
    modified: float


class ListResponse(BaseModel):
    items: List[FileItem]
    current: str


@router.get("/list", response_model=ListResponse)
def list_files(path: str = Query("")):
    if not path:
        path = DEFAULT_ROOT
    if not os.path.isdir(path):
        raise HTTPException(status_code=404, detail="Directory not found")
    items = []
    try:
        for entry in os.scandir(path):
            try:
                stat = entry.stat()
                items.append(
                    FileItem(
                        name=entry.name,
                        path=entry.path,
                        is_dir=entry.is_dir(),
                        size=stat.st_size,
                        modified=stat.st_mtime,
                    )
                )
            except Exception:
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    # Sort: dirs first, then files
    items.sort(key=lambda x: (not x.is_dir, x.name.lower()))
    return ListResponse(items=items, current=path)


@router.post("/upload")
def upload_file(path: str = Query(""), file: UploadFile = APIFile(...)):
    if not path or not os.path.isdir(path):
        path = DEFAULT_ROOT
    dest = os.path.join(path, file.filename)
    try:
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return {"ok": True, "path": dest}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download")
def download_file(path: str = Query(...)):
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    media_type, _ = mimetypes.guess_type(path)
    return FileResponse(
        path,
        media_type=media_type or "application/octet-stream",
        filename=os.path.basename(path),
    )


@router.delete("/delete")
def delete_file(path: str = Query(...)):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Not found")
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rename")
def rename_file(old: str = Query(...), new: str = Query(...)):
    if not os.path.exists(old):
        raise HTTPException(status_code=404, detail="Not found")
    try:
        os.rename(old, new)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mkdir")
def make_dir(path: str = Query(...)):
    try:
        os.makedirs(path, exist_ok=True)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
