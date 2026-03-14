import unittest
from unittest.mock import AsyncMock, MagicMock
from app.services.eah_agent.storage.session_history import SessionHistory
from app.models.chat import ChatSession, ChatMessage

class TestSessionHistory(unittest.IsolatedAsyncioTestCase):
    async def test_create_session(self):
        # Mock DB
        mock_db = AsyncMock()
        mock_db.add = MagicMock() # Sync method
        
        history = SessionHistory(mock_db)
        session = await history.create_session("user1", "agent1", "Test Chat")
        
        self.assertIsNotNone(session)
        self.assertEqual(session.title, "Test Chat")
        self.assertEqual(session.user_id, "user1")
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_add_message(self):
        # Mock DB
        mock_db = AsyncMock()
        mock_db.add = MagicMock() # Sync method
        
        history = SessionHistory(mock_db)
        msg = await history.add_message("session1", "user", "Hello")
        
        self.assertEqual(msg.session_id, "session1")
        self.assertEqual(msg.role, "user")
        self.assertEqual(msg.content, "Hello")
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_get_session(self):
        # Mock DB execute result
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_session = ChatSession(id="session1", title="Found")
        mock_result.scalars.return_value.first.return_value = mock_session
        mock_db.execute.return_value = mock_result
        
        history = SessionHistory(mock_db)
        session = await history.get_session("session1")
        
        self.assertEqual(session.title, "Found")
        mock_db.execute.assert_called_once()

if __name__ == '__main__':
    unittest.main()
