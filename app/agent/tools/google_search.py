"""
Google Search Tool for the ice breaker agent.
"""
import json
import requests
from typing import List, Dict, Any, Optional
from app.core.logging import logger
from app.models.schemas import SearchResult

class GoogleSearchTool:
    """Tool for searching Google via various APIs."""
    
    def __init__(self, api_type: str, api_key: str, cse_id: Optional[str] = None):
        """Initialize the Google search tool.
        
        Args:
            api_type: Type of API to use ("serpapi" or "google_cse")
            api_key: API key for the selected service
            cse_id: Custom Search Engine ID (only required for google_cse)
        """
        self.api_type = api_type
        self.api_key = api_key
        self.cse_id = cse_id
        
        if api_type == "google_cse" and not cse_id:
            raise ValueError("CSE ID must be provided for Google Custom Search API")
    
    async def search(self, query: str) -> List[SearchResult]:
        """Search Google for the given query.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        logger.info(f"Searching Google for: {query}")
        
        try:
            if self.api_type == "serpapi":
                return await self._search_serpapi(query)
            elif self.api_type == "google_cse":
                return await self._search_google_cse(query)
            else:
                raise ValueError(f"Unsupported API type: {self.api_type}")
        except Exception as e:
            logger.error(f"Error searching Google: {str(e)}", exc_info=True)
            return [
                SearchResult(
                    title="Error searching Google",
                    link="",
                    snippet=f"An error occurred while searching Google: {str(e)}",
                    source="error"
                )
            ]
    
    async def _search_serpapi(self, query: str) -> List[SearchResult]:
        """Search Google using SerpAPI.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": self.api_key,
            "engine": "google",
            "num": 10,
            "gl": "us",
            "hl": "en"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("organic_results", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    link=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="serpapi"
                )
            )
        
        return results
    
    async def _search_google_cse(self, query: str) -> List[SearchResult]:
        """Search Google using Custom Search API.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "key": self.api_key,
            "cx": self.cse_id,
            "num": 10
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("items", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    link=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source="google_cse"
                )
            )
        
        return results