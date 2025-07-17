from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from datetime import datetime
import logging

from app.database.models.tenant.ai_task import AITask
from app.database.models.tenant.ai_notes import AINotes
from app.database.models.tenant.ai_person import AIPerson
from app.database.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

class AITaskRepository(BaseRepository[AITask]):
    def __init__(self, session: AsyncSession):
        super().__init__(AITask, session)
    async def create_ai_task(
        self, 
        tenant_id: int,
        task_data: Dict[str, Any],
        ai_result: Dict[str, Any]
    ) -> AITask:
        try:
            ai_task = AITask(
                task_title=task_data.get('task_title'),
                task_description=task_data.get('task_description'),
                task_type=task_data.get('task_type'),
                task_status=task_data.get('task_status'),
                task_priority=task_data.get('task_priority'),
                task_type_flag=task_data.get('task_type_flag'),
                created_by=task_data.get('created_by'),
                recipient_person_id=task_data.get('recipient_person_id'),
                recipient_id=task_data.get('recipient_id'),
                recipient_family_id=task_data.get('recipient_family_id'),
                task_assignee_id=task_data.get('task_assignee_id'),
                follow_up_user=task_data.get('follow_up_user'),
                assign_usertype=task_data.get('assign_usertype'),
                routed_to=task_data.get('routed_to'),
                follow_up_prev_task=task_data.get('follow_up_prev_task'),
                ai_agent_type=ai_result.get('ai_agent_type'),
                ai_processing_status=ai_result.get('ai_processing_status', 'completed'),
                ai_confidence_score=ai_result.get('confidence_score'),
                ai_model_version=ai_result.get('model_version', 'gpt-4')
            )
            return await self.create(ai_task)
        except Exception as e:
            logger.error(f"Error creating AI task: {str(e)}")
            raise
    async def get_by_id(
        self, 
        task_id: int, 
        tenant_id: int
    ) -> Optional[AITask]:
        try:
            stmt = select(AITask).where(
                AITask.id == task_id,
                AITask.tenant_id == tenant_id  # Assuming tenant_id is added to model
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting AI task by ID {task_id}: {str(e)}")
            raise
    async def update_processing_status(
        self, 
        task_id: int, 
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        try:
            update_data = {
                "ai_processing_status": status,
                "updated_at": datetime.utcnow()
            }
            if status == 'processing':
                update_data["processing_started_at"] = datetime.utcnow()
            elif status == 'completed':
                update_data["processing_completed_at"] = datetime.utcnow()
            elif status == 'failed' and error_message:
                update_data["error_message"] = error_message
            stmt = update(AITask).where(
                AITask.id == task_id
            ).values(**update_data)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating task status {task_id}: {str(e)}")
            await self.session.rollback()
            raise
class AINotesRepository(BaseRepository[AINotes]):
    def __init__(self, session: AsyncSession):
        super().__init__(AINotes, session)
    async def create_note(
        self,
        task_id: int,
        tenant_id: int,
        note_data: Dict[str, Any],
        ai_metadata: Dict[str, Any]
    ) -> AINotes:
        try:
            note = AINotes(
                title=note_data.get('title'),
                notes_body=note_data.get('notes_body'),
                person_id=note_data.get('person_id'),
                task_id=task_id,
                task_assignee_id=note_data.get('task_assignee_id'),
                recipient_id=note_data.get('recipient_id'),
                recipient_family_id=note_data.get('recipient_family_id'),
                note_link=note_data.get('note_link'),
                meta=note_data.get('meta'),
                ai_generated=True,
                ai_model_used=ai_metadata.get('ai_model_used'),
                ai_generation_prompt=ai_metadata.get('ai_generation_prompt'),
                ai_review_status='pending',
                ai_confidence_score=ai_metadata.get('confidence_score')  # If applicable
            )
            return await self.create(note)
        except Exception as e:
            logger.error(f"Error creating AI note: {str(e)}")
            raise
    async def get_by_id(
        self, 
        task_id: int, 
        tenant_id: int
    ) -> Optional[AITask]:
        try:
            stmt = select(AITask).where(
                AITask.id == task_id,
                AITask.tenant_id == tenant_id  # Assuming tenant_id is added to model
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting AI task by ID {task_id}: {str(e)}")
            raise
    async def update_processing_status(
        self, 
        task_id: int, 
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        try:
            update_data = {
                "ai_processing_status": status,
                "updated_at": datetime.utcnow()
            }
            if status == 'processing':
                update_data["processing_started_at"] = datetime.utcnow()
            elif status == 'completed':
                update_data["processing_completed_at"] = datetime.utcnow()
            elif status == 'failed' and error_message:
                update_data["error_message"] = error_message
            stmt = update(AITask).where(
                AITask.id == task_id
            ).values(**update_data)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating task status {task_id}: {str(e)}")
            await self.session.rollback()
            raise