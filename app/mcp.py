
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
import asyncio
from datetime import datetime, date

# Import real PostgreSQL service only
from app.postgres_service import postgres_service as real_postgres_service

logger = get_logger(__name__)
router = APIRouter(dependencies=[Depends(verify_mcp_api_key)])

# Global service management
current_service = None

async def get_postgres_service():
    """Get PostgreSQL service - real service only"""
    global current_service
    
    if current_service is None:
        await real_postgres_service.initialize_pool()
        connection_test = await real_postgres_service.test_connection()
        
        if connection_test.get("status") == "connected":
            current_service = real_postgres_service
            logger.info("PostgreSQL service initialized successfully")
        else:
            raise Exception(f"PostgreSQL connection failed: {connection_test.get('error', 'Unknown error')}")
            
    return current_service


class PostgreSQLMCPServer:
    """PostgreSQL MCP Server implementation using JSON-RPC 2.0"""
    
    def __init__(self):
        self.name = "postgres-mcp-server"
        self.version = "1.0.0"
        
    async def handle_initialize(self, params: dict = None) -> dict:
        """Handle initialize request from MCP client"""
        # Try to initialize PostgreSQL connection pool (optional)
        try:
            await get_postgres_service()
            logger.info("PostgreSQL service initialized successfully")
        except Exception as e:
            logger.warning(f"PostgreSQL service initialization failed: {e}")
        
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
                },
                {
                    "name": "postgres_connection_test",
                    "description": "Test PostgreSQL database connection",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                },
                {
                    "name": "postgres_query",
                    "description": "Execute a SQL query on PostgreSQL database",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL query to execute"
                            },
                            "params": {
                                "type": "array",
                                "description": "Query parameters (optional)",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "postgres_schema",
                    "description": "Get database schema information",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                },
                {
                    "name": "postgres_table_info",
                    "description": "Get detailed information about a specific table",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "table_name": {
                                "type": "string",
                                "description": "Name of the table"
                            },
                            "schema": {
                                "type": "string",
                                "description": "Schema name (default: public)",
                                "default": "public"
                            }
                        },
                        "required": ["table_name"]
                    }
                },
                {
                    "name": "postgres_query_analyze",
                    "description": "Analyze SQL query performance using EXPLAIN",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "SQL query to analyze"
                            }
                        },
                        "required": ["query"]
                    }
                }
            ]
        }
    
    async def handle_tools_call(self, params: dict) -> dict:
        """Handle tool calls"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            # Handle echo tool without requiring PostgreSQL connection
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
            
            # Check for valid PostgreSQL tools before trying to connect
            valid_postgres_tools = {
                "postgres_connection_test", 
                "postgres_query", 
                "postgres_schema", 
                "postgres_table_info", 
                "postgres_query_analyze"
            }
            
            if tool_name not in valid_postgres_tools:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            # For PostgreSQL tools, require PostgreSQL service
            service = await get_postgres_service()
            
            if tool_name == "postgres_connection_test":
                result = await service.test_connection()
                
                if result["status"] == "connected":
                    output = "✅ PostgreSQL Connection Test: SUCCESS\n\n"
                    output += f"Database Version: {result['version']}\n"
                    output += f"Current Database: {result['database']}\n"
                    output += f"Current User: {result['user']}\n"
                    output += f"Host: {result['connection_info']['host']}\n"
                    output += f"Port: {result['connection_info']['port']}\n"
                else:
                    output = f"❌ PostgreSQL Connection Test: FAILED\n\nError: {result['error']}"
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": output
                        }
                    ],
                    "isError": result["status"] != "connected"
                }
            
            elif tool_name == "postgres_query":
                query = arguments.get("query", "")
                params_list = arguments.get("params", [])
                
                if not query.strip():
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "Error: Query cannot be empty"
                            }
                        ],
                        "isError": True
                    }
                
                result = await service.execute_query(query, params_list)
                
                if result["success"]:
                    if result.get("query_type") == "SELECT":
                        output = f"Query executed successfully!\n"
                        output += f"Returned {result['row_count']} rows\n"
                        if result.get('columns'):
                            output += f"Columns: {', '.join(result['columns'])}\n\n"
                        
                        # Format data as table
                        if result["data"]:
                            # Show first 10 rows
                            for i, row in enumerate(result["data"][:10]):
                                # Convert any datetime objects to strings for JSON serialization
                                serializable_row = {}
                                for k, v in row.items():
                                    if isinstance(v, (datetime, date)):
                                        serializable_row[k] = v.isoformat()
                                    else:
                                        serializable_row[k] = v
                                output += f"Row {i+1}: {json.dumps(serializable_row, indent=2, ensure_ascii=False)}\n"
                            
                            if len(result["data"]) > 10:
                                output += f"... and {len(result['data']) - 10} more rows"
                    else:
                        output = f"Query executed successfully!\n"
                        output += f"Query type: {result['query_type']}\n"
                        output += f"Affected rows: {result.get('affected_rows', 'N/A')}\n"
                        output += f"Message: {result.get('message', '')}"
                else:
                    output = f"Query failed: {result['error']}"
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": output
                        }
                    ],
                    "isError": not result["success"]
                }
            
            elif tool_name == "postgres_schema":
                result = await service.get_database_schema()
                
                if result["success"]:
                    output = f"Database Schema for: {result['database']}\n"
                    output += f"Schemas: {result['schema_count']}\n"
                    output += f"Tables: {result['table_count']}\n\n"
                    
                    for table_name, table_info in result["schema"]["tables"].items():
                        output += f"Table: {table_name}\n"
                        output += f"  Owner: {table_info['owner']}\n"
                        output += f"  Columns: {len(table_info['columns'])}\n"
                        for col in table_info['columns'][:5]:  # Show first 5 columns
                            output += f"    - {col['column_name']} ({col['data_type']})\n"
                        if len(table_info['columns']) > 5:
                            output += f"    ... and {len(table_info['columns']) - 5} more columns\n"
                        output += "\n"
                else:
                    output = f"Failed to get schema: {result['error']}"
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": output
                        }
                    ],
                    "isError": not result["success"]
                }
            
            elif tool_name == "postgres_table_info":
                table_name = arguments.get("table_name", "")
                schema = arguments.get("schema", "public")
                
                if not table_name:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "Error: table_name is required"
                            }
                        ],
                        "isError": True
                    }
                
                result = await service.get_table_info(table_name, schema)
                
                if result["success"]:
                    output = f"Table Information: {schema}.{table_name}\n\n"
                    
                    # Basic info
                    table_info = result["table_info"]
                    output += f"Owner: {table_info.get('tableowner', 'N/A')}\n"
                    output += f"Has Indexes: {table_info.get('hasindexes', False)}\n"
                    output += f"Has Rules: {table_info.get('hasrules', False)}\n"
                    output += f"Has Triggers: {table_info.get('hastriggers', False)}\n"
                    output += f"Row Count: {result['row_count']}\n\n"
                    
                    # Columns
                    output += "Columns:\n"
                    for col in result["columns"]:
                        nullable = "NULL" if col["is_nullable"] == "YES" else "NOT NULL"
                        default = f" DEFAULT {col['column_default']}" if col["column_default"] else ""
                        output += f"  - {col['column_name']}: {col['data_type']} {nullable}{default}\n"
                    
                    # Indexes
                    if result["indexes"]:
                        output += "\nIndexes:\n"
                        for idx in result["indexes"]:
                            output += f"  - {idx['indexname']}\n"
                else:
                    output = f"Failed to get table info: {result['error']}"
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": output
                        }
                    ],
                    "isError": not result["success"]
                }
            
            elif tool_name == "postgres_query_analyze":
                query = arguments.get("query", "")
                
                if not query.strip():
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "Error: Query cannot be empty"
                            }
                        ],
                        "isError": True
                    }
                
                result = await service.analyze_query_performance(query)
                
                if result["success"]:
                    output = f"Query Performance Analysis\n"
                    output += f"Query: {result['query']}\n\n"
                    
                    analysis = result["analysis"]
                    output += f"Performance Metrics:\n"
                    output += f"  - Total Cost: {analysis.get('total_cost', 'N/A')}\n"
                    output += f"  - Startup Cost: {analysis.get('startup_cost', 'N/A')}\n"
                    output += f"  - Actual Time: {analysis.get('actual_time', 'N/A')} ms\n"
                    output += f"  - Rows: {analysis.get('rows', 'N/A')}\n"
                    output += f"  - Node Type: {analysis.get('node_type', 'N/A')}\n"
                    
                    output += f"\nFull Execution Plan:\n{json.dumps(result['execution_plan'], indent=2, ensure_ascii=False)}"
                else:
                    output = f"Query analysis failed: {result['error']}"
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": output
                        }
                    ],
                    "isError": not result["success"]
                }
                
        except ValueError as e:
            # Re-raise ValueError for test compatibility
            raise e
        except Exception as e:
            logger.error(f"Error in tool {tool_name}: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Tool execution error: {str(e)}"
                    }
                ],
                "isError": True
            }
    
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
mcp_server = PostgreSQLMCPServer()


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
        return response.model_dump()
        
    except ValueError as e:
        # Method not found or tool not found
        error_response = create_error_response(
            "METHOD_NOT_FOUND", 
            str(e), 
            request_data.get("id")
        )
        return error_response.model_dump()
        
    except Exception as e:
        logger.error(f"Error processing JSON-RPC request: {e}")
        error_response = create_error_response(
            "INTERNAL_ERROR", 
            "Internal server error", 
            request_data.get("id")
        )
        return error_response.model_dump()


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
            "message": "Welcome to the PostgreSQL MCP API!",
            "protocol": "JSON-RPC 2.0",
            "server": {
                "name": mcp_server.name,
                "version": mcp_server.version
            },
            "available_tools": [
                "echo",
                "postgres_connection_test",
                "postgres_query", 
                "postgres_schema",
                "postgres_table_info",
                "postgres_query_analyze"
            ]
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
            return UnicodeJSONResponse(error_response.model_dump(), status_code=400)
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            error_response = create_error_response(
                "INTERNAL_ERROR", 
                "Internal server error"
            )
            return UnicodeJSONResponse(error_response.model_dump(), status_code=500)
    
    else:
        raise HTTPException(status_code=405, detail="Method Not Allowed")