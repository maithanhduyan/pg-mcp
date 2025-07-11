"""
Test 1: Core Database Connectivity and Schema Management
Tests basic pg-mcp functionality and database operations
"""

import asyncio
import sys
import os

# Add the parent directory to the path to import the app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.mcp import PostgreSQLMCPServer, process_jsonrpc_request


async def execute_mcp_tool(tool_name, arguments=None):
    """Helper function to execute MCP tool"""
    if arguments is None:
        arguments = {}
        
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    try:
        response = await process_jsonrpc_request(request)
        if "error" not in response:
            return True, response["result"]
        else:
            return False, response["error"]
    except Exception as e:
        return False, str(e)


async def test_core_connectivity():
    """Test core database connectivity and basic operations"""
    
    print("=== Test 1: Core Database Connectivity ===\n")
    
    test_results = {}
    
    # Test 1.1: Echo Tool (JSON-RPC Protocol Test)
    print("1.1 Testing JSON-RPC Protocol with Echo...")
    success, result = await execute_mcp_tool("echo", {"message": "Test message for pg-mcp"})
    test_results["echo_test"] = success
    if success:
        print("✅ Echo tool working - JSON-RPC 2.0 protocol functional")
        print(f"   Response: {result['content'][0]['text']}")
    else:
        print(f"❌ Echo tool failed: {result}")
    
    # Test 1.2: Database Connection
    print("\n1.2 Testing Database Connection...")
    success, result = await execute_mcp_tool("postgres_connection_test")
    test_results["connection_test"] = success
    if success:
        print("✅ Database connection successful")
        print(f"   Status: {result['content'][0]['text']}")
    else:
        print(f"❌ Database connection failed: {result}")
        return test_results
    
    # Test 1.3: Schema Information
    print("\n1.3 Testing Schema Discovery...")
    success, result = await execute_mcp_tool("postgres_schema")
    test_results["schema_discovery"] = success
    if success:
        print("✅ Schema discovery successful")
        content = result["content"][0]["text"]
        
        # Count schemas and tables
        schemas = content.count("Schema:")
        tables = content.count("Table:")
        print(f"   Found {schemas} schemas and {tables} tables")
        
        # Check for expected schemas
        expected_schemas = ["portfolio", "public"]
        found_schemas = [schema for schema in expected_schemas if schema in content]
        print(f"   Expected schemas found: {found_schemas}")
    else:
        print(f"❌ Schema discovery failed: {result}")
    
    # Test 1.4: Table Information Detail
    print("\n1.4 Testing Table Information Detail...")
    success, result = await execute_mcp_tool("postgres_table_info", {
        "table_name": "holdings",
        "schema": "portfolio"
    })
    test_results["table_info"] = success
    if success:
        print("✅ Table information retrieval successful")
        content = result["content"][0]["text"]
        
        # Check for key table components
        components = ["Columns:", "Constraints:", "Indexes:"]
        found_components = [comp for comp in components if comp in content]
        print(f"   Table components found: {found_components}")
        
        # Check for expected columns
        expected_columns = ["portfolio_id", "asset_id", "quantity", "market_value"]
        found_columns = [col for col in expected_columns if col in content]
        print(f"   Expected columns found: {found_columns}")
    else:
        print(f"❌ Table information failed: {result}")
    
    # Test 1.5: Basic Query Execution
    print("\n1.5 Testing Basic Query Execution...")
    test_query = """
    SELECT 
        schemaname,
        tablename,
        tableowner
    FROM pg_tables 
    WHERE schemaname IN ('portfolio', 'public')
    ORDER BY schemaname, tablename
    LIMIT 10;
    """
    
    success, result = await execute_mcp_tool("postgres_query", {"query": test_query})
    test_results["basic_query"] = success
    if success:
        print("✅ Basic query execution successful")
        content = result["content"][0]["text"]
        
        # Check if we got results
        if "Row 1:" in content:
            rows = content.count("Row ")
            print(f"   Retrieved {rows} rows of table information")
        else:
            print("   Query executed but no rows returned")
    else:
        print(f"❌ Basic query failed: {result}")
    
    # Test 1.6: Query Performance Analysis
    print("\n1.6 Testing Query Performance Analysis...")
    perf_query = """
    SELECT COUNT(*) as total_tables
    FROM information_schema.tables 
    WHERE table_schema NOT IN ('information_schema', 'pg_catalog');
    """
    
    success, result = await execute_mcp_tool("postgres_query_analyze", {"query": perf_query})
    test_results["performance_analysis"] = success
    if success:
        print("✅ Query performance analysis successful")
        content = result["content"][0]["text"]
        
        # Check for performance metrics
        perf_indicators = ["Performance Metrics", "Execution Time", "Planning Time"]
        found_indicators = [ind for ind in perf_indicators if ind in content]
        print(f"   Performance indicators found: {found_indicators}")
    else:
        print(f"❌ Query performance analysis failed: {result}")
    
    # Summary
    print("\n=== Test 1 Summary ===")
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"Passed: {passed_tests}/{total_tests} tests")
    for test_name, result in test_results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎯 Core connectivity: FULLY FUNCTIONAL")
        print("   pg-mcp core database operations are working correctly")
    elif passed_tests >= total_tests * 0.8:
        print("\n⚠️  Core connectivity: MOSTLY FUNCTIONAL")
        print("   pg-mcp has minor issues but core functionality works")
    else:
        print("\n❌ Core connectivity: NEEDS ATTENTION")
        print("   pg-mcp has significant issues that need to be resolved")
    
    return test_results


if __name__ == "__main__":
    asyncio.run(test_core_connectivity())
