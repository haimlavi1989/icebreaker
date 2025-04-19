# Ice Breaker Generator

A backend microservice that uses LangChain and LLMs to generate personalized ice breakers based on information found online about a person.

## Project Structure

```
icebreaker/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py          # API routes
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── icebreaker_agent.py    # LangChain agent implementation
│   │   ├── prompts.py         # Prompt templates
│   │   └── tools/
│   │       ├── __init__.py
│   │       ├── google_search.py   # Google search tool
│   │       ├── web_scraper.py     # Web scraping tool
│   │       └── profile_identifier.py  # Profile identification tool
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Pydantic models
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration
│   │   └── logging.py         # Logging setup
│   └── utils/
│       ├── __init__.py
│       └── helpers.py         # Helper functions
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_agent.py
│   └── test_tools.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Technology Stack

- **Python 3.10+**: Core programming language
- **FastAPI**: Web framework for building APIs
- **LangChain**: Framework for building LLM applications
- **Open Source LLMs**: Mistral, LLaMA, GPT4All for inference
- **BeautifulSoup4**: HTML parsing and web scraping
- **Pydantic**: Data validation and settings management
- **Docker**: Containerization for easy deployment
- **Pytest**: Testing framework
- **SERP API/Google CSE**: For web search functionality
- **Loguru**: Enhanced logging capabilities

## Features

- **Personalized Ice Breaker Generation**: Generate relevant conversation starters based on a person's online presence
- **Intelligent Web Search**: Automatically search for relevant profiles online
- **Profile Identification**: Detect and prioritize relevant social profiles like LinkedIn and Twitter
- **Web Scraping**: Extract relevant information from supported platforms
- **Profile Analysis**: Intelligent information extraction from different profile types
- **Asynchronous Processing**: Support for both synchronous and asynchronous processing
- **Task Status Tracking**: Monitor the progress of asynchronous requests
- **Comprehensive Logging**: Detailed logs for debugging and monitoring
- **Multiple LLM Support**: Flexibility to use different open-source language models
- **Health Monitoring**: Endpoint for system health checks

## Installation & Setup

### Prerequisites

- Docker and Docker Compose
- Google Search API key (SerpAPI or Google Custom Search)
- LLM model files (for local inference) or API access
- Python 3.10 or higher (for local development)

### Docker Setup (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/icebreaker.git
   cd icebreaker
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. Download model files (if using local inference):
   ```bash
   mkdir -p models
   # Download your preferred model to the models directory
   # Example:
   # wget -O models/mistral-7b-instruct-v0.1.Q4_K_M.gguf https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf
   ```

4. Build and run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

5. Access the API documentation:
   ```
   http://localhost:8000/docs
   ```

### Local Development Setup

If you prefer to run the service directly on your machine:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/icebreaker.git
   cd icebreaker
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. Download model files (if using local inference):
   ```bash
   mkdir -p models
   # Download your preferred model to the models directory
   ```

5. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

6. Access the API documentation:
   ```
   http://localhost:8000/docs
   ```

## API Usage

### Generate Ice Breakers (Synchronous)

```
POST /api/v1/icebreakers
```

**Request**:
```json
{
  "name": "John Doe"
}
```

**Response**:
```json
{
  "ice_breakers": [
    "I noticed you worked at Google. What was your most interesting project there?",
    "I saw your article on AI ethics. What inspired you to write about that topic?",
    "Your Twitter thread on renewable energy was fascinating. Have you always been interested in sustainability?"
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
  ],
  "execution_time": 12.34
}
```

### Generate Ice Breakers (Asynchronous)

```
POST /api/v1/icebreakers/async
```

**Request**:
```json
{
  "name": "John Doe"
}
```

**Response**:
```json
{
  "task_id": "task_1619855468_1234",
  "status": "processing"
}
```

### Check Task Status

```
GET /api/v1/icebreakers/status/{task_id}
```

**Response** (processing):
```json
{
  "status": "processing",
  "name": "John Doe",
  "created_at": 1619855468.123
}
```

**Response** (completed):
```json
{
  "status": "completed",
  "name": "John Doe",
  "created_at": 1619855468.123,
  "completed_at": 1619855483.456,
  "result": {
    "ice_breakers": [...],
    "sources": [...],
    "execution_time": 15.333
  }
}
```

## Check Health

```
GET /api/v1/health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "Ice Breaker Generator"
}
```

## API Documentation

The API is documented using OpenAPI/Swagger. After starting the service, you can access the interactive API documentation at:

```
http://localhost:8000/docs
```

This documentation provides:

- Detailed description of all endpoints
- Request and response schemas
- Interactive testing capability
- Examples of valid requests

## Testing

Run the tests using pytest:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app tests/

# Run specific test modules
pytest tests/test_api.py
pytest tests/test_tools.py
```

The test suite includes:

- Unit tests for API endpoints
- Mocked tests for external services (Google Search, web scraping)
- Function tests for the agent and tools
- Basic integration tests

## Performance Considerations

- **Execution Time**: The synchronous API has a default timeout of 60 seconds
- **Rate Limiting**: The Google Search tool implements rate limiting to avoid API blocks
- **Caching**: Consider implementing a caching layer for frequently searched profiles
- **Resource Usage**: LLM inference can be resource-intensive; ensure sufficient memory
- **Scaling**: For high-load scenarios, consider deploying multiple instances behind a load balancer
- **Asynchronous Processing**: Use the async API for better user experience with long-running requests

## Future Improvements

- Add support for more social media platforms
- Implement memory with vector storage for caching results
- Add sentiment analysis for better conversation starters
- Implement rate limiting and throttling for API calls
- Support for multi-language ice breakers
- Add more comprehensive error handling and recovery mechanisms
- Implement user feedback mechanism to improve ice breaker quality
- Add authentication and rate limiting for the API
- Create a simple frontend for demonstration purposes
- Support for batch processing of multiple names
