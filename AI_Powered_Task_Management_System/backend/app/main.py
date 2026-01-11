"""
Main FastAPI application entry point.

Configures and initializes the FastAPI application with all necessary
middleware, exception handlers, and route inclusions.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup: Initialize database
    print("Initializing database...")
    init_db()
    print("Database initialized successfully")

    yield

    # Shutdown: Cleanup operations
    print("Application shutdown")


# Create FastAPI application instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered task management system with intelligent assistance",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": "INVALID_VALUE",
                "message": str(exc),
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    if settings.DEBUG:
        # In debug mode, include detailed error information
        import traceback
        error_detail = {
            "code": "INTERNAL_ERROR",
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    else:
        # In production, hide detailed error information
        error_detail = {
            "code": "INTERNAL_ERROR",
            "message": "An internal error occurred. Please try again later.",
        }

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": error_detail
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns application status and version information.
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "api": settings.API_V1_PREFIX,
    }


# Include API routers
from app.api.v1.api import api_router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
