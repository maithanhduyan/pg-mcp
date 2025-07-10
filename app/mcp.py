
from fastapi import APIRouter, Depends, HTTPException, Request
from app.auth import verify_mcp_api_key
from app.json_rpc import (
    JsonRpcRequest, 
    JsonRpcResponse, 
    JsonRpcErrorResponse,
    UnicodeJSONResponse,
    create_error_response,
    create_success_response
)
from app.logger import get_logger
import json

logger = get_logger(__name__)
router = APIRouter(dependencies=[Depends(verify_mcp_api_key)])


class EchoMCPServer:
    """Echo MCP Server implementation using JSON-RPC 2.0"""
    
    def __init__(self):
        self.name = "echo-mcp-server"
        self.version = "1.0.0"
        
    async def handle_initialize(self, params: dict = None) -> dict:
        """Handle initialize request from MCP client"""
        return {
            "protocol_version": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": False
                },
                "resources": {
                    "listChanged": False
                }
            },
            "server_info": {
                "name": self.name,
                "version": self.version
            }
        }
    
    async def handle_tools_list(self, params: dict = None) -> dict:
        """List available tools"""
        return {
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
        }
    
    async def handle_tools_call(self, params: dict) -> dict:
        """Handle tool calls"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "echo":
            message = arguments.get("message", "")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Echo: {message}"
                    }
                ],
                "isError": False
            }
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def handle_resources_list(self, params: dict = None) -> dict:
        """List available resources"""
        return {
            "resources": []
        }
    
    async def dispatch_request(self, method: str, params: dict = None) -> dict:
        """Dispatch JSON-RPC request to appropriate handler"""
        handlers = {
            "initialize": self.handle_initialize,
            "tools/list": self.handle_tools_list,
            "tools/call": self.handle_tools_call,
            "resources/list": self.handle_resources_list,
        }
        
        handler = handlers.get(method)
        if not handler:
            raise ValueError(f"Method not found: {method}")
        
        return await handler(params)


# Global MCP server instance
mcp_server = EchoMCPServer()


async def process_jsonrpc_request(request_data: dict) -> dict:
    """Process a JSON-RPC 2.0 request"""
    try:
        # Parse request
        rpc_request = JsonRpcRequest(**request_data)
        
        # Dispatch to MCP server
        result = await mcp_server.dispatch_request(
            rpc_request.method, 
            rpc_request.params
        )
        
        # Create success response
        response = create_success_response(result, rpc_request.id)
        return response.dict()
        
    except ValueError as e:
        # Method not found or tool not found
        error_response = create_error_response(
            "METHOD_NOT_FOUND", 
            str(e), 
            request_data.get("id")
        )
        return error_response.dict()
        
    except Exception as e:
        logger.error(f"Error processing JSON-RPC request: {e}")
        error_response = create_error_response(
            "INTERNAL_ERROR", 
            "Internal server error", 
            request_data.get("id")
        )
        return error_response.dict()


# Main MCP endpoint for VS Code integration  
@router.api_route("/", methods=["GET", "POST"])
@router.api_route("", methods=["GET", "POST"])
async def mcp_endpoint(request: Request):
    """
    Main endpoint for MCP API.
    Handles both GET and POST requests with JSON-RPC 2.0 protocol.
    """
    if request.method == "GET":
        return UnicodeJSONResponse({
            "message": "Welcome to the Echo MCP API!",
            "protocol": "JSON-RPC 2.0",
            "server": {
                "name": mcp_server.name,
                "version": mcp_server.version
            }
        })
    
    elif request.method == "POST":
        try:
            request_data = await request.json()
            logger.info(f"Received JSON-RPC request: {request_data}")
            
            # Process JSON-RPC request
            response_data = await process_jsonrpc_request(request_data)
            
            logger.info(f"Sending JSON-RPC response: {response_data}")
            return UnicodeJSONResponse(response_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in request: {e}")
            error_response = create_error_response(
                "PARSE_ERROR", 
                "Invalid JSON"
            )
            return UnicodeJSONResponse(error_response.dict(), status_code=400)
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            error_response = create_error_response(
                "INTERNAL_ERROR", 
                "Internal server error"
            )
            return UnicodeJSONResponse(error_response.dict(), status_code=500)
    
    else:
        raise HTTPException(status_code=405, detail="Method Not Allowed")