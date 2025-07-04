import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.batch_tenant_service import BatchTenantService
from app.api.schemas.batch_tenant import (
    BatchTenantCreate, TenantProvisioningConfig, TenantBulkUpdate,
    BatchProvisioningStatus, TenantProvisioningResult
)
from app.api.schemas.tenant import TenantCreate, TenantInDB


class TestBatchTenantService:
    """Test suite for BatchTenantService."""
    
    @pytest.fixture
    def batch_service(self):
        """Create a BatchTenantService instance for testing."""
        return BatchTenantService()
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def sample_tenant_data(self):
        """Create sample tenant data for testing."""
        return [
            TenantCreate(
                tenant_name="Test Church 1",
                domain="test-church-1.com",
                tenant_type="church",
                email="admin@test-church-1.com",
                provision_schema=True,
                run_migrations=True
            ),
            TenantCreate(
                tenant_name="Test Church 2",
                domain="test-church-2.com",
                tenant_type="church",
                email="admin@test-church-2.com",
                provision_schema=True,
                run_migrations=True
            )
        ]
    
    @pytest.fixture
    def sample_batch_request(self, sample_tenant_data):
        """Create a sample batch request."""
        return BatchTenantCreate(
            tenants=sample_tenant_data,
            provision_schema=True,
            run_migrations=True,
            parallel_processing=True,
            max_concurrent=2,
            continue_on_error=True
        )
    
    @pytest.mark.asyncio
    async def test_validate_tenant_data_success(self, batch_service, sample_tenant_data):
        """Test successful tenant data validation."""
        errors = await batch_service.validate_tenant_data(sample_tenant_data)
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_tenant_data_duplicate_domains(self, batch_service):
        """Test validation with duplicate domains."""
        tenant_data = [
            TenantCreate(
                tenant_name="Church 1",
                domain="duplicate.com",
                tenant_type="church"
            ),
            TenantCreate(
                tenant_name="Church 2",
                domain="duplicate.com",  # Duplicate domain
                tenant_type="church"
            )
        ]
        
        errors = await batch_service.validate_tenant_data(tenant_data)
        assert len(errors) > 0
        assert any("Duplicate domain" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_validate_tenant_data_invalid_domain(self, batch_service):
        """Test validation with invalid domain format."""
        tenant_data = [
            TenantCreate(
                tenant_name="Invalid Church",
                domain="invalid@domain!.com",  # Invalid characters
                tenant_type="church"
            )
        ]
        
        errors = await batch_service.validate_tenant_data(tenant_data)
        assert len(errors) > 0
        assert any("Invalid domain format" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_validate_tenant_data_empty_name(self, batch_service):
        """Test validation with empty tenant name."""
        tenant_data = [
            TenantCreate(
                tenant_name="",  # Empty name
                domain="valid-domain.com",
                tenant_type="church"
            )
        ]
        
        errors = await batch_service.validate_tenant_data(tenant_data)
        assert len(errors) > 0
        assert any("cannot be empty" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_estimate_batch_time_parallel(self, batch_service):
        """Test batch time estimation for parallel processing."""
        tenant_count = 10
        estimated_time = await batch_service.estimate_batch_time(tenant_count, parallel=True)
        
        # Should be less than sequential processing
        sequential_time = await batch_service.estimate_batch_time(tenant_count, parallel=False)
        assert estimated_time < sequential_time
        assert estimated_time > 0
    
    @pytest.mark.asyncio
    async def test_estimate_batch_time_sequential(self, batch_service):
        """Test batch time estimation for sequential processing."""
        tenant_count = 5
        estimated_time = await batch_service.estimate_batch_time(tenant_count, parallel=False)
        
        # Should be roughly proportional to tenant count
        assert estimated_time > 0
        assert estimated_time > tenant_count * 10  # Base time per tenant
    
    def test_update_config(self, batch_service):
        """Test configuration updates."""
        new_config = TenantProvisioningConfig(
            max_concurrent_operations=8,
            operation_timeout_seconds=600,
            retry_attempts=2,
            retry_delay_seconds=3,
            enable_rollback=True
        )
        
        batch_service.update_config(new_config)
        
        assert batch_service.config.max_concurrent_operations == 8
        assert batch_service.config.operation_timeout_seconds == 600
        assert batch_service.config.retry_attempts == 2
        assert batch_service._semaphore._value == 8
    
    @pytest.mark.asyncio
    async def test_get_batch_status_existing(self, batch_service):
        """Test getting status of existing batch."""
        # Create a mock batch response
        batch_id = str(uuid.uuid4())
        mock_response = Mock()
        mock_response.batch_id = batch_id
        mock_response.status = BatchProvisioningStatus.COMPLETED
        
        batch_service.active_batches[batch_id] = mock_response
        
        result = await batch_service.get_batch_status(batch_id)
        assert result == mock_response
    
    @pytest.mark.asyncio
    async def test_get_batch_status_nonexistent(self, batch_service):
        """Test getting status of non-existent batch."""
        result = await batch_service.get_batch_status("non-existent-id")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_active_batches(self, batch_service):
        """Test listing active batches."""
        # Add some mock batches
        batch1 = Mock()
        batch2 = Mock()
        
        batch_service.active_batches["batch1"] = batch1
        batch_service.active_batches["batch2"] = batch2
        
        result = await batch_service.list_active_batches()
        assert len(result) == 2
        assert batch1 in result
        assert batch2 in result
    
    @pytest.mark.asyncio
    async def test_cleanup_completed_batches(self, batch_service):
        """Test cleanup of completed batches."""
        # Create old completed batch
        old_batch = Mock()
        old_batch.status = BatchProvisioningStatus.COMPLETED
        old_batch.completed_at = datetime.utcnow().replace(year=2020)  # Very old
        
        # Create recent batch
        recent_batch = Mock()
        recent_batch.status = BatchProvisioningStatus.IN_PROGRESS
        recent_batch.completed_at = None
        
        batch_service.active_batches["old"] = old_batch
        batch_service.active_batches["recent"] = recent_batch
        
        await batch_service.cleanup_completed_batches(max_age_hours=1)
        
        # Old batch should be removed, recent should remain
        assert "old" not in batch_service.active_batches
        assert "recent" in batch_service.active_batches
    
    @pytest.mark.asyncio
    @patch('app.services.batch_tenant_service.BatchTenantService._provision_single_tenant')
    async def test_process_tenants_sequential_success(self, mock_provision, batch_service, sample_batch_request, mock_db_session):
        """Test sequential processing with all successful tenants."""
        # Mock successful provisioning
        mock_provision.return_value = TenantProvisioningResult(
            tenant_name="Test Church",
            domain="test-church.com",
            success=True,
            tenant_id=123,
            schema_name="test_church_com",
            api_key="test-api-key",
            schema_created=True,
            migrations_applied=True,
            processing_time_seconds=10.0
        )
        
        results = await batch_service._process_tenants_sequential(
            sample_batch_request, mock_db_session, "test-batch-id"
        )
        
        assert len(results) == 2
        assert all(result.success for result in results)
        assert mock_provision.call_count == 2
    
    @pytest.mark.asyncio
    @patch('app.services.batch_tenant_service.BatchTenantService._provision_single_tenant')
    async def test_process_tenants_sequential_with_failure(self, mock_provision, batch_service, sample_batch_request, mock_db_session):
        """Test sequential processing with one failure and continue_on_error=True."""
        # Mock first success, second failure
        mock_provision.side_effect = [
            TenantProvisioningResult(
                tenant_name="Test Church 1",
                domain="test-church-1.com",
                success=True,
                tenant_id=123,
                schema_name="test_church_1_com",
                api_key="test-api-key-1",
                schema_created=True,
                migrations_applied=True,
                processing_time_seconds=10.0
            ),
            TenantProvisioningResult(
                tenant_name="Test Church 2",
                domain="test-church-2.com",
                success=False,
                error_message="Database error",
                processing_time_seconds=5.0
            )
        ]
        
        results = await batch_service._process_tenants_sequential(
            sample_batch_request, mock_db_session, "test-batch-id"
        )
        
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
        assert "Database error" in results[1].error_message
    
    @pytest.mark.asyncio
    @patch('app.services.batch_tenant_service.BatchTenantService._provision_single_tenant')
    async def test_process_tenants_parallel_success(self, mock_provision, batch_service, sample_batch_request, mock_db_session):
        """Test parallel processing with all successful tenants."""
        # Mock successful provisioning
        mock_provision.return_value = TenantProvisioningResult(
            tenant_name="Test Church",
            domain="test-church.com",
            success=True,
            tenant_id=123,
            schema_name="test_church_com",
            api_key="test-api-key",
            schema_created=True,
            migrations_applied=True,
            processing_time_seconds=10.0
        )
        
        results = await batch_service._process_tenants_parallel(
            sample_batch_request, mock_db_session, "test-batch-id"
        )
        
        assert len(results) == 2
        assert all(result.success for result in results)
        assert mock_provision.call_count == 2
    
    @pytest.mark.asyncio
    @patch('app.services.multi_tenant_service.MultiTenantService.create_tenant')
    async def test_provision_single_tenant_success(self, mock_create_tenant, batch_service, sample_batch_request, mock_db_session):
        """Test successful single tenant provisioning."""
        # Mock successful tenant creation
        mock_tenant = TenantInDB(
            id=123,
            tenant_name="Test Church",
            domain="test-church.com",
            tenant_type="church",
            is_active=True,
            api_key="test-api-key",
            schema_name="test_church_com",
            schema_provisioned=True,
            migrations_applied=True,
            created_at=datetime.utcnow()
        )
        mock_create_tenant.return_value = mock_tenant
        
        tenant_data = sample_batch_request.tenants[0]
        result = await batch_service._provision_single_tenant(
            tenant_data, mock_db_session, sample_batch_request, "test-batch-id"
        )
        
        assert result.success is True
        assert result.tenant_id == 123
        assert result.schema_name == "test_church_com"
        assert result.api_key == "test-api-key"
        assert result.schema_created is True
        assert result.migrations_applied is True
    
    @pytest.mark.asyncio
    @patch('app.services.multi_tenant_service.MultiTenantService.create_tenant')
    async def test_provision_single_tenant_failure(self, mock_create_tenant, batch_service, sample_batch_request, mock_db_session):
        """Test single tenant provisioning failure."""
        # Mock tenant creation failure
        mock_create_tenant.side_effect = Exception("Database connection failed")
        
        tenant_data = sample_batch_request.tenants[0]
        result = await batch_service._provision_single_tenant(
            tenant_data, mock_db_session, sample_batch_request, "test-batch-id"
        )
        
        assert result.success is False
        assert "Database connection failed" in result.error_message
        assert result.tenant_id is None
    
    @pytest.mark.asyncio
    @patch('app.services.multi_tenant_service.MultiTenantService.create_tenant')
    async def test_provision_single_tenant_retry_success(self, mock_create_tenant, batch_service, sample_batch_request, mock_db_session):
        """Test single tenant provisioning with retry success."""
        # Mock first failure, then success
        mock_tenant = TenantInDB(
            id=123,
            tenant_name="Test Church",
            domain="test-church.com",
            tenant_type="church",
            is_active=True,
            api_key="test-api-key",
            schema_name="test_church_com",
            schema_provisioned=True,
            migrations_applied=True,
            created_at=datetime.utcnow()
        )
        
        mock_create_tenant.side_effect = [
            Exception("Temporary failure"),
            mock_tenant
        ]
        
        # Set retry configuration
        batch_service.config.retry_attempts = 1
        batch_service.config.retry_delay_seconds = 0.1  # Fast retry for testing
        
        tenant_data = sample_batch_request.tenants[0]
        result = await batch_service._provision_single_tenant(
            tenant_data, mock_db_session, sample_batch_request, "test-batch-id"
        )
        
        assert result.success is True
        assert result.tenant_id == 123
        assert mock_create_tenant.call_count == 2
    
    @pytest.mark.asyncio
    @patch('app.services.multi_tenant_service.MultiTenantService.update_tenant')
    async def test_bulk_update_tenants_success(self, mock_update_tenant, batch_service, mock_db_session):
        """Test successful bulk tenant updates."""
        # Mock successful updates
        mock_tenant = TenantInDB(
            id=123,
            tenant_name="Updated Church",
            domain="updated-church.com",
            tenant_type="church",
            is_active=True,
            api_key="test-api-key",
            schema_name="updated_church_com",
            schema_provisioned=True,
            migrations_applied=True,
            created_at=datetime.utcnow()
        )
        mock_update_tenant.return_value = mock_tenant
        
        bulk_update = TenantBulkUpdate(
            tenant_ids=[123, 124],
            update_data={"tenant_timezone": "America/Los_Angeles"},
            apply_migrations=False
        )
        
        result = await batch_service.bulk_update_tenants(bulk_update, mock_db_session)
        
        assert result.total_tenants == 2
        assert result.successful_updates == 2
        assert result.failed_updates == 0
        assert len(result.results) == 2
        assert mock_update_tenant.call_count == 2
    
    @pytest.mark.asyncio
    @patch('app.services.multi_tenant_service.MultiTenantService.update_tenant')
    async def test_bulk_update_tenants_partial_failure(self, mock_update_tenant, batch_service, mock_db_session):
        """Test bulk tenant updates with partial failures."""
        # Mock first success, second failure
        mock_tenant = TenantInDB(
            id=123,
            tenant_name="Updated Church",
            domain="updated-church.com",
            tenant_type="church",
            is_active=True,
            api_key="test-api-key",
            schema_name="updated_church_com",
            schema_provisioned=True,
            migrations_applied=True,
            created_at=datetime.utcnow()
        )
        
        mock_update_tenant.side_effect = [mock_tenant, None]  # Second returns None (not found)
        
        bulk_update = TenantBulkUpdate(
            tenant_ids=[123, 999],  # 999 doesn't exist
            update_data={"tenant_timezone": "America/Los_Angeles"},
            apply_migrations=False
        )
        
        result = await batch_service.bulk_update_tenants(bulk_update, mock_db_session)
        
        assert result.total_tenants == 2
        assert result.successful_updates == 1
        assert result.failed_updates == 1
        assert len(result.results) == 2
        assert result.results[0]["success"] is True
        assert result.results[1]["success"] is False
        assert "Tenant not found" in result.results[1]["error"]


class TestBatchTenantAPI:
    """Test suite for batch tenant API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test batch service health check endpoint."""
        response = client.get("/api/v1/batch-tenants/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "service_ready" in data
    
    def test_get_config(self, client):
        """Test getting batch configuration."""
        response = client.get("/api/v1/batch-tenants/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "max_concurrent_operations" in data
        assert "operation_timeout_seconds" in data
        assert "retry_attempts" in data
    
    def test_validate_tenant_data_valid(self, client):
        """Test tenant data validation with valid data."""
        payload = {
            "tenants": [
                {
                    "tenant_name": "Valid Church",
                    "domain": "valid-church.com",
                    "tenant_type": "church",
                    "email": "admin@valid-church.com"
                }
            ],
            "parallel_processing": True,
            "max_concurrent": 3
        }
        
        response = client.post("/api/v1/batch-tenants/validate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is True
        assert "estimated_processing_time_seconds" in data
    
    def test_validate_tenant_data_invalid(self, client):
        """Test tenant data validation with invalid data."""
        payload = {
            "tenants": [
                {
                    "tenant_name": "",  # Invalid: empty name
                    "domain": "invalid-church.com",
                    "tenant_type": "church"
                }
            ],
            "parallel_processing": True
        }
        
        response = client.post("/api/v1/batch-tenants/validate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is False
        assert "errors" in data
        assert len(data["errors"]) > 0
    
    def test_batch_create_oversized(self, client):
        """Test batch creation with oversized batch."""
        # Create a batch with too many tenants
        tenants = []
        for i in range(51):  # Exceeds limit of 50
            tenants.append({
                "tenant_name": f"Church {i}",
                "domain": f"church{i}.com",
                "tenant_type": "church"
            })
        
        payload = {
            "tenants": tenants,
            "parallel_processing": True
        }
        
        response = client.post("/api/v1/batch-tenants/batch-create", json=payload)
        assert response.status_code == 400
        
        data = response.json()
        assert "cannot exceed 50 tenants" in data["detail"]
    
    def test_bulk_update_oversized(self, client):
        """Test bulk update with oversized batch."""
        # Create a bulk update with too many tenant IDs
        tenant_ids = list(range(1, 102))  # Exceeds limit of 100
        
        payload = {
            "tenant_ids": tenant_ids,
            "update_data": {"tenant_timezone": "America/New_York"},
            "apply_migrations": False
        }
        
        response = client.post("/api/v1/batch-tenants/bulk-update", json=payload)
        assert response.status_code == 400
        
        data = response.json()
        assert "cannot exceed 100 tenants" in data["detail"]
    
    def test_bulk_update_empty_data(self, client):
        """Test bulk update with empty update data."""
        payload = {
            "tenant_ids": [1, 2, 3],
            "update_data": {},  # Empty update data
            "apply_migrations": False
        }
        
        response = client.post("/api/v1/batch-tenants/bulk-update", json=payload)
        assert response.status_code == 400
        
        data = response.json()
        assert "cannot be empty" in data["detail"]
    
    def test_cleanup_invalid_age(self, client):
        """Test cleanup with invalid max age."""
        response = client.delete("/api/v1/batch-tenants/cleanup?max_age_hours=0")
        assert response.status_code == 400
        
        data = response.json()
        assert "must be between 1 and 168" in data["detail"]
    
    def test_get_nonexistent_batch_status(self, client):
        """Test getting status of non-existent batch."""
        response = client.get("/api/v1/batch-tenants/batch-status/non-existent-id")
        assert response.status_code == 404
        
        data = response.json()
        assert "not found" in data["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])