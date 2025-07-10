# Echo MCP Server

Một ứng dụng Echo Server sử dụng Model Context Protocol (MCP) với JSON-RPC 2.0 để tích hợp với VS Code.

## Tính năng

- ✅ Tuân thủ chuẩn JSON-RPC 2.0
- ✅ Hỗ trợ MCP protocol version 2024-11-05
- ✅ Echo tool để phản hồi lại tin nhắn
- ✅ Authentication với API Key
- ✅ Logging chi tiết
- ✅ Hỗ trợ Unicode/tiếng Việt
- ✅ Error handling đầy đủ

## Cài đặt

1. Clone repository:
```bash
git clone <repository-url>
cd pg-mcp
```

2. Cài đặt dependencies:
```bash
uv sync
# hoặc
pip install -e .
```

## Chạy Server

```bash
# Sử dụng Python module
python -m app.main

# Hoặc sử dụng script entry point
pg-mcp

# Hoặc với uvicorn trực tiếp
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Server sẽ chạy tại: `http://localhost:8000`

## Cấu hình VS Code

1. Tạo file `.vscode/mcp.json`:
```json
{
    "servers": {
        "pg_mcp": {
            "url": "http://localhost:8000/mcp",
            "headers": {
                "X-API-Key": "pg-mcp-key-2025-super-secure-token"
            }
        }
    }
}
```

2. Cài đặt MCP extension trong VS Code (nếu có).

## API Endpoints

### GET /
Root endpoint trả về thông tin cơ bản.

### GET /mcp
Endpoint chính cho MCP, trả về thông tin server.

### POST /mcp
Endpoint xử lý JSON-RPC 2.0 requests.

## JSON-RPC Methods

### initialize
Khởi tạo kết nối MCP.

**Request:**
```json
{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "protocol_version": "2024-11-05",
        "client_info": {
            "name": "vscode",
            "version": "1.0.0"
        }
    },
    "id": 1
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "result": {
        "protocol_version": "2024-11-05",
        "capabilities": {
            "tools": {"listChanged": false},
            "resources": {"listChanged": false}
        },
        "server_info": {
            "name": "echo-mcp-server",
            "version": "1.0.0"
        }
    },
    "id": 1
}
```

### tools/list
Liệt kê các tools có sẵn.

**Request:**
```json
{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 2
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "result": {
        "tools": [
            {
                "name": "echo",
                "description": "Echo back the input message",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo back"
                        }
                    },
                    "required": ["message"]
                }
            }
        ]
    },
    "id": 2
}
```

### tools/call
Gọi một tool cụ thể.

**Request:**
```json
{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "echo",
        "arguments": {
            "message": "Hello, World!"
        }
    },
    "id": 3
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "result": {
        "content": [
            {
                "type": "text",
                "text": "Echo: Hello, World!"
            }
        ],
        "isError": false
    },
    "id": 3
}
```

## Testing

Chạy test script để kiểm tra server:

```bash
python test_echo_mcp.py
```

Test sẽ kiểm tra:
- ✅ Initialize connection
- ✅ List tools
- ✅ Echo tool với các message khác nhau
- ✅ Error handling cho invalid tools

## Configuration

### Environment Variables

- `HOST`: Host để bind server (default: 0.0.0.0)
- `PORT`: Port để bind server (default: 8000)
- `PGMCP_API_KEY`: API key cho authentication (default: pg-mcp-key-2025-super-secure-token)
- `JWT_SECRET_KEY`: Secret key cho JWT tokens
- `DB_PATH`: Đường dẫn đến SQLite database

### Security

Server yêu cầu API key trong header `X-API-Key` cho tất cả requests đến `/mcp` endpoints.

Default API key: `pg-mcp-key-2025-super-secure-token`

**⚠️ Lưu ý:** Thay đổi API key trong production environment!

## Architecture

```
pg-mcp/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app và entry point
│   ├── mcp.py           # Echo MCP Server implementation
│   ├── json_rpc.py      # JSON-RPC 2.0 models
│   ├── auth.py          # Authentication và API key
│   ├── db.py            # Database operations
│   ├── logger.py        # Logging configuration
│   ├── api.py           # Additional API endpoints
│   └── config.py        # Configuration
├── .vscode/
│   └── mcp.json         # VS Code MCP configuration
├── test_echo_mcp.py     # Test client
├── pyproject.toml       # Project configuration
└── README.md
```

## Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## License

MIT License - xem file LICENSE để biết thêm chi tiết.
