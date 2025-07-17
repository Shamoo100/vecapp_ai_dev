#!/usr/bin/env python3
"""
Test script to verify AI service response integration with member service.
This script tests the follow-up note generation and response sending functionality.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

from app.services.messaging_service import MessagingService
from app.api.routes.followup_task_processor import TaskData, PersonData, RecipientData, AssigneeData
from app.agents.followup_summary_agent import FollowupSummaryAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample test data
SAMPLE_TASK_DATA = {
    "id": 12345,
    "process_id": 1001,
    "created_by": "550e8400-e29b-41d4-a716-446655440000",
    "task_title": "Follow-up with new visitor - John Smith",
    "task_description": "New visitor John Smith attended Sunday service. Showed interest in volunteering and asked about small groups. Please follow up within 48 hours.",
    "task_type": "follow_up",
    "task_status": "pending",
    "task_priority": "high",
    "task_planned_startdate": "2024-01-08",
    "task_planned_enddate": "2024-01-10",
    "tenant_id": 1,
    "recipient": {
        "id": 2001,
        "person_id": "person-uuid-12345",
        "fam_id": 3001,
        "task_type_flag": "visitor_followup",
        "person": {
            "id": "person-uuid-12345",
            "first_name": "John",
            "last_name": "Smith",
            "relationship": "visitor",
            "email": "john.smith@email.com",
            "profile_pic_url": None,
            "avatar_color": "#4A90E2"
        }
    },
    "assignees": [
        {
            "id": "assignee-uuid-001",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "email": "sarah.johnson@church.org",
            "profile_pic_url": None,
            "assignee_id": 5001,
            "task_assignee_id": "task-assignee-001",
            "is_accept": True,
            "avatar_color": "#E94B3C"
        }
    ],
    "notes": []
}

class ResponseIntegrationTester:
    """Test class for verifying response integration functionality"""
    
    def __init__(self):
        self.messaging_service = MessagingService()
        self.test_results = []
    
    async def test_successful_note_generation(self) -> Dict[str, Any]:
        """Test successful AI note generation and response sending"""
        logger.info("Testing successful note generation...")
        
        try:
            # Create task data object
            task_data = TaskData(**SAMPLE_TASK_DATA)
            
            # Initialize AI agent
            agent = FollowupSummaryAgent(
                agent_id="test-agent-1",
                schema="test_tenant"
            )
            
            # Prepare visitor data
            visitor_data = {
                "person_id": task_data.recipient.person_id,
                "first_name": task_data.recipient.person.first_name,
                "last_name": task_data.recipient.person.last_name,
                "relationship": task_data.recipient.person.relationship,
                "email": task_data.recipient.person.email,
                "task_description": task_data.task_description,
                "task_title": task_data.task_title,
                "task_type_flag": task_data.recipient.task_type_flag,
                "assignees": [
                    {
                        "name": f"{assignee.first_name} {assignee.last_name}",
                        "email": assignee.email,
                        "role": "assignee"
                    } for assignee in task_data.assignees
                ]
            }
            
            # Generate AI note
            logger.info("Generating AI follow-up note...")
            followup_result = await agent.generate_followup_note(visitor_data)
            
            # Send response to member service
            logger.info("Sending response to member service...")
            response = await self.messaging_service.send_followup_response(
                task_id=task_data.id,
                person_id=task_data.recipient.person_id,
                generated_note=followup_result.get('note', ''),
                ai_confidence_score=followup_result.get('confidence_score', 0.8),
                status="completed",
                recommended_actions=followup_result.get('recommended_actions', []),
                additional_metadata={
                    "ai_model_version": "gpt-4",
                    "processing_time": datetime.utcnow().isoformat(),
                    "tenant_id": task_data.tenant_id,
                    "test_mode": True
                }
            )
            
            result = {
                "test_name": "successful_note_generation",
                "status": "passed",
                "task_id": task_data.id,
                "generated_note": followup_result.get('note', ''),
                "confidence_score": followup_result.get('confidence_score', 0.8),
                "recommended_actions": followup_result.get('recommended_actions', []),
                "message_id": response.get('message_id'),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Test passed: {result['test_name']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Test failed: {str(e)}")
            return {
                "test_name": "successful_note_generation",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def test_error_response_handling(self) -> Dict[str, Any]:
        """Test error response handling and sending"""
        logger.info("Testing error response handling...")
        
        try:
            # Simulate an error scenario
            task_id = 99999
            person_id = "error-test-person-id"
            error_message = "Simulated AI processing error for testing"
            
            # Send error response
            response = await self.messaging_service.send_followup_response(
                task_id=task_id,
                person_id=person_id,
                generated_note="",
                ai_confidence_score=0.0,
                status="failed",
                error_message=error_message,
                additional_metadata={
                    "test_mode": True,
                    "error_type": "simulated_error"
                }
            )
            
            result = {
                "test_name": "error_response_handling",
                "status": "passed",
                "task_id": task_id,
                "error_message": error_message,
                "message_id": response.get('message_id'),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Test passed: {result['test_name']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Test failed: {str(e)}")
            return {
                "test_name": "error_response_handling",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def test_message_format_validation(self) -> Dict[str, Any]:
        """Test that response messages have the correct format"""
        logger.info("Testing message format validation...")
        
        try:
            # Test with minimal data
            response = await self.messaging_service.send_followup_response(
                task_id=12345,
                person_id="test-person-id",
                generated_note="Test note content",
                ai_confidence_score=0.75,
                status="completed",
                recommended_actions=["Test action 1", "Test action 2"]
            )
            
            # Validate response structure
            required_fields = ['message_id']
            for field in required_fields:
                if field not in response:
                    raise ValueError(f"Missing required field in response: {field}")
            
            result = {
                "test_name": "message_format_validation",
                "status": "passed",
                "message_id": response.get('message_id'),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Test passed: {result['test_name']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Test failed: {str(e)}")
            return {
                "test_name": "message_format_validation",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        logger.info("🚀 Starting response integration tests...")
        
        tests = [
            self.test_successful_note_generation,
            self.test_error_response_handling,
            self.test_message_format_validation
        ]
        
        results = []
        passed_count = 0
        
        for test in tests:
            result = await test()
            results.append(result)
            if result['status'] == 'passed':
                passed_count += 1
        
        summary = {
            "total_tests": len(tests),
            "passed": passed_count,
            "failed": len(tests) - passed_count,
            "success_rate": f"{(passed_count / len(tests)) * 100:.1f}%",
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"📊 Test Summary: {passed_count}/{len(tests)} tests passed ({summary['success_rate']})")
        
        return summary

async def main():
    """Main function to run the integration tests"""
    print("\n" + "="*60)
    print("AI SERVICE RESPONSE INTEGRATION TESTS")
    print("="*60)
    
    tester = ResponseIntegrationTester()
    
    try:
        results = await tester.run_all_tests()
        
        print("\n" + "="*60)
        print("TEST RESULTS")
        print("="*60)
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        print(f"Success Rate: {results['success_rate']}")
        
        print("\nDetailed Results:")
        for result in results['results']:
            status_icon = "✅" if result['status'] == 'passed' else "❌"
            print(f"{status_icon} {result['test_name']}: {result['status']}")
            if result['status'] == 'failed':
                print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Save results to file
        with open('test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: test_results.json")
        
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        print(f"\n❌ Test execution failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())