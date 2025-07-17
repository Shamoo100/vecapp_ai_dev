from typing import Dict, Any
import datetime
from app.agents.followup_note_agent import FollowupNoteAgent
from app.database.repositories.tenant_context import TenantContextMiddleware
from app.services.member_service import MemberService
from app.services.calendar_service import CalendarService
from app.services.connect_service import ConnectService
from app.database.repositories.connection import DatabaseConnection
from app.data.interfaces.ai_task_repository import AITaskRepository, AINotesRepository  
from app.config.settings import settings  # Assuming settings has OPENAI_API_KEY
import json
import os  # Add this for env var check

class FollowupService:
    async def generate_summary_note(self, schema_name: str, person_id: int, task_id: int) -> Dict[str, Any]:
        """
        Generate AI summary note for follow-up based on visitor data.
        Uses mock data if TEST_MODE is enabled or real fetching fails.
        """
        try:
            with TenantContextMiddleware(schema_name):
                test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
                
                try:
                    # Fetch real data
                    visitor_data = await MemberService.get_person_by_id(person_id)
                    task_data = await MemberService.get_task_by_id(task_id)
                    events = await CalendarService.get_upcoming_events()
                    teams = await ConnectService.get_church_teams()
                    groups = await ConnectService.get_church_groups()
                except Exception as e:
                    if not test_mode:
                        raise ValueError(f"Failed to fetch data: {str(e)}")
                    # Use mock data
                    visitor_data = {
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'email': 'john@example.com',
                        'phone': '123-456-7890',
                        'first_time_visit': True,
                        'visit_date': datetime.datetime.now().isoformat()
                    }
                    task_data = {'id': task_id, 'type': 'followup'}
                    events = [{'name': 'Sunday Service', 'date': '2024-10-20'}]
                    teams = [{'name': 'Worship Team'}]
                    groups = [{'name': 'Bible Study Group'}]
                
                # Compile context
                context = {
                    'visitor': visitor_data,
                    'task': task_data,
                    'events': events,
                    'teams': teams,
                    'groups': groups,
                    'timestamp': datetime.datetime.now().isoformat()
                }
                
                # Instantiate agent
                agent = FollowupNoteAgent(
                    agent_id="followup_note_agent",
                    schema=schema_name,
                    openai_key=settings.OPENAI_API_KEY
                )
                
                # Generate note
                note = await agent.generate_note(context)
                
                # Write back to MemberService
                saved_note = await MemberService.create_note(note)
                
                # Save to AI service DB
                async with DatabaseConnection.get_session() as session:
                    task_repo = AITaskRepository(session)
                    note_repo = AINotesRepository(session)
                
                # Create FollowUpTask (adjust data as per your schema)
                ai_result = {
                    'note': note,
                    'confidence_score': note.get('sentiment_analysis', {}).get('confidence', 0.92),
                    'recommended_actions': [rec['action'] for rec in note.get('recommendations', [])],
                    'model_version': 'gpt-4'  # Example; pull from agent if available
                }
                task_data = {
                    'process_id': task_id,  # Adjust mappings as needed
                    'created_by': 'AI System',
                    'task_title': 'Follow-up Note Generation',
                    'task_description': 'AI-generated note for visitor',
                    'task_type': 'followup',
                    'task_status': 'completed',
                    'task_priority': 'medium',
                    'task_type_flag': 1,
                    'person_id': person_id,
                    'recipient_id': person_id,
                    'recipient_fam_id': None,
                    'assigned_to_email': None
                }
                followup_task = await task_repo.create_followup_task(
                    external_task_id=task_id,
                    tenant_id=1,  # Replace with actual tenant_id retrieval
                    task_data=task_data,
                    ai_result=ai_result
                )
                
                # Create FollowUpNote
                ai_metadata = {
                    'confidence_score': ai_result['confidence_score'],
                    'model_version': ai_result['model_version'],
                    'prompt_version': '1.0',  # Example
                    'context': context
                }
                note_data = {
                    'title': note['header']['title'],
                    'notes_body': note,
                    'person_id': person_id,
                    'recipient_id': person_id,
                    'recipient_fam_id': None
                }
                async with DatabaseConnection.get_session() as session:
                    task_repo = AITaskRepository(session)
                    note_repo = AINotesRepository(session)
                    await note_repo.create_note(
                        task_id=followup_task.id,
                        tenant_id=1,  # Replace with actual
                        note_data=note_data,
                        ai_metadata=ai_metadata
                    )
                    await session.commit()  # Commit the transaction
                
                return saved_note
        except Exception as e:
            print(f"Error generating summary note: {str(e)}")  # Replace with logging
            raise