"""
Tests for the agent tools.
"""
import pytest
from unittest.mock import patch, MagicMock
import json
import aiohttp
from bs4 import BeautifulSoup
from langchain.llms.base import LLM

from app.agent.tools.google_search import GoogleSearchTool
from app.agent.tools.web_scraper import WebScraperTool
from app.agent.tools.profile_identifier import ProfileIdentifierTool


@pytest.fixture
def mock_requests_get():
    """Fixture for mocking requests.get."""
    with patch("requests.get") as mock:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "organic_results": [
                {
                    "title": "John Doe | LinkedIn",
                    "link": "https://www.linkedin.com/in/johndoe",
                    "snippet": "John Doe - Software Engineer at Tech Company - View profile on LinkedIn"
                },
                {
                    "title": "John Doe (@johndoe) | Twitter",
                    "link": "https://twitter.com/johndoe",
                    "snippet": "The latest Tweets from John Doe (@johndoe). Software Engineer, AI enthusiast."
                }
            ],
            "items": [
                {
                    "title": "John Doe | LinkedIn",
                    "link": "https://www.linkedin.com/in/johndoe",
                    "snippet": "John Doe - Software Engineer at Tech Company - View profile on LinkedIn"
                },
                {
                    "title": "John Doe (@johndoe) | Twitter",
                    "link": "https://twitter.com/johndoe",
                    "snippet": "The latest Tweets from John Doe (@johndoe). Software Engineer, AI enthusiast."
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock.return_value = mock_response
        yield mock


@pytest.fixture
def mock_aiohttp_get():
    """Fixture for mocking aiohttp.ClientSession.get."""
    class MockResponse:
        def __init__(self, text, status):
            self._text = text
            self.status = status
        
        async def text(self):
            return self._text
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
    
    with patch("aiohttp.ClientSession.get") as mock:
        # Create a sample HTML content
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>John Doe | LinkedIn</title>
        </head>
        <body>
            <main>
                <div class="profile-header">
                    <h1 class="text-heading-xlarge">John Doe</h1>
                    <p class="text-body-medium">Software Engineer at Tech Company</p>
                </div>
                <section id="about-section">
                    <p>Experienced Software Engineer with a passion for AI and machine learning.</p>
                </section>
                <section id="experience-section">
                    <div class="experience-item">
                        <h3>Software Engineer</h3>
                        <p>Tech Company</p>
                        <p>2018 - Present</p>
                    </div>
                </section>
            </main>
        </body>
        </html>
        """
        
        mock.return_value = MockResponse(html_content, 200)
        yield mock


@pytest.fixture
def mock_llm():
    """Fixture for mocking LLM."""
    mock_llm = MagicMock(spec=LLM)
    
    async def ainvoke(prompt):
        # Return a sample identification response
        if "search results" in prompt.get("template", ""):
            return {
                "text": """
                1. LinkedIn Profile
                   URL: https://www.linkedin.com/in/johndoe
                   Platform: LinkedIn
                   Relevance Score: 0.9
                   
                2. Twitter Profile
                   URL: https://twitter.com/johndoe
                   Platform: Twitter
                   Relevance Score: 0.8
                """
            }
        # Return a sample analysis response
        elif "profile page" in prompt.get("template", ""):
            return {
                "text": """
                # Name
                John Doe
                
                # Title
                Software Engineer at Tech Company
                
                # Bio
                Experienced Software Engineer with a passion for AI and machine learning.
                
                # Experience
                - Software Engineer at Tech Company (2018 - Present)
                
                # Skills
                - Python
                - Machine Learning
                - AI
                
                # Interests
                - Technology
                - Artificial Intelligence
                - Hiking
                """
            }
        else:
            return {"text": "Default response"}
    
    mock_llm.ainvoke = ainvoke
    return mock_llm


@pytest.mark.asyncio
async def test_google_search_tool_serpapi(mock_requests_get):
    """Test the Google Search Tool with SerpAPI."""
    tool = GoogleSearchTool(api_type="serpapi", api_key="fake_key")
    results = await tool.search("John Doe")
    
    # Check that the search was performed
    mock_requests_get.assert_called_once()
    
    # Check the results
    assert len(results) == 2
    assert results[0].title == "John Doe | LinkedIn"
    assert results[0].link == "https://www.linkedin.com/in/johndoe"
    assert "Software Engineer" in results[0].snippet


@pytest.mark.asyncio
async def test_google_search_tool_google_cse(mock_requests_get):
    """Test the Google Search Tool with Google CSE."""
    tool = GoogleSearchTool(api_type="google_cse", api_key="fake_key", cse_id="fake_cse_id")
    results = await tool.search("John Doe")
    
    # Check that the search was performed
    mock_requests_get.assert_called_once()
    
    # Check the results
    assert len(results) == 2
    assert results[0].title == "John Doe | LinkedIn"
    assert results[0].link == "https://www.linkedin.com/in/johndoe"
    assert "Software Engineer" in results[0].snippet


@pytest.mark.asyncio
async def test_web_scraper_tool(mock_aiohttp_get):
    """Test the Web Scraper Tool."""
    tool = WebScraperTool(user_agent="test_agent")
    result = await tool.scrape("https://www.linkedin.com/in/johndoe")
    
    # Check that the scraping was performed
    mock_aiohttp_get.assert_called_once()
    
    # Check the results
    assert result["success"] is True
    assert result["url"] == "https://www.linkedin.com/in/johndoe"
    assert result["platform"] == "LinkedIn"
    assert "John Doe" in result["content"]
    assert "Software Engineer" in result["content"]


@pytest.mark.asyncio
async def test_profile_identifier_tool_identify(mock_llm):
    """Test the Profile Identifier Tool's identify_profiles function."""
    tool = ProfileIdentifierTool(llm=mock_llm)
    
    search_results = [
        {
            "title": "John Doe | LinkedIn",
            "link": "https://www.linkedin.com/in/johndoe",
            "snippet": "John Doe - Software Engineer at Tech Company - View profile on LinkedIn"
        },
        {
            "title": "John Doe (@johndoe) | Twitter",
            "link": "https://twitter.com/johndoe",
            "snippet": "The latest Tweets from John Doe (@johndoe). Software Engineer, AI enthusiast."
        }
    ]
    
    results = await tool.identify_profiles(search_results)
    
    # Check the results
    assert len(results) == 2
    assert results[0]["url"] == "https://www.linkedin.com/in/johndoe"
    assert results[0]["platform"] == "LinkedIn"
    assert results[0]["relevance_score"] == 0.9
    
    assert results[1]["url"] == "https://twitter.com/johndoe"
    assert results[1]["platform"] == "Twitter"
    assert results[1]["relevance_score"] == 0.8


@pytest.mark.asyncio
async def test_profile_identifier_tool_analyze(mock_llm):
    """Test the Profile Identifier Tool's analyze_profile function."""
    tool = ProfileIdentifierTool(llm=mock_llm)
    
    profile_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>John Doe | LinkedIn</title>
    </head>
    <body>
        <main>
            <div class="profile-header">
                <h1>John Doe</h1>
                <p>Software Engineer at Tech Company</p>
            </div>
            <section id="about-section">
                <p>Experienced Software Engineer with a passion for AI and machine learning.</p>
            </section>
        </main>
    </body>
    </html>
    """
    
    result = await tool.analyze_profile(profile_content)
    
    # Check the results
    assert result["name"] == "John Doe"
    assert result["title"] == "Software Engineer at Tech Company"
    assert "Experienced Software Engineer" in result["bio"]
    assert len(result["experience"]) == 1
    assert "Tech Company" in result["experience"][0]["description"]
    assert len(result["skills"]) == 3
    assert "Python" in result["skills"]
    assert len(result["interests"]) == 3
    assert "Artificial Intelligence" in result["interests"]