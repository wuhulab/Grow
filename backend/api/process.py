import psutil
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List

router = APIRouter()


class ProcessItem(BaseModel):
    pid: int
    name: str
    username: str
    status: str
    cpu_percent: float
    memory_percent: float
    create_time: float
    cmdline: str


@router.get("/list", response_model=List[ProcessItem])
def list_processes(search: str = Query("")):
    processes = []
    for p in psutil.process_iter(
        [
            "pid",
            "name",
            "username",
            "status",
            "cpu_percent",
            "memory_percent",
            "create_time",
            "cmdline",
        ]
    ):
        try:
            info = p.info
            cmd = " ".join(info.get("cmdline") or [])
            name = info.get("name") or ""
            if (
                search
                and search.lower() not in name.lower()
                and search.lower() not in cmd.lower()
            ):
                continue
            processes.append(
                ProcessItem(
                    pid=info["pid"],
                    name=name,
                    username=info.get("username") or "",
                    status=info.get("status") or "",
                    cpu_percent=info.get("cpu_percent") or 0.0,
                    memory_percent=info.get("memory_percent") or 0.0,
                    create_time=info.get("create_time") or 0,
                    cmdline=cmd,
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes


@router.post("/{pid}/kill")
def kill_process(pid: int):
    try:
        p = psutil.Process(pid)
        p.kill()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{pid}/terminate")
def terminate_process(pid: int):
    try:
        p = psutil.Process(pid)
        p.terminate()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
