"""
Test 2: Sales & CRM Analytics Capabilities
Tests pg-mcp ability to handle sales data and CRM-like analytics
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


async def test_sales_crm_analytics():
    """Test sales and CRM analytics capabilities"""
    
    print("=== Test 2: Sales & CRM Analytics ===\n")
    
    test_results = {}
    
    # Test 2.1: Sales Schema Setup
    print("2.1 Setting up Sales Analytics Schema...")
    setup_query = """
    CREATE SCHEMA IF NOT EXISTS sales;
    
    DROP TABLE IF EXISTS sales.sales_transactions CASCADE;
    DROP TABLE IF EXISTS sales.customers CASCADE;
    DROP TABLE IF EXISTS sales.products CASCADE;
    DROP TABLE IF EXISTS sales.sales_reps CASCADE;
    
    CREATE TABLE sales.sales_reps (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        region VARCHAR(50),
        hire_date DATE,
        quota DECIMAL(12,2) DEFAULT 100000.00
    );
    
    CREATE TABLE sales.customers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        industry VARCHAR(50),
        city VARCHAR(50),
        registration_date DATE,
        customer_tier VARCHAR(20) DEFAULT 'Standard'
    );
    
    CREATE TABLE sales.products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        category VARCHAR(50),
        price DECIMAL(10,2),
        cost DECIMAL(10,2)
    );
    
    CREATE TABLE sales.sales_transactions (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER REFERENCES sales.customers(id),
        product_id INTEGER REFERENCES sales.products(id),
        sales_rep_id INTEGER REFERENCES sales.sales_reps(id),
        quantity INTEGER,
        unit_price DECIMAL(10,2),
        discount_percent DECIMAL(5,2) DEFAULT 0.00,
        total_amount DECIMAL(12,2),
        sale_date DATE,
        status VARCHAR(20) DEFAULT 'Completed'
    );
    """
    
    success, result = await execute_query(setup_query, "Sales schema creation")
    test_results["schema_setup"] = success
    
    # Test 2.2: Sample Data Insertion
    print("\n2.2 Inserting Sample Sales Data...")
    data_query = """
    INSERT INTO sales.sales_reps (name, region, hire_date, quota) VALUES
    ('Alice Johnson', 'North', '2020-01-15', 150000.00),
    ('Bob Smith', 'South', '2019-06-10', 120000.00),
    ('Carol Davis', 'East', '2021-03-20', 140000.00),
    ('David Wilson', 'West', '2020-09-05', 130000.00),
    ('Eva Martinez', 'Central', '2022-01-10', 110000.00);
    
    INSERT INTO sales.customers (name, industry, city, registration_date, customer_tier) VALUES
    ('TechCorp Inc', 'Technology', 'San Francisco', '2021-01-10', 'Enterprise'),
    ('HealthPlus Ltd', 'Healthcare', 'New York', '2020-05-15', 'Premium'),
    ('EduSoft Solutions', 'Education', 'Boston', '2021-09-20', 'Standard'),
    ('RetailMax', 'Retail', 'Chicago', '2020-11-30', 'Premium'),
    ('ManufacturePro', 'Manufacturing', 'Detroit', '2021-07-12', 'Enterprise'),
    ('StartupXYZ', 'Technology', 'Austin', '2023-03-15', 'Standard'),
    ('GlobalCorp', 'Consulting', 'Seattle', '2020-08-20', 'Enterprise');
    
    INSERT INTO sales.products (name, category, price, cost) VALUES
    ('Enterprise Software License', 'Software', 5000.00, 2000.00),
    ('Cloud Storage Package', 'Cloud Services', 1200.00, 400.00),
    ('Consulting Hours', 'Services', 150.00, 75.00),
    ('Training Package', 'Education', 800.00, 300.00),
    ('Support Contract', 'Support', 2400.00, 800.00),
    ('Analytics Dashboard', 'Software', 3500.00, 1200.00),
    ('Security Audit', 'Services', 5000.00, 2500.00);
    
    INSERT INTO sales.sales_transactions (customer_id, product_id, sales_rep_id, quantity, unit_price, discount_percent, total_amount, sale_date, status) VALUES
    (1, 1, 1, 2, 5000.00, 10.00, 9000.00, '2024-01-15', 'Completed'),
    (2, 2, 2, 5, 1200.00, 5.00, 5700.00, '2024-01-20', 'Completed'),
    (3, 4, 3, 10, 800.00, 0.00, 8000.00, '2024-02-10', 'Completed'),
    (1, 3, 1, 40, 150.00, 15.00, 5100.00, '2024-02-15', 'Completed'),
    (4, 5, 4, 1, 2400.00, 0.00, 2400.00, '2024-03-01', 'Completed'),
    (5, 1, 2, 1, 5000.00, 8.00, 4600.00, '2024-03-10', 'Completed'),
    (2, 3, 3, 20, 150.00, 10.00, 2700.00, '2024-03-20', 'Completed'),
    (6, 6, 5, 2, 3500.00, 12.00, 6160.00, '2024-04-05', 'Completed'),
    (7, 7, 1, 1, 5000.00, 5.00, 4750.00, '2024-04-15', 'Completed'),
    (5, 5, 2, 2, 2400.00, 0.00, 4800.00, '2024-05-01', 'Completed'),
    (3, 2, 4, 3, 1200.00, 0.00, 3600.00, '2024-05-10', 'Pending'),
    (4, 4, 5, 8, 800.00, 5.00, 6080.00, '2024-05-15', 'Completed');
    """
    
    success, result = await execute_query(data_query, "Sample data insertion")
    test_results["data_insertion"] = success
    
    # Test 2.3: Sales Performance by Representative
    print("\n2.3 Testing Sales Performance Analysis...")
    sales_perf_query = """
    SELECT 
        sr.name as sales_rep,
        sr.region,
        sr.quota,
        COUNT(st.id) as total_deals,
        SUM(st.total_amount) as total_revenue,
        AVG(st.total_amount) as avg_deal_size,
        MAX(st.total_amount) as largest_deal,
        ROUND((SUM(st.total_amount) * 100.0 / sr.quota), 2) as quota_achievement_percent,
        CASE 
            WHEN SUM(st.total_amount) >= sr.quota THEN 'Quota Met'
            WHEN SUM(st.total_amount) >= sr.quota * 0.8 THEN 'Close to Quota'
            ELSE 'Below Target'
        END as performance_status
    FROM sales.sales_reps sr
    LEFT JOIN sales.sales_transactions st ON sr.id = st.sales_rep_id AND st.status = 'Completed'
    GROUP BY sr.id, sr.name, sr.region, sr.quota
    ORDER BY total_revenue DESC NULLS LAST;
    """
    
    success, result = await execute_query(sales_perf_query, "Sales rep performance analysis")
    test_results["sales_performance"] = success
    if success:
        # Verify we have performance data
        if "quota_achievement_percent" in result and "performance_status" in result:
            print("   Contains quota tracking and performance status")
    
    # Test 2.4: Customer Analytics
    print("\n2.4 Testing Customer Analytics...")
    customer_analytics_query = """
    SELECT 
        c.name as customer,
        c.industry,
        c.customer_tier,
        COUNT(st.id) as total_orders,
        SUM(st.total_amount) as total_spent,
        AVG(st.total_amount) as avg_order_value,
        MIN(st.sale_date) as first_purchase,
        MAX(st.sale_date) as last_purchase,
        CASE 
            WHEN SUM(st.total_amount) >= 10000 THEN 'High Value'
            WHEN SUM(st.total_amount) >= 5000 THEN 'Medium Value'
            ELSE 'Low Value'
        END as customer_value_segment
    FROM sales.customers c
    LEFT JOIN sales.sales_transactions st ON c.id = st.customer_id AND st.status = 'Completed'
    GROUP BY c.id, c.name, c.industry, c.customer_tier
    ORDER BY total_spent DESC NULLS LAST;
    """
    
    success, result = await execute_query(customer_analytics_query, "Customer analytics and segmentation")
    test_results["customer_analytics"] = success
    if success:
        if "customer_value_segment" in result and "avg_order_value" in result:
            print("   Contains customer segmentation and value analysis")
    
    # Test 2.5: Product Performance Analysis
    print("\n2.5 Testing Product Performance...")
    product_perf_query = """
    SELECT 
        p.name as product,
        p.category,
        p.price as list_price,
        p.cost,
        COUNT(st.id) as units_sold,
        SUM(st.quantity) as total_quantity,
        SUM(st.total_amount) as total_revenue,
        SUM((st.unit_price - p.cost) * st.quantity) as total_profit,
        ROUND(AVG(st.unit_price), 2) as avg_selling_price,
        ROUND((SUM((st.unit_price - p.cost) * st.quantity) * 100.0 / SUM(st.total_amount)), 2) as profit_margin_percent
    FROM sales.products p
    LEFT JOIN sales.sales_transactions st ON p.id = st.product_id AND st.status = 'Completed'
    GROUP BY p.id, p.name, p.category, p.price, p.cost
    ORDER BY total_revenue DESC NULLS LAST;
    """
    
    success, result = await execute_query(product_perf_query, "Product performance and profitability")
    test_results["product_performance"] = success
    if success:
        if "profit_margin_percent" in result and "total_profit" in result:
            print("   Contains profitability analysis and margin calculations")
    
    # Test 2.6: Sales Trends and Forecasting Data
    print("\n2.6 Testing Sales Trends Analysis...")
    trends_query = """
    SELECT 
        TO_CHAR(sale_date, 'YYYY-MM') as month,
        COUNT(*) as transactions_count,
        COUNT(DISTINCT customer_id) as unique_customers,
        SUM(total_amount) as monthly_revenue,
        AVG(total_amount) as avg_transaction_value,
        SUM(CASE WHEN status = 'Completed' THEN total_amount ELSE 0 END) as completed_revenue,
        SUM(CASE WHEN status = 'Pending' THEN total_amount ELSE 0 END) as pending_revenue,
        ROUND(AVG(discount_percent), 2) as avg_discount_percent
    FROM sales.sales_transactions
    GROUP BY TO_CHAR(sale_date, 'YYYY-MM')
    ORDER BY month;
    """
    
    success, result = await execute_query(trends_query, "Monthly sales trends and forecasting data")
    test_results["sales_trends"] = success
    if success:
        if "pending_revenue" in result and "avg_discount_percent" in result:
            print("   Contains pipeline data and discount analysis")
    
    # Test 2.7: Regional Performance Comparison
    print("\n2.7 Testing Regional Performance...")
    regional_query = """
    WITH regional_stats AS (
        SELECT 
            sr.region,
            COUNT(DISTINCT sr.id) as sales_reps_count,
            COUNT(DISTINCT st.customer_id) as unique_customers,
            COUNT(st.id) as total_transactions,
            SUM(st.total_amount) as total_revenue,
            AVG(st.total_amount) as avg_deal_size
        FROM sales.sales_reps sr
        LEFT JOIN sales.sales_transactions st ON sr.id = st.sales_rep_id AND st.status = 'Completed'
        GROUP BY sr.region
    )
    SELECT 
        region,
        sales_reps_count,
        unique_customers,
        total_transactions,
        total_revenue,
        ROUND(avg_deal_size, 2) as avg_deal_size,
        ROUND(total_revenue / NULLIF(sales_reps_count, 0), 2) as revenue_per_rep,
        ROUND(total_revenue / NULLIF(unique_customers, 0), 2) as revenue_per_customer
    FROM regional_stats
    ORDER BY total_revenue DESC NULLS LAST;
    """
    
    success, result = await execute_query(regional_query, "Regional performance comparison")
    test_results["regional_performance"] = success
    if success:
        if "revenue_per_rep" in result and "revenue_per_customer" in result:
            print("   Contains efficiency metrics and regional comparisons")
    
    # Test Summary
    print("\n=== Test 2 Summary ===")
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"Passed: {passed_tests}/{total_tests} tests")
    for test_name, result in test_results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎯 Sales & CRM Analytics: FULLY CAPABLE")
        print("   pg-mcp can handle comprehensive sales analytics including:")
        print("   • Sales performance tracking and quota management")
        print("   • Customer segmentation and lifetime value analysis")
        print("   • Product profitability and margin analysis")
        print("   • Regional performance comparisons")
        print("   • Sales forecasting and trend analysis")
        print("   • CRM-style customer relationship metrics")
    elif passed_tests >= total_tests * 0.8:
        print("\n⚠️  Sales & CRM Analytics: MOSTLY CAPABLE")
        print("   pg-mcp handles most sales analytics with minor issues")
    else:
        print("\n❌ Sales & CRM Analytics: NEEDS IMPROVEMENT")
        print("   pg-mcp has significant issues with sales analytics")
    
    return test_results


if __name__ == "__main__":
    asyncio.run(test_sales_crm_analytics())
