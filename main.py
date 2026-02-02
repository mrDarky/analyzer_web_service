from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional
import os

from database import init_db, get_session
from models import User, Project, Service, UserStory
from schemas import (
    UserCreate, UserLogin, UserResponse, Token,
    ProjectCreate, ProjectResponse,
    ServiceCreate, ServiceResponse,
    UserStoryCreate, UserStoryResponse,
    AnalysisResult
)
from auth import verify_password, get_password_hash, create_access_token, decode_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from analyzer import WebsiteAnalyzer
from datetime import timedelta

app = FastAPI(title="Website Analyzer Service")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Security
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()

# Authentication Endpoints
@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    """Register a new user"""
    # Check if user exists
    result = await session.execute(
        select(User).where(
            or_(User.username == user_data.username, User.email == user_data.email)
        )
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return new_user

@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin, session: AsyncSession = Depends(get_session)):
    """Login and get access token"""
    result = await session.execute(
        select(User).where(User.username == user_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user

# Project Endpoints
@app.post("/api/projects", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Create a new project"""
    new_project = Project(
        name=project_data.name,
        url=project_data.url,
        description=project_data.description,
        owner_id=current_user.id
    )
    
    session.add(new_project)
    await session.commit()
    await session.refresh(new_project)
    
    return new_project

@app.get("/api/projects", response_model=List[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """List all projects for current user"""
    result = await session.execute(
        select(Project).where(Project.owner_id == current_user.id)
    )
    projects = result.scalars().all()
    return projects

@app.get("/api/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get a specific project"""
    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project

@app.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete a project"""
    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await session.delete(project)
    await session.commit()
    
    return {"message": "Project deleted successfully"}

@app.post("/api/projects/{project_id}/analyze", response_model=AnalysisResult)
async def analyze_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Analyze a project's website"""
    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Analyze website
    analyzer = WebsiteAnalyzer(project.url, max_pages=20)
    pages = await analyzer.crawl()
    
    # Save services
    services = []
    for page_data in pages:
        service = Service(
            project_id=project.id,
            page_url=page_data['url'],
            title=page_data['title'],
            functionality=page_data['functionality'],
            elements=page_data['elements']
        )
        session.add(service)
        services.append(service)
    
    # Generate and save user stories
    story_data = analyzer.generate_user_stories(pages)
    user_stories = []
    for story in story_data:
        user_story = UserStory(
            project_id=project.id,
            title=story['title'],
            description=story['description'],
            gherkin=story['gherkin']
        )
        session.add(user_story)
        user_stories.append(user_story)
    
    # Mark project as analyzed
    project.analyzed = True
    
    await session.commit()
    
    # Refresh to get IDs
    for service in services:
        await session.refresh(service)
    for user_story in user_stories:
        await session.refresh(user_story)
    
    return {
        "pages_found": len(pages),
        "services": services,
        "user_stories": user_stories
    }

# Service Endpoints
@app.get("/api/projects/{project_id}/services", response_model=List[ServiceResponse])
async def list_services(
    project_id: int,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """List all services for a project with optional search"""
    # Verify project ownership
    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Query services
    query = select(Service).where(Service.project_id == project_id)
    
    if search:
        query = query.where(
            or_(
                Service.title.ilike(f"%{search}%"),
                Service.page_url.ilike(f"%{search}%"),
                Service.functionality.ilike(f"%{search}%")
            )
        )
    
    result = await session.execute(query)
    services = result.scalars().all()
    
    return services

@app.post("/api/projects/{project_id}/services", response_model=ServiceResponse)
async def create_service(
    project_id: int,
    service_data: ServiceCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Add a service manually to a project"""
    # Verify project ownership
    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    new_service = Service(
        project_id=project_id,
        page_url=service_data.page_url,
        title=service_data.title,
        functionality=service_data.functionality,
        elements=service_data.elements
    )
    
    session.add(new_service)
    await session.commit()
    await session.refresh(new_service)
    
    return new_service

@app.delete("/api/projects/{project_id}/services/{service_id}")
async def delete_service(
    project_id: int,
    service_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete a service"""
    # Verify project ownership
    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get and delete service
    result = await session.execute(
        select(Service).where(Service.id == service_id, Service.project_id == project_id)
    )
    service = result.scalar_one_or_none()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    await session.delete(service)
    await session.commit()
    
    return {"message": "Service deleted successfully"}

# User Story Endpoints
@app.get("/api/projects/{project_id}/stories", response_model=List[UserStoryResponse])
async def list_user_stories(
    project_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """List all user stories for a project"""
    # Verify project ownership
    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = await session.execute(
        select(UserStory).where(UserStory.project_id == project_id)
    )
    stories = result.scalars().all()
    
    return stories

@app.post("/api/projects/{project_id}/stories", response_model=UserStoryResponse)
async def create_user_story(
    project_id: int,
    story_data: UserStoryCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Add a user story manually to a project"""
    # Verify project ownership
    result = await session.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    new_story = UserStory(
        project_id=project_id,
        title=story_data.title,
        description=story_data.description,
        gherkin=story_data.gherkin
    )
    
    session.add(new_story)
    await session.commit()
    await session.refresh(new_story)
    
    return new_story

# HTML Pages
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Register page"""
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/project/{project_id}", response_class=HTMLResponse)
async def project_page(request: Request, project_id: int):
    """Project detail page"""
    return templates.TemplateResponse("project.html", {"request": request, "project_id": project_id})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
