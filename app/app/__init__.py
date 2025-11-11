import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from .config import Config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize optional SQLAlchemy (kept for future use)
    if app.config.get('SQLALCHEMY_DATABASE_URI'):
        db.init_app(app)
        Migrate(app, db)

    # Attach Supabase client lazily via helper import to avoid import cycles
    from .supabase_client import make_supabase_client
    app.supabase = make_supabase_client(app)

    # Register routes
    from . import routes
    app.register_blueprint(routes.bp)

    # Simple root route to serve the homepage (templates/index.html exists)
    from flask import render_template

    @app.route('/')
    def index():
        return render_template('index.html')

    logging.getLogger('werkzeug').setLevel(logging.INFO)

    return app