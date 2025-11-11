# Paper Collaboration Platform

## Overview

A Flask web application for managing academic paper collaborations between authors and companies. Authors can upload papers, collaborate with other authors, and publish their work. Companies can browse published papers, mark their interests, and download papers.

## Features

- **User Management**
  - Author registration (first name, last name, university, email)
  - Company registration (company name, address, email)
  - Session-based authentication with password hashing

- **Paper Management**
  - Create and upload papers (PDF format)
  - Update paper titles
  - Upload new PDF versions (replaces previous)
  - Publish papers to make them visible to companies
  - Draft papers remain private to collaborators

- **Collaboration**
  - Add/remove collaborators on papers
  - Any collaborator can update the paper
  - View all papers you're collaborating on

- **Company Features**
  - Browse published papers
  - Search by title or author name
  - Mark papers as interesting
  - Download PDFs of published papers
  - See authors of papers

- **Privacy**
  - Authors can only see papers they collaborate on
  - Companies can only see published papers
  - Authors can see which companies are interested in their papers
  - Companies can see authors of published papers

## Technology Stack

- **Backend:** Flask (Python web framework)
- **Database:** PostgreSQL (via Supabase or any PostgreSQL server)
- **File Storage:** Supabase Storage (cloud file storage)
- **Authentication:** Flask sessions with werkzeug password hashing
- **Database Access:** Direct SQL queries using psycopg2

## Project Structure

```
PaperProject/
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── db.py               # Database utilities
├── storage.py          # Cloud file storage interface
├── requirements.txt    # Python dependencies (6 packages)
├── schema.sql          # Database schema
├── setup.sh            # Automated setup script
├── .env                # Environment variables (not in git)
├── .env.example        # Template for environment variables
│
├── routes/             # Application routes (blueprints)
│   ├── auth.py         # Authentication (login, register, logout)
│   ├── papers.py       # Paper management (CRUD operations)
│   ├── collaborators.py # Collaborator management
│   └── interests.py    # Company interests
│
├── templates/          # HTML templates
└── static/             # CSS, JavaScript, images
```

## Database Schema

### Tables

**users** - Both authors and companies
- Common fields: id, email, password_hash, user_type
- Author fields: first_name, last_name, university
- Company fields: company_name, address

**papers** - Research papers
- id, title, status (draft/published)
- file_path (path to PDF in storage)
- created_by, timestamps

**paper_collaborators** - Junction table
- Links papers to authors who can edit them

**paper_interests** - Junction table
- Links papers to companies interested in them

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- PostgreSQL database (Supabase recommended)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up PostgreSQL Database

Create a `.env` file:
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@host:port/database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key
```

**For Supabase:**
- Go to Project Settings → Database
- Find "Connection String" → "URI"
- Copy and paste into `DATABASE_URL`
- Go to Project Settings → API
- Copy "Project URL" into `SUPABASE_URL`
- Copy "anon public" key into `SUPABASE_KEY`

### 3. Create Database Schema

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
python app.py
```

Visit `http://localhost:5000`

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
1. Company views list of published papers
2. Can search by title or author name
3. Can mark papers as "interested"
4. Can download PDFs of published papers
5. Authors see which companies are interested

## Code Organization

### app.py
- Creates Flask application
- Registers all route blueprints
- Simple home page route

### db.py
- `get_db_connection()` - Context manager for DB connections
- `execute_query()` - Execute query and fetch all results
- `execute_query_one()` - Execute query and fetch one result

### storage.py
- `upload_paper_pdf()` - Upload PDF to Supabase Storage
- `download_paper_pdf()` - Download PDF from Supabase Storage
- `delete_paper_pdf()` - Delete PDF from Supabase Storage

### routes/auth.py
- `register_author()` - Create author account
- `register_company()` - Create company account
- `login()` - Authenticate user
- `logout()` - Clear session
- Decorators: `@login_required`, `@author_required`, `@company_required`

### routes/papers.py
- `author_dashboard()` - Show author's papers
- `company_dashboard()` - Show published papers with search
- `create_paper()` - Create new paper with PDF upload
- `view_paper()` - View paper details (different for authors/companies)
- `update_paper()` - Update title or upload new PDF
- `publish_paper()` - Change status to published
- `download_paper()` - Download PDF file

### routes/collaborators.py
- `add_collaborator()` - Add author to paper
- `remove_collaborator()` - Remove author from paper

### routes/interests.py
- `toggle_interest()` - Add/remove company interest
- `my_interests()` - View company's interested papers

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

## Common Tasks

### Add a new field to users
```sql
-- 1. Update database
ALTER TABLE users ADD COLUMN phone TEXT;

-- 2. Update registration form in template
<input name="phone" type="tel">

-- 3. Update registration route
phone = request.form['phone']
execute_query("INSERT INTO users (..., phone) VALUES (..., %s)", (..., phone))
```

### Add a new feature
1. Create new route file if needed
2. Add routes with appropriate decorators
3. Create database queries
4. Create HTML templates
5. Register blueprint in `app.py`

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
- Check SUPABASE_URL and SUPABASE_KEY in `.env`
- Verify storage bucket named "papers" exists
- Ensure bucket is public or has correct policies

## License

This project is for educational purposes.

