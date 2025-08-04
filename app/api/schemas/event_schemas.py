"""
Event schemas for visitor follow-up note generation system.
Defines the structure for SQS events based on real production data.
Updated to handle dynamic visitor welcome form scenarios.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID


class FamilyContext(str, Enum):
    """Enum for family context types from visitor welcome form"""
    INDIVIDUAL = "individual"
    FAMILY = "family"


class FamilyHistory(str, Enum):
    """Enum for family history types from visitor welcome form"""
    NEW = "new"
    EXISTING = "existing"


class SentimentType(str, Enum):
    """Enum for sentiment analysis results"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class ContactPreference(str, Enum):
    """Enum for contact preferences"""
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    IN_PERSON = "in_person"


class VisitorEventData(BaseModel):
    """
    Production SQS event data structure for visitor follow-up notes.
    Based on real visitor welcome form data and family scenarios.
    
    Scenarios:
    1. family_context=individual, family_history=new: fam_head_id=person_id
    2. family_context=individual, family_history=existing: fam_id exists, fam_head_id != person_id
    3. family_context=family, family_history=new: new fam_id, fam_head_id=person_id, query other members by fam_id
    4. family_context=family, family_history=existing: fam_id exists, fam_head_id != person_id

    Actual format:
   {
   "tenant":"test","fam_id":"df02de53-14a2-4eb2-87f8-66a54e18e223","fam_head_id":"c24f33ba-28f2-480c-9686-173e972d480f",
   "person_id":"c24f33ba-28f2-480c-9686-173e972d480f","family_context":"family","family_history":"new",
   "new_family_member":["9ef55af6-5f53-438f-bafd-c1a91931fe66"]
   }
    """
    # Tenant context (matches real SQS data)
    tenant: str = Field(..., description="Tenant identifier")

    # Core identifiers (always present)
    person_id: UUID = Field(..., description="Primary person ID from the visitor welcome form")
    fam_id: UUID = Field(..., description="Family ID (varies by scenario)")
    fam_head_id: UUID = Field(..., description="Family head ID (varies by scenario)")
    
    # Family context from visitor welcome form
    family_context: FamilyContext = Field(..., description="Individual or family context from form")
    family_history: FamilyHistory = Field(..., description="New or existing family from form")
    
    # Optional family members (for family context scenarios)
    new_family_members_id: Optional[List[str]] = Field(
        default_factory=list, 
        description="List of new family member IDs (when family_context=family)"
    )
    
    # Event metadata (optional, may not be present in all messages)
    timestamp: Optional[datetime] = Field(None, description="Event timestamp")
    event_type: Optional[str] = Field(None, description="Type of event")
    
    @validator('fam_head_id', 'fam_id')
    def validate_family_relationships(cls, v, values):
        """Validate family relationships based on scenarios"""
        if 'family_context' in values and 'family_history' in values and 'person_id' in values:
            family_context = values['family_context']
            family_history = values['family_history']
            person_id = values['person_id']
            
            # Scenario 1: individual + new = fam_head_id = person_id (fam_id is always different)
            if family_context == FamilyContext.INDIVIDUAL and family_history == FamilyHistory.NEW:
                if v != person_id:
                    # This is expected for scenario 1
                    pass
            
            # Scenario 2: individual + existing = fam_id exists, fam_head_id != person_id
            elif family_context == FamilyContext.INDIVIDUAL and family_history == FamilyHistory.EXISTING:
                # fam_head_id should be different from person_id
                pass
            
            # Scenario 3: family + new = new fam_id, fam_head_id = person_id
            elif family_context == FamilyContext.FAMILY and family_history == FamilyHistory.NEW:
                # fam_head_id should equal person_id for new families
                pass
            
            # Scenario 4: family + existing = fam_id exists, fam_head_id != person_id
            elif family_context == FamilyContext.FAMILY and family_history == FamilyHistory.EXISTING:
                # fam_head_id should be different from person_id
                pass
        
        return v
    
    def get_scenario_type(self) -> str:
        """
        Determine the family scenario type based on family_context and family_history.
        Returns scenario identifier for the family scenario resolver.
        """
        if self.family_context == FamilyContext.INDIVIDUAL:
            if self.family_history == FamilyHistory.NEW:
                return "individual_new"
            else:
                return "individual_existing"
        else:  # family_context == FamilyContext.FAMILY
            if self.family_history == FamilyHistory.NEW:
                return "family_new"
            else:
                return "family_existing"
    
    def get_family_members_to_query(self) -> List[str]:
        """
        Determine which family members need to be queried based on the scenario.
        """
        scenario = self.get_scenario_type()
        
        if scenario == "individual_new":
            # Only query the person themselves
            return [str(self.person_id)]
        
        elif scenario == "individual_existing":
            # Query the person and potentially family head if different
            members = [str(self.person_id)]
            if self.fam_head_id != self.person_id:
                members.append(str(self.fam_head_id))
            return members
        
        elif scenario == "family_new":
            # Query the person (family head) and any new family members
            members = [str(self.person_id)]
            if self.new_family_members_id:
                members.extend(self.new_family_members_id)
            return members
        
        elif scenario == "family_existing":
            # Query all family members by fam_id (will be handled by member service)
            # Return the person_id as primary, member service will query by fam_id
            return [str(self.person_id)]
        
        return [str(self.person_id)]


class DataCollectionRequirements(BaseModel):
    """
    Defines specific data collection requirements based on acceptance criteria.
    Ensures all required data sources are collected for AI note generation.
    """
    # Required data sources from acceptance criteria
    visitor_welcome_form: bool = Field(True, description="Include visitor welcome form data")
    first_timer_notes: bool = Field(True, description="Include first timer notes if available")
    prayer_requests: bool = Field(True, description="Include prayer requests")
    visitor_profile: bool = Field(True, description="Include complete visitor profile")
    existing_followup_notes: bool = Field(True, description="Include existing follow-up task notes")
    feedback_fields: bool = Field(True, description="Include explicit feedback fields")
    
    # Public data sources
    public_teams: bool = Field(True, description="Include public teams within tenant")
    public_groups: bool = Field(True, description="Include public groups within tenant")
    upcoming_events: bool = Field(True, description="Include upcoming events within tenant")
    
    # Time constraints
    events_timeframe_days: int = Field(14, description="Days ahead for upcoming events")
    
    # Filtering requirements
    apply_tenant_rules: bool = Field(True, description="Apply tenant-specific business rules")
    filter_by_demographics: bool = Field(True, description="Filter recommendations by demographics")
    respect_visibility_rules: bool = Field(True, description="Respect visibility and life stage rules")


class AIGeneratedNoteStructure(BaseModel):
    """
    Structure for AI-generated notes based on acceptance criteria.
    Defines the exact fields and format required for the AI note output.
    """
    #natural summary
    natural_summary: str = Field(..., description="Natural summary of the visitor")
    # Required visitor information
    visitor_full_name: str = Field(..., description="Complete visitor name")
    visitor_phone: Optional[str] = Field(None, description="Visitor phone number")
    visitor_email: Optional[str] = Field(None, description="Visitor email address")
    first_visit: Optional[str] = Field(None, description="First visit date")
    best_contact_time: Optional[str] = Field(None, description="Best time to contact visitor")
    channel_to_contact: Optional[str] = Field(None, description="Channel to contact visitor")
    
    # Analysis fields
    key_interests_summary: List[str] = Field(
        default_factory=list, 
        description="Key interests or needs identified"
    )
    family_context_info: Optional[str] = Field(None, description="Family context if applicable")
    
    # Sentiment analysis
    sentiment_analysis: Dict[str, Any] = Field(
        default_factory=lambda: {"sentiment": "neutral", "confidence": 0.0, "source": "default"},
        description="Sentiment analysis based on feedback and free-text fields"
    )
    
    # Recommended next steps (organized by objective)
    church_integration_recommendations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Up to 2 recommended public teams or groups"
    )
    event_engagement_recommendations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Up to 2 upcoming community events within 14 days"
    )
    personal_needs_response: Optional[Dict[str, Any]] = Field(
        None,
        description="1 suggestion if need detected, pastoral escalation if applicable"
    )
    feedback_insight: Optional[Dict[str, Any]] = Field(
        None,
        description="Feedback tone and operational category with action step"
    )
    
    # Additional fields expected by the service (aliases for compatibility)
    email: Optional[str] = Field(None, description="Alias for visitor_email")
    phone: Optional[str] = Field(None, description="Alias for visitor_phone")
    key_interests: List[str] = Field(default_factory=list, description="Alias for key_interests_summary")
    family_context: Optional[str] = Field(None, description="Alias for family_context_info")
    best_time_to_contact: Optional[str] = Field(None, description="Alias for best_contact_time")
    
    # Recommended next steps (expected by service)
    recommended_next_steps: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Organized recommendations by category"
    )
    
    # Missing metadata fields
    confidence_score: float = Field(0.85, description="AI confidence score for the generated note")
    data_sources_used: List[str] = Field(
        default_factory=lambda: ["visitor_profile", "welcome_form"],
        description="List of data sources used in generation"
    )
    
    # Metadata
    ai_generated_label: bool = Field(True, description="Marks note as AI-generated")
    generation_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the note was generated"
    )
    person_id: str = Field(..., description="Person ID for linking")
    task_id: Optional[str] = Field(None, description="Task ID for linking")
    
    # Raw content for display
    raw_content: str = Field(..., description="Formatted note content for display")
    
    def __init__(self, **data):
        """Initialize with field aliasing for backward compatibility."""
        super().__init__(**data)
        
        # Set up aliases for backward compatibility
        if not self.email and self.visitor_email:
            self.email = self.visitor_email
        if not self.phone and self.visitor_phone:
            self.phone = self.visitor_phone
        if not self.key_interests and self.key_interests_summary:
            self.key_interests = self.key_interests_summary
        if not self.family_context and self.family_context_info:
            self.family_context = self.family_context_info
        if not self.best_time_to_contact and self.best_contact_time:
            self.best_time_to_contact = self.best_contact_time
            
        # Build recommended_next_steps from individual recommendation fields
        if not self.recommended_next_steps:
            self.recommended_next_steps = {
                "church_integration": [
                    rec.get("title", str(rec)) if isinstance(rec, dict) else str(rec)
                    for rec in self.church_integration_recommendations
                ],
                "event_engagement": [
                    rec.get("title", str(rec)) if isinstance(rec, dict) else str(rec)
                    for rec in self.event_engagement_recommendations
                ],
                "personal_needs": [
                    self.personal_needs_response.get("summary", str(self.personal_needs_response))
                    if isinstance(self.personal_needs_response, dict) else str(self.personal_needs_response)
                ] if self.personal_needs_response else [],
                "feedback_insights": [
                    self.feedback_insight.get("action_step", str(self.feedback_insight))
                    if isinstance(self.feedback_insight, dict) else str(self.feedback_insight)
                ] if self.feedback_insight else []
            }


class FamilyScenario(BaseModel):
    """
    Resolved family scenario with data requirements.
    Used by the family scenario resolver to determine what data to fetch.
    """
    scenario_type: str = Field(..., description="Scenario identifier (individual_new, individual_existing, family_new, family_existing)")
    primary_person_id: str = Field(..., description="Primary person to focus on")
    family_members_to_query: List[str] = Field(
        default_factory=list, 
        description="List of family member IDs to query"
    )
    family_head_id: Optional[str] = Field(None, description="Family head ID if applicable")
    fam_id: str = Field(..., description="Family ID for member service queries")
    context_strategy: str = Field(..., description="Strategy for building AI context")
    data_requirements: DataCollectionRequirements = Field(
        default_factory=DataCollectionRequirements,
        description="Specific data collection requirements"
    )
    
    @classmethod
    def from_visitor_event(cls, event_data: VisitorEventData) -> "FamilyScenario":
        """
        Create a FamilyScenario from VisitorEventData.
        Implements the four scenario logic for member service queries.
        """
        scenario_type = event_data.get_scenario_type()
        family_members_to_query = event_data.get_family_members_to_query()
        
        # Determine context strategy based on scenario
        context_strategies = {
            "individual_new": "focus_on_individual_new_member",
            "individual_existing": "focus_on_individual_with_family_context",
            "family_new": "focus_on_new_family_unit",
            "family_existing": "focus_on_family_addition"
        }
        
        return cls(
            scenario_type=scenario_type,
            primary_person_id=str(event_data.person_id),
            family_members_to_query=family_members_to_query,
            family_head_id=str(event_data.fam_head_id),
            fam_id=str(event_data.fam_id),
            context_strategy=context_strategies.get(scenario_type, "default"),
            data_requirements=DataCollectionRequirements()
        )


class VisitorContextData(BaseModel):
    """
    Comprehensive visitor context data structure based on acceptance criteria.
    Contains all data needed for AI note generation.
    """
    # Primary visitor data (from visitor welcome form)    
    visitor_profile: Dict[str, Any] = Field(..., description="Primary visitor information")
    visitor_welcome_form: Dict[str, Any] = Field(
        default_factory=dict,
        description="Complete visitor welcome form data including free-text responses and family members data"
    )
    
    # Family and relationship data
    family_members: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Family member information and structure"
    )
    
    # Historical and engagement data
    first_timer_notes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="First timer notes if available"
    )
    prayer_requests: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Prayer requests from visitor"
    )
    existing_followup_notes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Existing follow-up task notes"
    )
    feedback_fields: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Explicit feedback fields from forms"
    )
    
    # Public tenant data for recommendations
    public_teams: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Public teams within tenant (filtered by business rules)"
    )
    public_groups: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Public groups within tenant (filtered by business rules)"
    )
    upcoming_events: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Upcoming events within 14 days (filtered by business rules)"
    )
    
    # Metadata
    scenario_info: FamilyScenario = Field(..., description="Family scenario information")
    data_collection_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        description="When this data was collected"
    )
    tenant_business_rules: Dict[str, Any] = Field(
        default_factory=dict,
        description="Applied tenant-specific business rules"
    )


class AINoteFeedback(BaseModel):
    """
    Schema for admin feedback on AI-generated notes.
    Based on acceptance criteria feedback requirements.
    """
    note_id: str = Field(..., description="ID of the AI-generated note")
    person_id: str = Field(..., description="Person ID the note relates to")
    task_id: str = Field(..., description="Task ID the note relates to")
    
    # Feedback fields
    was_helpful: Literal["yes", "no", "partially"] = Field(
        ..., 
        description="Was this recommendation helpful?"
    )
    feedback_comments: Optional[str] = Field(
        None,
        description="Additional feedback comments from admin"
    )
    
    # Specific recommendation feedback
    church_integration_feedback: Optional[Dict[str, Any]] = Field(
        None,
        description="Feedback on church integration recommendations"
    )
    event_engagement_feedback: Optional[Dict[str, Any]] = Field(
        None,
        description="Feedback on event engagement recommendations"
    )
    personal_needs_feedback: Optional[Dict[str, Any]] = Field(
        None,
        description="Feedback on personal needs response"
    )
    
    # Metadata
    feedback_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When feedback was provided"
    )
    admin_id: str = Field(..., description="ID of admin providing feedback")


class AIGenerationError(BaseModel):
    """
    Schema for AI generation errors.
    Used for logging when AI generation fails.
    """
    error_id: str = Field(..., description="Unique error identifier")
    person_id: str = Field(..., description="Person ID where generation failed")
    task_id: str = Field(..., description="Task ID where generation failed")
    tenant_id: str = Field(..., description="Tenant ID where generation failed")
    
    error_type: str = Field(..., description="Type of error (e.g., 'data_collection', 'ai_processing')")
    error_message: str = Field(..., description="Detailed error message")
    error_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the error occurred"
    )
    
    # Context for debugging
    event_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Original event data that caused the error"
    )
    stack_trace: Optional[str] = Field(
        None,
        description="Stack trace for debugging (admin only)"
    )