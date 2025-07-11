"""
Test 3: HR Analytics Capabilities
Tests pg-mcp ability to handle human resources data and analytics
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


async def test_hr_analytics():
    """Test HR analytics capabilities"""
    
    print("=== Test 3: HR Analytics ===\n")
    
    test_results = {}
    
    # Test 3.1: HR Schema Setup
    print("3.1 Setting up HR Analytics Schema...")
    setup_query = """
    CREATE SCHEMA IF NOT EXISTS hr;
    
    DROP TABLE IF EXISTS hr.performance_reviews CASCADE;
    DROP TABLE IF EXISTS hr.training_records CASCADE;
    DROP TABLE IF EXISTS hr.employees CASCADE;
    DROP TABLE IF EXISTS hr.departments CASCADE;
    
    CREATE TABLE hr.departments (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        budget DECIMAL(15,2),
        manager_id INTEGER,
        location VARCHAR(100)
    );
    
    CREATE TABLE hr.employees (
        id SERIAL PRIMARY KEY,
        employee_id VARCHAR(20) UNIQUE,
        name VARCHAR(100),
        department_id INTEGER REFERENCES hr.departments(id),
        position VARCHAR(100),
        level VARCHAR(20),
        salary DECIMAL(10,2),
        hire_date DATE,
        status VARCHAR(20) DEFAULT 'Active',
        manager_id INTEGER
    );
    
    CREATE TABLE hr.performance_reviews (
        id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES hr.employees(id),
        review_period VARCHAR(20),
        review_date DATE,
        rating INTEGER CHECK (rating BETWEEN 1 AND 5),
        goals_met INTEGER CHECK (goals_met BETWEEN 0 AND 100),
        technical_score INTEGER CHECK (technical_score BETWEEN 1 AND 10),
        leadership_score INTEGER CHECK (leadership_score BETWEEN 1 AND 10),
        communication_score INTEGER CHECK (communication_score BETWEEN 1 AND 10),
        comments TEXT,
        reviewer_id INTEGER
    );
    
    CREATE TABLE hr.training_records (
        id SERIAL PRIMARY KEY,
        employee_id INTEGER REFERENCES hr.employees(id),
        training_name VARCHAR(200),
        training_category VARCHAR(50),
        completion_date DATE,
        score INTEGER CHECK (score BETWEEN 0 AND 100),
        certification_earned BOOLEAN DEFAULT FALSE,
        training_hours INTEGER
    );
    """
    
    success, result = await execute_query(setup_query, "HR schema creation")
    test_results["schema_setup"] = success
    
    # Test 3.2: Sample HR Data Insertion
    print("\n3.2 Inserting Sample HR Data...")
    data_query = """
    INSERT INTO hr.departments (name, budget, location) VALUES
    ('Engineering', 2500000.00, 'San Francisco'),
    ('Sales', 1800000.00, 'New York'),
    ('Marketing', 1200000.00, 'Chicago'),
    ('HR', 800000.00, 'Austin'),
    ('Finance', 1000000.00, 'Boston'),
    ('Operations', 1500000.00, 'Seattle'),
    ('Customer Success', 900000.00, 'Denver');
    
    INSERT INTO hr.employees (employee_id, name, department_id, position, level, salary, hire_date, status, manager_id) VALUES
    ('ENG001', 'John Smith', 1, 'Senior Software Engineer', 'Senior', 120000.00, '2020-01-15', 'Active', NULL),
    ('ENG002', 'Jane Doe', 1, 'Staff Engineer', 'Staff', 150000.00, '2019-03-10', 'Active', NULL),
    ('ENG003', 'Mike Johnson', 1, 'Junior Developer', 'Junior', 85000.00, '2022-06-20', 'Active', 1),
    ('SAL001', 'Sarah Wilson', 2, 'Sales Manager', 'Manager', 95000.00, '2019-08-15', 'Active', NULL),
    ('SAL002', 'Tom Brown', 2, 'Sales Representative', 'Mid', 75000.00, '2021-01-10', 'Active', 4),
    ('SAL003', 'Lisa Garcia', 2, 'Senior Sales Rep', 'Senior', 85000.00, '2020-05-12', 'Active', 4),
    ('MKT001', 'David Lee', 3, 'Marketing Manager', 'Manager', 90000.00, '2020-11-30', 'Active', NULL),
    ('MKT002', 'Emily Chen', 3, 'Content Specialist', 'Mid', 65000.00, '2021-09-15', 'Active', 7),
    ('HR001', 'Amanda Taylor', 4, 'HR Business Partner', 'Senior', 80000.00, '2020-02-20', 'Active', NULL),
    ('FIN001', 'Robert Kim', 5, 'Financial Analyst', 'Mid', 75000.00, '2021-07-01', 'Active', NULL),
    ('OPS001', 'Maria Rodriguez', 6, 'Operations Manager', 'Manager', 95000.00, '2019-12-05', 'Active', NULL),
    ('CS001', 'Kevin Wong', 7, 'Customer Success Manager', 'Senior', 85000.00, '2021-03-15', 'Active', NULL);
    
    INSERT INTO hr.performance_reviews (employee_id, review_period, review_date, rating, goals_met, technical_score, leadership_score, communication_score, comments, reviewer_id) VALUES
    (1, '2024-Q1', '2024-03-15', 5, 95, 9, 7, 8, 'Excellent technical performance, strong code quality', NULL),
    (2, '2024-Q1', '2024-03-20', 5, 92, 10, 9, 9, 'Outstanding leadership and technical expertise', NULL),
    (3, '2024-Q1', '2024-03-10', 4, 78, 7, 5, 7, 'Good progress, needs more experience with complex projects', 1),
    (4, '2024-Q1', '2024-03-25', 4, 88, 6, 8, 9, 'Strong team management and sales strategy', NULL),
    (5, '2024-Q1', '2024-03-12', 3, 72, 5, 4, 6, 'Meeting targets but could improve client relationship skills', 4),
    (6, '2024-Q1', '2024-03-18', 5, 94, 7, 6, 8, 'Exceeded sales targets, excellent customer relationships', 4),
    (7, '2024-Q1', '2024-03-22', 4, 85, 6, 7, 8, 'Great marketing campaigns, good team collaboration', NULL),
    (8, '2024-Q1', '2024-03-14', 4, 82, 8, 5, 7, 'Creative content, consistent quality output', 7),
    (9, '2024-Q1', '2024-03-28', 5, 90, 6, 9, 9, 'Excellent employee relations and HR strategy', NULL),
    (10, '2024-Q1', '2024-03-16', 4, 86, 8, 5, 7, 'Solid financial analysis and reporting', NULL);
    
    INSERT INTO hr.training_records (employee_id, training_name, training_category, completion_date, score, certification_earned, training_hours) VALUES
    (1, 'Advanced React Development', 'Technical', '2024-02-15', 92, TRUE, 40),
    (1, 'Leadership Fundamentals', 'Leadership', '2024-01-20', 85, FALSE, 16),
    (2, 'System Architecture Design', 'Technical', '2024-01-10', 95, TRUE, 60),
    (2, 'Managing Technical Teams', 'Leadership', '2024-03-05', 88, TRUE, 24),
    (3, 'JavaScript Fundamentals', 'Technical', '2024-01-25', 78, FALSE, 32),
    (4, 'Sales Management Excellence', 'Sales', '2024-02-10', 91, TRUE, 20),
    (5, 'Customer Relationship Management', 'Sales', '2024-01-15', 75, FALSE, 16),
    (6, 'Advanced Sales Techniques', 'Sales', '2024-02-20', 89, TRUE, 18),
    (7, 'Digital Marketing Strategy', 'Marketing', '2024-01-30', 87, TRUE, 25),
    (8, 'Content Creation Mastery', 'Marketing', '2024-02-05', 84, FALSE, 20);
    """
    
    success, result = await execute_query(data_query, "Sample HR data insertion")
    test_results["data_insertion"] = success
    
    # Test 3.3: Employee Performance Analysis
    print("\n3.3 Testing Employee Performance Analysis...")
    performance_query = """
    SELECT 
        e.name as employee,
        e.employee_id,
        d.name as department,
        e.position,
        e.level,
        e.salary,
        pr.rating,
        pr.goals_met,
        pr.technical_score,
        pr.leadership_score,
        pr.communication_score,
        ROUND((pr.technical_score + pr.leadership_score + pr.communication_score) / 3.0, 2) as overall_skill_score,
        CASE 
            WHEN pr.rating >= 5 AND pr.goals_met >= 90 THEN 'Top Performer'
            WHEN pr.rating >= 4 AND pr.goals_met >= 80 THEN 'High Performer'
            WHEN pr.rating >= 3 AND pr.goals_met >= 70 THEN 'Meets Expectations'
            ELSE 'Needs Improvement'
        END as performance_category,
        EXTRACT(YEAR FROM AGE(CURRENT_DATE, e.hire_date)) as years_with_company
    FROM hr.employees e
    JOIN hr.departments d ON e.department_id = d.id
    LEFT JOIN hr.performance_reviews pr ON e.id = pr.employee_id
    WHERE e.status = 'Active'
    ORDER BY pr.rating DESC NULLS LAST, pr.goals_met DESC NULLS LAST;
    """
    
    success, result = await execute_query(performance_query, "Employee performance analysis")
    test_results["performance_analysis"] = success
    if success:
        if "performance_category" in result and "overall_skill_score" in result:
            print("   Contains performance categorization and skill assessments")
    
    # Test 3.4: Department Analytics
    print("\n3.4 Testing Department Analytics...")
    department_query = """
    SELECT 
        d.name as department,
        d.location,
        d.budget,
        COUNT(e.id) as employee_count,
        AVG(e.salary) as avg_salary,
        SUM(e.salary) as total_payroll,
        MIN(e.salary) as min_salary,
        MAX(e.salary) as max_salary,
        ROUND((SUM(e.salary) * 100.0 / d.budget), 2) as budget_utilization_percent,
        AVG(pr.rating) as avg_performance_rating,
        AVG(pr.goals_met) as avg_goals_completion,
        COUNT(CASE WHEN pr.rating >= 4 THEN 1 END) as high_performers,
        ROUND(COUNT(CASE WHEN pr.rating >= 4 THEN 1 END) * 100.0 / COUNT(pr.rating), 2) as high_performer_percentage
    FROM hr.departments d
    LEFT JOIN hr.employees e ON d.id = e.department_id AND e.status = 'Active'
    LEFT JOIN hr.performance_reviews pr ON e.id = pr.employee_id
    GROUP BY d.id, d.name, d.location, d.budget
    ORDER BY employee_count DESC;
    """
    
    success, result = await execute_query(department_query, "Department analytics and budget analysis")
    test_results["department_analytics"] = success
    if success:
        if "budget_utilization_percent" in result and "high_performer_percentage" in result:
            print("   Contains budget utilization and performance distribution metrics")
    
    # Test 3.5: Training Effectiveness Analysis
    print("\n3.5 Testing Training Effectiveness...")
    training_query = """
    SELECT 
        tr.training_category,
        COUNT(tr.id) as total_trainings,
        COUNT(DISTINCT tr.employee_id) as employees_trained,
        AVG(tr.score) as avg_training_score,
        SUM(tr.training_hours) as total_training_hours,
        COUNT(CASE WHEN tr.certification_earned THEN 1 END) as certifications_earned,
        ROUND(COUNT(CASE WHEN tr.certification_earned THEN 1 END) * 100.0 / COUNT(tr.id), 2) as certification_rate,
        AVG(CASE WHEN tr.completion_date IS NOT NULL THEN tr.score END) as completion_avg_score
    FROM hr.training_records tr
    GROUP BY tr.training_category
    ORDER BY total_trainings DESC;
    """
    
    success, result = await execute_query(training_query, "Training effectiveness analysis")
    test_results["training_analysis"] = success
    if success:
        if "certification_rate" in result and "completion_avg_score" in result:
            print("   Contains training ROI and certification tracking")
    
    # Test 3.6: Employee Development Tracking
    print("\n3.6 Testing Employee Development Tracking...")
    development_query = """
    WITH employee_training AS (
        SELECT 
            e.id,
            e.name,
            e.department_id,
            e.position,
            e.level,
            COUNT(tr.id) as trainings_completed,
            SUM(tr.training_hours) as total_training_hours,
            AVG(tr.score) as avg_training_score,
            COUNT(CASE WHEN tr.certification_earned THEN 1 END) as certifications_earned
        FROM hr.employees e
        LEFT JOIN hr.training_records tr ON e.id = tr.employee_id
        WHERE e.status = 'Active'
        GROUP BY e.id, e.name, e.department_id, e.position, e.level
    )
    SELECT 
        et.name as employee,
        d.name as department,
        et.position,
        et.level,
        et.trainings_completed,
        et.total_training_hours,
        ROUND(et.avg_training_score, 2) as avg_training_score,
        et.certifications_earned,
        pr.rating as current_performance_rating,
        pr.goals_met as current_goals_completion,
        CASE 
            WHEN et.trainings_completed >= 3 AND et.certifications_earned >= 1 THEN 'High Development'
            WHEN et.trainings_completed >= 2 OR et.certifications_earned >= 1 THEN 'Moderate Development'
            WHEN et.trainings_completed >= 1 THEN 'Basic Development'
            ELSE 'No Development Activity'
        END as development_level
    FROM employee_training et
    JOIN hr.departments d ON et.department_id = d.id
    LEFT JOIN hr.performance_reviews pr ON et.id = pr.employee_id
    ORDER BY et.trainings_completed DESC, et.certifications_earned DESC;
    """
    
    success, result = await execute_query(development_query, "Employee development tracking")
    test_results["development_tracking"] = success
    if success:
        if "development_level" in result and "avg_training_score" in result:
            print("   Contains comprehensive development pathway analysis")
    
    # Test 3.7: Compensation Analysis
    print("\n3.7 Testing Compensation Analysis...")
    compensation_query = """
    SELECT 
        d.name as department,
        e.level,
        COUNT(e.id) as employee_count,
        MIN(e.salary) as min_salary,
        MAX(e.salary) as max_salary,
        AVG(e.salary) as avg_salary,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY e.salary) as median_salary,
        STDDEV(e.salary) as salary_std_dev,
        AVG(pr.rating) as avg_performance_rating,
        CORR(e.salary, pr.rating) as salary_performance_correlation
    FROM hr.employees e
    JOIN hr.departments d ON e.department_id = d.id
    LEFT JOIN hr.performance_reviews pr ON e.id = pr.employee_id
    WHERE e.status = 'Active'
    GROUP BY d.name, e.level
    HAVING COUNT(e.id) >= 1
    ORDER BY d.name, 
        CASE e.level 
            WHEN 'Junior' THEN 1
            WHEN 'Mid' THEN 2  
            WHEN 'Senior' THEN 3
            WHEN 'Staff' THEN 4
            WHEN 'Manager' THEN 5
            ELSE 6
        END;
    """
    
    success, result = await execute_query(compensation_query, "Compensation analysis by department and level")
    test_results["compensation_analysis"] = success
    if success:
        if "median_salary" in result and "salary_performance_correlation" in result:
            print("   Contains statistical salary analysis and pay equity metrics")
    
    # Test Summary
    print("\n=== Test 3 Summary ===")
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"Passed: {passed_tests}/{total_tests} tests")
    for test_name, result in test_results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    if passed_tests == total_tests:
        print("\n🎯 HR Analytics: FULLY CAPABLE")
        print("   pg-mcp can handle comprehensive HR analytics including:")
        print("   • Employee performance management and reviews")
        print("   • Department budget analysis and workforce planning")
        print("   • Training effectiveness and ROI tracking")
        print("   • Employee development pathway analysis")
        print("   • Compensation analysis and pay equity")
        print("   • Performance correlation and statistical analysis")
        print("   • Suitable for HRMS and workforce analytics platforms")
    elif passed_tests >= total_tests * 0.8:
        print("\n⚠️  HR Analytics: MOSTLY CAPABLE")
        print("   pg-mcp handles most HR analytics with minor issues")
    else:
        print("\n❌ HR Analytics: NEEDS IMPROVEMENT")
        print("   pg-mcp has significant issues with HR analytics")
    
    return test_results


if __name__ == "__main__":
    asyncio.run(test_hr_analytics())
