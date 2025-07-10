# File: app/api.py

from fastapi import FastAPI, APIRouter
router = APIRouter()

@router.get("/")
def health_check():
    """Home endpoint for the application."""
    return {"status": "ok", "message": "Welcome to the Assistant Service!"}

@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Server is healthy"}

