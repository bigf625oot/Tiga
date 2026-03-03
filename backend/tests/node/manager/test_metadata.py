"""
Tests for NodeMetadataManager
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.node import Node, NodeStatus
from app.services.openclaw.node.manager.metadata import NodeMetadataManager

@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.mark.asyncio
async def test_update_node_metadata(mock_db_session):
    # Mock node retrieval
    node = Node(id="1", tags={}, config={})
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = node
    mock_db_session.execute.return_value = mock_result
    
    metadata = {
        "tags": {"env": "prod"},
        "resources": {"cpu": 8},
        "location": {"country": "US"}
    }
    
    await NodeMetadataManager.update_node_metadata(mock_db_session, "1", metadata)
    
    assert node.tags == {"env": "prod"}
    assert node.config["resources"] == {"cpu": 8}
    assert node.config["location"] == {"country": "US"}
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_filter_nodes_by_tags(mock_db_session):
    # Setup nodes
    node1 = Node(id="1", status=NodeStatus.ONLINE, tags={"env": "prod", "gpu": "true"})
    node2 = Node(id="2", status=NodeStatus.ONLINE, tags={"env": "dev"})
    node3 = Node(id="3", status=NodeStatus.ONLINE, tags={"env": "prod", "gpu": "false"})
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [node1, node2, node3]
    mock_db_session.execute.return_value = mock_result
    
    # Filter: env=prod
    nodes = await NodeMetadataManager.filter_nodes_by_tags(mock_db_session, {"env": "prod"})
    assert len(nodes) == 2
    assert node1 in nodes
    assert node3 in nodes
    
    # Filter: env=prod, gpu=true
    nodes = await NodeMetadataManager.filter_nodes_by_tags(mock_db_session, {"env": "prod", "gpu": "true"})
    assert len(nodes) == 1
    assert node1 in nodes
