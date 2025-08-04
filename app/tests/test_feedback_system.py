import pytest
import asyncio
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base

# Create a simple base for testing
Base = declarative_base()

# Import only the models we need for testing
from app.database.models.followup_task import FollowUpNote, AINoteFeedback, FeedbackHelpfulness
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.feedback import SubmitFeedbackRequest, FeedbackHelpfulness as SchemaFeedbackHelpfulness

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_feedback.db"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestFeedbackSystem:
    """Test suite for AI note feedback functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test database before each test"""
        # Import the actual models to create tables
        from app.database.models.followup_task import Base as ActualBase
        ActualBase.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
        
        # Create test AI-generated note with recommendations
        self.test_note = FollowUpNote(
            id=uuid4(),
            visitor_id=uuid4(),
            tenant_id=uuid4(),
            content="AI Summary: Visitor showed high interest in sustainability programs. Recommendations: 1) Follow up with environmental volunteer opportunities 2) Share upcoming green initiatives 3) Connect with sustainability coordinator",
            ai_generated=True,
            ai_model_version="gpt-4",
            ai_confidence_score=0.95,
            feedback_received=False
        )
        self.db.add(self.test_note)
        self.db.commit()
        
        # Initialize repository with test database
        self.feedback_repo = FeedbackRepository()
    
    def teardown_method(self):
        """Clean up after each test"""
        self.db.close()
        from app.database.models.followup_task import Base as ActualBase
        ActualBase.metadata.drop_all(bind=engine)
    
    def test_submit_feedback_success(self):
        """Test successful feedback submission for AI-generated note summary and recommendations"""
        feedback_request = SubmitFeedbackRequest(
            note_id=self.test_note.id,
            visitor_id=uuid4(),
            admin_id=uuid4(),
            tenant_id=uuid4(),
            helpfulness=SchemaFeedbackHelpfulness.yes,
            comment="AI summary accurately captured visitor interests. Recommendations are actionable and relevant for follow-up."
        )
        
        # Test repository method directly
        result = asyncio.run(self.feedback_repo.submit_feedback(
            self.db, feedback_request
        ))
        
        assert result is not None
        assert "feedback_id" in result
        
        # Verify note is marked as feedback received
        updated_note = self.db.query(FollowUpNote).filter(FollowUpNote.id == self.test_note.id).first()
        assert updated_note.feedback_received == True
    
    def test_submit_feedback_duplicate(self):
        """Test duplicate feedback submission for AI recommendations"""
        feedback_request = SubmitFeedbackRequest(
            note_id=self.test_note.id,
            visitor_id=uuid4(),
            admin_id=uuid4(),
            tenant_id=uuid4(),
            helpfulness=SchemaFeedbackHelpfulness.yes,
            comment="AI recommendations are well-targeted for this visitor profile"
        )
        
        # Submit first feedback
        result1 = asyncio.run(self.feedback_repo.submit_feedback(
            self.db, feedback_request
        ))
        assert result1 is not None
        
        # Try to submit duplicate feedback
        feedback_request.comment = "Updated: AI summary could include more specific volunteer role suggestions"
        try:
            result2 = asyncio.run(self.feedback_repo.submit_feedback(
                self.db, feedback_request
            ))
            assert False, "Should have raised an exception for duplicate feedback"
        except Exception as e:
            assert "already submitted feedback" in str(e).lower() or "duplicate" in str(e).lower()
    
    def test_submit_feedback_nonexistent_note(self):
        """Test feedback submission for non-existent note"""
        feedback_request = SubmitFeedbackRequest(
            note_id=uuid4(),  # Non-existent note ID
            visitor_id=uuid4(),
            admin_id=uuid4(),
            tenant_id=uuid4(),
            helpfulness=SchemaFeedbackHelpfulness.yes,
            comment="Test comment"
        )
        
        # Test repository method directly
        try:
            result = asyncio.run(self.feedback_repo.submit_feedback(
                self.db, feedback_request
            ))
            assert False, "Should have raised an exception for non-existent note"
        except Exception as e:
            assert "not found" in str(e).lower() or "does not exist" in str(e).lower()
    
    def test_get_feedback_for_note(self):
        """Test retrieving feedback for AI-generated note to help refine AI service"""
        # Submit feedback first on AI recommendations
        feedback_request = SubmitFeedbackRequest(
            note_id=self.test_note.id,
            visitor_id=uuid4(),
            admin_id=uuid4(),
            tenant_id=uuid4(),
            helpfulness=SchemaFeedbackHelpfulness.yes,
            comment="AI correctly identified visitor's sustainability interests. Recommendations align well with available programs."
        )
        
        # Test repository method directly
        result = asyncio.run(self.feedback_repo.submit_feedback(
            self.db, feedback_request
        ))
        
        assert result is not None
        
        # Now retrieve feedback for the note
        feedback_list = asyncio.run(self.feedback_repo.get_feedback_for_note(
            self.db, self.test_note.id
        ))
        
        assert len(feedback_list) == 1
        assert feedback_list[0].helpfulness == FeedbackHelpfulness.yes
        assert feedback_list[0].comment == "AI correctly identified visitor's sustainability interests. Recommendations align well with available programs."
    
    def test_get_feedback_by_admin(self):
        """Test retrieving feedback by admin"""
        # Submit multiple feedback entries
        for i in range(3):
            note = FollowUpNote(
                followup_task_id=i+2,
                external_task_id=i+2,
                title=f"Test Note {i+2}",
                notes_body=f"Test content {i+2}",
                person_id=uuid4(),
                is_ai_generated=True,
                ai_confidence_score=0.8,
                ai_model_version="gpt-4-turbo"
            )
            self.db.add(note)
            self.db.commit()
            self.db.refresh(note)
            
            feedback_request = SubmitFeedbackRequest(
                note_id=note.id,
                visitor_id=uuid4(),
                admin_id=self.admin_id,
                tenant_id=self.tenant_id,
                helpfulness="yes" if i % 2 == 0 else "no"
            )
            
            client.post("/api/v1/feedback/submit", json=feedback_request.model_dump())
        
        # Get feedback by admin
        response = client.get(
            f"/api/v1/feedback/admin/{self.admin_id}?tenant_id={self.tenant_id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        assert all(feedback["admin_id"] == str(self.admin_id) for feedback in data)
    
    def test_feedback_stats(self):
        """Test feedback statistics endpoint"""
        # Submit various feedback
        helpfulness_values = ["yes", "no", "partially", "yes", "yes"]
        
        for i, helpfulness in enumerate(helpfulness_values):
            note = FollowUpNote(
                followup_task_id=i+10,
                external_task_id=i+10,
                title=f"Stats Test Note {i+1}",
                notes_body=f"Stats test content {i+1}",
                person_id=uuid4(),
                is_ai_generated=True,
                ai_confidence_score=0.8,
                ai_model_version="gpt-4-turbo"
            )
            self.db.add(note)
            self.db.commit()
            self.db.refresh(note)
            
            feedback_request = SubmitFeedbackRequest(
                note_id=note.id,
                visitor_id=uuid4(),
                admin_id=uuid4(),  # Different admin for each
                tenant_id=self.tenant_id,
                helpfulness=helpfulness
            )
            
            client.post("/api/v1/feedback/submit", json=feedback_request.model_dump())
        
        # Get stats
        response = client.get(f"/api/v1/feedback/stats?tenant_id={self.tenant_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_feedback"] == 5
        assert data["helpfulness_breakdown"]["FeedbackHelpfulness.YES"] == 3
        assert data["helpfulness_breakdown"]["FeedbackHelpfulness.NO"] == 1
        assert data["helpfulness_breakdown"]["FeedbackHelpfulness.PARTIALLY"] == 1
        assert data["notes_with_feedback"] == 5
    
    def test_feedback_repository_direct(self):
        """Test feedback repository methods for AI service refinement data collection"""
        repo = FeedbackRepository(self.db)
        
        # Test submit feedback on AI-generated recommendations
        feedback_request = SubmitFeedbackRequest(
            note_id=self.test_note.id,
            visitor_id=uuid4(),
            admin_id=uuid4(),
            tenant_id=uuid4(),
            helpfulness=SchemaFeedbackHelpfulness.yes,
            comment="AI model correctly identified key visitor interests. Recommendations are specific and actionable for volunteer coordination."
        )
        
        feedback = repo.submit_feedback(feedback_request)
        assert feedback is not None
        assert feedback.helpfulness == FeedbackHelpfulness.YES
        assert feedback.comment == "Direct repo test"
        
        # Test get feedback for note
        feedback_list = repo.get_feedback_for_note(self.test_note.id, self.tenant_id)
        assert len(feedback_list) == 1
        assert feedback_list[0].id == feedback.id
        
        # Test check note exists
        assert repo.check_note_exists(self.test_note.id, self.tenant_id) is True
        assert repo.check_note_exists(99999, self.tenant_id) is False
    
    def test_feedback_validation(self):
        """Test input validation for feedback"""
        # Test invalid helpfulness value
        invalid_request = {
            "note_id": self.test_note.id,
            "visitor_id": str(self.visitor_id),
            "admin_id": str(self.admin_id),
            "tenant_id": self.tenant_id,
            "helpfulness": "invalid_value",
            "comment": "Test comment"
        }
        
        response = client.post("/api/v1/feedback/submit", json=invalid_request)
        assert response.status_code == 422  # Validation error
        
        # Test comment too long
        long_comment_request = {
            "note_id": self.test_note.id,
            "visitor_id": str(self.visitor_id),
            "admin_id": str(self.admin_id),
            "tenant_id": self.tenant_id,
            "helpfulness": "yes",
            "comment": "x" * 101  # Exceeds 100 character limit
        }
        
        response = client.post("/api/v1/feedback/submit", json=long_comment_request)
        assert response.status_code == 422  # Validation error
    
    def test_health_check(self):
        """Test feedback service health check"""
        response = client.get("/api/v1/feedback/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "feedback"
        assert "message" in data

if __name__ == "__main__":
    # Run tests
    pytest.main(["-v", __file__])