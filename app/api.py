# File: app/api.py

from fastapi import FastAPI, APIRouter
router = APIRouter()

@router.get("/")
def api_root():
    """API root endpoint for the application."""
    return {"status": "ok", "message": "Welcome to the Postgres MCP Service!"}

@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Server is healthy"}

