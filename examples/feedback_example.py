#!/usr/bin/env python3
"""
AI Note Feedback System Example

This script demonstrates how to use the AI note feedback system API endpoints.
It shows examples of submitting feedback, retrieving feedback, and getting statistics.

Usage:
    python feedback_example.py

Requirements:
    - requests library: pip install requests
    - Running AI service with feedback endpoints
    - Valid API credentials
"""

import requests
import json
from uuid import uuid4
from datetime import datetime
from typing import Optional, Dict, Any

class FeedbackAPIExample:
    """Example client for the AI note feedback system"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "test-api-key"):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
        
        # Example data
        self.tenant_id = 1
        self.admin_id = str(uuid4())
        self.visitor_id = str(uuid4())
        self.note_id = 1  # Assuming there's an AI-generated note with ID 1
    
    def submit_feedback_example(self):
        """Example: Submit feedback on an AI-generated note"""
        print("\n🔄 Submitting feedback example...")
        
        feedback_data = {
            "note_id": self.note_id,
            "visitor_id": self.visitor_id,
            "admin_id": self.admin_id,
            "tenant_id": self.tenant_id,
            "helpfulness": "yes",
            "comment": "Very insightful analysis of visitor behavior patterns"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/feedback/submit",
                json=feedback_data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Feedback submitted successfully!")
                print(f"   Feedback ID: {result['feedback']['id']}")
                print(f"   Helpfulness: {result['feedback']['helpfulness']}")
                print(f"   Comment: {result['feedback']['comment']}")
                print(f"   Note updated: {result['note_updated']}")
                return result['feedback']['id']
            else:
                print(f"❌ Error submitting feedback: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return None
    
    def get_feedback_for_note_example(self):
        """Example: Get all feedback for a specific note"""
        print("\n🔍 Getting feedback for note example...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/feedback/note/{self.note_id}",
                params={"tenant_id": self.tenant_id},
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Retrieved feedback for note {self.note_id}")
                print(f"   Feedback count: {result['feedback_count']}")
                print(f"   Feedback received: {result['feedback_received']}")
                
                if result['feedback_list']:
                    print("   Recent feedback:")
                    for feedback in result['feedback_list'][:3]:  # Show first 3
                        print(f"     - {feedback['helpfulness']} by admin {feedback['admin_id'][:8]}...")
                        if feedback['comment']:
                            print(f"       Comment: {feedback['comment']}")
                else:
                    print("   No feedback found for this note")
                    
                return result
            else:
                print(f"❌ Error getting feedback: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return None
    
    def get_feedback_by_admin_example(self):
        """Example: Get feedback submitted by a specific admin"""
        print("\n👤 Getting feedback by admin example...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/feedback/admin/{self.admin_id}",
                params={"tenant_id": self.tenant_id, "limit": 10},
                headers=self.headers
            )
            
            if response.status_code == 200:
                feedback_list = response.json()
                print(f"✅ Retrieved {len(feedback_list)} feedback entries by admin")
                
                if feedback_list:
                    print("   Recent feedback by this admin:")
                    for feedback in feedback_list:
                        print(f"     - Note {feedback['note_id']}: {feedback['helpfulness']}")
                        if feedback['comment']:
                            print(f"       Comment: {feedback['comment']}")
                else:
                    print("   No feedback found for this admin")
                    
                return feedback_list
            else:
                print(f"❌ Error getting admin feedback: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return None
    
    def get_feedback_stats_example(self):
        """Example: Get feedback statistics"""
        print("\n📊 Getting feedback statistics example...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/feedback/stats",
                params={"tenant_id": self.tenant_id, "days": 30},
                headers=self.headers
            )
            
            if response.status_code == 200:
                stats = response.json()
                print("✅ Retrieved feedback statistics")
                print(f"   Total feedback: {stats['total_feedback']}")
                print(f"   Notes with feedback: {stats['notes_with_feedback']}")
                print(f"   Total AI notes: {stats['total_ai_notes']}")
                print(f"   Feedback rate: {stats['feedback_rate']}%")
                
                if stats['helpfulness_breakdown']:
                    print("   Helpfulness breakdown:")
                    for rating, count in stats['helpfulness_breakdown'].items():
                        print(f"     - {rating}: {count}")
                        
                return stats
            else:
                print(f"❌ Error getting stats: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return None
    
    def submit_multiple_feedback_example(self):
        """Example: Submit multiple feedback entries with different ratings"""
        print("\n🔄 Submitting multiple feedback examples...")
        
        feedback_examples = [
            {
                "helpfulness": "yes",
                "comment": "Excellent insights into visitor preferences"
            },
            {
                "helpfulness": "partially",
                "comment": "Good analysis but missing some context"
            },
            {
                "helpfulness": "no",
                "comment": "Analysis seems inaccurate for this visitor"
            }
        ]
        
        submitted_count = 0
        
        for i, feedback_example in enumerate(feedback_examples, 1):
            # Use different admin IDs to avoid duplicate constraint
            admin_id = str(uuid4())
            
            feedback_data = {
                "note_id": self.note_id,
                "visitor_id": self.visitor_id,
                "admin_id": admin_id,
                "tenant_id": self.tenant_id,
                **feedback_example
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/v1/feedback/submit",
                    json=feedback_data,
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Feedback {i}: {feedback_example['helpfulness']} - submitted")
                    submitted_count += 1
                else:
                    print(f"   ❌ Feedback {i}: Failed - {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Feedback {i}: Network error - {e}")
        
        print(f"\n📈 Successfully submitted {submitted_count}/{len(feedback_examples)} feedback entries")
        return submitted_count
    
    def health_check_example(self):
        """Example: Check feedback service health"""
        print("\n🏥 Checking feedback service health...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/feedback/health",
                headers=self.headers
            )
            
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Feedback service is {health['status']}")
                print(f"   Service: {health['service']}")
                print(f"   Message: {health['message']}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Health check network error: {e}")
            return False
    
    def run_all_examples(self):
        """Run all feedback API examples"""
        print("🚀 AI Note Feedback System API Examples")
        print("=" * 50)
        print(f"Base URL: {self.base_url}")
        print(f"Tenant ID: {self.tenant_id}")
        print(f"Admin ID: {self.admin_id}")
        print(f"Note ID: {self.note_id}")
        
        # Check service health first
        if not self.health_check_example():
            print("\n❌ Service is not healthy. Stopping examples.")
            return
        
        # Run examples
        self.submit_feedback_example()
        self.get_feedback_for_note_example()
        self.get_feedback_by_admin_example()
        self.submit_multiple_feedback_example()
        self.get_feedback_stats_example()
        
        print("\n🎯 Examples completed!")
        print("\n💡 Integration Tips:")
        print("   1. Always check for existing feedback before submitting")
        print("   2. Handle validation errors gracefully")
        print("   3. Use feedback statistics for AI improvement insights")
        print("   4. Implement proper error handling and retries")
        print("   5. Consider rate limiting for feedback submission")

def main():
    """Main function to run the feedback examples"""
    print("AI Note Feedback System - API Examples")
    print("This script demonstrates the feedback system functionality.\n")
    
    # Configuration
    BASE_URL = "http://localhost:8000"  # Change to your AI service URL
    API_KEY = "test-api-key"  # Change to your actual API key
    
    # Create example client
    feedback_client = FeedbackAPIExample(BASE_URL, API_KEY)
    
    # Run all examples
    feedback_client.run_all_examples()

if __name__ == "__main__":
    main()