# Website Analyzer Service

A comprehensive web service for analyzing websites built with FastAPI, Python, Bootstrap, and SQLite with async support.

## Features

- **User Authentication**: Register and login with JWT token-based authentication
- **Project Management**: Create and manage website analysis projects
- **Website Crawling**: Automatically crawl websites to discover all pages
- **Site Mapping**: Generate comprehensive site maps with all discovered pages
- **Functionality Analysis**: Analyze page elements (forms, buttons, tables, images, links)
- **User Story Generation**: Automatically generate user stories based on website features
- **Gherkin Scenarios**: Generate Gherkin format test scenarios for each user story
- **Services Management**: Full CRUD operations on analyzed services/pages
- **Search Functionality**: Search through discovered services
- **Responsive UI**: Bootstrap-based responsive interface

## Technologies

- **Backend**: Python 3.12, FastAPI, SQLAlchemy (async)
- **Database**: SQLite with aiosqlite
- **Authentication**: JWT tokens with password hashing (bcrypt)
- **Web Crawling**: aiohttp, BeautifulSoup4
- **Frontend**: Bootstrap 5, vanilla JavaScript
- **Templates**: Jinja2

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mrDarky/analyzer_web_service.git
cd analyzer_web_service
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

The server will start on `http://localhost:8000`

## Usage

### 1. Register an Account
- Navigate to `/register`
- Enter username, email, and password (minimum 6 characters)
- Click "Register"

### 2. Login
- Navigate to `/login`
- Enter your credentials
- You'll be redirected to the dashboard

### 3. Create a Project
- Click "+ Add New Project" on the dashboard
- Enter project name and website URL
- Optionally add a description
- Click "Add Project"

### 4. Analyze Website
- Click "Analyze" button on your project card
- The system will crawl the website and:
  - Discover all pages on the same domain
  - Analyze page elements (forms, buttons, tables, etc.)
  - Extract page titles and URLs
  - Generate user stories based on functionality
  - Create Gherkin test scenarios

### 5. View Results
- Click "View" on a project to see:
  - **Services Tab**: Table of all discovered pages with search functionality
  - **User Stories Tab**: Generated user stories with Gherkin scenarios

### 6. Manage Services
- Add services manually using "+ Add Service"
- Search services using the search box
- View service details by clicking "View"
- Delete services with the "Delete" button

### 7. Manage User Stories
- View auto-generated stories with Gherkin scenarios
- Add custom stories using "+ Add User Story"

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info

### Projects
- `GET /api/projects` - List user's projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details
- `DELETE /api/projects/{id}` - Delete project
- `POST /api/projects/{id}/analyze` - Analyze project website

### Services
- `GET /api/projects/{id}/services` - List project services (with optional search)
- `POST /api/projects/{id}/services` - Add service manually
- `DELETE /api/projects/{id}/services/{service_id}` - Delete service

### User Stories
- `GET /api/projects/{id}/stories` - List project user stories
- `POST /api/projects/{id}/stories` - Add user story manually

## Project Structure

```
analyzer_web_service/
├── main.py              # FastAPI application and routes
├── database.py          # Database configuration
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── auth.py              # Authentication utilities
├── analyzer.py          # Website analyzer logic
├── requirements.txt     # Python dependencies
├── templates/           # HTML templates
│   ├── index.html      # Home page
│   ├── login.html      # Login page
│   ├── register.html   # Registration page
│   ├── dashboard.html  # User dashboard
│   └── project.html    # Project details page
└── README.md           # This file
```

## Configuration

You can configure the application using environment variables:

- `DATABASE_URL` - Database connection string (default: `sqlite+aiosqlite:///./analyzer.db`)
- `SECRET_KEY` - JWT secret key (change in production!)

## Development

The application uses:
- Async/await throughout for better performance
- JWT tokens for stateless authentication
- Password hashing with bcrypt
- SQLAlchemy ORM with async support
- Responsive Bootstrap UI

## Security Notes

- Change the `SECRET_KEY` in production
- Use HTTPS in production
- Passwords are hashed with bcrypt
- JWT tokens expire after 30 minutes
- CORS should be configured for production use

## License

MIT