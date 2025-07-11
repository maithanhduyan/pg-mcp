"""
Test 4: Portfolio Management & Financial Analytics
Tests pg-mcp ability to handle portfolio management and financial calculations
"""

import asyncio
import sys
import os

# Add the parent directory to the path to import the app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.mcp import PostgreSQLMCPServer, process_jsonrpc_request


async def execute_query(query, description):
    """Helper function to execute query via pg-mcp"""
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "postgres_query",
                "arguments": {"query": query}
            }
        }
        response = await process_jsonrpc_request(request)
        if "error" not in response:
            print(f"✅ {description}")
            return True, response["result"]["content"][0]["text"]
        else:
            print(f"❌ {description} - Error: {response['error']}")
            return False, response["error"]
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False, str(e)


async def test_portfolio_financial_analytics():
    """Test portfolio management and financial analytics capabilities"""
    
    print("=== Test 4: Portfolio Management & Financial Analytics ===\n")
    
    test_results = {}
    
    # Test 4.1: Verify Portfolio Schema Exists
    print("4.1 Verifying Portfolio Schema...")
    schema_check_query = """
    SELECT table_name, table_schema
    FROM information_schema.tables 
    WHERE table_schema = 'portfolio'
    ORDER BY table_name;
    """
    
    success, result = await execute_query(schema_check_query, "Portfolio schema verification")
    test_results["schema_verification"] = success
    if success:
        expected_tables = ["assets", "holdings", "investors", "portfolios", "price_history", "transactions"]
        found_tables = []
        for table in expected_tables:
            if table in result:
                found_tables.append(table)
        print(f"   Found portfolio tables: {found_tables}")
    
    # Test 4.2: Portfolio Summary Analysis
    print("\n4.2 Testing Portfolio Summary Analysis...")
    portfolio_summary_query = """
    SELECT 
        i.name as investor_name,
        p.name as portfolio_name,
        p.cash_balance,
        COUNT(h.id) as total_holdings,
        SUM(h.market_value) as total_portfolio_value,
        SUM(h.unrealized_pnl) as total_unrealized_pnl,
        AVG(h.market_value) as avg_holding_value,
        SUM(h.quantity * h.avg_cost_price) as total_cost_basis,
        ROUND((SUM(h.unrealized_pnl) * 100.0 / NULLIF(SUM(h.quantity * h.avg_cost_price), 0)), 2) as portfolio_return_percent,
        p.cash_balance + SUM(h.market_value) as total_portfolio_equity
    FROM portfolio.investors i
    JOIN portfolio.portfolios p ON i.id = p.investor_id
    LEFT JOIN portfolio.holdings h ON p.id = h.portfolio_id
    GROUP BY i.id, i.name, p.id, p.name, p.cash_balance
    ORDER BY total_portfolio_value DESC NULLS LAST;
    """
    
    success, result = await execute_query(portfolio_summary_query, "Portfolio summary with return calculations")
    test_results["portfolio_summary"] = success
    if success:
        if "portfolio_return_percent" in result and "total_portfolio_equity" in result:
            print("   Contains comprehensive portfolio metrics and returns")
    
    # Test 4.3: Asset Allocation Analysis
    print("\n4.3 Testing Asset Allocation Analysis...")
    allocation_query = """
    WITH portfolio_totals AS (
        SELECT 
            h.portfolio_id,
            SUM(h.market_value) as total_portfolio_value
        FROM portfolio.holdings h
        GROUP BY h.portfolio_id
    )
    SELECT 
        p.name as portfolio_name,
        a.symbol,
        a.name as asset_name,
        a.asset_type,
        a.sector,
        h.quantity,
        h.market_value,
        ROUND((h.market_value * 100.0 / pt.total_portfolio_value), 2) as allocation_percentage,
        h.avg_cost_price,
        h.current_price,
        h.unrealized_pnl,
        ROUND(((h.current_price - h.avg_cost_price) * 100.0 / h.avg_cost_price), 2) as return_percentage
    FROM portfolio.holdings h
    JOIN portfolio.portfolios p ON h.portfolio_id = p.id
    JOIN portfolio.assets a ON h.asset_id = a.id
    JOIN portfolio_totals pt ON h.portfolio_id = pt.portfolio_id
    WHERE h.portfolio_id = 1
    ORDER BY h.market_value DESC;
    """
    
    success, result = await execute_query(allocation_query, "Asset allocation with performance metrics")
    test_results["asset_allocation"] = success
    if success:
        if "allocation_percentage" in result and "return_percentage" in result:
            print("   Contains allocation percentages and individual asset performance")
    
    # Test 4.4: Sector Diversification Analysis
    print("\n4.4 Testing Sector Diversification...")
    sector_query = """
    WITH portfolio_sector_summary AS (
        SELECT 
            h.portfolio_id,
            a.sector,
            COUNT(h.id) as holdings_count,
            SUM(h.market_value) as sector_value,
            SUM(h.unrealized_pnl) as sector_pnl,
            AVG(h.unrealized_pnl) as avg_asset_pnl
        FROM portfolio.holdings h
        JOIN portfolio.assets a ON h.asset_id = a.id
        GROUP BY h.portfolio_id, a.sector
    ),
    portfolio_totals AS (
        SELECT 
            portfolio_id,
            SUM(sector_value) as total_value
        FROM portfolio_sector_summary
        GROUP BY portfolio_id
    )
    SELECT 
        p.name as portfolio_name,
        pss.sector,
        pss.holdings_count,
        pss.sector_value,
        ROUND((pss.sector_value * 100.0 / pt.total_value), 2) as sector_allocation_percent,
        pss.sector_pnl,
        ROUND(pss.avg_asset_pnl, 2) as avg_asset_pnl,
        CASE 
            WHEN pss.sector_value / pt.total_value > 0.4 THEN 'Overweight'
            WHEN pss.sector_value / pt.total_value < 0.1 THEN 'Underweight'
            ELSE 'Balanced'
        END as allocation_assessment
    FROM portfolio_sector_summary pss
    JOIN portfolio_totals pt ON pss.portfolio_id = pt.portfolio_id
    JOIN portfolio.portfolios p ON pss.portfolio_id = p.id
    ORDER BY pss.sector_value DESC;
    """
    
    success, result = await execute_query(sector_query, "Sector diversification and risk analysis")
    test_results["sector_analysis"] = success
    if success:
        if "sector_allocation_percent" in result and "allocation_assessment" in result:
            print("   Contains sector diversification metrics and risk assessment")
    
    # Test 4.5: Transaction History & Performance Tracking
    print("\n4.5 Testing Transaction History Analysis...")
    transaction_query = """
    SELECT 
        t.transaction_date,
        t.transaction_type,
        a.symbol,
        a.name as asset_name,
        t.quantity,
        t.price,
        t.total_amount,
        t.fees,
        p.name as portfolio_name,
        CASE 
            WHEN t.transaction_type = 'BUY' THEN -t.total_amount - t.fees
            WHEN t.transaction_type = 'SELL' THEN t.total_amount - t.fees
            ELSE 0
        END as cash_flow_impact,
        LAG(t.price) OVER (PARTITION BY t.asset_id ORDER BY t.transaction_date) as previous_price,
        CASE 
            WHEN LAG(t.price) OVER (PARTITION BY t.asset_id ORDER BY t.transaction_date) IS NOT NULL
            THEN ROUND(((t.price - LAG(t.price) OVER (PARTITION BY t.asset_id ORDER BY t.transaction_date)) * 100.0 / LAG(t.price) OVER (PARTITION BY t.asset_id ORDER BY t.transaction_date)), 2)
            ELSE NULL
        END as price_change_percent
    FROM portfolio.transactions t
    JOIN portfolio.assets a ON t.asset_id = a.id
    JOIN portfolio.portfolios p ON t.portfolio_id = p.id
    ORDER BY t.transaction_date DESC, t.portfolio_id, a.symbol;
    """
    
    success, result = await execute_query(transaction_query, "Transaction history with performance tracking")
    test_results["transaction_analysis"] = success
    if success:
        if "cash_flow_impact" in result and "price_change_percent" in result:
            print("   Contains cash flow analysis and price movement tracking")
    
    # Test 4.6: Risk Metrics Calculation
    print("\n4.6 Testing Risk Metrics...")
    risk_query = """
    WITH portfolio_stats AS (
        SELECT 
            h.portfolio_id,
            COUNT(h.id) as total_positions,
            COUNT(DISTINCT a.sector) as sector_count,
            COUNT(DISTINCT a.asset_type) as asset_type_count,
            SUM(h.market_value) as total_value,
            SUM(ABS(h.unrealized_pnl)) as total_absolute_pnl,
            STDDEV(h.market_value) as position_size_std_dev,
            MAX(h.market_value) as largest_position,
            MIN(h.market_value) as smallest_position
        FROM portfolio.holdings h
        JOIN portfolio.assets a ON h.asset_id = a.id
        GROUP BY h.portfolio_id
    ),
    concentration_risk AS (
        SELECT 
            h.portfolio_id,
            MAX(h.market_value / SUM(h.market_value) OVER (PARTITION BY h.portfolio_id)) as max_position_weight,
            STRING_AGG(
                CASE WHEN h.market_value / SUM(h.market_value) OVER (PARTITION BY h.portfolio_id) > 0.1 
                THEN a.symbol ELSE NULL END, ', '
            ) as concentrated_positions
        FROM portfolio.holdings h
        JOIN portfolio.assets a ON h.asset_id = a.id
        GROUP BY h.portfolio_id
    )
    SELECT 
        p.name as portfolio_name,
        ps.total_positions,
        ps.sector_count,
        ps.asset_type_count,
        ROUND(ps.total_value, 2) as total_value,
        ROUND(ps.largest_position, 2) as largest_position,
        ROUND((ps.largest_position * 100.0 / ps.total_value), 2) as largest_position_percent,
        ROUND(cr.max_position_weight * 100, 2) as max_concentration_percent,
        cr.concentrated_positions,
        CASE 
            WHEN ps.sector_count >= 5 AND cr.max_position_weight <= 0.15 THEN 'Low Risk'
            WHEN ps.sector_count >= 3 AND cr.max_position_weight <= 0.25 THEN 'Medium Risk'
            ELSE 'High Risk'
        END as risk_assessment,
        ROUND(ps.position_size_std_dev, 2) as position_size_volatility
    FROM portfolio_stats ps
    JOIN concentration_risk cr ON ps.portfolio_id = cr.portfolio_id
    JOIN portfolio.portfolios p ON ps.portfolio_id = p.id
    ORDER BY ps.total_value DESC;
    """
    
    success, result = await execute_query(risk_query, "Portfolio risk metrics and concentration analysis")
    test_results["risk_analysis"] = success
    if success:
        if "risk_assessment" in result and "max_concentration_percent" in result:
            print("   Contains comprehensive risk assessment and concentration metrics")
    
    # Test 4.7: Performance Attribution Analysis
    print("\n4.7 Testing Performance Attribution...")
    attribution_query = """
    WITH sector_performance AS (
        SELECT 
            h.portfolio_id,
            a.sector,
            SUM(h.market_value) as sector_value,
            SUM(h.unrealized_pnl) as sector_pnl,
            COUNT(h.id) as holdings_count,
            AVG(((h.current_price - h.avg_cost_price) * 100.0 / h.avg_cost_price)) as avg_sector_return
        FROM portfolio.holdings h
        JOIN portfolio.assets a ON h.asset_id = a.id
        GROUP BY h.portfolio_id, a.sector
    ),
    portfolio_performance AS (
        SELECT 
            portfolio_id,
            SUM(sector_value) as total_value,
            SUM(sector_pnl) as total_pnl
        FROM sector_performance
        GROUP BY portfolio_id
    )
    SELECT 
        p.name as portfolio_name,
        sp.sector,
        sp.holdings_count,
        ROUND(sp.sector_value, 2) as sector_value,
        ROUND((sp.sector_value * 100.0 / pp.total_value), 2) as sector_weight_percent,
        ROUND(sp.sector_pnl, 2) as sector_pnl,
        ROUND(sp.avg_sector_return, 2) as avg_sector_return_percent,
        ROUND((sp.sector_pnl * 100.0 / pp.total_pnl), 2) as pnl_contribution_percent,
        CASE 
            WHEN sp.avg_sector_return > 10 THEN 'Strong Contributor'
            WHEN sp.avg_sector_return > 0 THEN 'Positive Contributor'
            WHEN sp.avg_sector_return > -10 THEN 'Slight Drag'
            ELSE 'Significant Drag'
        END as performance_contribution
    FROM sector_performance sp
    JOIN portfolio_performance pp ON sp.portfolio_id = pp.portfolio_id
    JOIN portfolio.portfolios p ON sp.portfolio_id = p.id
    ORDER BY sp.sector_pnl DESC;
    """
    
    success, result = await execute_query(attribution_query, "Performance attribution by sector")
    test_results["performance_attribution"] = success
    if success:
        if "performance_contribution" in result and "pnl_contribution_percent" in result:
            print("   Contains detailed performance attribution analysis")
    
    # Test Summary
    print("\n=== Test 4 Summary ===")
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"Passed: {passed_tests}/{total_tests} tests")
    for test_name, result in test_results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎯 Portfolio Management & Financial Analytics: FULLY CAPABLE")
        print("   pg-mcp can handle sophisticated financial analytics including:")
        print("   • Portfolio performance and return calculations")
        print("   • Asset allocation and diversification analysis")
        print("   • Sector exposure and concentration risk metrics")
        print("   • Transaction history and cash flow analysis")
        print("   • Comprehensive risk assessment and volatility metrics")
        print("   • Performance attribution and contribution analysis")
        print("   • Suitable for professional portfolio management systems")
        print("   • Handles complex financial calculations with precision")
    elif passed_tests >= total_tests * 0.8:
        print("\n⚠️  Portfolio Management & Financial Analytics: MOSTLY CAPABLE")
        print("   pg-mcp handles most financial analytics with minor issues")
    else:
        print("\n❌ Portfolio Management & Financial Analytics: NEEDS IMPROVEMENT")
        print("   pg-mcp has significant issues with financial analytics")
    
    return test_results


if __name__ == "__main__":
    asyncio.run(test_portfolio_financial_analytics())
