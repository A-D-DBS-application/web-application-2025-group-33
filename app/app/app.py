"""
Simple Flask application for paper collaboration platform.
This is a student-friendly version with minimal complexity.
"""

from flask import Flask, render_template, session
from config import Config
from routes.auth import auth_bp
from routes.papers import papers_bp
from routes.collaborators import collaborators_bp
from routes.interests import interests_bp
from extensions import db, migrate

# Create Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)

# Register blueprints (route modules)
app.register_blueprint(auth_bp)
app.register_blueprint(papers_bp)
app.register_blueprint(collaborators_bp)
app.register_blueprint(interests_bp)


# Context processor to make logged_in and user_type available in all templates
@app.context_processor
def inject_user():
    return {
        'logged_in': 'user_id' in session,
        'user_type': session.get('user_type')
    }


@app.route('/')
def home():
    """Home page with login/register options"""
    if 'user_id' in session:
        user_type = session.get('user_type')
        return render_template('home.html', logged_in=True, user_type=user_type)
    return render_template('home.html', logged_in=False)


if __name__ == '__main__':
    # Honor FLASK_DEBUG or use default debug True for development convenience
    debug_mode = app.config.get('DEBUG', None)
    if debug_mode is None:
        # Keep default behavior (debug True in development runs)
        app.run(debug=True)
    else:
        app.run(debug=bool(debug_mode))
