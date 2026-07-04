import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from api import system, docker, process, file, note, terminal

static_dir = os.path.join(os.path.dirname(__file__), "dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Server Panel", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router, prefix="/api/system")
app.include_router(docker.router, prefix="/api/docker")
app.include_router(process.router, prefix="/api/process")
app.include_router(file.router, prefix="/api/file")
app.include_router(note.router, prefix="/api/note")
app.include_router(terminal.router, prefix="/api/terminal")

if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
