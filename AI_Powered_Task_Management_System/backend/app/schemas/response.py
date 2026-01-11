"""
Standard API response schemas.

Provides consistent response formatting across all API endpoints.
"""

from typing import Generic, TypeVar, Optional
from pydantic import BaseModel


DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    """
    Standard API response wrapper.

    Provides consistent response structure with success flag,
    data payload, and optional metadata.
    """
    success: bool = True
    data: Optional[DataT] = None
    message: Optional[str] = None
    meta: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": 1, "title": "Example Task"},
                "message": "Task created successfully",
                "meta": {"timestamp": "2024-01-11T10:00:00Z"}
            }
        }


class ErrorResponse(BaseModel):
    """
    Standard error response schema.

    Provides consistent error formatting with error code,
    message, and optional details.
    """
    success: bool = False
    error: dict

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Task title is required",
                    "details": {"field": "title"}
                }
            }
        }
