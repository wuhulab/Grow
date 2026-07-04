import psutil
import platform
import time
import asyncio
from fastapi import APIRouter, WebSocket
from pydantic import BaseModel
from typing import List

router = APIRouter()


class CPUInfo(BaseModel):
    percent: float
    count: int
    freq: float


class MemoryInfo(BaseModel):
    total: int
    used: int
    percent: float


class DiskInfo(BaseModel):
    device: str
    total: int
    used: int
    percent: float


class DiskIOInfo(BaseModel):
    read_bytes: int
    write_bytes: int


class NetIOInfo(BaseModel):
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int


class SystemInfo(BaseModel):
    hostname: str
    platform: str
    version: str
    arch: str
    uptime: int


class LoadInfo(BaseModel):
    load1: float
    load5: float
    load15: float


@router.get("/info", response_model=SystemInfo)
def get_system_info():
    boot_time = psutil.boot_time()
    uptime = int(time.time() - boot_time)
    return SystemInfo(
        hostname=platform.node(),
        platform=platform.system(),
        version=platform.version(),
        arch=platform.machine(),
        uptime=uptime,
    )


@router.get("/cpu", response_model=CPUInfo)
def get_cpu():
    freq = psutil.cpu_freq()
    return CPUInfo(
        percent=psutil.cpu_percent(interval=0.5),
        count=psutil.cpu_count(),
        freq=freq.current if freq else 0,
    )


@router.get("/memory", response_model=MemoryInfo)
def get_memory():
    mem = psutil.virtual_memory()
    return MemoryInfo(
        total=mem.total,
        used=mem.used,
        percent=mem.percent,
    )


@router.get("/disk", response_model=List[DiskInfo])
def get_disk():
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append(
                DiskInfo(
                    device=part.device,
                    total=usage.total,
                    used=usage.used,
                    percent=usage.percent,
                )
            )
        except Exception:
            continue
    return disks


@router.get("/load", response_model=LoadInfo)
def get_load():
    loads = psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0, 0, 0)
    return LoadInfo(load1=loads[0], load5=loads[1], load15=loads[2])


@router.get("/network", response_model=NetIOInfo)
def get_network():
    net = psutil.net_io_counters()
    return NetIOInfo(
        bytes_sent=net.bytes_sent,
        bytes_recv=net.bytes_recv,
        packets_sent=net.packets_sent,
        packets_recv=net.packets_recv,
    )


@router.get("/diskio", response_model=DiskIOInfo)
def get_diskio():
    io = psutil.disk_io_counters()
    return DiskIOInfo(
        read_bytes=io.read_bytes if io else 0,
        write_bytes=io.write_bytes if io else 0,
    )


@router.websocket("/ws")
async def system_ws(websocket: WebSocket):
    await websocket.accept()
    last_net = psutil.net_io_counters()
    last_disk = psutil.disk_io_counters()
    try:
        while True:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            loads = psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0, 0, 0)
            net = psutil.net_io_counters()
            dio = psutil.disk_io_counters()

            net_sent = net.bytes_sent - last_net.bytes_sent
            net_recv = net.bytes_recv - last_net.bytes_recv
            dio_read = dio.read_bytes - last_disk.read_bytes if dio else 0
            dio_write = dio.write_bytes - last_disk.write_bytes if dio else 0
            last_net = net
            last_disk = dio

            await websocket.send_json(
                {
                    "cpu": cpu,
                    "memory": mem.percent,
                    "memory_used": mem.used,
                    "memory_total": mem.total,
                    "disk": disk.percent,
                    "disk_used": disk.used,
                    "disk_total": disk.total,
                    "load1": loads[0],
                    "load5": loads[1],
                    "load15": loads[2],
                    "net_sent": net_sent,
                    "net_recv": net_recv,
                    "dio_read": dio_read,
                    "dio_write": dio_write,
                }
            )
            await asyncio.sleep(2)
    except Exception:
        pass
    finally:
        await websocket.close()
