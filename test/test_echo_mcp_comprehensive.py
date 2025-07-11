#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test suite for Echo MCP Server
Tests both direct server functionality and VS Code integration
"""

import pytest
import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.mcp import PostgreSQLMCPServer, process_jsonrpc_request


class TestPostgreSQLMCPServer:
    """Test suite for PostgreSQL MCP Server functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.server = PostgreSQLMCPServer()
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test server initialization"""
        result = await self.server.handle_initialize()
        
        assert result["protocol_version"] == "2024-11-05"
        assert "capabilities" in result
        assert "tools" in result["capabilities"]
        assert "resources" in result["capabilities"]
        assert result["server_info"]["name"] == "postgres-mcp-server"
        assert result["server_info"]["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_tools_list(self):
        """Test tools listing"""
        result = await self.server.handle_tools_list()
        
        assert "tools" in result
        assert len(result["tools"]) == 6  # Updated to match actual number of tools
        
        # Find echo tool
        echo_tool = next((tool for tool in result["tools"] if tool["name"] == "echo"), None)
        assert echo_tool is not None
        assert echo_tool["name"] == "echo"
        assert echo_tool["description"] == "Echo back the input message"
        assert "inputSchema" in echo_tool
        assert echo_tool["inputSchema"]["type"] == "object"
        assert "message" in echo_tool["inputSchema"]["properties"]
        assert echo_tool["inputSchema"]["required"] == ["message"]
    
    @pytest.mark.asyncio
    async def test_echo_tool_basic(self):
        """Test basic echo functionality"""
        params = {
            "name": "echo",
            "arguments": {
                "message": "Hello, World!"
            }
        }
        
        result = await self.server.handle_tools_call(params)
        
        assert "content" in result
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "text"
        assert result["content"][0]["text"] == "Echo: Hello, World!"
        assert result["isError"] is False
    
    @pytest.mark.asyncio
    async def test_echo_tool_unicode(self):
        """Test echo with Unicode characters"""
        params = {
            "name": "echo",
            "arguments": {
                "message": "Xin chào từ Vietnam! 🇻🇳🚀"
            }
        }
        
        result = await self.server.handle_tools_call(params)
        
        assert result["content"][0]["text"] == "Echo: Xin chào từ Vietnam! 🇻🇳🚀"
        assert result["isError"] is False
    
    @pytest.mark.asyncio
    async def test_echo_tool_multiline(self):
        """Test echo with multi-line content"""
        message = "Line 1\nLine 2\nLine 3 with emoji 🎉"
        params = {
            "name": "echo",
            "arguments": {
                "message": message
            }
        }
        
        result = await self.server.handle_tools_call(params)
        
        assert result["content"][0]["text"] == f"Echo: {message}"
        assert result["isError"] is False
    
    @pytest.mark.asyncio
    async def test_echo_tool_empty_message(self):
        """Test echo with empty message"""
        params = {
            "name": "echo",
            "arguments": {
                "message": ""
            }
        }
        
        result = await self.server.handle_tools_call(params)
        
        assert result["content"][0]["text"] == "Echo: "
        assert result["isError"] is False
    
    @pytest.mark.asyncio
    async def test_invalid_tool(self):
        """Test calling invalid tool"""
        params = {
            "name": "invalid_tool",
            "arguments": {}
        }
        
        with pytest.raises(ValueError, match="Unknown tool: invalid_tool"):
            await self.server.handle_tools_call(params)
    
    @pytest.mark.asyncio
    async def test_resources_list(self):
        """Test resources listing"""
        result = await self.server.handle_resources_list()
        
        assert "resources" in result
        assert result["resources"] == []
    
    @pytest.mark.asyncio
    async def test_dispatch_request_initialize(self):
        """Test request dispatching for initialize"""
        result = await self.server.dispatch_request("initialize")
        
        assert result["protocol_version"] == "2024-11-05"
        assert "capabilities" in result
    
    @pytest.mark.asyncio
    async def test_dispatch_request_tools_list(self):
        """Test request dispatching for tools/list"""
        result = await self.server.dispatch_request("tools/list")
        
        assert "tools" in result
        assert len(result["tools"]) == 6
    
    @pytest.mark.asyncio
    async def test_dispatch_request_tools_call(self):
        """Test request dispatching for tools/call"""
        params = {
            "name": "echo",
            "arguments": {
                "message": "Test dispatch"
            }
        }
        
        result = await self.server.dispatch_request("tools/call", params)
        
        assert result["content"][0]["text"] == "Echo: Test dispatch"
        assert result["isError"] is False
    
    @pytest.mark.asyncio
    async def test_dispatch_request_invalid_method(self):
        """Test dispatching invalid method"""
        with pytest.raises(ValueError, match="Method not found: invalid_method"):
            await self.server.dispatch_request("invalid_method")


class TestJSONRPCProcessing:
    """Test suite for JSON-RPC 2.0 processing"""
    
    @pytest.mark.asyncio
    async def test_jsonrpc_initialize_request(self):
        """Test JSON-RPC initialize request"""
        request_data = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocol_version": "2024-11-05",
                "client_info": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }
        
        response = await process_jsonrpc_request(request_data)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["protocol_version"] == "2024-11-05"
    
    @pytest.mark.asyncio
    async def test_jsonrpc_echo_request(self):
        """Test JSON-RPC echo tool request"""
        request_data = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "echo",
                "arguments": {
                    "message": "Test JSON-RPC echo"
                }
            },
            "id": 2
        }
        
        response = await process_jsonrpc_request(request_data)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert "result" in response
        assert response["result"]["content"][0]["text"] == "Echo: Test JSON-RPC echo"
        assert response["result"]["isError"] is False
    
    @pytest.mark.asyncio
    async def test_jsonrpc_invalid_method(self):
        """Test JSON-RPC invalid method request"""
        request_data = {
            "jsonrpc": "2.0",
            "method": "invalid/method",
            "id": 3
        }
        
        response = await process_jsonrpc_request(request_data)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 3
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "Method not found" in response["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_jsonrpc_invalid_tool(self):
        """Test JSON-RPC invalid tool request"""
        request_data = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "invalid_tool",
                "arguments": {}
            },
            "id": 4
        }
        
        response = await process_jsonrpc_request(request_data)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 4
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "Unknown tool" in response["error"]["message"]


def run_manual_tests():
    """Run manual tests that can be executed without pytest"""
    print("🔍 Running manual Echo MCP Server tests...")
    
    async def test_basic_functionality():
        server = PostgreSQLMCPServer()
        
        # Test 1: Initialize
        print("\n1️⃣ Testing initialization...")
        init_result = await server.handle_initialize()
        print(f"✅ Initialize result: {json.dumps(init_result, indent=2)}")
        
        # Test 2: Tools list
        print("\n2️⃣ Testing tools list...")
        tools_result = await server.handle_tools_list()
        print(f"✅ Tools list result: {json.dumps(tools_result, indent=2)}")
        
        # Test 3: Echo tool
        print("\n3️⃣ Testing echo tool...")
        test_messages = [
            "Hello, Manual Test!",
            "Tiếng Việt và emoji 🇻🇳🚀",
            "Multi\nline\ntest"
        ]
        
        for i, message in enumerate(test_messages, 1):
            params = {
                "name": "echo",
                "arguments": {"message": message}
            }
            echo_result = await server.handle_tools_call(params)
            print(f"✅ Echo test {i}: {echo_result['content'][0]['text']}")
        
        # Test 4: JSON-RPC processing
        print("\n4️⃣ Testing JSON-RPC processing...")
        request_data = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "echo",
                "arguments": {"message": "JSON-RPC Test"}
            },
            "id": 999
        }
        
        rpc_result = await process_jsonrpc_request(request_data)
        print(f"✅ JSON-RPC result: {json.dumps(rpc_result, indent=2)}")
        
        print("\n🎉 All manual tests completed successfully!")
    
    # Run the async tests
    asyncio.run(test_basic_functionality())


if __name__ == "__main__":
    # Check if pytest is available
    try:
        import pytest
        print("📋 Running pytest test suite...")
        # Run pytest programmatically
        exit_code = pytest.main([__file__, "-v"])
        if exit_code == 0:
            print("✅ All pytest tests passed!")
        else:
            print("❌ Some pytest tests failed!")
    except ImportError:
        print("⚠️ pytest not available, running manual tests...")
        run_manual_tests()
