import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.logging import setup_logging, logger

def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Ice Breaker Generator",
        description="A microservice that generates personalized ice breakers based on information found online.",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup logging
    setup_logging()

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Global exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred."},
        )

    # Add custom OpenAPI documentation
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="Ice Breaker Generator API",
            oauth2_redirect_url=None,
        )

    @app.get("/openapi.json", include_in_schema=False)
    async def get_open_api_endpoint():
        return get_openapi(
            title="Ice Breaker Generator API",
            version="0.1.0",
            description="A microservice that generates personalized ice breakers based on information found online.",
            routes=app.routes,
        )

    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": "Welcome to the Ice Breaker Generator API. Visit /docs for documentation."}

    return app

app = create_application()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )