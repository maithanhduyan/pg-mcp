"""
Test cases for Portfolio Management using pg-mcp as core engine.
This demonstrates how external applications like Portfolio Management systems
can leverage pg-mcp for database operations and analytics.
"""

import pytest
import asyncio
import json
from decimal import Decimal
from datetime import datetime, date
import sys
import os
import pytest_asyncio

# Add the parent directory to the path to import the app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.mcp import PostgreSQLMCPServer, process_jsonrpc_request


class PortfolioManagementAPI:
    """
    Portfolio Management API that uses pg-mcp as core database engine.
    This simulates how external applications would interact with pg-mcp.
    """
    
    def __init__(self):
        self.mcp_server = PostgreSQLMCPServer()
    
    async def execute_mcp_tool(self, tool_name: str, arguments: dict = None):
        """Execute MCP tool and return result"""
        if arguments is None:
            arguments = {}
            
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = await process_jsonrpc_request(request_data)
        
        if "error" in response:
            raise Exception(f"MCP Error: {response['error']}")
            
        return response["result"]
    
    async def get_portfolio_summary(self, investor_id: int):
        """Get portfolio summary for an investor"""
        query = """
        SELECT 
            p.id as portfolio_id,
            p.name as portfolio_name,
            p.description,
            p.cash_balance,
            COALESCE(SUM(h.market_value), 0) as total_holdings_value,
            p.cash_balance + COALESCE(SUM(h.market_value), 0) as total_portfolio_value,
            COALESCE(SUM(h.unrealized_pnl), 0) as total_unrealized_pnl,
            COUNT(h.id) as number_of_holdings
        FROM portfolio.portfolios p
        LEFT JOIN portfolio.holdings h ON p.id = h.portfolio_id
        WHERE p.investor_id = %s
        GROUP BY p.id, p.name, p.description, p.cash_balance
        ORDER BY total_portfolio_value DESC
        """
        
        result = await self.execute_mcp_tool("postgres_query", {
            "query": query.replace("%s", str(investor_id))
        })
        
        return result
    
    async def get_asset_allocation(self, portfolio_id: int):
        """Get asset allocation breakdown for a portfolio"""
        query = """
        SELECT 
            a.asset_type,
            a.sector,
            SUM(h.market_value) as market_value,
            SUM(h.quantity) as total_quantity,
            ROUND(
                (SUM(h.market_value) * 100.0 / 
                 (SELECT SUM(market_value) FROM portfolio.holdings WHERE portfolio_id = %s)
                ), 2
            ) as allocation_percentage
        FROM portfolio.holdings h
        JOIN portfolio.assets a ON h.asset_id = a.id
        WHERE h.portfolio_id = %s
        GROUP BY a.asset_type, a.sector
        ORDER BY market_value DESC
        """
        
        result = await self.execute_mcp_tool("postgres_query", {
            "query": query.replace("%s", str(portfolio_id))
        })
        
        return result
    
    async def get_performance_metrics(self, portfolio_id: int):
        """Calculate portfolio performance metrics"""
        query = """
        WITH portfolio_metrics AS (
            SELECT 
                p.id as portfolio_id,
                p.name,
                SUM(h.market_value) as current_value,
                SUM(h.quantity * h.avg_cost_price) as cost_basis,
                SUM(h.unrealized_pnl) as unrealized_pnl,
                CASE 
                    WHEN SUM(h.quantity * h.avg_cost_price) > 0 
                    THEN ROUND((SUM(h.unrealized_pnl) * 100.0 / SUM(h.quantity * h.avg_cost_price)), 2)
                    ELSE 0
                END as return_percentage
            FROM portfolio.portfolios p
            LEFT JOIN portfolio.holdings h ON p.id = h.portfolio_id
            WHERE p.id = %s
            GROUP BY p.id, p.name
        ),
        transaction_summary AS (
            SELECT 
                COUNT(*) as total_transactions,
                SUM(CASE WHEN transaction_type = 'buy' THEN 1 ELSE 0 END) as buy_transactions,
                SUM(CASE WHEN transaction_type = 'sell' THEN 1 ELSE 0 END) as sell_transactions,
                SUM(CASE WHEN transaction_type = 'dividend' THEN total_amount ELSE 0 END) as total_dividends
            FROM portfolio.transactions
            WHERE portfolio_id = %s
        )
        SELECT 
            pm.*,
            ts.total_transactions,
            ts.buy_transactions,
            ts.sell_transactions,
            ts.total_dividends
        FROM portfolio_metrics pm
        CROSS JOIN transaction_summary ts
        """
        
        result = await self.execute_mcp_tool("postgres_query", {
            "query": query.replace("%s", str(portfolio_id))
        })
        
        return result
    
    async def get_top_performers(self, portfolio_id: int, limit: int = 5):
        """Get top performing assets in portfolio"""
        query = """
        SELECT 
            a.symbol,
            a.name,
            a.asset_type,
            h.quantity,
            h.avg_cost_price,
            h.current_price,
            h.market_value,
            h.unrealized_pnl,
            CASE 
                WHEN h.avg_cost_price > 0 
                THEN ROUND((h.unrealized_pnl * 100.0 / (h.quantity * h.avg_cost_price)), 2)
                ELSE 0
            END as return_percentage
        FROM portfolio.holdings h
        JOIN portfolio.assets a ON h.asset_id = a.id
        WHERE h.portfolio_id = %s
        ORDER BY return_percentage DESC
        LIMIT %s
        """
        
        result = await self.execute_mcp_tool("postgres_query", {
            "query": query.replace("%s", str(portfolio_id)).replace("%s", str(limit))
        })
        
        return result
    
    async def calculate_risk_metrics(self, portfolio_id: int):
        """Calculate portfolio risk metrics"""
        query = """
        WITH portfolio_stats AS (
            SELECT 
                COUNT(*) as total_positions,
                SUM(h.market_value) as total_value,
                AVG(h.market_value) as avg_position_size,
                STDDEV(h.market_value) as position_size_stddev,
                MAX(h.market_value) as largest_position,
                MIN(h.market_value) as smallest_position
            FROM portfolio.holdings h
            WHERE h.portfolio_id = %s
        ),
        sector_concentration AS (
            SELECT 
                a.sector,
                SUM(h.market_value) as sector_value,
                COUNT(*) as positions_in_sector
            FROM portfolio.holdings h
            JOIN portfolio.assets a ON h.asset_id = a.id
            WHERE h.portfolio_id = %s
            GROUP BY a.sector
            ORDER BY sector_value DESC
            LIMIT 1
        )
        SELECT 
            ps.*,
            sc.sector as largest_sector,
            sc.sector_value as largest_sector_value,
            ROUND((sc.sector_value * 100.0 / ps.total_value), 2) as largest_sector_percentage
        FROM portfolio_stats ps
        CROSS JOIN sector_concentration sc
        """
        
        result = await self.execute_mcp_tool("postgres_query", {
            "query": query.replace("%s", str(portfolio_id))
        })
        
        return result
    
    async def get_transaction_history(self, portfolio_id: int, limit: int = 20):
        """Get recent transaction history"""
        query = """
        SELECT 
            t.id,
            a.symbol,
            a.name,
            t.transaction_type,
            t.quantity,
            t.price,
            t.total_amount,
            t.fees,
            t.transaction_date,
            t.notes
        FROM portfolio.transactions t
        JOIN portfolio.assets a ON t.asset_id = a.id
        WHERE t.portfolio_id = %s
        ORDER BY t.transaction_date DESC
        LIMIT %s
        """
        
        result = await self.execute_mcp_tool("postgres_query", {
            "query": query.replace("%s", str(portfolio_id)).replace("%s", str(limit))
        })
        
        return result


@pytest.mark.asyncio
class TestPortfolioManagement:
    """Test Portfolio Management functionality using pg-mcp"""
    
    async def test_connection(self):
        """Test database connection through MCP"""
        portfolio_api = PortfolioManagementAPI()
        result = await portfolio_api.execute_mcp_tool("postgres_connection_test")
        
        assert "content" in result
        assert len(result["content"]) > 0
        assert "PostgreSQL Connection Test: SUCCESS" in result["content"][0]["text"]
        assert result["isError"] == False
    
    async def test_portfolio_summary(self):
        """Test getting portfolio summary for an investor"""
        portfolio_api = PortfolioManagementAPI()
        result = await portfolio_api.get_portfolio_summary(investor_id=1)
        
        assert "content" in result
        assert result["isError"] == False
        
        # Check that we have portfolio data
        content_text = result["content"][0]["text"]
        assert "Query executed successfully" in content_text
        assert "Row 1:" in content_text
    
    async def test_asset_allocation(self):
        """Test asset allocation analysis"""
        portfolio_api = PortfolioManagementAPI()
        result = await portfolio_api.get_asset_allocation(portfolio_id=1)
        
        assert "content" in result
        assert result["isError"] == False
        
        content_text = result["content"][0]["text"]
        assert "Query executed successfully" in content_text
        
        # Should contain allocation data
        assert "allocation_percentage" in content_text
    
    async def test_performance_metrics(self):
        """Test portfolio performance calculations"""
        portfolio_api = PortfolioManagementAPI()
        result = await portfolio_api.get_performance_metrics(portfolio_id=1)
        
        assert "content" in result
        assert result["isError"] == False
        
        content_text = result["content"][0]["text"]
        assert "return_percentage" in content_text
        assert "unrealized_pnl" in content_text
    
    async def test_top_performers(self):
        """Test getting top performing assets"""
        portfolio_api = PortfolioManagementAPI()
        result = await portfolio_api.get_top_performers(portfolio_id=1, limit=3)
        
        assert "content" in result
        assert result["isError"] == False
        
        content_text = result["content"][0]["text"]
        assert "symbol" in content_text
        assert "return_percentage" in content_text
    
    async def test_risk_metrics(self):
        """Test portfolio risk analysis"""
        portfolio_api = PortfolioManagementAPI()
        result = await portfolio_api.calculate_risk_metrics(portfolio_id=1)
        
        assert "content" in result
        assert result["isError"] == False
        
        content_text = result["content"][0]["text"]
        assert "total_positions" in content_text
        assert "largest_sector" in content_text
    
    async def test_transaction_history(self):
        """Test transaction history retrieval"""
        portfolio_api = PortfolioManagementAPI()
        result = await portfolio_api.get_transaction_history(portfolio_id=1, limit=5)
        
        assert "content" in result
        assert result["isError"] == False
        
        content_text = result["content"][0]["text"]
        assert "transaction_type" in content_text
        assert "symbol" in content_text
    
    async def test_schema_validation(self):
        """Test portfolio schema structure"""
        portfolio_api = PortfolioManagementAPI()
        result = await portfolio_api.execute_mcp_tool("postgres_schema")
        
        assert "content" in result
        assert result["isError"] == False
        
        content_text = result["content"][0]["text"]
        
        # Check for our portfolio tables
        expected_tables = [
            "investors", "assets", "portfolios", 
            "holdings", "transactions", "price_history"
        ]
        
        for table in expected_tables:
            assert table in content_text
    
    async def test_table_structure(self):
        """Test specific table structure"""
        portfolio_api = PortfolioManagementAPI()
        result = await portfolio_api.execute_mcp_tool("postgres_table_info", {
            "table_name": "holdings",
            "schema": "portfolio"
        })
        
        assert "content" in result
        assert result["isError"] == False
        
        content_text = result["content"][0]["text"]
        
        # Check for expected columns
        expected_columns = [
            "portfolio_id", "asset_id", "quantity", 
            "avg_cost_price", "current_price", "market_value"
        ]
        
        for column in expected_columns:
            assert column in content_text
    
    async def test_performance_analysis(self):
        """Test query performance analysis"""
        portfolio_api = PortfolioManagementAPI()
        complex_query = """
        SELECT 
            i.name as investor_name,
            p.name as portfolio_name,
            SUM(h.market_value) as total_value,
            COUNT(h.id) as holdings_count,
            AVG(h.unrealized_pnl) as avg_pnl
        FROM portfolio.investors i
        JOIN portfolio.portfolios p ON i.id = p.investor_id
        LEFT JOIN portfolio.holdings h ON p.id = h.portfolio_id
        GROUP BY i.id, i.name, p.id, p.name
        ORDER BY total_value DESC
        """
        
        result = await portfolio_api.execute_mcp_tool("postgres_query_analyze", {
            "query": complex_query
        })
        
        assert "content" in result
        assert result["isError"] == False
        
        content_text = result["content"][0]["text"]
        assert "Performance Metrics" in content_text
        assert "Total Cost" in content_text
    
    async def test_data_integrity(self):
        """Test data integrity constraints"""
        portfolio_api = PortfolioManagementAPI()
        # Test referential integrity
        integrity_query = """
        SELECT 
            'holdings_portfolio_fk' as constraint_name,
            COUNT(*) as violations
        FROM portfolio.holdings h
        LEFT JOIN portfolio.portfolios p ON h.portfolio_id = p.id
        WHERE p.id IS NULL
        
        UNION ALL
        
        SELECT 
            'holdings_asset_fk' as constraint_name,
            COUNT(*) as violations
        FROM portfolio.holdings h
        LEFT JOIN portfolio.assets a ON h.asset_id = a.id
        WHERE a.id IS NULL
        
        UNION ALL
        
        SELECT 
            'portfolios_investor_fk' as constraint_name,
            COUNT(*) as violations
        FROM portfolio.portfolios p
        LEFT JOIN portfolio.investors i ON p.investor_id = i.id
        WHERE i.id IS NULL
        """
        
        result = await portfolio_api.execute_mcp_tool("postgres_query", {
            "query": integrity_query
        })
        
        assert "content" in result
        assert result["isError"] == False
        
        # All violation counts should be 0
        content_text = result["content"][0]["text"]
        assert '"violations": "0"' in content_text or '"violations": 0' in content_text


@pytest.mark.asyncio
async def test_portfolio_full_workflow():
    """Test complete portfolio management workflow"""
    api = PortfolioManagementAPI()
    
    print("\n=== Portfolio Management Integration Test ===")
    
    # 1. Test connection
    print("\n1. Testing database connection...")
    connection_result = await api.execute_mcp_tool("postgres_connection_test")
    assert connection_result["isError"] == False
    print("✅ Database connection successful")
    
    # 2. Get portfolio summary
    print("\n2. Getting portfolio summary for investor #1...")
    summary = await api.get_portfolio_summary(investor_id=1)
    assert summary["isError"] == False
    print("✅ Portfolio summary retrieved")
    
    # 3. Analyze asset allocation
    print("\n3. Analyzing asset allocation for portfolio #1...")
    allocation = await api.get_asset_allocation(portfolio_id=1)
    assert allocation["isError"] == False
    print("✅ Asset allocation analysis completed")
    
    # 4. Calculate performance metrics
    print("\n4. Calculating performance metrics...")
    performance = await api.get_performance_metrics(portfolio_id=1)
    assert performance["isError"] == False
    print("✅ Performance metrics calculated")
    
    # 5. Get top performers
    print("\n5. Getting top performing assets...")
    top_performers = await api.get_top_performers(portfolio_id=1)
    assert top_performers["isError"] == False
    print("✅ Top performers identified")
    
    # 6. Risk analysis
    print("\n6. Performing risk analysis...")
    risk_metrics = await api.calculate_risk_metrics(portfolio_id=1)
    assert risk_metrics["isError"] == False
    print("✅ Risk analysis completed")
    
    print("\n🎉 Portfolio Management integration test completed successfully!")
    print("pg-mcp successfully serves as core engine for Portfolio Management system")


if __name__ == "__main__":
    # Run the full workflow test
    asyncio.run(test_portfolio_full_workflow())
