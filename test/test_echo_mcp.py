#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Echo MCP Server
Tests the JSON-RPC 2.0 implementation
"""

import asyncio
import json
import aiohttp
import pytest
from typing import Dict, Any


class MCPClient:
    """Simple MCP client for testing"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.request_id = 0
    
    def _get_next_id(self) -> int:
        """Get next request ID"""
        self.request_id += 1
        return self.request_id
    
    async def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send JSON-RPC 2.0 request"""
        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._get_next_id()
        }
        
        if params is not None:
            request_data["params"] = params
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/mcp",
                json=request_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    text = await response.text()
                    raise Exception(f"HTTP {response.status}: {text}")
    
    async def initialize(self) -> Dict[str, Any]:
        """Initialize MCP connection"""
        return await self.send_request("initialize", {
            "protocol_version": "2024-11-05",
            "client_info": {
                "name": "test-client",
                "version": "1.0.0"
            }
        })
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        return await self.send_request("tools/list")
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool"""
        return await self.send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
    
    async def echo(self, message: str) -> Dict[str, Any]:
        """Call echo tool"""
        return await self.call_tool("echo", {"message": message})


@pytest.mark.asyncio
async def test_mcp_server():
    """Test the Echo MCP Server"""
    
    # Configuration
    base_url = "http://localhost:8000"
    api_key = "pg-mcp-key-2025-super-secure-token"
    
    client = MCPClient(base_url, api_key)
    
    try:
        print("🔍 Testing Echo MCP Server...")
        print(f"📡 Server: {base_url}")
        print(f"🔑 API Key: {api_key[:20]}...")
        print()
        
        # Test 1: Initialize
        print("1️⃣ Testing initialization...")
        init_response = await client.initialize()
        print(f"✅ Initialize response: {json.dumps(init_response, indent=2, ensure_ascii=False)}")
        print()
        
        # Test 2: List tools
        print("2️⃣ Testing tools list...")
        tools_response = await client.list_tools()
        print(f"✅ Tools list response: {json.dumps(tools_response, indent=2, ensure_ascii=False)}")
        print()
        
        # Test 3: Echo tool
        print("3️⃣ Testing echo tool...")
        test_messages = [
            "Hello, World!",
            "Xin chào from Vietnam! 🇻🇳",
            "Test message with emoji 🚀✨",
            "Multiple\nlines\ntest"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"📝 Test {i}: Echo '{message}'")
            echo_response = await client.echo(message)
            print(f"✅ Echo response: {json.dumps(echo_response, indent=2, ensure_ascii=False)}")
            print()
        
        # Test 4: Invalid tool
        print("4️⃣ Testing invalid tool...")
        try:
            invalid_response = await client.call_tool("invalid_tool", {})
            print(f"❌ Expected error but got: {invalid_response}")
        except Exception as e:
            print(f"✅ Expected error for invalid tool: {e}")
        print()
        
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
