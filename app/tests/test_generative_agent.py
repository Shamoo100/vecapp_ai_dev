import pytest
from unittest.mock import Mock, patch
from agents.generative_agent import GenerativeAgent
from app.core.messaging import MessageQueue
from datetime import datetime

@pytest.fixture
def message_queue():
    return Mock(spec=MessageQueue)

@pytest.fixture
def generative_agent(message_queue):
    return GenerativeAgent(
        agent_id="test-ga",
        tenant_id="test-tenant",
        openai_key="test-key",
        message_queue=message_queue
    )

@pytest.mark.asyncio
async def test_generate_persona(generative_agent):
    visitor_data = {
        'visitor_data': {
            'visitor_id': '123',
            'tenant_id': 'test-tenant',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'visit_date': datetime.now().isoformat()
        }
    }

    with patch('openai.ChatCompletion.create') as mock_openai:
        mock_openai.return_value.choices = [
            Mock(message=Mock(content="Test persona response"))
        ]
        
        result = await generative_agent.process(visitor_data)
        
        assert result['visitor_id'] == '123'
        assert 'persona' in result
        assert 'recommendations' in result
        assert 'follow_up_time' in result