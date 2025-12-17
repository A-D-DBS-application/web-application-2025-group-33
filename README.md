# Paper Collaboration Platform

## Overview

A Flask web application for managing academic paper collaborations between authors and companies. Authors can upload papers, collaborate with other authors, and publish their work. Companies can browse published papers, discover relevant research through AI-powered recommendations, mark their interests, review papers, and download PDFs.

## User Stories

Voor een overzicht van alle user stories, zie [USER_STORIES.md](USER_STORIES.md).

## Features

### User Management
- **Author Registration**
  - First name, last name, university, email
  - Field of research (for matching with company interests)
  - Years of experience (for relevance scoring)
  - Session-based authentication with password hashing

- **Company Registration**
  - Company name, address, email
  - Research interests (comma-separated, used for AI recommendations)
  - Session-based authentication with password hashing

### Paper Management
- **Create & Upload**
  - Create papers with title and subject (keywords for matching)
  - Upload PDF files (stored in Supabase Storage)
  - Automatic collaborator assignment (creator is first collaborator)

- **Update & Edit**
  - Update paper title
  - Update paper subject/keywords
  - Upload new PDF versions (replaces previous version)
  - Any collaborator can make updates

- **Publishing**
  - Publish papers to make them visible to companies
  - Draft papers remain private to collaborators only
  - Published papers visible in company dashboard and recommendations

- **Deletion**
  - Authors can delete papers they created or collaborate on
  - Cascading deletion of collaborators, interests, and reviews

### Collaboration System
- **Collaborator Management**
  - Add collaborators by email address
  - Remove collaborators (except paper creator)
  - All collaborators can view, edit, and publish papers
  - View all papers you're collaborating on in author dashboard

### Company Features
- **Browse & Search**
  - Browse all published papers
  - Search by title, author name, or field of research
  - View paper details including authors, subjects, and download counts

- **Interest Management**
  - Mark papers as interesting
  - View list of all interested papers
  - Mark papers as "business critical" for priority tracking
  - Toggle interest on/off

- **AI-Powered Recommendations**
  - Personalized paper recommendations based on:
    - Company research interests matching paper subjects (50% weight)
    - Author field of research matching (35% weight)
    - Author experience level (10% weight)
    - Boost if company interested in other papers by same authors (30% boost)
  - Relevance scores displayed as percentages
  - Recommendations page showing top matches

- **Business Relevance Scoring**
  - Automatic calculation of business relevance scores
  - Factors include:
    - Popularity (number of interested companies)
    - Business critical status (if any company marked as critical)
  - Detailed breakdown view available

- **Paper Downloads**
  - Download PDFs of published papers
  - Download count tracking (incremented per company download)
  - Authors can also download their own papers (not counted)

- **Research Interests**
  - Companies can set/update their research interests
  - Used for matching and recommendations
  - Comma-separated keywords

### Review System
- **Paper Reviews**
  - Authors and companies can review published papers
  - 1-5 star rating system
  - Optional text comments
  - Average rating displayed on paper page
  - Authors cannot review their own papers
  - One review per user/company per paper
  - Companies can edit and delete their own reviews

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

**users** - Author accounts
- id (UUID, primary key)
- email (unique)
- password_hash
- first_name, last_name
- university
- field_of_research (for matching with company interests)
- years_of_experience (for relevance scoring)
- created_at

**companies** - Company accounts
- id (UUID, primary key)
- email (unique)
- password_hash
- company_name
- address
- research_interests (comma-separated keywords for matching)
- created_at

**papers** - Research papers
- id (UUID, primary key)
- title
- subject (keywords for matching, comma-separated)
- status (enum: draft/published)
- file_path (path to PDF in Supabase Storage)
- download_count (number of company downloads)
- created_by (foreign key to users.id)
- created_at, updated_at

**paper_collaborators** - Junction table
- paper_id (foreign key to papers.id)
- user_id (foreign key to users.id)
- added_at
- Composite primary key: (paper_id, user_id)

**paper_interests** - Company interests in papers
- paper_id (foreign key to papers.id)
- company_id (foreign key to companies.id)
- added_at
- relevance_score (calculated relevance to company)
- business_relevance_score (calculated business importance)
- is_business_critical (boolean flag)
- Composite primary key: (paper_id, company_id)

**reviews** - Paper reviews
- id (UUID, primary key)
- paper_id (foreign key to papers.id)
- user_id (foreign key to users.id, nullable)
- company_id (foreign key to companies.id, nullable)
- rating (1-5 stars)
- comment (text, optional)
- created_at
- Constraints: rating between 1-5, either user_id or company_id must be set, unique per paper per reviewer

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

## How It Works

### Authentication Flow
1. User registers (author or company)
2. Password is hashed and stored in database
3. User logs in with email/password
4. Session stores user_id and user_type
5. Decorators check session for protected routes

### Paper Management Flow
1. Author creates paper with PDF upload
2. PDF saved to Supabase Storage
3. Author added as first collaborator
4. Other authors can be added as collaborators
5. Any collaborator can update title or upload new PDF
6. Paper can be published (makes it visible to companies)

### Company Interaction Flow
1. Company sets research interests (optional, improves recommendations)
2. Views list of published papers or gets AI recommendations
3. Can search by title, author name, or field of research
4. Can mark papers as "interested" or "business critical"
5. Can download PDFs of published papers (download count incremented)
6. Can review papers with ratings and comments
7. Authors see which companies are interested and download counts

### Recommendation System Flow
1. Company sets research interests (comma-separated keywords)
2. System calculates relevance scores for all published papers:
   - Paper subject match: 50%
   - Author field match: 35%
   - Author experience: 10%
   - Boost if interested in other papers by same authors: +30%
3. Papers sorted by relevance score
4. Top recommendations displayed on recommendations page

### Review System Flow
1. User (author or company) views published paper
2. Can submit review with 1-5 star rating and optional comment
3. Authors cannot review their own papers
4. One review per user/company per paper
5. Average rating displayed on paper page
6. Companies can edit or delete their own reviews

## Code Organization

### app.py
- Creates Flask application
- Initializes SQLAlchemy and Flask-Migrate
- Registers all route blueprints
- Home page route with platform statistics
- Context processor for user info in templates

### models.py
- **User**: Author model with field_of_research, years_of_experience
- **Company**: Company model with research_interests
- **Paper**: Paper model with subject, download_count, status enum
- **PaperCollaborator**: Many-to-many relationship
- **PaperInterest**: Interest tracking with relevance scores
- **Review**: Review model with rating and comment
- **PaperStatus**: Enum for draft/published status

### config.py
- Environment variable loading (supports multiple .env files)
- Configuration class with database, Supabase, and Flask settings
- Command-line argument parsing for environment selection

### extensions.py
- Flask-SQLAlchemy database instance
- Flask-Migrate instance for database migrations

### storage.py
- `get_storage_client()` - Initialize Supabase client with service key
- `upload_paper_pdf()` - Upload PDF to Supabase Storage
- `download_paper_pdf()` - Download PDF from Supabase Storage
- `delete_paper_pdf()` - Delete PDF from Supabase Storage

### routes/auth.py
- `register_author()` - Create author account with research fields
- `register_company()` - Create company account with interests
- `login()` - Authenticate user (author or company)
- `logout()` - Clear session
- **Decorators:**
  - `@login_required` - Requires authenticated user
  - `@author_required` - Requires author role
  - `@company_required` - Requires company role

### routes/papers.py
- `author_dashboard()` - Show author's papers with collaborators and interests
- `company_dashboard()` - Show published papers with search functionality
- `update_research_interests()` - Update company research interests
- `recommended_papers()` - AI-powered paper recommendations
- `create_paper()` - Create new paper with PDF upload and subject
- `view_paper()` - View paper details (different views for authors/companies)
- `update_paper()` - Update title, subject, or upload new PDF
- `publish_paper()` - Change status to published
- `download_paper()` - Download PDF file (tracks download count)
- `delete_paper()` - Delete paper and all related data
- `submit_review()` - Submit review for published paper
- `edit_review()` - Edit existing review (companies only)
- `delete_review()` - Delete review (companies only)
- `toggle_business_critical()` - Mark/unmark paper as business critical
- `get_business_score_details()` - Show business relevance score breakdown
- **Helper Functions:**
  - `calculate_relevance_score()` - Calculate relevance between paper and company
  - `calculate_business_relevance_score()` - Calculate business importance score
  - `get_recommended_papers()` - Get top recommended papers for company

### routes/collaborators.py
- `add_collaborator()` - Add author to paper by email
- `remove_collaborator()` - Remove author from paper (cannot remove creator)

### routes/interests.py
- `toggle_interest()` - Add/remove company interest in paper
- `my_interests()` - View company's list of interested papers

## Security

Security is handled at the application level:

1. **Authentication**: Session-based, checked by decorators
2. **Authorization**: Each route checks user permissions
3. **Password Storage**: Hashed using werkzeug (bcrypt)
4. **SQL Injection**: Prevented using parameterized queries
5. **Access Control**:
   - Authors can only see/edit papers they collaborate on
   - Companies can only see published papers
   - File downloads are permission-checked

## Recommendation Algorithm

The recommendation system calculates relevance scores between papers and companies using a weighted scoring system:

### Relevance Score Calculation

1. **Paper Subject Match (50% weight)**
   - Compares paper subject keywords with company research interests
   - Uses substring matching and word overlap
   - Full 50% if any subject matches

2. **Author Field Match (35% weight)**
   - Compares author's field of research with company interests
   - Calculates percentage of authors with matching fields
   - Weighted by number of matching authors

3. **Author Experience (10% weight)**
   - Based on average years of experience of paper authors
   - Normalized: 20 years = 100% of this component

4. **Author Interest Boost (+30%)**
   - If company is interested in other papers by the same authors
   - Multiplies base score by 1.3

### Business Relevance Score

Calculated separately for business importance:

1. **Popularity Score (0-40%)**
   - Based on number of companies interested
   - Normalized: 10+ interested companies = 40%

2. **Business Critical Score (0-60%)**
   - Based on number of companies marking as business critical
   - Normalized: 3+ critical marks = 60%

Final score is capped at 100%.

## Common Tasks

### Add a new field to users
```python
# 1. Update model in models.py
class User(db.Model):
    # ... existing fields ...
    phone = db.Column(db.String(20))

# 2. Create migration
flask db migrate -m "Add phone to users"
flask db upgrade

# 3. Update registration form in template
<input name="phone" type="tel">

# 4. Update registration route in routes/auth.py
phone = request.form.get('phone', '').strip()
user = User(..., phone=phone if phone else None)
```

### Add a new feature
1. Create new route file in `routes/` if needed
2. Add routes with appropriate decorators (`@login_required`, etc.)
3. Use SQLAlchemy models for database operations
4. Create HTML templates in `templates/`
5. Register blueprint in `app.py`
6. Create database migration if schema changes: `flask db migrate -m "Description"`

## Development

### Team Workflow
- Each developer works on own branch
- Test locally with own database
- Create Pull Request to main
- Team reviews code together
- Merge to main when approved

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

