from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
import re

class IceBreakerRequest(BaseModel):
    """Request model for the ice breaker generator."""
    name: str = Field(..., description="The name of the person to generate ice breakers for")
    
    @validator("name")
    def validate_name(cls, v):
        """Validate that the name contains only valid characters and is not too long."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        
        if len(v) > 100:
            raise ValueError("Name is too long (max 100 characters)")
        
        # Basic validation to prevent injection attacks
        if re.search(r'[<>{}()\[\]\\/]', v):
            raise ValueError("Name contains invalid characters")
        
        return v.strip()

class ProfileSource(BaseModel):
    """Model for a source of information about a person."""
    url: str = Field(..., description="URL of the profile")
    platform: str = Field(..., description="Platform name (e.g., LinkedIn, Twitter)")
    title: Optional[str] = Field(None, description="Title of the profile page")
    relevance_score: float = Field(..., description="Relevance score (0.0 to 1.0)")
    
    @validator("relevance_score")
    def validate_score(cls, v):
        """Validate that the relevance score is between 0 and 1."""
        if v < 0.0 or v > 1.0:
            raise ValueError("Relevance score must be between 0.0 and 1.0")
        return v

class IceBreakerResponse(BaseModel):
    """Response model for the ice breaker generator."""
    ice_breakers: List[str] = Field(
        ..., 
        description="List of personalized ice breakers",
        example=[
            "I noticed you worked at Google. What was your most interesting project there?",
            "I saw your article on AI ethics. What inspired you to write about that topic?",
            "Your Twitter thread on renewable energy was fascinating. Have you always been interested in sustainability?"
        ]
    )
    sources: List[ProfileSource] = Field(
        ..., 
        description="Sources of information used to generate the ice breakers"
    )
    execution_time: float = Field(
        ..., 
        description="Time taken to generate the ice breakers in seconds"
    )

class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str = Field(..., description="Error message")

class AgentAction(BaseModel):
    """Model for an agent action."""
    tool: str = Field(..., description="Name of the tool to use")
    tool_input: Dict[str, Any] = Field(..., description="Input for the tool")
    log: Optional[str] = Field(None, description="Log message for the action")

class AgentObservation(BaseModel):
    """Model for an observation after an agent action."""
    output: Any = Field(..., description="Output from the tool")
    log: Optional[str] = Field(None, description="Log message for the observation")

class AgentStep(BaseModel):
    """Model for a step in the agent's reasoning process."""
    action: AgentAction
    observation: AgentObservation

class AgentFinish(BaseModel):
    """Model for the agent's final response."""
    return_values: Dict[str, Any] = Field(..., description="Values returned by the agent")
    log: Optional[str] = Field(None, description="Log message for the finish")

class SearchResult(BaseModel):
    """Model for a search result."""
    title: str = Field(..., description="Title of the search result")
    link: str = Field(..., description="URL of the search result")
    snippet: Optional[str] = Field(None, description="Snippet of text from the search result")
    source: str = Field("google", description="Source of the search result")

class ProfileInfo(BaseModel):
    """Model for information extracted from a profile."""
    url: str = Field(..., description="URL of the profile")
    platform: str = Field(..., description="Platform name (e.g., LinkedIn, Twitter)")
    name: Optional[str] = Field(None, description="Name found on the profile")
    title: Optional[str] = Field(None, description="Professional title or headline")
    bio: Optional[str] = Field(None, description="Biography or about section")
    experience: Optional[List[Dict[str, Any]]] = Field(None, description="Work experience")
    education: Optional[List[Dict[str, Any]]] = Field(None, description="Education history")
    skills: Optional[List[str]] = Field(None, description="Professional skills")
    interests: Optional[List[str]] = Field(None, description="Interests or hobbies")
    posts: Optional[List[Dict[str, Any]]] = Field(None, description="Recent posts or activities")
    raw_text: Optional[str] = Field(None, description="Raw text extracted from the profile")