"""
Enterprise pg-mcp Test Suite Runner
Runs all enterprise capability tests in sequence and provides comprehensive assessment
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Add the parent directory to the path to import the app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all test modules
from test_01_core_connectivity import test_core_connectivity
from test_02_sales_crm import test_sales_crm_analytics
from test_03_hr_analytics import test_hr_analytics
from test_04_portfolio_financial import test_portfolio_financial_analytics
from test_05_advanced_analytics import test_advanced_analytics


async def run_enterprise_test_suite():
    """Run complete enterprise test suite for pg-mcp"""
    
    print("=" * 80)
    print("🚀 pg-mcp ENTERPRISE CAPABILITY ASSESSMENT")
    print("=" * 80)
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Testing Question: 'Với các công cụ #pg_mcp thì có đủ để truy vấn các thống kê trong một doanh nghiệp không?'")
    print("=" * 80)
    
    start_time = time.time()
    all_results = {}
    
    # Test 1: Core Database Connectivity
    print("\n🔧 PHASE 1: CORE DATABASE CONNECTIVITY")
    print("-" * 50)
    try:
        test1_start = time.time()
        results = await test_core_connectivity()
        test1_time = time.time() - test1_start
        all_results["Core Connectivity"] = {
            "results": results,
            "duration": test1_time,
            "success": all(results.values()) if results else False
        }
        print(f"Phase 1 completed in {test1_time:.2f} seconds")
    except Exception as e:
        print(f"❌ Phase 1 failed with error: {e}")
        all_results["Core Connectivity"] = {"results": {}, "duration": 0, "success": False}
    
    # Test 2: Sales & CRM Analytics
    print("\n💼 PHASE 2: SALES & CRM ANALYTICS")
    print("-" * 50)
    try:
        test2_start = time.time()
        results = await test_sales_crm_analytics()
        test2_time = time.time() - test2_start
        all_results["Sales & CRM"] = {
            "results": results,
            "duration": test2_time,
            "success": all(results.values()) if results else False
        }
        print(f"Phase 2 completed in {test2_time:.2f} seconds")
    except Exception as e:
        print(f"❌ Phase 2 failed with error: {e}")
        all_results["Sales & CRM"] = {"results": {}, "duration": 0, "success": False}
    
    # Test 3: HR Analytics
    print("\n👥 PHASE 3: HR ANALYTICS")
    print("-" * 50)
    try:
        test3_start = time.time()
        results = await test_hr_analytics()
        test3_time = time.time() - test3_start
        all_results["HR Analytics"] = {
            "results": results,
            "duration": test3_time,
            "success": all(results.values()) if results else False
        }
        print(f"Phase 3 completed in {test3_time:.2f} seconds")
    except Exception as e:
        print(f"❌ Phase 3 failed with error: {e}")
        all_results["HR Analytics"] = {"results": {}, "duration": 0, "success": False}
    
    # Test 4: Portfolio & Financial Analytics
    print("\n💰 PHASE 4: PORTFOLIO & FINANCIAL ANALYTICS")
    print("-" * 50)
    try:
        test4_start = time.time()
        results = await test_portfolio_financial_analytics()
        test4_time = time.time() - test4_start
        all_results["Portfolio & Financial"] = {
            "results": results,
            "duration": test4_time,
            "success": all(results.values()) if results else False
        }
        print(f"Phase 4 completed in {test4_time:.2f} seconds")
    except Exception as e:
        print(f"❌ Phase 4 failed with error: {e}")
        all_results["Portfolio & Financial"] = {"results": {}, "duration": 0, "success": False}
    
    # Test 5: Advanced Analytics & BI
    print("\n📊 PHASE 5: ADVANCED ANALYTICS & BUSINESS INTELLIGENCE")
    print("-" * 50)
    try:
        test5_start = time.time()
        results = await test_advanced_analytics()
        test5_time = time.time() - test5_start
        all_results["Advanced Analytics & BI"] = {
            "results": results,
            "duration": test5_time,
            "success": all(results.values()) if results else False
        }
        print(f"Phase 5 completed in {test5_time:.2f} seconds")
    except Exception as e:
        print(f"❌ Phase 5 failed with error: {e}")
        all_results["Advanced Analytics & BI"] = {"results": {}, "duration": 0, "success": False}
    
    total_time = time.time() - start_time
    
    # Generate comprehensive assessment report
    print("\n" + "=" * 80)
    print("📋 COMPREHENSIVE ASSESSMENT REPORT")
    print("=" * 80)
    
    total_tests = 0
    passed_tests = 0
    successful_phases = 0
    
    print("\n📊 PHASE-BY-PHASE RESULTS:")
    print("-" * 50)
    
    for phase_name, phase_data in all_results.items():
        results = phase_data["results"]
        duration = phase_data["duration"]
        success = phase_data["success"]
        
        if results:
            phase_total = len(results)
            phase_passed = sum(results.values())
            total_tests += phase_total
            passed_tests += phase_passed
            
            success_rate = (phase_passed / phase_total * 100) if phase_total > 0 else 0
            status_icon = "✅" if success else "⚠️" if success_rate >= 80 else "❌"
            
            print(f"{status_icon} {phase_name}:")
            print(f"   Tests: {phase_passed}/{phase_total} passed ({success_rate:.1f}%)")
            print(f"   Duration: {duration:.2f} seconds")
            
            if success:
                successful_phases += 1
        else:
            print(f"❌ {phase_name}: FAILED TO EXECUTE")
        
        print()
    
    # Overall assessment
    print("🎯 OVERALL ASSESSMENT:")
    print("-" * 50)
    
    overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    phase_success_rate = (successful_phases / len(all_results) * 100) if all_results else 0
    
    print(f"Total Tests: {passed_tests}/{total_tests} passed ({overall_success_rate:.1f}%)")
    print(f"Successful Phases: {successful_phases}/{len(all_results)} ({phase_success_rate:.1f}%)")
    print(f"Total Duration: {total_time:.2f} seconds")
    
    # Final verdict
    print("\n🏆 FINAL VERDICT:")
    print("-" * 50)
    
    if overall_success_rate >= 95 and successful_phases >= 4:
        verdict = "HOÀN TOÀN ĐỦ KHẢ NĂNG"
        verdict_icon = "🟢"
        confidence = "HIGH CONFIDENCE"
    elif overall_success_rate >= 85 and successful_phases >= 3:
        verdict = "ĐỦ KHẢ NĂNG VỚI VÀI GIỚI HẠN NHỎ"
        verdict_icon = "🟡"
        confidence = "MEDIUM-HIGH CONFIDENCE"
    elif overall_success_rate >= 70 and successful_phases >= 2:
        verdict = "CƠ BẢN ĐỦ KHẢ NĂNG"
        verdict_icon = "🟠"
        confidence = "MEDIUM CONFIDENCE"
    else:
        verdict = "CHƯA ĐỦ KHẢ NĂNG"
        verdict_icon = "🔴"
        confidence = "LOW CONFIDENCE"
    
    print(f"{verdict_icon} {verdict}")
    print(f"Confidence Level: {confidence}")
    
    print(f"\n📝 ANSWER TO ORIGINAL QUESTION:")
    print("'Với các công cụ #pg_mcp thì có đủ để truy vấn các thống kê trong một doanh nghiệp không?'")
    print(f"👉 {verdict}")
    
    # Detailed capabilities summary
    print(f"\n✅ PROVEN CAPABILITIES:")
    print("-" * 30)
    
    capabilities = []
    if all_results.get("Core Connectivity", {}).get("success"):
        capabilities.append("Database connectivity & schema management")
    if all_results.get("Sales & CRM", {}).get("success"):
        capabilities.append("Sales analytics & CRM functionality")
    if all_results.get("HR Analytics", {}).get("success"):
        capabilities.append("Human resources analytics & workforce management")
    if all_results.get("Portfolio & Financial", {}).get("success"):
        capabilities.append("Financial analytics & portfolio management")
    if all_results.get("Advanced Analytics & BI", {}).get("success"):
        capabilities.append("Advanced business intelligence & data analytics")
    
    for capability in capabilities:
        print(f"• {capability}")
    
    # Enterprise applications ready for
    print(f"\n🏢 ENTERPRISE APPLICATIONS READY FOR:")
    print("-" * 40)
    
    if len(capabilities) >= 4:
        apps = [
            "CRM (Customer Relationship Management)",
            "ERP (Enterprise Resource Planning)",
            "HRMS (Human Resource Management Systems)",
            "Portfolio Management Systems",
            "Business Intelligence Platforms",
            "Financial Reporting Systems",
            "Data Analytics Applications"
        ]
        for app in apps:
            print(f"• {app}")
    elif len(capabilities) >= 2:
        print("• Basic enterprise applications with some limitations")
    else:
        print("• Limited enterprise application support")
    
    print("\n" + "=" * 80)
    print(f"Assessment completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return all_results, verdict, overall_success_rate


if __name__ == "__main__":
    asyncio.run(run_enterprise_test_suite())
