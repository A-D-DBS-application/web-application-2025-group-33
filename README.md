# Paper Collaboration Platform

## Overview

A Flask web application for managing academic paper collaborations between authors and companies. Authors can upload papers, collaborate with other authors, and publish their work. Companies can browse published papers, discover relevant research through recommendations, mark their interests, review papers, and download PDFs.

## User Stories

Voor een overzicht van alle user stories, zie [USER_STORIES.md](USER_STORIES.md).

## Features

### User Management
- **Author Registration**
 
- **Company Registration**
 

### Paper Management
- **Create & Upload**
 

- **Update & Edit**
 

- **Publishing**
 
- **Deletion**


### Collaboration System
- **Collaborator Management**

  
### Company Features
- **Browse & Search**
  
- **Interests**
 
- **Recommendations**
 
- **Business Relevance Scoring**

- **Paper Downloads**
  
- **Research Interests**
  
### Review System
- **Paper Reviews**
 

### Privacy & Access Control
- **Author Access**
  - Authors can only see papers they collaborate on
  - Can see which companies are interested in their published papers
  - Can see download counts for their papers

- **Company Access**
  - Companies can only see published papers
  - Can see authors, subjects, and metadata of published papers
  - Cannot see draft papers or unpublished content

## Technology Stack

- **Backend:** Flask 3.1.2 (Python web framework)
- **Database:** PostgreSQL (via Supabase or any PostgreSQL server)
- **ORM:** SQLAlchemy 2.0.44 with Flask-SQLAlchemy 3.1.1
- **Migrations:** Flask-Migrate 4.1.0
- **File Storage:** Supabase Storage (cloud file storage)
- **Authentication:** Flask sessions with Werkzeug password hashing
- **HTTP Client:** httpx 0.28.1 (for Supabase API calls)
- **Environment:** python-dotenv 1.2.1

## Project Structure

```
web-application-2025-group-33/
├── app/
│   ├── app.py              # Main Flask application
│   ├── config.py           # Configuration settings (env loading, Supabase config)
│   ├── models.py           # SQLAlchemy models (User, Company, Paper, etc.)
│   ├── extensions.py       # Flask extensions (db, migrate)
│   ├── storage.py          # Supabase Storage interface
│   ├── requirements.txt    # Python dependencies (9 packages)
│   ├── schema.sql          # Database schema (if using raw SQL)
│   ├── .env.development    # Development environment variables
│   ├── .env.example        # Template for environment variables
│   │
│   ├── routes/             # Application routes (blueprints)
│   │   ├── auth.py         # Authentication (login, register, logout)
│   │   ├── papers.py       # Paper management (CRUD, reviews, recommendations)
│   │   ├── collaborators.py # Collaborator management
│   │   └── interests.py    # Company interests
│   │
│   ├── templates/          # HTML templates (Jinja2)
│   │   ├── auth/           # Login, registration pages
│   │   ├── papers/         # Paper views, dashboards, recommendations
│   │   ├── interests/      # Interest management
│   │   ├── base.html       # Base template
│   │   └── home.html       # Home page
│   │
│   └── static/             # Static files
│       ├── css/            # Stylesheets
│       └── js/             # JavaScript files
│
├── requirements.txt        # Root-level requirements (if different)
└── run.py                 # Application entry point (if exists)
```

## Database Schema

### Tables

**users** 

**companies** 

**papers** 

**paper_collaborators** 

**paper_interests**

**reviews** 

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- PostgreSQL database (Supabase recommended)

### 1. Install Dependencies
```bash
cd app
pip install -r requirements.txt
```

**Dependencies:**
- Flask 3.1.2
- Flask-SQLAlchemy 3.1.1
- Flask-Migrate 4.1.0
- SQLAlchemy 2.0.44
- psycopg2-binary 2.9.11
- supabase 2.24.0
- httpx 0.28.1
- Werkzeug 3.1.3
- python-dotenv 1.2.1

### 2. Set up PostgreSQL Database

Create a `.env` or `.env.development` file:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@host:port/database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

**For Supabase:**
- Go to Project Settings → Database
- Find "Connection String" → "URI"
- Copy and paste into `DATABASE_URL`
- Go to Project Settings → API
- Copy "Project URL" into `SUPABASE_URL`
- Copy "anon public" key into `SUPABASE_KEY`
- Copy "service_role" key into `SUPABASE_SERVICE_KEY` (needed for storage operations)

**Note:** The application supports multiple environment files:
- `.env` (default)
- `.env.development` (used if `.env` doesn't exist)
- Use `--env <name>` flag to specify: `python app.py --env development`

### 3. Create Database Schema

**Option A: Using Flask-Migrate (Recommended)**
```bash
# Initialize migrations (first time only)
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

**Option B: Using SQL Schema File**
Run the schema file in your PostgreSQL database:
```bash
psql -d your_database -f schema.sql
```

Or using Supabase SQL Editor:
- Copy contents of `schema.sql`
- Paste into SQL Editor
- Run

### 4. Create Storage Bucket (Supabase only)

If using Supabase, create a storage bucket for PDF files:
- Go to Storage in Supabase dashboard
- Click "New bucket"
- Name: `papers`
- Public: ✅ Check this
- Click "Create bucket"

See `STORAGE_SETUP.md` for detailed instructions.

### 5. Run the Application

```bash
cd app
python app.py
```

Or with specific environment:
```bash
python app.py --env development
```

Visit `http://localhost:5000`

The application will:
- Show which environment file is being used
- Display the database host being connected to
- Run in debug mode by default (unless FLASK_DEBUG is set)


### Database Setup
- **Development**: Each developer has own Supabase project
- **Demo/Production**: Shared Supabase project for demonstrations

### Running Locally
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

## Troubleshooting

### Module not found errors
```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Database connection errors
- Check your DATABASE_URL in `.env`
- Make sure password is correct
- Verify Supabase project is running

### "relation does not exist" errors
- Run `schema.sql` in your database
- Make sure you're connected to the correct database

### File upload/download errors
- Check SUPABASE_URL and SUPABASE_SERVICE_KEY in `.env`
- Verify storage bucket named "papers" exists
- Ensure bucket is public or has correct policies
- Service key is required for storage operations (bypasses RLS)

### Migration errors
- If using Flask-Migrate, ensure database is initialized: `flask db init`
- Check that DATABASE_URL is correct
- Verify SQLAlchemy models match database schema

## License

This project is for educational purposes.

