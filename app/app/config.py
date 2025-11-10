import os
import sys
from dotenv import load_dotenv

# Check if environment file specified on command line
# Usage: python app.py --env development
#    or: python app.py --env shared
#    or: python app.py (uses .env if exists, otherwise .env.development)
env_file = '.env'  # default

if '--env' in sys.argv:
    try:
        env_index = sys.argv.index('--env')
        env_name = sys.argv[env_index + 1]
        env_file = f'.env.{env_name}'
        print(f"Loading environment from: {env_file}")
    except (IndexError, ValueError):
        print("Warning: --env flag requires a value (e.g., --env development)")
        print("Falling back to .env")
elif not os.path.exists('.env') and os.path.exists('.env.development'):
    # If .env doesn't exist but .env.development does, use that as default
    env_file = '.env.development'
    print(f"Loading environment from: {env_file} (default)")

# Load the environment file
if os.path.exists(env_file):
    load_dotenv(env_file)
    # Show which database we're using (without showing password)
    db_url = os.getenv('DATABASE_URL', '')
    if db_url:
        # Extract host from connection string
        if '@' in db_url:
            host = db_url.split('@')[1].split(':')[0] if ':' in db_url.split('@')[1] else db_url.split('@')[1].split('/')[0]
            print(f"Using database: {host}")
else:
    print(f"Warning: Environment file '{env_file}' not found!")
    print("Please create it from .env.example")

class Config:
    """Simple configuration for the Flask application"""

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Database settings (PostgreSQL connection string)
    # Format: postgresql://user:password@host:port/database
    DATABASE_URL = os.getenv('DATABASE_URL')

    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Supabase settings (for file storage only)
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

    # File upload settings
    ALLOWED_EXTENSIONS = {'pdf'}
