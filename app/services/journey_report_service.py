from typing import Dict, List, Any
from datetime import datetime
import logging
import uuid
from app.agents.followup_journey_report_agent import FollowupJourneyReportAgent
from app.api.schemas.journey_report import JourneyReportRequest, JourneyReportResponse, VisitorJourneyEntry
from app.services.member_service import MemberService
from app.data.models.member_service_models import JourneyReportData
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class JourneyReportService:
    """Service for generating follow-up journey reports"""
    
    def __init__(self, tenant: str):
        self.tenant = tenant
        self.member_service = MemberService(schema_name=tenant)
        self.journey_agent = FollowupJourneyReportAgent(agent_id=f"journey-{tenant}", schema=tenant)
    
    async def generate_journey_report(self, request: JourneyReportRequest) -> JourneyReportResponse:
        """Generate comprehensive journey report with AI analysis"""
        try:
            # Initialize member service
            await self.member_service.initialize()
            
            # 1. Fetch visitors within date range
            visitors_data = await self._fetch_visitors_in_range(
                request.start_date, request.end_date
            )
            
            if not visitors_data:
                raise HTTPException(
                    status_code=404, 
                    detail="No visitor records found for the selected range."
                )
            
            # 2. Aggregate follow-up data for each visitor/family
            enriched_data = await self._enrich_with_followup_data(visitors_data)
            
            # 3. Generate AI analysis for each entry
            analyzed_entries = await self.journey_agent.analyze_journey_entries(enriched_data)
            
            # 4. Group by family and determine primary contacts
            grouped_entries = await self._group_by_family(analyzed_entries)
            
            # 5. Generate summary statistics
            summary_stats = self._calculate_summary_stats(grouped_entries)
            
            return JourneyReportResponse(
                report_id=str(uuid.uuid4()),
                generated_at=datetime.now(),
                report_purpose=request.report_purpose,
                date_range={
                    "start_date": request.start_date,
                    "end_date": request.end_date
                },
                summary_stats=summary_stats,
                entries=grouped_entries,
                total_visitors=len(grouped_entries),
                visitors_joined=summary_stats.get("joined", 0),
                visitors_undecided=summary_stats.get("undecided", 0),
                visitors_not_interested=summary_stats.get("not_interested", 0)
            )
            
        except Exception as e:
            logger.error(f"Journey report generation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Something went wrong while generating the report. Please try again."
            )
        finally:
            await self.member_service.close()
    
    async def _fetch_visitors_in_range(self, start_date: datetime, end_date: datetime) -> List[JourneyReportData]:
        """Fetch visitors and their journey data within the specified date range"""
        try:
            visitors_journey_data = await self.member_service.get_visitors_journey_data(
                start_date=start_date,
                end_date=end_date,
                limit=200
            )
            
            logger.info(f"Fetched {len(visitors_journey_data)} visitors for journey report")
            return visitors_journey_data
            
        except Exception as e:
            logger.error(f"Error fetching visitors in range: {str(e)}")
            raise
    
    async def _enrich_with_followup_data(self, visitors_data: List[JourneyReportData]) -> List[Dict[str, Any]]:
        """Enrich visitor data with structured follow-up information for AI analysis"""
        enriched_entries = []
        
        for visitor_data in visitors_data:
            try:
                # Structure data for AI agent
                enriched_entry = {
                    "visitor_id": str(visitor_data.person_id),
                    "profile": {
                        "name": f"{visitor_data.person_profile.first_name} {visitor_data.person_profile.last_name}",
                        "email": visitor_data.person_profile.email,
                        "phone": visitor_data.person_profile.phone,
                        "family_id": str(visitor_data.person_profile.fam_id) if visitor_data.person_profile.fam_id else None,
                        "join_date": visitor_data.person_profile.join_date.isoformat() if visitor_data.person_profile.join_date else None,
                        "spiritual_need": visitor_data.person_profile.spiritual_need,
                        "prayer_request": visitor_data.person_profile.prayer_request
                    },
                    "tasks": [
                        {
                            "id": task.id,
                            "title": task.task_title,
                            "description": task.task_description,
                            "status": task.task_status,
                            "type": task.task_type,
                            "priority": task.task_priority,
                            "created_at": task.created_at.isoformat() if task.created_at else None,
                            "planned_start": task.task_planned_startdate.isoformat() if task.task_planned_startdate else None,
                            "planned_end": task.task_planned_enddate.isoformat() if task.task_planned_enddate else None,
                            "actual_start": task.task_actual_startdatetime.isoformat() if task.task_actual_startdatetime else None,
                            "actual_end": task.task_actual_enddatetime.isoformat() if task.task_actual_enddatetime else None,
                            "assignees": [assignee.assignee_name for assignee in task.assignees if assignee.assignee_name],
                            "feedback": [
                                {
                                    "contacted": feedback.is_contacted,
                                    "responded": feedback.has_responded,
                                    "agreed_to_join": feedback.agreed_to_join,
                                    "provider": feedback.provider_name
                                } for feedback in task.feedback
                            ]
                        } for task in visitor_data.follow_up_tasks
                    ],
                    "notes": [
                        {
                            "id": note.id,
                            "title": note.title,
                            "body": note.notes_body,
                            "type": note.type,
                            "created_at": note.created_at.isoformat() if note.created_at else None
                        } for note in visitor_data.notes
                    ],
                    "interactions": [],  # Can be extended with additional interaction data
                    "prayer_requests": [
                        {
                            "request": pr.prayer_request,
                            "created_at": pr.created_at.isoformat() if pr.created_at else None
                        } for pr in visitor_data.prayer_requests
                    ],
                    "feedback_entries": [
                        {
                            "feedback": fb.feedback,
                            "created_at": fb.created_at.isoformat() if fb.created_at else None
                        } for fb in visitor_data.feedback_entries
                    ],
                    "decisions": [
                        {
                            "consider_joining": dec.consider_joining,
                            "joining_our_church": dec.joining_our_church,
                            "daily_devotional": dec.daily_devotional,
                            "just_relocated": dec.just_relocated
                        } for dec in visitor_data.decisions
                    ],
                    "metrics": {
                        "total_tasks": visitor_data.total_tasks,
                        "completed_tasks": visitor_data.completed_tasks,
                        "pending_tasks": visitor_data.pending_tasks,
                        "last_contact_date": visitor_data.last_contact_date.isoformat() if visitor_data.last_contact_date else None,
                        "engagement_score": visitor_data.engagement_score
                    }
                }
                
                enriched_entries.append(enriched_entry)
                
            except Exception as e:
                logger.error(f"Error enriching visitor data for {visitor_data.person_id}: {str(e)}")
                # Add minimal entry to avoid losing the visitor
                enriched_entries.append({
                    "visitor_id": str(visitor_data.person_id),
                    "profile": {"name": "Unknown"},
                    "tasks": [],
                    "notes": [],
                    "interactions": [],
                    "metrics": {"total_tasks": 0, "completed_tasks": 0, "pending_tasks": 0}
                })
        
        return enriched_entries
    
    async def _group_by_family(self, analyzed_entries: List[Dict[str, Any]]) -> List[VisitorJourneyEntry]:
        """Group analyzed entries by family and create VisitorJourneyEntry objects"""
        family_groups = {}
        individual_entries = []
        
        # Group by family
        for entry in analyzed_entries:
            family_id = entry.get("profile", {}).get("family_id")
            
            if family_id:
                if family_id not in family_groups:
                    family_groups[family_id] = []
                family_groups[family_id].append(entry)
            else:
                individual_entries.append(entry)
        
        journey_entries = []
        
        # Process family groups
        for family_id, family_members in family_groups.items():
            # Determine primary contact (first member or head of family)
            primary_contact = family_members[0]
            
            # Aggregate family data
            all_tasks = []
            all_assignees = set()
            task_dates = []
            
            for member in family_members:
                for task in member.get("tasks", []):
                    all_tasks.append(task)
                    all_assignees.update(task.get("assignees", []))
                    if task.get("created_at"):
                        task_dates.append(task["created_at"])
            
            # Create family journey entry
            family_entry = VisitorJourneyEntry(
                visitor_family_name=f"{primary_contact.get('profile', {}).get('name', 'Unknown')} Family",
                follow_up_context="Family",
                family_size=len(family_members),
                first_time_visit_date=datetime.fromisoformat(primary_contact.get("profile", {}).get("join_date", datetime.now().isoformat())),
                primary_contact=primary_contact.get("profile", {}).get("name", "Unknown"),
                contact_attempts=len(all_tasks),
                task_summary=f"{len(all_tasks)} total – {sum(1 for t in all_tasks if t.get('status') == 'completed')} completed, {sum(1 for t in all_tasks if t.get('status') in ['pending', 'in_progress'])} pending",
                task_assignees=list(all_assignees),
                task_creation_date=datetime.fromisoformat(min(task_dates)) if task_dates else None,
                task_completion_date=datetime.fromisoformat(max([t["actual_end"] for t in all_tasks if t.get("actual_end")])) if any(t.get("actual_end") for t in all_tasks) else None,
                unresolved_needs=primary_contact.get("unresolved_needs", []),
                visitor_decision=primary_contact.get("visitor_decision", "undecided"),
                decision_rationale=primary_contact.get("decision_rationale", "No analysis available"),
                ai_recommendations=primary_contact.get("ai_recommendations", [])
            )
            
            journey_entries.append(family_entry)
        
        # Process individual entries
        for entry in individual_entries:
            tasks = entry.get("tasks", [])
            task_dates = [t["created_at"] for t in tasks if t.get("created_at")]
            assignees = set()
            for task in tasks:
                assignees.update(task.get("assignees", []))
            
            individual_entry = VisitorJourneyEntry(
                visitor_family_name=entry.get("profile", {}).get("name", "Unknown"),
                follow_up_context="Individual",
                family_size=1,
                first_time_visit_date=datetime.fromisoformat(entry.get("profile", {}).get("join_date", datetime.now().isoformat())),
                primary_contact=entry.get("profile", {}).get("name", "Unknown"),
                contact_attempts=len(tasks),
                task_summary=f"{len(tasks)} total – {sum(1 for t in tasks if t.get('status') == 'completed')} completed, {sum(1 for t in tasks if t.get('status') in ['pending', 'in_progress'])} pending",
                task_assignees=list(assignees),
                task_creation_date=datetime.fromisoformat(min(task_dates)) if task_dates else None,
                task_completion_date=datetime.fromisoformat(max([t["actual_end"] for t in tasks if t.get("actual_end")])) if any(t.get("actual_end") for t in tasks) else None,
                unresolved_needs=entry.get("unresolved_needs", []),
                visitor_decision=entry.get("visitor_decision", "undecided"),
                decision_rationale=entry.get("decision_rationale", "No analysis available"),
                ai_recommendations=entry.get("ai_recommendations", [])
            )
            
            journey_entries.append(individual_entry)
        
        return journey_entries
    
    def _calculate_summary_stats(self, entries: List[VisitorJourneyEntry]) -> Dict[str, Any]:
        """Calculate summary statistics for the report"""
        total_visitors = len(entries)
        joined = sum(1 for entry in entries if entry.visitor_decision == "joined")
        undecided = sum(1 for entry in entries if entry.visitor_decision == "undecided")
        not_interested = sum(1 for entry in entries if entry.visitor_decision == "not_interested")
        
        total_tasks = sum(len(entry.task_assignees) for entry in entries)
        total_families = sum(1 for entry in entries if entry.follow_up_context == "Family")
        total_individuals = sum(1 for entry in entries if entry.follow_up_context == "Individual")
        
        return {
            "total_visitors": total_visitors,
            "joined": joined,
            "undecided": undecided,
            "not_interested": not_interested,
            "total_tasks": total_tasks,
            "total_families": total_families,
            "total_individuals": total_individuals,
            "join_rate": round((joined / total_visitors * 100), 2) if total_visitors > 0 else 0,
            "engagement_rate": round(((joined + undecided) / total_visitors * 100), 2) if total_visitors > 0 else 0
        }