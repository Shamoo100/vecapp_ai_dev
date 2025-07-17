# AI Note Feedback System

This document describes the feedback system for AI-generated visitor insight notes in the VecApp AI service.

## Overview

The feedback system allows administrators to provide structured feedback on AI-generated notes to help improve future recommendations and track AI effectiveness. The system captures feedback ratings, optional comments, and maintains audit trails.

## Features

### Core Functionality
- **Structured Feedback**: Admins can rate notes as "helpful", "not helpful", or "partially helpful"
- **Optional Comments**: Up to 100 characters of additional feedback
- **Feedback Tracking**: Notes are marked when feedback is received
- **Audit Trail**: Complete history of who provided feedback and when
- **Analytics**: Statistics on feedback patterns and AI effectiveness

### Data Persistence
- Feedback is stored in the `ai_note_feedback` table
- Notes are updated with `feedback_received` flag
- Prevents duplicate feedback from the same admin on the same note
- Maintains referential integrity with foreign key constraints

## API Endpoints

### Submit Feedback
```http
POST /api/v1/feedback/submit
```

Submit feedback on an AI-generated note.

**Request Body:**
```json
{
  "note_id": 123,
  "visitor_id": "550e8400-e29b-41d4-a716-446655440000",
  "admin_id": "550e8400-e29b-41d4-a716-446655440001",
  "tenant_id": 1,
  "helpfulness": "yes",
  "comment": "Very insightful analysis of visitor behavior"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Feedback submitted successfully",
  "feedback": {
    "id": 1,
    "note_id": 123,
    "visitor_id": "550e8400-e29b-41d4-a716-446655440000",
    "admin_id": "550e8400-e29b-41d4-a716-446655440001",
    "tenant_id": 1,
    "helpfulness": "yes",
    "comment": "Very insightful analysis of visitor behavior",
    "ai_model_version": "gpt-4-turbo",
    "ai_confidence_score": 0.85,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "note_updated": true
}
```

### Get Feedback for Note
```http
GET /api/v1/feedback/note/{note_id}?tenant_id={tenant_id}
```

Retrieve all feedback for a specific note.

**Response:**
```json
{
  "note_id": 123,
  "feedback_count": 2,
  "feedback_received": true,
  "feedback_list": [
    {
      "id": 1,
      "note_id": 123,
      "visitor_id": "550e8400-e29b-41d4-a716-446655440000",
      "admin_id": "550e8400-e29b-41d4-a716-446655440001",
      "tenant_id": 1,
      "helpfulness": "yes",
      "comment": "Very helpful",
      "ai_model_version": "gpt-4-turbo",
      "ai_confidence_score": 0.85,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Get Feedback by Admin
```http
GET /api/v1/feedback/admin/{admin_id}?tenant_id={tenant_id}&limit=50
```

Retrieve feedback submitted by a specific admin.

### Get Feedback Statistics
```http
GET /api/v1/feedback/stats?tenant_id={tenant_id}&days=30
```

Get analytics on feedback patterns.

**Response:**
```json
{
  "total_feedback": 150,
  "helpfulness_breakdown": {
    "yes": 85,
    "no": 25,
    "partially": 40
  },
  "notes_with_feedback": 120,
  "total_ai_notes": 200,
  "feedback_rate": 60.0,
  "period_days": 30
}
```

### Health Check
```http
GET /api/v1/feedback/health
```

Check the status of the feedback service.

## Database Schema

### ai_note_feedback Table
```sql
CREATE TABLE ai_note_feedback (
    id SERIAL PRIMARY KEY,
    note_id INTEGER NOT NULL,
    visitor_id UUID NOT NULL,
    admin_id UUID NOT NULL,
    tenant_id INTEGER NOT NULL,
    helpfulness VARCHAR(20) NOT NULL CHECK (helpfulness IN ('yes', 'no', 'partially')),
    comment VARCHAR(100),
    ai_model_version VARCHAR(50),
    ai_confidence_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_ai_note_feedback_note_id 
        FOREIGN KEY (note_id) 
        REFERENCES followup_notes(id) 
        ON DELETE CASCADE,
    
    CONSTRAINT unique_admin_note_feedback 
        UNIQUE (note_id, admin_id)
);
```

### followup_notes Table Updates
```sql
ALTER TABLE followup_notes 
ADD COLUMN feedback_received BOOLEAN DEFAULT FALSE;
```

## Usage Examples

### Frontend Integration

```javascript
// Submit feedback
async function submitFeedback(noteId, visitorId, adminId, tenantId, helpfulness, comment) {
  const response = await fetch('/api/v1/feedback/submit', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify({
      note_id: noteId,
      visitor_id: visitorId,
      admin_id: adminId,
      tenant_id: tenantId,
      helpfulness: helpfulness,
      comment: comment
    })
  });
  
  return await response.json();
}

// Get feedback for a note
async function getFeedbackForNote(noteId, tenantId) {
  const response = await fetch(`/api/v1/feedback/note/${noteId}?tenant_id=${tenantId}`);
  return await response.json();
}

// Get feedback statistics
async function getFeedbackStats(tenantId, days = 30) {
  const response = await fetch(`/api/v1/feedback/stats?tenant_id=${tenantId}&days=${days}`);
  return await response.json();
}
```

### Python Client Example

```python
import requests
from typing import Optional

class FeedbackClient:
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {auth_token}'
        }
    
    def submit_feedback(self, note_id: int, visitor_id: str, admin_id: str, 
                       tenant_id: int, helpfulness: str, comment: Optional[str] = None):
        """Submit feedback on an AI-generated note"""
        data = {
            'note_id': note_id,
            'visitor_id': visitor_id,
            'admin_id': admin_id,
            'tenant_id': tenant_id,
            'helpfulness': helpfulness,
            'comment': comment
        }
        
        response = requests.post(
            f'{self.base_url}/api/v1/feedback/submit',
            json=data,
            headers=self.headers
        )
        
        return response.json()
    
    def get_feedback_stats(self, tenant_id: int, days: int = 30):
        """Get feedback statistics"""
        response = requests.get(
            f'{self.base_url}/api/v1/feedback/stats',
            params={'tenant_id': tenant_id, 'days': days},
            headers=self.headers
        )
        
        return response.json()
```

## Validation Rules

### Input Validation
- **helpfulness**: Must be one of "yes", "no", or "partially"
- **comment**: Optional, maximum 100 characters
- **note_id**: Must reference an existing AI-generated note
- **admin_id**: Must be a valid UUID
- **visitor_id**: Must be a valid UUID
- **tenant_id**: Must be a valid integer

### Business Rules
- Only one feedback entry per admin per note
- Only AI-generated notes can receive feedback
- Feedback can only be submitted for notes within the same tenant
- Comments are trimmed and empty comments are stored as NULL

## Error Handling

### Common Error Responses

**404 - Note Not Found**
```json
{
  "detail": "AI-generated note with ID 123 not found"
}
```

**400 - Duplicate Feedback**
```json
{
  "detail": "Failed to submit feedback. Feedback may already exist from this admin for this note."
}
```

**422 - Validation Error**
```json
{
  "detail": [
    {
      "loc": ["helpfulness"],
      "msg": "value is not a valid enumeration member",
      "type": "type_error.enum"
    }
  ]
}
```

## Testing

### Running Tests
```bash
# Run all feedback tests
pytest tests/test_feedback_system.py -v

# Run specific test
pytest tests/test_feedback_system.py::TestFeedbackSystem::test_submit_feedback_success -v
```

### Test Coverage
The test suite covers:
- Successful feedback submission
- Duplicate feedback prevention
- Input validation
- Error handling
- Repository methods
- API endpoints
- Statistics generation

## Deployment

### Database Migration
```bash
# Run the migration script
psql -d your_database -f migrations/add_feedback_system.sql
```

### Environment Variables
No additional environment variables are required. The feedback system uses the existing database connection and authentication mechanisms.

### Monitoring

#### Key Metrics to Monitor
- Feedback submission rate
- Distribution of helpfulness ratings
- Response times for feedback endpoints
- Database query performance
- Error rates

#### Logging
The system logs:
- Successful feedback submissions
- Failed submissions with reasons
- Database errors
- Validation errors

## Security Considerations

### Access Control
- All endpoints require proper authentication
- Tenant isolation is enforced
- Admin permissions should be verified (implementation dependent)

### Data Privacy
- Feedback comments are limited to 100 characters
- No sensitive visitor information is stored in feedback
- Audit trail maintains accountability

### Rate Limiting
- Consider implementing rate limiting for feedback submission
- Prevent spam or abuse of the feedback system

## Future Enhancements

### Potential Improvements
1. **Feedback Categories**: Add specific categories for feedback (accuracy, relevance, completeness)
2. **Bulk Operations**: Allow bulk feedback submission for multiple notes
3. **Feedback Templates**: Predefined comment templates for common feedback
4. **AI Model Training**: Use feedback data to improve AI model performance
5. **Notification System**: Notify relevant parties when feedback is received
6. **Advanced Analytics**: More detailed analytics and reporting dashboards
7. **Feedback Workflows**: Approval workflows for feedback processing
8. **Integration**: Integration with external analytics and monitoring tools

## Support

For questions or issues with the feedback system:
1. Check the logs for error details
2. Verify database connectivity and schema
3. Ensure proper authentication and permissions
4. Review the test suite for usage examples
5. Contact the development team for additional support