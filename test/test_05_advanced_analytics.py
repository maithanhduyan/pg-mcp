"""
Test 5: Advanced Analytics & Business Intelligence
Tests pg-mcp advanced analytical capabilities for enterprise BI
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


async def execute_analyze_query(query, description):
    """Helper function to execute query analysis via pg-mcp"""
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "postgres_query_analyze",
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


async def test_advanced_analytics():
    """Test advanced analytics and business intelligence capabilities"""
    
    print("=== Test 5: Advanced Analytics & Business Intelligence ===\n")
    
    test_results = {}
    
    # Test 5.1: Cross-Module Data Integration
    print("5.1 Testing Cross-Module Data Integration...")
    integration_query = """
    WITH business_metrics AS (
        -- Sales Revenue
        SELECT 
            'Sales' as business_unit,
            'Revenue' as metric_type,
            SUM(total_amount) as metric_value,
            COUNT(*) as transaction_count,
            '2024' as period
        FROM sales.sales_transactions
        WHERE sale_date >= '2024-01-01'
        
        UNION ALL
        
        -- HR Costs
        SELECT 
            'HR' as business_unit,
            'Payroll_Cost' as metric_type,
            SUM(salary * 12) as metric_value,
            COUNT(*) as employee_count,
            '2024' as period
        FROM hr.employees 
        WHERE status = 'Active'
        
        UNION ALL
        
        -- Portfolio Value
        SELECT 
            'Portfolio' as business_unit,
            'Asset_Value' as metric_type,
            SUM(market_value) as metric_value,
            COUNT(*) as holding_count,
            '2024' as period
        FROM portfolio.holdings
    )
    SELECT 
        business_unit,
        metric_type,
        ROUND(metric_value, 2) as metric_value,
        transaction_count as supporting_count,
        period,
        ROUND((metric_value * 100.0 / SUM(metric_value) OVER()), 2) as percentage_of_total
    FROM business_metrics
    ORDER BY metric_value DESC;
    """
    
    success, result = await execute_query(integration_query, "Cross-module business metrics integration")
    test_results["cross_module_integration"] = success
    if success:
        if "percentage_of_total" in result and "business_unit" in result:
            print("   Successfully integrated data from Sales, HR, and Portfolio modules")
    
    # Test 5.2: Complex Window Functions & Analytics
    print("\n5.2 Testing Advanced Window Functions...")
    window_functions_query = """
    WITH sales_analysis AS (
        SELECT 
            sr.name as sales_rep,
            sr.region,
            st.sale_date,
            st.total_amount,
            -- Window functions for analytics
            ROW_NUMBER() OVER (PARTITION BY sr.region ORDER BY st.total_amount DESC) as deal_rank_in_region,
            RANK() OVER (ORDER BY st.total_amount DESC) as overall_deal_rank,
            LAG(st.total_amount) OVER (PARTITION BY sr.id ORDER BY st.sale_date) as previous_deal_amount,
            LEAD(st.sale_date) OVER (PARTITION BY sr.id ORDER BY st.sale_date) as next_deal_date,
            AVG(st.total_amount) OVER (PARTITION BY sr.region) as region_avg_deal_size,
            SUM(st.total_amount) OVER (PARTITION BY sr.id ORDER BY st.sale_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as cumulative_sales,
            COUNT(*) OVER (PARTITION BY sr.region) as total_deals_in_region,
            PERCENT_RANK() OVER (ORDER BY st.total_amount) as deal_percentile
        FROM sales.sales_reps sr
        JOIN sales.sales_transactions st ON sr.id = st.sales_rep_id
        WHERE st.status = 'Completed'
    )
    SELECT 
        sales_rep,
        region,
        total_amount,
        deal_rank_in_region,
        overall_deal_rank,
        previous_deal_amount,
        ROUND(region_avg_deal_size, 2) as region_avg_deal_size,
        ROUND(cumulative_sales, 2) as cumulative_sales,
        ROUND(deal_percentile * 100, 2) as deal_percentile,
        CASE 
            WHEN deal_percentile >= 0.9 THEN 'Top 10%'
            WHEN deal_percentile >= 0.75 THEN 'Top 25%'
            WHEN deal_percentile >= 0.5 THEN 'Above Average'
            ELSE 'Below Average'
        END as performance_tier
    FROM sales_analysis
    ORDER BY overall_deal_rank
    LIMIT 15;
    """
    
    success, result = await execute_query(window_functions_query, "Advanced window functions and analytics")
    test_results["window_functions"] = success
    if success:
        if "deal_percentile" in result and "performance_tier" in result:
            print("   Successfully executed complex window functions and ranking analytics")
    
    # Test 5.3: Statistical Analysis Functions
    print("\n5.3 Testing Statistical Analysis...")
    statistical_query = """
    WITH performance_stats AS (
        SELECT 
            d.name as department,
            -- Basic statistics
            COUNT(e.id) as employee_count,
            AVG(e.salary) as mean_salary,
            STDDEV(e.salary) as salary_std_dev,
            VAR_POP(e.salary) as salary_variance,
            
            -- Percentiles
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY e.salary) as q1_salary,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY e.salary) as median_salary,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY e.salary) as q3_salary,
            PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY e.salary) as p90_salary,
            
            -- Performance correlations
            CORR(e.salary, pr.rating) as salary_rating_correlation,
            CORR(EXTRACT(YEAR FROM AGE(CURRENT_DATE, e.hire_date)), e.salary) as tenure_salary_correlation,
            
            -- Advanced metrics
            COUNT(CASE WHEN pr.rating >= 4 THEN 1 END) as high_performers,
            COUNT(CASE WHEN pr.rating <= 2 THEN 1 END) as low_performers
        FROM hr.departments d
        LEFT JOIN hr.employees e ON d.id = e.department_id AND e.status = 'Active'
        LEFT JOIN hr.performance_reviews pr ON e.id = pr.employee_id
        GROUP BY d.id, d.name
        HAVING COUNT(e.id) > 0
    )
    SELECT 
        department,
        employee_count,
        ROUND(mean_salary, 2) as mean_salary,
        ROUND(salary_std_dev, 2) as salary_std_dev,
        ROUND(median_salary, 2) as median_salary,
        ROUND(q1_salary, 2) as q1_salary,
        ROUND(q3_salary, 2) as q3_salary,
        ROUND(salary_rating_correlation, 3) as salary_rating_correlation,
        ROUND(tenure_salary_correlation, 3) as tenure_salary_correlation,
        high_performers,
        low_performers,
        ROUND((high_performers * 100.0 / employee_count), 2) as high_performer_percentage,
        CASE 
            WHEN salary_rating_correlation > 0.5 THEN 'Strong Pay-Performance Link'
            WHEN salary_rating_correlation > 0.2 THEN 'Moderate Pay-Performance Link'
            ELSE 'Weak Pay-Performance Link'
        END as compensation_assessment
    FROM performance_stats
    ORDER BY employee_count DESC;
    """
    
    success, result = await execute_query(statistical_query, "Statistical analysis with correlations and percentiles")
    test_results["statistical_analysis"] = success
    if success:
        if "salary_rating_correlation" in result and "compensation_assessment" in result:
            print("   Successfully computed statistical measures and correlation analysis")
    
    # Test 5.4: Time Series Analysis
    print("\n5.4 Testing Time Series Analysis...")
    time_series_query = """
    WITH monthly_metrics AS (
        SELECT 
            DATE_TRUNC('month', st.sale_date) as month,
            COUNT(*) as monthly_transactions,
            SUM(st.total_amount) as monthly_revenue,
            AVG(st.total_amount) as avg_deal_size,
            COUNT(DISTINCT st.customer_id) as unique_customers
        FROM sales.sales_transactions st
        WHERE st.status = 'Completed'
        GROUP BY DATE_TRUNC('month', st.sale_date)
    ),
    time_series_analytics AS (
        SELECT 
            month,
            monthly_transactions,
            monthly_revenue,
            avg_deal_size,
            unique_customers,
            
            -- Period-over-period analysis
            LAG(monthly_revenue) OVER (ORDER BY month) as prev_month_revenue,
            LAG(monthly_transactions) OVER (ORDER BY month) as prev_month_transactions,
            
            -- Moving averages
            AVG(monthly_revenue) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as revenue_3m_ma,
            AVG(monthly_transactions) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) as transactions_3m_ma,
            
            -- Growth calculations
            (monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY month)) as revenue_mom_change,
            ((monthly_revenue - LAG(monthly_revenue) OVER (ORDER BY month)) * 100.0 / LAG(monthly_revenue) OVER (ORDER BY month)) as revenue_mom_percent
        FROM monthly_metrics
    )
    SELECT 
        TO_CHAR(month, 'YYYY-MM') as month,
        monthly_transactions,
        ROUND(monthly_revenue, 2) as monthly_revenue,
        ROUND(avg_deal_size, 2) as avg_deal_size,
        unique_customers,
        ROUND(revenue_3m_ma, 2) as revenue_3m_moving_avg,
        ROUND(revenue_mom_change, 2) as revenue_mom_change,
        ROUND(revenue_mom_percent, 2) as revenue_mom_percent,
        CASE 
            WHEN revenue_mom_percent > 10 THEN 'Strong Growth'
            WHEN revenue_mom_percent > 0 THEN 'Positive Growth'
            WHEN revenue_mom_percent > -10 THEN 'Slight Decline'
            ELSE 'Significant Decline'
        END as growth_trend
    FROM time_series_analytics
    ORDER BY month;
    """
    
    success, result = await execute_query(time_series_query, "Time series analysis with trend calculations")
    test_results["time_series_analysis"] = success
    if success:
        if "revenue_mom_percent" in result and "growth_trend" in result:
            print("   Successfully performed time series analysis with growth metrics")
    
    # Test 5.5: Query Performance Analysis
    print("\n5.5 Testing Query Performance Analysis...")
    complex_performance_query = """
    SELECT 
        i.name as investor,
        p.name as portfolio,
        COUNT(h.id) as holdings,
        SUM(h.market_value) as total_value,
        AVG(h.market_value) as avg_holding_size,
        STRING_AGG(DISTINCT a.sector, ', ' ORDER BY a.sector) as sectors
    FROM portfolio.investors i
    JOIN portfolio.portfolios p ON i.id = p.investor_id
    LEFT JOIN portfolio.holdings h ON p.id = h.portfolio_id
    LEFT JOIN portfolio.assets a ON h.asset_id = a.id
    GROUP BY i.id, i.name, p.id, p.name
    HAVING COUNT(h.id) > 0
    ORDER BY total_value DESC;
    """
    
    success, result = await execute_analyze_query(complex_performance_query, "Complex query performance analysis")
    test_results["performance_analysis"] = success
    if success:
        if "Performance Metrics" in result or "Execution Time" in result:
            print("   Successfully analyzed query performance with execution metrics")
    
    # Test 5.6: Data Quality & Integrity Analysis
    print("\n5.6 Testing Data Quality Analysis...")
    data_quality_query = """
    WITH data_quality_checks AS (
        -- Check for orphaned records
        SELECT 
            'sales.transactions_without_customers' as check_name,
            COUNT(*) as issue_count,
            'Orphaned Records' as issue_type
        FROM sales.sales_transactions st
        LEFT JOIN sales.customers c ON st.customer_id = c.id
        WHERE c.id IS NULL
        
        UNION ALL
        
        SELECT 
            'hr.employees_without_departments' as check_name,
            COUNT(*) as issue_count,
            'Orphaned Records' as issue_type
        FROM hr.employees e
        LEFT JOIN hr.departments d ON e.department_id = d.id
        WHERE d.id IS NULL AND e.status = 'Active'
        
        UNION ALL
        
        -- Check for data consistency
        SELECT 
            'portfolio.negative_holdings' as check_name,
            COUNT(*) as issue_count,
            'Data Consistency' as issue_type
        FROM portfolio.holdings h
        WHERE h.quantity < 0 OR h.market_value < 0
        
        UNION ALL
        
        -- Check for missing critical data
        SELECT 
            'sales.transactions_missing_amounts' as check_name,
            COUNT(*) as issue_count,
            'Missing Data' as issue_type
        FROM sales.sales_transactions
        WHERE total_amount IS NULL OR total_amount = 0
        
        UNION ALL
        
        -- Check for performance review coverage
        SELECT 
            'hr.employees_without_reviews' as check_name,
            COUNT(*) as issue_count,
            'Missing Data' as issue_type
        FROM hr.employees e
        LEFT JOIN hr.performance_reviews pr ON e.id = pr.employee_id
        WHERE e.status = 'Active' AND pr.id IS NULL
    )
    SELECT 
        check_name,
        issue_count,
        issue_type,
        CASE 
            WHEN issue_count = 0 THEN 'PASS'
            WHEN issue_count <= 5 THEN 'WARNING'
            ELSE 'FAIL'
        END as quality_status
    FROM data_quality_checks
    ORDER BY issue_count DESC, check_name;
    """
    
    success, result = await execute_query(data_quality_query, "Data quality and integrity analysis")
    test_results["data_quality"] = success
    if success:
        if "quality_status" in result and "issue_type" in result:
            print("   Successfully performed comprehensive data quality checks")
    
    # Test 5.7: Advanced Aggregation & Grouping Sets
    print("\n5.7 Testing Advanced Aggregation...")
    grouping_sets_query = """
    SELECT 
        COALESCE(d.name, 'ALL_DEPARTMENTS') as department,
        COALESCE(e.level, 'ALL_LEVELS') as level,
        COUNT(e.id) as employee_count,
        ROUND(AVG(e.salary), 2) as avg_salary,
        ROUND(SUM(e.salary), 2) as total_salary,
        ROUND(MIN(e.salary), 2) as min_salary,
        ROUND(MAX(e.salary), 2) as max_salary,
        CASE 
            WHEN GROUPING(d.name) = 1 AND GROUPING(e.level) = 1 THEN 'GRAND_TOTAL'
            WHEN GROUPING(d.name) = 1 THEN 'LEVEL_SUBTOTAL'
            WHEN GROUPING(e.level) = 1 THEN 'DEPARTMENT_SUBTOTAL'
            ELSE 'DETAIL'
        END as aggregation_level
    FROM hr.employees e
    JOIN hr.departments d ON e.department_id = d.id
    WHERE e.status = 'Active'
    GROUP BY GROUPING SETS (
        (d.name, e.level),  -- Detail level
        (d.name),           -- Department subtotals
        (e.level),          -- Level subtotals
        ()                  -- Grand total
    )
    ORDER BY 
        CASE aggregation_level
            WHEN 'GRAND_TOTAL' THEN 1
            WHEN 'DEPARTMENT_SUBTOTAL' THEN 2
            WHEN 'LEVEL_SUBTOTAL' THEN 3
            ELSE 4
        END,
        department, level;
    """
    
    success, result = await execute_query(grouping_sets_query, "Advanced aggregation with grouping sets")
    test_results["advanced_aggregation"] = success
    if success:
        if "aggregation_level" in result and "GRAND_TOTAL" in result:
            print("   Successfully executed advanced aggregation with multiple grouping levels")
    
    # Test Summary
    print("\n=== Test 5 Summary ===")
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"Passed: {passed_tests}/{total_tests} tests")
    for test_name, result in test_results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎯 Advanced Analytics & Business Intelligence: FULLY CAPABLE")
        print("   pg-mcp demonstrates enterprise-grade analytical capabilities:")
        print("   • Cross-module data integration and consolidation")
        print("   • Advanced window functions and ranking analytics")
        print("   • Statistical analysis with correlations and percentiles")
        print("   • Time series analysis with trend calculations")
        print("   • Query performance analysis and optimization")
        print("   • Data quality and integrity monitoring")
        print("   • Advanced aggregation with grouping sets")
        print("   • Suitable for sophisticated BI and analytics platforms")
        print("   • Ready for data warehouse and analytics workloads")
    elif passed_tests >= total_tests * 0.8:
        print("\n⚠️  Advanced Analytics & Business Intelligence: MOSTLY CAPABLE")
        print("   pg-mcp handles most advanced analytics with minor issues")
    else:
        print("\n❌ Advanced Analytics & Business Intelligence: NEEDS IMPROVEMENT")
        print("   pg-mcp has significant issues with advanced analytics")
    
    return test_results


if __name__ == "__main__":
    asyncio.run(test_advanced_analytics())
