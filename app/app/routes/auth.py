"""
Authentication routes for the paper collaboration platform.
Handles user registration, login, and logout for both authors and companies.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from extensions import db
from models import User, Company

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def author_required(f):
    """Decorator to require author role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        if session.get('user_type') != 'author':
            flash('This page is only accessible to authors.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def company_required(f):
    """Decorator to require company role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        if session.get('user_type') != 'company':
            flash('This page is only accessible to companies.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/register/author', methods=['GET', 'POST'])
def register_author():
    """Register a new author account"""
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            university = request.form['university']
            field_of_research = request.form['field_of_research']
            years_of_experience = request.form['years_of_experience']

            # Check if email already exists
            existing_user = User.query.filter_by(email=email).first()

            if existing_user:
                flash('Email already registered.', 'error')
                return redirect(request.url)

            # Validate years of experience
            try:
                years_exp = int(years_of_experience)
                if years_exp < 0 or years_exp > 70:
                    flash('Years of experience must be between 0 and 70.', 'error')
                    return redirect(request.url)
            except ValueError:
                flash('Years of experience must be a number.', 'error')
                return redirect(request.url)

            # Hash password and create user
            password_hash = generate_password_hash(password)
            user = User(
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                university=university,
                field_of_research=field_of_research,
                years_of_experience=years_exp,
            )
            db.session.add(user)
            db.session.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template('auth/register_author.html')


@auth_bp.route('/register/company', methods=['GET', 'POST'])
def register_company():
    """Register a new company account"""
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']
            company_name = request.form['company_name']
            address = request.form['address']
            research_interests = request.form['research_interests']

            # Check if email already exists
            existing_company = Company.query.filter_by(email=email).first()

            if existing_company:
                flash('Email already registered.', 'error')
                return redirect(request.url)

            # Validate research interests
            if not research_interests.strip():
                flash('Please enter at least one research interest.', 'error')
                return redirect(request.url)

            # Hash password and create company
            password_hash = generate_password_hash(password)
            company = Company(
                email=email,
                password_hash=password_hash,
                company_name=company_name,
                address=address,
                research_interests=research_interests,
            )
            db.session.add(company)
            db.session.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template('auth/register_company.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login for both authors and companies"""
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']

            # Try author login first
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                session['user_id'] = str(user.id)
                session['user_type'] = 'author'
                session['email'] = user.email
                flash('Login successful!', 'success')
                return redirect(url_for('papers.author_dashboard'))

            # Try company login
            company = Company.query.filter_by(email=email).first()
            if company and check_password_hash(company.password_hash, password):
                session['user_id'] = str(company.id)
                session['user_type'] = 'company'
                session['email'] = company.email
                flash('Login successful!', 'success')
                return redirect(url_for('papers.company_dashboard'))

            flash('Invalid email or password.', 'error')

        except Exception as e:
            flash(f'Error: {str(e)}', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """Logout current user"""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))
