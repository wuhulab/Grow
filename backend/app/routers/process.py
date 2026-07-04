from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio
import psutil

router = APIRouter()


class KillRequest(BaseModel):
    force: bool = False


@router.get("/list")
async def list_processes(sort_by: str = "cpu", limit: int = 200):
    # psutil calls are blocking; run them off the event loop so the server
    # stays responsive (the terminal websocket in particular is sensitive to
    # loop stalls, which previously caused large input-echo latency).
    result = await asyncio.to_thread(_list_processes_sync, sort_by, limit)
    return result


def _list_processes_sync(sort_by: str, limit: int):
    import time
    procs = []
    # Prime cpu_percent
    for p in psutil.process_iter(["pid", "name", "username", "status"]):
        try:
            p.cpu_percent(None)
        except Exception:
            pass
    time.sleep(0.1)
    for p in psutil.process_iter(["pid", "name", "username", "status", "memory_info", "create_time"]):
        try:
            info = p.info
            cpu = p.cpu_percent(None)
            mem = info.get("memory_info")
            procs.append({
                "pid": info.get("pid"),
                "name": info.get("name") or "",
                "username": info.get("username") or "",
                "status": info.get("status") or "",
                "cpu": round(cpu, 1),
                "memory": int(mem.rss) if mem else 0,
                "create_time": info.get("create_time") or 0,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    key_map = {"cpu": "cpu", "memory": "memory", "pid": "pid", "name": "name"}
    key = key_map.get(sort_by, "cpu")

    def _sort_key(x):
        v = x.get(key)
        if isinstance(v, bool):
            return 0
        if isinstance(v, (int, float)):
            return v
        return str(v).lower() if v is not None else ""

    procs.sort(key=_sort_key, reverse=(key in ("cpu", "memory")))
    return procs[:limit]


@router.post("/{pid}/kill")
async def kill_process(pid: int, req: KillRequest):
    try:
        p = psutil.Process(pid)
        if req.force:
            p.kill()
        else:
            p.terminate()
        return {"ok": True}
    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail="Process not found")
    except psutil.AccessDenied:
        raise HTTPException(status_code=403, detail="Access denied")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{pid}")
async def process_detail(pid: int):
    try:
        return await asyncio.to_thread(_process_detail_sync, pid)
    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail="Process not found")
    except psutil.AccessDenied:
        raise HTTPException(status_code=403, detail="Access denied")


def _process_detail_sync(pid: int):
    p = psutil.Process(pid)
    with p.oneshot():
        return {
            "pid": p.pid,
            "name": p.name(),
            "exe": p.exe() if hasattr(p, "exe") else "",
            "cmdline": p.cmdline(),
            "username": p.username(),
            "status": p.status(),
            "cpu": p.cpu_percent(0.1),
            "memory": p.memory_info().rss,
            "num_threads": p.num_threads(),
            "create_time": p.create_time(),
        }
