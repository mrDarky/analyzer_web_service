from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

# User Schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Project Schemas
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    url: str
    description: Optional[str]
    owner_id: int
    created_at: datetime
    analyzed: bool
    
    class Config:
        from_attributes = True

# Service Schemas
class ServiceCreate(BaseModel):
    page_url: str = Field(..., max_length=500)
    title: Optional[str] = None
    functionality: Optional[str] = None
    elements: Optional[str] = None

class ServiceResponse(BaseModel):
    id: int
    project_id: int
    page_url: str
    title: Optional[str]
    functionality: Optional[str]
    elements: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# User Story Schemas
class UserStoryCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: str
    gherkin: Optional[str] = None

class UserStoryResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: str
    gherkin: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Analysis Result Schema
class AnalysisResult(BaseModel):
    pages_found: int
    services: List[ServiceResponse]
    user_stories: List[UserStoryResponse]
