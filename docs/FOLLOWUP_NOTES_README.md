# Follow-up Notes Summary API

This document describes the AI service's follow-up notes summary functionality that integrates with the member service (Node.js backend) to automatically generate AI-powered follow-up notes for new visitors and tasks.

## Overview

The follow-up notes system works as follows:

1. **Member Service** creates a task for a new visitor
2. **Member Service** publishes visitor/task data to AWS SQS
3. **AI Service** receives the message and processes it
4. **AI Service** generates follow-up notes using LLM
5. **AI Service** sends the generated notes back to the member service
6. **Member Service** updates the task with AI-generated notes

## Architecture

```
┌─────────────────┐    SQS Message    ┌─────────────────┐
│   Member        │ ──────────────────▶│   AI Service    │
│   Service       │                    │                 │
│   (Node.js)     │◀────────────────── │   (Python)      │
└─────────────────┘    Response SQS    └─────────────────┘
        │                                       │
        ▼                                       ▼
┌─────────────────┐                    ┌─────────────────┐
│   Member DB     │                    │   AI Models     │
│   (Tasks)       │                    │   (LLM)         │
└─────────────────┘                    └─────────────────┘
```

## API Endpoints

### 1. Process SQS Message
**POST** `/api/v1/followup-tasks/process-sqs-message`

Processes incoming SQS messages from the member service containing task data.

### 2. Generate Note (Direct)
**POST** `/api/v1/followup-tasks/generate-note`

Direct endpoint for generating follow-up notes (for testing/debugging).

**Request Body:**
```json
{
  "id": 1,
  "task_title": "Follow-up with new visitor - John Smith",
  "task_description": "New visitor attended Sunday service...",
  "task_type": "follow_up",
  "tenant_id": 1,
  "recipient": {
    "person": {
      "first_name": "John",
      "last_name": "Smith",
      "email": "john.smith@email.com"
    }
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Follow-up note generated successfully",
  "result": {
    "task_id": 1,
    "person_id": "person_12345",
    "generated_note": "AI-generated follow-up note...",
    "recommended_actions": ["Schedule children's ministry tour"],
    "ai_confidence_score": 0.85
  }
}
```

### 3. Task Status
**GET** `/api/v1/followup-tasks/status/{task_id}`

Retrieve the status of a follow-up task.

### 4. Health Check
**GET** `/api/v1/followup-tasks/health`

Health check endpoint for monitoring.

## Data Models

### Task Data Structure

Based on the sample data provided, the task structure includes:

```python
class TaskData(BaseModel):
    id: int
    process_id: Optional[int]
    created_by: str
    task_title: str
    task_description: str
    task_type: str
    task_status: str
    task_priority: Optional[str]
    task_planned_startdate: Optional[str]
    task_planned_enddate: Optional[str]
    tenant_id: int
    recipient: RecipientData
    assignees: List[AssigneeData]
    notes: List[str]
```

### Person Data Structure

```python
class PersonData(BaseModel):
    id: str
    first_name: str
    last_name: str
    relationship: Optional[str]
    profile_pic_url: Optional[str]
    email: Optional[str]
    avatar_color: Optional[str]
```

## SQS Integration

### Message Format

Messages sent from the member service should follow this format:

```json
{
  "message_type": "task_created",
  "task_data": {
    // Task data structure as defined above
  },
  "timestamp": "2024-01-07T10:30:00Z",
  "source_service": "member_service"
}
```

### Queue Configuration

- **Input Queue**: `member-to-ai-tasks` (receives task data from member service)
- **Output Queue**: `ai-to-member-responses` (sends generated notes back)

## AI Note Generation

The AI service uses the `FollowupSummaryAgent` to generate personalized follow-up notes based on:

- Visitor information (name, contact details)
- Task description and context
- Church events and activities
- Team member assignments
- Historical patterns and preferences

### Generated Content

The AI generates:

1. **Personalized Follow-up Note**: Contextual message for the visitor
2. **Recommended Actions**: Suggested next steps for staff
3. **Confidence Score**: AI's confidence in the recommendations (0.0-1.0)

## Database Models

### FollowUpTask Model

The AI service maintains its own follow-up task records:

```python
class FollowUpTask(Base):
    __tablename__ = "followup_tasks"
    
    id = Column(Integer, primary_key=True)
    external_task_id = Column(Integer)  # Reference to member service task
    tenant_id = Column(Integer)
    person_id = Column(String)
    task_title = Column(String)
    task_description = Column(Text)
    generated_note = Column(Text)
    ai_confidence_score = Column(Float)
    recommended_actions = Column(JSON)
    status = Column(Enum(FollowUpStatus))
    priority = Column(Enum(FollowUpPriority))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

## Testing

Use the provided test script to verify the API functionality:

```bash
python test_followup_api.py
```

This script tests:
- Health check endpoint
- Direct note generation
- SQS message processing simulation
- Task status retrieval

## Configuration

### Environment Variables

```bash
# AWS SQS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
SQS_QUEUE_URL_INPUT=https://sqs.us-east-1.amazonaws.com/account/member-to-ai-tasks
SQS_QUEUE_URL_OUTPUT=https://sqs.us-east-1.amazonaws.com/account/ai-to-member-responses

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/ai_service_db

# AI Configuration
OPENAI_API_KEY=your_openai_api_key
AI_MODEL=gpt-4
```

## Deployment

1. **Database Migration**: Run Alembic migrations to create the `followup_tasks` table
2. **SQS Setup**: Configure AWS SQS queues for message passing
3. **Environment**: Set up environment variables
4. **Monitoring**: Configure logging and health checks

### Database Migration

```bash
# Generate migration for FollowUpTask model
alembic revision --autogenerate -m "Add followup_tasks table"

# Apply migration
alembic upgrade head
```

## Integration Flow

### Step-by-Step Process

1. **Task Creation** (Member Service):
   ```javascript
   // Member service creates task
   const task = await createFollowUpTask(visitorData);
   
   // Publish to SQS
   await sqsClient.sendMessage({
     QueueUrl: 'member-to-ai-tasks',
     MessageBody: JSON.stringify({
       message_type: 'task_created',
       task_data: task,
       timestamp: new Date().toISOString(),
       source_service: 'member_service'
     })
   });
   ```

2. **Message Processing** (AI Service):
   ```python
   # AI service receives and processes message
   async def process_followup_task(message_data):
       agent = FollowupSummaryAgent()
       result = await agent.generate_followup_note(task_data)
       
       # Send response back to member service
       await messaging_service.send_followup_response(result)
   ```

3. **Response Handling** (Member Service):
   ```javascript
   // Member service receives AI response
   const response = await sqsClient.receiveMessage({
     QueueUrl: 'ai-to-member-responses'
   });
   
   // Update task with AI-generated note
   await updateTaskWithAINote(response.task_id, response.generated_note);
   ```

## Error Handling

- **Message Validation**: Validates incoming SQS messages
- **Retry Logic**: Implements exponential backoff for failed operations
- **Dead Letter Queue**: Routes failed messages for manual review
- **Logging**: Comprehensive logging for debugging and monitoring

## Security

- **API Authentication**: Secure API endpoints with proper authentication
- **SQS Permissions**: Configure IAM roles for SQS access
- **Data Encryption**: Encrypt sensitive data in transit and at rest
- **Input Validation**: Validate all incoming data to prevent injection attacks

## Monitoring

- **Health Checks**: Regular health check endpoints
- **Metrics**: Track processing times, success rates, and error rates
- **Alerts**: Set up alerts for failed message processing
- **Logging**: Structured logging for troubleshooting

## Sample Data Files

The system uses the following sample data files for testing and development:

- `app/data/events/task_sample_data.json` - Sample task data structure
- `app/data/events/church_events_sample_data.json` - Church events data
- `app/data/events/team_sample_data.json` - Team member data

These files provide examples of the data structure expected from the member service.