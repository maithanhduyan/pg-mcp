# Examples - Echo MCP Server

## Sử dụng với curl

### 1. Kiểm tra server status
```bash
curl -X GET http://localhost:8000/
```

### 2. Kiểm tra MCP endpoint
```bash
curl -X GET http://localhost:8000/mcp \
  -H "X-API-Key: pg-mcp-key-2025-super-secure-token"
```

### 3. Initialize MCP connection
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: pg-mcp-key-2025-super-secure-token" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocol_version": "2024-11-05",
      "client_info": {
        "name": "curl-client",
        "version": "1.0.0"
      }
    },
    "id": 1
  }'
```

### 4. List available tools
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: pg-mcp-key-2025-super-secure-token" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 2
  }'
```

### 5. Call echo tool
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: pg-mcp-key-2025-super-secure-token" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "echo",
      "arguments": {
        "message": "Hello from curl!"
      }
    },
    "id": 3
  }'
```

### 6. Echo với tiếng Việt
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: pg-mcp-key-2025-super-secure-token" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "echo",
      "arguments": {
        "message": "Xin chào từ Việt Nam! 🇻🇳"
      }
    },
    "id": 4
  }'
```

## Sử dụng với Python

### Basic client
```python
import requests
import json

class SimpleMCPClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        })
        self.request_id = 0
    
    def send_request(self, method, params=None):
        self.request_id += 1
        data = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self.request_id
        }
        if params:
            data["params"] = params
        
        response = self.session.post(f"{self.base_url}/mcp", json=data)
        response.raise_for_status()
        return response.json()
    
    def echo(self, message):
        return self.send_request("tools/call", {
            "name": "echo",
            "arguments": {"message": message}
        })

# Sử dụng
client = SimpleMCPClient("http://localhost:8000", "pg-mcp-key-2025-super-secure-token")

# Initialize
init_resp = client.send_request("initialize", {
    "protocol_version": "2024-11-05",
    "client_info": {"name": "python-client", "version": "1.0.0"}
})
print("Init:", init_resp)

# Echo
echo_resp = client.echo("Hello from Python!")
print("Echo:", echo_resp)
```

## Sử dụng với JavaScript/Node.js

```javascript
const axios = require('axios');

class MCPClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.requestId = 0;
        this.client = axios.create({
            baseURL: this.baseUrl,
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': apiKey
            }
        });
    }
    
    async sendRequest(method, params = null) {
        this.requestId++;
        const data = {
            jsonrpc: "2.0",
            method: method,
            id: this.requestId
        };
        
        if (params) {
            data.params = params;
        }
        
        const response = await this.client.post('/mcp', data);
        return response.data;
    }
    
    async initialize() {
        return this.sendRequest('initialize', {
            protocol_version: "2024-11-05",
            client_info: {
                name: "js-client",
                version: "1.0.0"
            }
        });
    }
    
    async listTools() {
        return this.sendRequest('tools/list');
    }
    
    async echo(message) {
        return this.sendRequest('tools/call', {
            name: 'echo',
            arguments: { message }
        });
    }
}

// Sử dụng
(async () => {
    const client = new MCPClient('http://localhost:8000', 'pg-mcp-key-2025-super-secure-token');
    
    try {
        // Initialize
        const initResp = await client.initialize();
        console.log('Init:', JSON.stringify(initResp, null, 2));
        
        // List tools
        const toolsResp = await client.listTools();
        console.log('Tools:', JSON.stringify(toolsResp, null, 2));
        
        // Echo
        const echoResp = await client.echo('Hello from JavaScript!');
        console.log('Echo:', JSON.stringify(echoResp, null, 2));
        
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
})();
```

## Error Handling Examples

### 1. Missing API Key
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "id": 1}'
```

Response:
```json
{
  "detail": "Missing API key. Please provide X-API-Key header."
}
```

### 2. Invalid API Key
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: invalid-key" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "id": 1}'
```

Response:
```json
{
  "detail": "Invalid API key"
}
```

### 3. Unknown Method
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: pg-mcp-key-2025-super-secure-token" \
  -d '{
    "jsonrpc": "2.0",
    "method": "unknown/method",
    "id": 1
  }'
```

Response:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "Method not found: unknown/method",
    "data": null
  },
  "id": 1
}
```

### 4. Unknown Tool
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-API-Key: pg-mcp-key-2025-super-secure-token" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "unknown_tool",
      "arguments": {}
    },
    "id": 1
  }'
```

Response:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "Unknown tool: unknown_tool",
    "data": null
  },
  "id": 1
}
```
