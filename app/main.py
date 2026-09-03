from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth, boards, dashboards, issues, metadata, permissions, projects, saved_filters, users
from app.core.config import settings

app = FastAPI(title="Ticket System", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_v1_routers = [
    auth.router,
    users.router,
    projects.router,
    permissions.router,
    metadata.router,
    issues.router,
    boards.router,
    dashboards.router,
    saved_filters.router,
]
for router in api_v1_routers:
    app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
