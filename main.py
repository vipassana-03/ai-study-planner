from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router


app = FastAPI(
    title="AI Study Planner Backend",
    version="1.0.0",
    description="Backend API for task planning, scheduling, rescheduling, and session tracking.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "AI Study Planner Backend is running",
        "openapi": "/openapi.json",
        "docs": "/docs",
    }
