"""
Database configuration for pgrag project.
"""

import os

POSTGRES_DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "pgrag"),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", "postgres#2025"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
}

SQLITE_DB_CONFIG = {
    "dbname": os.getenv("SQLITE_DB", "pg_mcp.db"),
    "user": os.getenv("SQLITE_USER", ""),
    "password": os.getenv("SQLITE_PASSWORD", ""),
    "host": os.getenv("SQLITE_HOST", ""),
    "port": os.getenv("SQLITE_PORT", ""),
    "uri": os.getenv("SQLITE_URI", "sqlite:///pg_mcp.db"),
}

# JWT Configuration
JWT_SECRET_KEY= os.getenv("JWT_SECRET_KEY","your-super-secret-jwt-key-change-in-production")

# MCP API Key for VS Code integration
ASSISTANT_API_KEY= os.getenv("PGMCP_API_KEY", "pg-mcp-key-2025-super-secure-token")

# Default database path for SQLite
DB_PATH= os.getenv("DB_PATH", "pg_mcp.db")