import os
import asyncio
from fastapi import APIRouter, WebSocket

router = APIRouter()

if os.name == "nt":
    DEFAULT_SHELL = "cmd.exe"
else:
    DEFAULT_SHELL = "/bin/bash"


@router.websocket("/ws")
async def terminal_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        proc = await asyncio.create_subprocess_exec(
            DEFAULT_SHELL,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except Exception as e:
        await websocket.send_text(f"[error] Failed to spawn shell: {e}\r\n")
        await websocket.close()
        return

    async def read_stdout():
        try:
            while True:
                data = await proc.stdout.read(1024)
                if not data:
                    break
                await websocket.send_text(data.decode("utf-8", errors="replace"))
        except Exception:
            pass

    task = asyncio.create_task(read_stdout())

    try:
        while True:
            msg = await websocket.receive_text()
            if proc.stdin and not proc.stdin.is_closing():
                proc.stdin.write(msg.encode("utf-8"))
                await proc.stdin.drain()
    except Exception:
        pass
    finally:
        proc.kill()
        await proc.wait()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await websocket.close()
