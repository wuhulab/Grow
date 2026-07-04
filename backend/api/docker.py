import docker
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

try:
    _client = docker.from_env()
except Exception:
    _client = None


class ContainerItem(BaseModel):
    id: str
    name: str
    image: str
    status: str
    state: str
    ports: dict


class ImageItem(BaseModel):
    id: str
    tags: List[str]
    size: int


class DockerInfo(BaseModel):
    version: str
    containers: int
    images: int


@router.get("/info", response_model=DockerInfo)
def docker_info():
    if not _client:
        raise HTTPException(status_code=500, detail="Docker not available")
    info = _client.version()
    return DockerInfo(
        version=info.get("Version", "unknown"),
        containers=len(_client.containers.list(all=True)),
        images=len(_client.images.list()),
    )


@router.get("/containers", response_model=List[ContainerItem])
def list_containers(all: bool = True):
    if not _client:
        raise HTTPException(status_code=500, detail="Docker not available")
    containers = []
    for c in _client.containers.list(all=all):
        containers.append(
            ContainerItem(
                id=c.short_id,
                name=c.name,
                image=c.image.tags[0] if c.image.tags else "<none>",
                status=c.status,
                state=c.attrs.get("State", {}).get("Status", "unknown"),
                ports=c.ports,
            )
        )
    return containers


@router.post("/containers/{cid}/start")
def start_container(cid: str):
    if not _client:
        raise HTTPException(status_code=500, detail="Docker not available")
    try:
        c = _client.containers.get(cid)
        c.start()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/containers/{cid}/stop")
def stop_container(cid: str):
    if not _client:
        raise HTTPException(status_code=500, detail="Docker not available")
    try:
        c = _client.containers.get(cid)
        c.stop()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/containers/{cid}/restart")
def restart_container(cid: str):
    if not _client:
        raise HTTPException(status_code=500, detail="Docker not available")
    try:
        c = _client.containers.get(cid)
        c.restart()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/containers/{cid}")
def remove_container(cid: str):
    if not _client:
        raise HTTPException(status_code=500, detail="Docker not available")
    try:
        c = _client.containers.get(cid)
        c.remove(force=True)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/images", response_model=List[ImageItem])
def list_images():
    if not _client:
        raise HTTPException(status_code=500, detail="Docker not available")
    images = []
    for img in _client.images.list():
        tags = img.tags if img.tags else []
        images.append(
            ImageItem(
                id=img.short_id,
                tags=tags,
                size=img.attrs.get("Size", 0),
            )
        )
    return images
