from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.routers import system, docker_api, process, files, terminal, notes

app = FastAPI(title="Graw Server Panel", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(docker_api.router, prefix="/api/docker", tags=["docker"])
app.include_router(process.router, prefix="/api/process", tags=["process"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(terminal.router, prefix="/api/terminal", tags=["terminal"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])

# Serve frontend static files if built
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/")
    async def index():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
