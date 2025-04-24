import pytest
from datetime import datetime
from agents.data_collection_agent import DataCollectionAgent
from core.database import Database
from models.visitor import Visitor

@pytest.fixture
async def database():
    db = Database("postgresql://user:password@localhost:5432/church_mas_test")
    await db.initialize()
    return db

@pytest.fixture
def data_collection_agent(database):
    return DataCollectionAgent("test-agent", "test-tenant", database)

@pytest.mark.asyncio
async def test_process_valid_visitor_data(data_collection_agent):
    test_data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'phone': '1234567890',
        'visit_date': datetime.now().isoformat()
    }

    result = await data_collection_agent.process(test_data)

    assert result['tenant_id'] == 'test-tenant'
    assert result['visitor_data']['first_name'] == 'John'
    assert result['visitor_data']['email'] == 'john.doe@example.com'
    assert 'visitor_id' in result

@pytest.mark.asyncio
async def test_process_invalid_visitor_data(data_collection_agent):
    test_data = {
        'first_name': 'John',
        # Missing required fields
    }

    with pytest.raises(ValueError) as exc_info:
        await data_collection_agent.process(test_data)

    assert "Missing required fields" in str(exc_info.value) 