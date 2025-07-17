#!/usr/bin/env python3
"""
Test script for the Follow-up Notes Summary API
This script demonstrates how the AI service processes task data from the member service
and generates follow-up notes using the sample data provided.
"""

import json
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any

# Sample task data (based on the provided sample files from member service)
SAMPLE_TASK_DATA = {
    "id": 1,
    "process_id": 101,
    "created_by": "550e8400-e29b-41d4-a716-446655440000",  # UUID format
    "task_title": "Follow-up with new visitor - John Smith",
    "task_description": "New visitor attended Sunday service. Expressed interest in children's ministry and small groups. Has 2 young children (ages 5 and 7). Looking for a church home after recent move to the area.",
    "task_type": "follow_up",
    "task_status": "pending",
    "task_priority": "medium",
    "task_planned_startdate": "2024-01-07T09:00:00Z",
    "task_planned_enddate": "2024-01-14T17:00:00Z",
    "tenant_id": 1,
    "recipient": {
        "id": 1001,
        "person_id": "person_12345",
        "fam_id": "660e8400-e29b-41d4-a716-446655440000",  # UUID format
        "task_type_flag": "first_time_visitor",
        "person": {
            "id": "person_12345",
            "first_name": "John",
            "last_name": "Smith",
            "relationship": "head_of_household",
            "profile_pic_url": None,
            "email": "john.smith@email.com",
            "avatar_color": "#4A90E2"
        }
    },
    "assignees": [
        {
            "id": "staff_001",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "email": "sarah.johnson@church.org",
            "profile_pic_url": None,
            "assignee_id": 201,
            "task_assignee_id": "ta_001",
            "is_accept": True,
            "avatar_color": "#E94B3C"
        }
    ],
    "notes": []
}

# SQS Message format
SQS_MESSAGE_SAMPLE = {
    "message_type": "task_created",
    "task_data": SAMPLE_TASK_DATA,
    "timestamp": datetime.utcnow().isoformat(),
    "source_service": "member_service"
}

class FollowupAPITester:
    """Test class for the Follow-up Notes Summary API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_key = "test-api-key"  # Replace with actual API key
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
    
    async def test_health_check(self) -> Dict[str, Any]:
        """Test the health check endpoint"""
        print("\n🔍 Testing health check endpoint...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/followup-tasks/health",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Health check passed: {result}")
                    return result
                else:
                    print(f"❌ Health check failed: {response.status_code} - {response.text}")
                    return {"error": f"Status {response.status_code}"}
                    
            except Exception as e:
                print(f"❌ Health check error: {str(e)}")
                return {"error": str(e)}
    
    async def test_direct_note_generation(self) -> Dict[str, Any]:
        """Test direct follow-up note generation"""
        print("\n📝 Testing direct follow-up note generation...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/followup-tasks/generate-note",
                    headers=self.headers,
                    json=SAMPLE_TASK_DATA,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Follow-up note generated successfully:")
                    print(f"   Status: {result.get('status')}")
                    print(f"   Message: {result.get('message')}")
                    if 'result' in result:
                        note_result = result['result']
                        print(f"   Task ID: {note_result.get('task_id')}")
                        print(f"   Person: {note_result.get('person_id')}")
                        print(f"   Generated Note: {note_result.get('generated_note')}")
                        print(f"   Confidence Score: {note_result.get('ai_confidence_score')}")
                    return result
                else:
                    print(f"❌ Note generation failed: {response.status_code} - {response.text}")
                    return {"error": f"Status {response.status_code}"}
                    
            except Exception as e:
                print(f"❌ Note generation error: {str(e)}")
                return {"error": str(e)}
    
    async def test_sqs_message_processing(self) -> Dict[str, Any]:
        """Test SQS message processing (simulated)"""
        print("\n📨 Testing SQS message processing...")
        
        # Note: This would normally be handled by SQS, but we can test the endpoint
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/followup-tasks/process-sqs-message",
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ SQS processing endpoint accessible:")
                    print(f"   Status: {result.get('status')}")
                    print(f"   Message: {result.get('message')}")
                    return result
                else:
                    print(f"❌ SQS processing failed: {response.status_code} - {response.text}")
                    return {"error": f"Status {response.status_code}"}
                    
            except Exception as e:
                print(f"❌ SQS processing error: {str(e)}")
                return {"error": str(e)}
    
    async def test_task_status(self, task_id: int = 1) -> Dict[str, Any]:
        """Test task status endpoint"""
        print(f"\n📊 Testing task status for task {task_id}...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v1/followup-tasks/status/{task_id}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Task status retrieved:")
                    print(f"   Task ID: {result.get('task_id')}")
                    print(f"   Status: {result.get('status')}")
                    print(f"   Message: {result.get('message')}")
                    return result
                else:
                    print(f"❌ Task status failed: {response.status_code} - {response.text}")
                    return {"error": f"Status {response.status_code}"}
                    
            except Exception as e:
                print(f"❌ Task status error: {str(e)}")
                return {"error": str(e)}
    
    def print_sample_data(self):
        """Print the sample data being used for testing"""
        print("\n📋 Sample Task Data:")
        print("=" * 50)
        print(json.dumps(SAMPLE_TASK_DATA, indent=2))
        print("\n📨 Sample SQS Message:")
        print("=" * 50)
        print(json.dumps(SQS_MESSAGE_SAMPLE, indent=2))
    
    async def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Follow-up Notes Summary API Tests")
        print("=" * 60)
        
        # Print sample data
        self.print_sample_data()
        
        # Run tests
        results = {}
        
        results['health_check'] = await self.test_health_check()
        results['direct_note_generation'] = await self.test_direct_note_generation()
        results['sqs_processing'] = await self.test_sqs_message_processing()
        results['task_status'] = await self.test_task_status()
        
        # Summary
        print("\n📊 Test Results Summary:")
        print("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if 'error' not in result else "❌ FAILED"
            print(f"{test_name}: {status}")
            if 'error' in result:
                print(f"  Error: {result['error']}")
        
        return results

async def main():
    """Main test function"""
    print("Follow-up Notes Summary API Test Suite")
    print("This script tests the AI service's ability to process task data")
    print("from the member service and generate follow-up notes.\n")
    
    # Initialize tester
    tester = FollowupAPITester()
    
    # Run tests
    await tester.run_all_tests()
    
    print("\n🎯 Integration Flow:")
    print("1. Member service creates a task and publishes to SQS")
    print("2. AI service receives the task via SQS")
    print("3. AI service generates follow-up note using LLM")
    print("4. AI service sends the generated note back to member service")
    print("5. Member service updates the task with the AI-generated note")
    
    print("\n📝 Next Steps:")
    print("- Configure AWS SQS queues for message passing")
    print("- Set up proper authentication between services")
    print("- Implement database persistence for follow-up tasks")
    print("- Add monitoring and logging for production deployment")

if __name__ == "__main__":
    asyncio.run(main())