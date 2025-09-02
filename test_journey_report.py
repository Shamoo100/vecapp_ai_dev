#!/usr/bin/env python3
"""
Comprehensive test script for Journey Report feature
Tests API endpoints, services, repository methods, and LLM integration
"""

import asyncio
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any
import sys
import os

# Add app to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.journey_report_service import JourneyReportService
from app.services.member_service import MemberService
from app.agents.followup_journey_report_agent import FollowupJourneyReportAgent
from app.api.schemas.journey_report import JourneyReportRequest
from app.infastructure.ai.llm_provider_factory import LLMProviderFactory

class JourneyReportTester:
    def __init__(self, base_url: str = "http://localhost:8000", tenant: str = "test"):
        self.base_url = base_url
        self.tenant = tenant
        self.headers = {
            "Content-Type": "application/json",
            "X-Request-Tenant": tenant,
            "Authorization": "Bearer test_token"  # Replace with actual token
        }
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    async def test_api_endpoint(self):
        """Test the journey report API endpoint"""
        print("\n🧪 Testing Journey Report API Endpoint...")
        
        # Test data
        test_request = {
            "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
            "end_date": datetime.now().isoformat(),
            "report_purpose": "Monthly follow-up analysis"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/followup/journey-report",
                headers=self.headers,
                json=test_request,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Endpoint - Success Response", True, f"Status: {response.status_code}")
                self.log_test("API Response Schema", 
                            all(key in data for key in ["report_id", "generated_at", "entries"]),
                            f"Keys present: {list(data.keys())}")
            else:
                self.log_test("API Endpoint", False, f"Status: {response.status_code}, Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("API Endpoint", False, f"Request failed: {str(e)}")
    
    async def test_journey_report_service(self):
        """Test JourneyReportService methods"""
        print("\n🧪 Testing JourneyReportService...")
        
        try:
            service = JourneyReportService(tenant=self.tenant)
            self.log_test("JourneyReportService Initialization", True, "Service created successfully")
            
            # Test date range validation
            start_date = datetime.now() - timedelta(days=7)
            end_date = datetime.now()
            
            request = JourneyReportRequest(
                start_date=start_date,
                end_date=end_date,
                report_purpose="Test report"
            )
            
            # Test report generation (this will test the full pipeline)
            try:
                result = await service.generate_journey_report(request)
                self.log_test("Journey Report Generation", True, f"Generated report with {len(result.entries)} entries")
            except Exception as e:
                self.log_test("Journey Report Generation", False, f"Error: {str(e)}")
                
        except Exception as e:
            self.log_test("JourneyReportService Initialization", False, f"Error: {str(e)}")
    
    async def test_member_service_journey_methods(self):
        """Test MemberService journey data methods"""
        print("\n🧪 Testing MemberService Journey Methods...")
        
        try:
            # Initialize with proper repository
            from app.data.repositories.member_service_repository import MemberRepository
            from app.database.repositories.base_repository import BaseRepository
            
            # Mock repository for testing
            class MockRepository(BaseRepository):
                def __init__(self):
                    pass
                    
                async def get_visitors_by_date_range(self, start_date, end_date):
                    return []  # Mock empty result
            
            member_service = MemberService()
            member_service._repository = MockRepository()
            
            self.log_test("MemberService Initialization", True, "Service initialized with mock repository")
            
            # Test journey data methods
            start_date = datetime.now() - timedelta(days=7)
            end_date = datetime.now()
            
            try:
                visitors_data = await member_service.get_visitors_journey_data(start_date, end_date)
                self.log_test("get_visitors_journey_data", True, f"Returned {len(visitors_data)} visitors")
            except Exception as e:
                self.log_test("get_visitors_journey_data", False, f"Error: {str(e)}")
                
        except Exception as e:
            self.log_test("MemberService Journey Methods", False, f"Setup error: {str(e)}")
    
    async def test_followup_journey_report_agent(self):
        """Test FollowupJourneyReportAgent"""
        print("\n🧪 Testing FollowupJourneyReportAgent...")
        
        try:
            # Initialize agent
            llm_factory = LLMProviderFactory()
            agent = FollowupJourneyReportAgent(
                agent_id="test_agent",
                llm_provider_factory=llm_factory,
                schema={"test": "schema"}
            )
            
            self.log_test("Agent Initialization", True, "Agent created successfully")
            
            # Test process method (required by BaseAgent)
            try:
                test_data = {"test": "data"}
                result = await agent.process(test_data)
                self.log_test("Agent Process Method", True, "Process method executed")
            except Exception as e:
                self.log_test("Agent Process Method", False, f"Error: {str(e)}")
            
            # Test journey analysis with mock data
            mock_visitors = [
                {
                    "visitor_id": "test_1",
                    "first_name": "John",
                    "last_name": "Doe",
                    "follow_up_tasks": [],
                    "feedback_entries": [],
                    "prayer_requests": []
                }
            ]
            
            try:
                analysis_result = await agent.analyze_journey_entries(mock_visitors)
                self.log_test("Journey Analysis", True, f"Analyzed {len(mock_visitors)} visitors")
            except Exception as e:
                self.log_test("Journey Analysis", False, f"Error: {str(e)}")
                
        except Exception as e:
            self.log_test("Agent Initialization", False, f"Error: {str(e)}")
    
    async def test_llm_integration(self):
        """Test LLM provider integration"""
        print("\n🧪 Testing LLM Integration...")
        
        try:
            llm_factory = LLMProviderFactory()
            self.log_test("LLM Factory Initialization", True, "Factory created successfully")
            
            # Test content generation with journey report prompt
            test_prompt = """
            Analyze this visitor journey data and provide insights:
            Visitor: John Doe
            Visit Date: 2024-01-15
            Follow-up Tasks: 2 completed, 1 pending
            Feedback: Positive experience, interested in small groups
            
            Provide analysis in JSON format with visitor_decision and sentiment.
            """
            
            try:
                result = await llm_factory.generate_content(
                    prompt=test_prompt,
                    max_tokens=500,
                    temperature=0.3
                )
                
                if result and len(result.strip()) > 0:
                    self.log_test("LLM Content Generation", True, f"Generated {len(result)} characters")
                    
                    # Test JSON parsing
                    try:
                        json.loads(result)
                        self.log_test("LLM JSON Response", True, "Valid JSON returned")
                    except json.JSONDecodeError:
                        self.log_test("LLM JSON Response", False, "Invalid JSON format")
                else:
                    self.log_test("LLM Content Generation", False, "Empty or null response")
                    
            except Exception as e:
                self.log_test("LLM Content Generation", False, f"Error: {str(e)}")
                
        except Exception as e:
            self.log_test("LLM Integration", False, f"Setup error: {str(e)}")
    
    async def test_error_scenarios(self):
        """Test error handling scenarios"""
        print("\n🧪 Testing Error Scenarios...")
        
        # Test invalid date range
        invalid_request = {
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() - timedelta(days=30)).isoformat(),  # End before start
            "report_purpose": "Invalid date test"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/followup/journey-report",
                headers=self.headers,
                json=invalid_request,
                timeout=10
            )
            
            if response.status_code >= 400:
                self.log_test("Invalid Date Range Handling", True, f"Properly rejected with status {response.status_code}")
            else:
                self.log_test("Invalid Date Range Handling", False, "Should have rejected invalid date range")
                
        except requests.exceptions.RequestException as e:
            self.log_test("Error Scenario Testing", False, f"Request failed: {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🧪 JOURNEY REPORT TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n" + "="*60)
        
        return failed_tests == 0

async def main():
    """Run all journey report tests"""
    print("🚀 Starting Journey Report Feature Testing...")
    
    # Initialize tester
    tester = JourneyReportTester()
    
    # Run all tests
    await tester.test_member_service_journey_methods()
    await tester.test_journey_report_service()
    await tester.test_followup_journey_report_agent()
    await tester.test_llm_integration()
    await tester.test_api_endpoint()
    await tester.test_error_scenarios()
    
    # Print summary
    all_passed = tester.print_summary()
    
    if all_passed:
        print("\n🎉 All tests passed! Journey Report feature is ready for deployment.")
    else:
        print("\n⚠️  Some tests failed. Please review and fix issues before deployment.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())