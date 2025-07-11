[![Docker Image CI](https://github.com/maithanhduyan/pg-mcp/actions/workflows/docker-image.yml/badge.svg)](https://github.com/maithanhduyan/pg-mcp/actions/workflows/docker-image.yml)

# PostgreSQL Model Context Protocol (MCP) Server

A comprehensive **Model Context Protocol (MCP) Server** built with **FastAPI** that provides full PostgreSQL database operations through a standardized JSON-RPC 2.0 interface. This server can be integrated with VS Code and other MCP-compatible tools for seamless database management.

## Features

### 🚀 Core MCP Functionality
- **JSON-RPC 2.0** compliant API
- **VS Code integration** ready
- **Authentication** with API key
- **Comprehensive error handling**
- **Auto-fallback** to mock service when PostgreSQL is unavailable

### 🗄️ PostgreSQL Operations
#### Basic Operations
- **Connection Testing** - Test database connectivity and get server info
- **Query Execution** - Execute any SQL query (SELECT, INSERT, UPDATE, DELETE, etc.)
- **Schema Information** - Get complete database schema with tables and columns
- **Table Information** - Detailed table metadata, columns, indexes, and row counts

#### Advanced Operations
- **Query Performance Analysis** - EXPLAIN ANALYZE for query optimization
- **Database Size Information** - Database and table size statistics
- **Table Statistics** - Column statistics, null fractions, distinct values
- **Active Connections** - Monitor current database connections
- **Locks Information** - View database locks and blocking queries
- **Slow Queries Analysis** - Identify performance bottlenecks (requires pg_stat_statements)

#### Administrative Operations
- **Table Backup** - Create table copies with or without data
- **Index Creation** - Create indexes on tables (regular or unique)
- **Table Optimization** - VACUUM and ANALYZE tables for performance

#### Utility Operations
- **Echo Tool** - Simple echo for testing connectivity

## Available Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `echo` | Echo back input message | `message` (string) |
| `postgres_connection_test` | Test PostgreSQL connection | None |
| `postgres_query` | Execute SQL query | `query` (string), `params` (array, optional) |
| `postgres_schema` | Get database schema | None |
| `postgres_table_info` | Get table information | `table_name` (string), `schema` (string, default: "public") |
| `postgres_query_analyze` | Analyze query performance | `query` (string) |
| `postgres_database_size` | Get database size info | None |
| `postgres_table_stats` | Get table statistics | `table_name` (string), `schema` (string, default: "public") |
| `postgres_active_connections` | Get active connections | None |
| `postgres_backup_table` | Backup table | `source_table` (string), `backup_table` (string), `schema` (string), `include_data` (boolean) |
| `postgres_create_index` | Create table index | `table_name` (string), `column_names` (array), `index_name` (string, optional), `schema` (string), `unique` (boolean) |
| `postgres_slow_queries` | Get slow queries | `limit` (integer, default: 10) |
| `postgres_optimize_table` | Optimize table | `table_name` (string), `schema` (string, default: "public") |
| `postgres_locks_info` | Get database locks | None |

## Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd pg-mcp
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
# or using pyproject.toml
pip install -e .
```

3. **Configure PostgreSQL connection:**
Edit `app/config.py` with your PostgreSQL settings:
```python
POSTGRES_DB_CONFIG = {
    "host": "localhost",
    "port": "5432", 
    "dbname": "your_database",
    "user": "your_username",
    "password": "your_password"
}
```

4. **Set API key:**
Update `MCP_API_KEY` in `app/config.py` or set environment variable.

## Usage

### Start the Server
```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### VS Code Integration

1. **Install MCP extension** in VS Code
2. **Configure MCP settings** in `.vscode/mcp.json`:
```json
{
  "mcpServers": {
    "postgres-mcp": {
      "name": "PostgreSQL MCP Server",
      "url": "http://localhost:8000/mcp",
      "apiKey": "your-secret-mcp-api-key"
    }
  }
}
```

### Direct API Usage

**Test connection:**
```bash
curl -X GET http://localhost:8000/mcp \
  -H "Authorization: Bearer your-secret-mcp-api-key"
```

**Execute query:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-secret-mcp-api-key" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "postgres_query",
      "arguments": {
        "query": "SELECT version()"
      }
    }
  }'
```

## Testing

### Comprehensive Test Suite
```bash
# Run unit tests
pytest test/

# Run comprehensive integration test
python test_postgres_mcp_comprehensive.py
```

### Individual Tool Testing
```bash
# Test specific functionality
python test_postgres_mcp.py
```

## Architecture

```
pg-mcp/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── mcp.py               # MCP server implementation
│   ├── postgres_service.py  # PostgreSQL service layer
│   ├── postgres_mock.py     # Mock service for testing
│   ├── json_rpc.py          # JSON-RPC 2.0 implementation
│   ├── auth.py              # Authentication middleware
│   ├── config.py            # Configuration settings
│   └── logger.py            # Logging configuration
├── test/                    # Test files
├── .vscode/
│   └── mcp.json            # VS Code MCP configuration
└── pyproject.toml          # Project dependencies
```

## Key Features

### 🔒 Security
- **API key authentication** for all requests
- **SQL injection protection** through parameterized queries
- **Error sanitization** to prevent information leakage

### 🚀 Performance
- **Connection pooling** for database connections
- **Async/await** support throughout
- **Query optimization** tools and analysis

### 🛠️ Development
- **Auto-reload** support for development
- **Comprehensive logging** for debugging
- **Mock service** for testing without real database
- **Type hints** throughout codebase

### 🔧 Reliability
- **Automatic fallback** to mock service
- **Comprehensive error handling**
- **Connection retry logic**
- **Graceful degradation**

## Examples

### Query Execution
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "postgres_query",
    "arguments": {
      "query": "SELECT * FROM users WHERE active = $1",
      "params": ["true"]
    }
  }
}
```

### Table Backup
```json
{
  "jsonrpc": "2.0", 
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "postgres_backup_table",
    "arguments": {
      "source_table": "users",
      "backup_table": "users_backup_20240115",
      "schema": "public",
      "include_data": true
    }
  }
}
```

### Index Creation
```json
{
  "jsonrpc": "2.0",
  "id": 3, 
  "method": "tools/call",
  "params": {
    "name": "postgres_create_index",
    "arguments": {
      "table_name": "users",
      "column_names": ["email", "status"], 
      "index_name": "idx_users_email_status",
      "unique": false
    }
  }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the test files for usage examples
- Review the comprehensive test suite for full API coverage
