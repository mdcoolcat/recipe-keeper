from pydantic import BaseModel, HttpUrl
from typing import List, Optional


class ExtractRecipeRequest(BaseModel):
    """Request model for recipe extraction endpoint"""
    url: str


class Recipe(BaseModel):
    """Recipe data model"""
    title: str
    ingredients: List[str]
    steps: List[str]
    source_url: str
    platform: str
    language: str = "en"
    thumbnail_url: Optional[str] = None


class ExtractRecipeResponse(BaseModel):
    """Response model for recipe extraction endpoint"""
    success: bool
    platform: Optional[str] = None
    recipe: Optional[Recipe] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str = "1.0.0"
