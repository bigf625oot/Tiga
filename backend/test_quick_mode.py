import asyncio
from unittest.mock import MagicMock
from app.services.agent.orchestration.control_plane import AgnoControlPlane
from app.services.agent.orchestration.router import ModeRouter

async def test_quick_mode():
    db = MagicMock()
    llm_model = MagicMock()
    llm_model.provider = 'openai'
    llm_model.model_name = 'gpt-3.5-turbo'
    llm_model.api_key = 'fake'
    llm_model.base_url = 'fake'
    
    control_plane = AgnoControlPlane(llm_model=llm_model)
    
    # Mocking necessary methods to avoid DB hits
    async def mock_ensure(*args, **kwargs): pass
    async def mock_init(*args, **kwargs): pass
    control_plane._ensure_models = mock_ensure
    control_plane._init_history = mock_init
    
    # We want to catch the executor type in ModeRouter
    original_route = ModeRouter.route_request
    
    async def mock_route_request(self, user_input, db, kwargs, resolved_intent=None):
        print("Resolved intent passed to router:", resolved_intent.intent)
        executor, intent = await original_route(self, user_input, db, kwargs, resolved_intent)
        print("Selected executor:", type(executor).__name__)
        # Return a mock executor to avoid real LLM calls
        mock_executor = MagicMock()
        async def mock_exec(*args, **kwargs):
            yield {"type": "content", "content": "mock fast response"}
        mock_executor.execute = mock_exec
        return mock_executor, intent
        
    ModeRouter.route_request = mock_route_request
    
    async for chunk in control_plane.process_stream(
        user_input="写一首诗",
        db=db,
        session_id="test_session",
        mode="quick",
        persist_assistant_message=False,
        persist_user_message=False
    ):
        print("Chunk:", chunk)

asyncio.run(test_quick_mode())
