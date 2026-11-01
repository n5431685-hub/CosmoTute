"""
FastAPI application entry-point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.db import init_db
from app.routers import answers, questions, students, skills, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="CosmoTute – Adaptive Learning Engine",
    description="BKT-powered adaptive assessment API for Class 6–10 India",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(answers.router)
app.include_router(questions.router)
app.include_router(students.router)
app.include_router(skills.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"message": "CosmoTute API running 🚀", "docs": "/docs"}
