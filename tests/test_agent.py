"""
Tests for the ice breaker agent.
"""
import pytest
import re
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from typing import List, Dict, Any

from langchain.agents.agent import AgentExecutor
from langchain.prompts import PromptTemplate
from langchain.llms.base import LLM

from app.agent.icebreaker_agent import create_icebreaker_agent, generate_icebreakers, get_llm, AgentCallbackHandler
from app.models.schemas import ProfileSource


@pytest.fixture
def mock_llm():
    """Fixture for mocking LLM."""
    mock_llm = MagicMock(spec=LLM)
    mock_llm.predict = MagicMock(return_value="Test response")
    return mock_llm


@pytest.fixture
def mock_agent_executor():
    """Fixture for mocking AgentExecutor."""
    mock_executor = MagicMock(spec=AgentExecutor)
    
    # Define async behavior
    async def mock_ainvoke(input_data, callbacks=None):
        return {
            "output": "Test agent output",
            "profile_data": [
                {
                    "name": "John Doe",
                    "title": "Software Engineer",
                    "bio": "Experienced engineer with passion for AI",
                    "experience": [{"company": "Tech Corp", "role": "Engineer"}],
                    "skills": ["Python", "Machine Learning"],
                    "interests": ["AI", "Technology"]
                }
            ],
            "sources": [
                {
                    "url": "https://www.linkedin.com/in/johndoe",
                    "platform": "LinkedIn",
                    "title": "John Doe | LinkedIn",
                    "relevance_score": 0.9
                },
                {
                    "url": "https://twitter.com/johndoe",
                    "platform": "Twitter",
                    "title": "John Doe (@johndoe) / Twitter",
                    "relevance_score": 0.8
                }
            ]
        }
    
    mock_executor.ainvoke = AsyncMock(side_effect=mock_ainvoke)
    return mock_executor


@pytest.fixture
def mock_tools():
    """Fixture for mocking agent tools."""
    return [
        MagicMock(name="GoogleSearch"),
        MagicMock(name="WebScraper"),
        MagicMock(name="ProfileIdentifier"),
        MagicMock(name="ProfileAnalyzer")
    ]


@patch("app.agent.icebreaker_agent.settings")
def test_get_llm_local(mock_settings):
    """Test getting a local LLM."""
    # Configure mock settings
    mock_settings.get_llm_config.return_value = {
        "type": "mistral",
        "model_path": "/path/to/model.gguf",
        "api_url": None,
        "api_key": None
    }
    
    with patch("app.agent.icebreaker_agent.LlamaCpp") as mock_llama:
        mock_llama.return_value = MagicMock()
        
        # Test function
        llm = get_llm()
        
        # Verify LlamaCpp was called
        mock_llama.assert_called_once()
        assert llm is not None


@patch("app.agent.icebreaker_agent.settings")
def test_get_llm_api(mock_settings):
    """Test getting an API-based LLM."""
    # Configure mock settings
    mock_settings.get_llm_config.return_value = {
        "type": "mistral",
        "model_path": None,
        "api_url": "https://api.example.com",
        "api_key": "test_api_key"
    }
    
    with patch("app.agent.icebreaker_agent.ChatOpenAI") as mock_chat:
        mock_chat.return_value = MagicMock()
        
        # Test function
        llm = get_llm()
        
        # Verify ChatOpenAI was called
        mock_chat.assert_called_once()
        assert llm is not None


@patch("app.agent.icebreaker_agent.get_llm")
@patch("app.agent.icebreaker_agent.create_react_agent")
@patch("app.agent.icebreaker_agent.Tool")
@patch("app.agent.icebreaker_agent.AgentExecutor")
@patch("app.agent.icebreaker_agent.GoogleSearchTool")
@patch("app.agent.icebreaker_agent.WebScraperTool")
@patch("app.agent.icebreaker_agent.ProfileIdentifierTool")
@patch("app.agent.icebreaker_agent.settings")
def test_create_icebreaker_agent(
    mock_settings,
    mock_profile_identifier,
    mock_web_scraper,
    mock_google_search,
    mock_agent_executor,
    mock_tool,
    mock_create_agent,
    mock_get_llm
):
    """Test creating the ice breaker agent."""
    # Configure mocks
    mock_get_llm.return_value = MagicMock()
    mock_create_agent.return_value = MagicMock()
    mock_agent_executor.from_agent_and_tools.return_value = MagicMock()
    mock_settings.get_search_config.return_value = {
        "type": "serpapi",
        "api_key": "test_key"
    }
    mock_settings.MAX_ITERATIONS = 5
    mock_settings.MAX_EXECUTION_TIME = 60
    mock_settings.DEBUG = False
    
    # Test function
    agent = create_icebreaker_agent()
    
    # Verify agent creation
    assert agent is not None
    assert mock_get_llm.called
    assert mock_google_search.called
    assert mock_web_scraper.called
    assert mock_profile_identifier.called
    assert mock_tool.call_count == 4  # Four tools
    assert mock_create_agent.called
    assert mock_agent_executor.from_agent_and_tools.called


@pytest.mark.asyncio
async def test_agent_callback_handler():
    """Test the agent callback handler."""
    handler = AgentCallbackHandler()
    
    # Test action logging
    action = MagicMock()
    action.tool = "TestTool"
    action.tool_input = {"query": "test"}
    handler.on_agent_action(action)
    
    assert len(handler.steps) == 1
    assert handler.steps[0]["type"] == "action"
    
    # Test finish logging
    finish = MagicMock()
    finish.return_values = {"output": "test"}
    handler.on_agent_finish(finish)
    
    assert len(handler.steps) == 2
    assert handler.steps[1]["type"] == "finish"


@pytest.mark.asyncio
@patch("app.agent.icebreaker_agent.get_llm")
@patch("app.agent.icebreaker_agent.LLMChain")
async def test_generate_icebreakers(mock_llm_chain, mock_get_llm, mock_agent_executor):
    """Test generating ice breakers."""
    # Configure mocks
    mock_get_llm.return_value = MagicMock()
    
    # Mock LLMChain
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(return_value={"text": """
    1. I noticed you worked at Tech Corp. What was your most interesting project there?
    2. You seem passionate about AI. What specific area of AI excites you the most?
    3. How did you first get interested in machine learning?
    """})
    mock_llm_chain.return_value = mock_chain
    
    # Test function
    ice_breakers, sources = await generate_icebreakers(mock_agent_executor, "John Doe")
    
    # Verify results
    assert len(ice_breakers) == 3
    assert "Tech Corp" in ice_breakers[0]
    assert "AI" in ice_breakers[1]
    assert "machine learning" in ice_breakers[2]
    
    assert len(sources) == 2
    assert sources[0].platform == "LinkedIn"
    assert sources[1].platform == "Twitter"


@pytest.mark.asyncio
@patch("app.agent.icebreaker_agent.get_llm")
@patch("app.agent.icebreaker_agent.LLMChain")
async def test_generate_icebreakers_empty_result(mock_llm_chain, mock_get_llm, mock_agent_executor):
    """Test generating ice breakers with empty result."""
    # Configure mocks
    mock_get_llm.return_value = MagicMock()
    
    # Override agent executor to return empty profile data
    async def mock_empty_ainvoke(input_data, callbacks=None):
        return {
            "output": "No information found",
            "profile_data": [],
            "sources": []
        }
    
    mock_agent_executor.ainvoke = AsyncMock(side_effect=mock_empty_ainvoke)
    
    # Test function
    ice_breakers, sources = await generate_icebreakers(mock_agent_executor, "Unknown Person")
    
    # Verify fallback ice breakers are generated
    assert len(ice_breakers) == 3
    for ice_breaker in ice_breakers:
        assert "Unknown Person" in ice_breaker
    
    assert len(sources) == 0


@pytest.mark.asyncio
@patch("app.agent.icebreaker_agent.get_llm")
@patch("app.agent.icebreaker_agent.LLMChain")
async def test_generate_icebreakers_error_handling(mock_llm_chain, mock_get_llm, mock_agent_executor):
    """Test error handling in generate_icebreakers."""
    # Configure mocks
    mock_get_llm.return_value = MagicMock()
    
    # Make LLMChain raise an exception
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(side_effect=Exception("Test error"))
    mock_llm_chain.return_value = mock_chain
    
    # Test function
    ice_breakers, sources = await generate_icebreakers(mock_agent_executor, "John Doe")
    
    # Verify fallback ice breakers are generated despite error
    assert len(ice_breakers) == 3
    assert len(sources) == 2  # Sources should still be returned