import asyncio
from typing import List, Tuple, Dict, Any, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain.callbacks.base import BaseCallbackHandler
from langchain_community.llms import LlamaCpp
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from app.agent.tools.google_search import GoogleSearchTool
from app.agent.tools.web_scraper import WebScraperTool
from app.agent.tools.profile_identifier import ProfileIdentifierTool
from app.agent.prompts import (
    ICEBREAKER_AGENT_PROMPT,
    ICEBREAKER_GENERATION_PROMPT,
    PROFILE_ANALYSIS_PROMPT
)
from app.core.config import settings
from app.core.logging import logger
from app.models.schemas import ProfileSource

class AgentCallbackHandler(BaseCallbackHandler):
    """Callback handler for the agent."""
    
    def __init__(self):
        self.steps = []
        
    def on_agent_action(self, action, **kwargs):
        """Log agent actions."""
        self.steps.append({
            "type": "action",
            "action": action,
        })
        logger.debug(f"Agent action: {action.tool} with input: {action.tool_input}")
        
    def on_agent_finish(self, finish, **kwargs):
        """Log agent completion."""
        self.steps.append({
            "type": "finish",
            "finish": finish,
        })
        logger.debug(f"Agent finished with output: {finish.return_values}")
        
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Log when LLM starts."""
        logger.debug(f"LLM starting with prompts: {prompts[:1]}")
        
    def on_llm_error(self, error, **kwargs):
        """Log LLM errors."""
        logger.error(f"LLM error: {error}")
        
    def on_tool_start(self, serialized, input_str, **kwargs):
        """Log when tool starts."""
        logger.debug(f"Tool starting with input: {input_str[:100]}...")
        
    def on_tool_error(self, error, **kwargs):
        """Log tool errors."""
        logger.error(f"Tool error: {error}")
        
    def on_tool_finish(self, output, **kwargs):
        """Log when tool finishes."""
        if isinstance(output, str) and len(output) > 100:
            logger.debug(f"Tool finished with output: {output[:100]}...")
        else:
            logger.debug(f"Tool finished with output: {output}")
            
    def on_text(self, text, **kwargs):
        """Log text."""
        if len(text) > 100:
            logger.debug(f"Text: {text[:100]}...")
        else:
            logger.debug(f"Text: {text}")


def get_llm():
    """Get the appropriate LLM based on configuration."""
    llm_config = settings.get_llm_config()
    
    if llm_config["type"] in ["mistral", "llama", "gpt4all"]:
        # For local models
        if not llm_config["model_path"]:
            raise ValueError(f"Model path must be provided for {llm_config['type']}")
        
        logger.info(f"Loading local {llm_config['type']} model from {llm_config['model_path']}")
        return LlamaCpp(
            model_path=llm_config["model_path"],
            temperature=0.7,
            max_tokens=2000,
            top_p=0.95,
            n_ctx=4096,
            verbose=settings.DEBUG,
        )
    elif llm_config["api_url"] and llm_config["api_key"]:
        # For API-based models
        logger.info(f"Using API-based model at {llm_config['api_url']}")
        return ChatOpenAI(
            temperature=0.7,
            api_key=llm_config["api_key"],
            base_url=llm_config["api_url"],
            max_tokens=2000,
        )
    else:
        raise ValueError("Invalid LLM configuration")


def create_icebreaker_agent():
    """Create the ice breaker agent with all necessary tools."""
    # Get the LLM
    llm = get_llm()
    
    # Create the tools
    search_config = settings.get_search_config()
    
    google_search_tool = GoogleSearchTool(
        api_type=search_config["type"],
        api_key=search_config["api_key"],
        cse_id=search_config.get("cse_id")
    )
    
    web_scraper_tool = WebScraperTool(
        user_agent=settings.USER_AGENT,
        timeout=settings.REQUEST_TIMEOUT
    )
    
    profile_identifier_tool = ProfileIdentifierTool(
        llm=llm
    )
    
    tools = [
        Tool(
            name="GoogleSearch",
            func=google_search_tool.search,
            description="Search Google for information about a person. Input should be a search query string."
        ),
        Tool(
            name="WebScraper",
            func=web_scraper_tool.scrape,
            description="Scrape content from a web page. Input should be a URL string."
        ),
        Tool(
            name="ProfileIdentifier",
            func=profile_identifier_tool.identify_profiles,
            description="Identify if a search result is a relevant social media profile. Input should be a list of search results."
        ),
        Tool(
            name="ProfileAnalyzer",
            func=profile_identifier_tool.analyze_profile,
            description="Analyze a profile page to extract structured information. Input should be the raw HTML or text content of a profile page."
        )
    ]
    
    # Create the agent
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=PromptTemplate.from_template(ICEBREAKER_AGENT_PROMPT)
    )
    
    # Create the agent executor
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        verbose=settings.DEBUG,
        max_iterations=settings.MAX_ITERATIONS,
        max_execution_time=settings.MAX_EXECUTION_TIME,
        handle_parsing_errors=True
    )
    
    return agent_executor


async def generate_icebreakers(agent, name: str) -> Tuple[List[str], List[ProfileSource]]:
    """Generate ice breakers using the agent.
    
    Args:
        agent: The agent executor
        name: The name of the person to generate ice breakers for
        
    Returns:
        Tuple of (ice_breakers, sources)
    """
    logger.info(f"Generating ice breakers for: {name}")
    
    # Create callback handler for logging
    callbacks = [AgentCallbackHandler()]
    
    # Run the agent
    result = await agent.ainvoke(
        {
            "input": f"Generate personalized ice breakers for {name}",
            "name": name
        },
        callbacks=callbacks
    )
    
    # Extract information from the result
    raw_info = result.get("output", "")
    profile_data = result.get("profile_data", [])
    sources = result.get("sources", [])
    
    # Convert profile data to ProfileSource objects
    profile_sources = []
    for source in sources:
        try:
            profile_sources.append(
                ProfileSource(
                    url=source["url"],
                    platform=source["platform"],
                    title=source.get("title"),
                    relevance_score=float(source.get("relevance_score", 0.8))
                )
            )
        except Exception as e:
            logger.warning(f"Error converting source to ProfileSource: {e}")
    
    # Generate ice breakers based on the profile data
    ice_breakers = []
    if profile_data:
        try:
            # Create ice breaker generation prompt
            template = PromptTemplate.from_template(ICEBREAKER_GENERATION_PROMPT)
            chain = LLMChain(llm=get_llm(), prompt=template)
            
            # Run the chain to generate ice breakers
            response = await chain.ainvoke(
                {
                    "name": name,
                    "profile_data": profile_data
                }
            )
            
            # Parse the ice breakers from the response
            raw_breakers = response.get("text", "")
            for line in raw_breakers.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and not line.lower().startswith("ice breaker"):
                    # Remove numbers or dashes at the beginning
                    clean_line = re.sub(r"^[\d\-\.\*]+[\s\.]+", "", line).strip()
                    if clean_line:
                        ice_breakers.append(clean_line)
        except Exception as e:
            logger.error(f"Error generating ice breakers: {e}", exc_info=True)
    
    # Ensure we have at least some ice breakers
    if not ice_breakers:
        logger.warning(f"No ice breakers generated for {name}, using fallbacks")
        ice_breakers = [
            f"I'd love to hear more about your professional background. What kind of work do you do, {name}?",
            f"What are you passionate about in your field, {name}?",
            f"What's the most interesting project you've worked on recently, {name}?"
        ]
    
    # Limit to 5 ice breakers
    ice_breakers = ice_breakers[:5]
    
    logger.info(f"Generated {len(ice_breakers)} ice breakers for {name}")
    return ice_breakers, profile_sources