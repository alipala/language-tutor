"""
Routes package for Language Tutor Backend
Modular route organization for better maintainability
"""

from .health_routes import router as health_router
from .mock_routes import router as mock_router

__all__ = [
    "health_router",
    "mock_router",
]
