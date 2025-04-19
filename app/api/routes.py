from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from app.models.schemas import IceBreakerRequest, IceBreakerResponse, ErrorResponse
from app.agent.icebreaker_agent import create_icebreaker_agent, generate_icebreakers
from app.core.logging import logger
import asyncio
import time
from typing import Dict, Any

router = APIRouter()

# In-memory cache for results
results_cache: Dict[str, Any] = {}

@router.post(
    "/icebreakers",
    response_model=IceBreakerResponse,
    responses={
        200: {"model": IceBreakerResponse, "description": "Ice breakers generated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"},
        504: {"model": ErrorResponse, "description": "Request timeout"},
    },
    summary="Generate personalized ice breakers",
    description="Generate personalized conversation starters based on information found online about a person.",
)
async def create_icebreakers(request: IceBreakerRequest):
    """
    Generate personalized ice breakers based on a person's name.
    
    The API will:
    1. Search for the person online
    2. Identify relevant profiles (LinkedIn, Twitter, etc.)
    3. Extract information from these profiles
    4. Generate personalized ice breakers
    
    Returns a list of ice breakers and the sources of information used.
    """
    try:
        logger.info(f"Received ice breaker request for: {request.name}")
        
        # Create the agent
        agent = create_icebreaker_agent()
        
        # Execute the agent and get results
        start_time = time.time()
        ice_breakers, sources = await generate_icebreakers(agent, request.name)
        execution_time = time.time() - start_time
        
        logger.info(f"Generated {len(ice_breakers)} ice breakers in {execution_time:.2f} seconds")
        
        # Create the response
        response = IceBreakerResponse(
            ice_breakers=ice_breakers,
            sources=sources,
            execution_time=execution_time
        )
        
        return response
    
    except asyncio.TimeoutError:
        logger.error(f"Request timed out for: {request.name}")
        raise HTTPException(
            status_code=504,
            detail="The request took too long to process. Please try again later."
        )
    
    except Exception as e:
        logger.error(f"Error generating ice breakers for {request.name}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while generating ice breakers: {str(e)}"
        )


@router.post(
    "/icebreakers/async",
    response_model=dict,
    summary="Generate personalized ice breakers asynchronously",
    description="Start the ice breaker generation process in the background and return a task ID.",
)
async def create_icebreakers_async(
    request: IceBreakerRequest, background_tasks: BackgroundTasks
):
    """
    Start the ice breaker generation process asynchronously.
    
    Returns a task ID that can be used to check the status of the request.
    """
    try:
        logger.info(f"Received async ice breaker request for: {request.name}")
        
        # Generate a task ID
        task_id = f"task_{int(time.time())}_{hash(request.name) % 10000}"
        
        # Store initial state in cache
        results_cache[task_id] = {
            "status": "processing",
            "name": request.name,
            "created_at": time.time(),
            "result": None
        }
        
        # Create the background task
        background_tasks.add_task(
            _background_icebreaker_task,
            task_id,
            request.name
        )
        
        return {"task_id": task_id, "status": "processing"}
    
    except Exception as e:
        logger.error(f"Error starting async task for {request.name}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred: {str(e)}"
        )


@router.get(
    "/icebreakers/status/{task_id}",
    response_model=dict,
    summary="Check the status of an asynchronous ice breaker request",
    description="Get the current status or results of an asynchronous ice breaker generation task.",
)
async def check_icebreakers_status(task_id: str):
    """
    Check the status of an asynchronous ice breaker generation task.
    
    Returns the current status or the results if the task is complete.
    """
    if task_id not in results_cache:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    
    task_data = results_cache[task_id]
    
    # Clean up old completed tasks
    if task_data["status"] == "completed" and (time.time() - task_data["completed_at"]) > 3600:
        # Remove tasks completed more than an hour ago
        results_cache.pop(task_id, None)
        raise HTTPException(
            status_code=404,
            detail="Task results expired"
        )
    
    return task_data


async def _background_icebreaker_task(task_id: str, name: str):
    """Background task for generating ice breakers asynchronously."""
    try:
        # Create the agent
        agent = create_icebreaker_agent()
        
        # Execute the agent and get results
        ice_breakers, sources = await generate_icebreakers(agent, name)
        
        # Update the cache with results
        results_cache[task_id] = {
            "status": "completed",
            "name": name,
            "created_at": results_cache[task_id]["created_at"],
            "completed_at": time.time(),
            "result": {
                "ice_breakers": ice_breakers,
                "sources": sources,
                "execution_time": time.time() - results_cache[task_id]["created_at"]
            }
        }
        
        logger.info(f"Background task {task_id} completed successfully")
        
    except Exception as e:
        # Update the cache with error
        results_cache[task_id] = {
            "status": "error",
            "name": name,
            "created_at": results_cache[task_id]["created_at"],
            "completed_at": time.time(),
            "error": str(e)
        }
        
        logger.error(f"Background task {task_id} failed: {str(e)}", exc_info=True)


@router.get(
    "/health",
    summary="Health check endpoint",
    description="Check if the API is up and running.",
)
async def health_check():
    """Simple health check endpoint to verify the API is running."""
    return {"status": "healthy", "service": "Ice Breaker Generator"}