"""
Paper management routes.
Handles paper creation, viewing, updating, and file uploads.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from routes.auth import login_required, author_required, company_required
from extensions import db
from models import Paper, User, Company, PaperCollaborator, PaperInterest, PaperStatus, Review
from config import Config
from storage import upload_paper_pdf, download_paper_pdf
import uuid
import io

papers_bp = Blueprint('papers', __name__)


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@papers_bp.route('/author/dashboard')
@author_required
def author_dashboard():
    """Author dashboard showing their papers"""
    user_id = session['user_id']

    # Query papers where user is a collaborator
    paper_rows = (
        db.session.query(Paper)
        .join(PaperCollaborator, Paper.id == PaperCollaborator.paper_id)
        .filter(PaperCollaborator.user_id == user_id)
        .order_by(Paper.updated_at.desc())
        .all()
    )

    papers = []
    for p in paper_rows:
        paper = {
            'id': p.id,
            'title': p.title,
            'status': p.status.value if hasattr(p.status, 'value') else p.status,
            'file_path': p.file_path,
            'created_at': p.created_at,
            'updated_at': p.updated_at,
            'created_by': p.created_by,
        }

        # collaborators
        collaborators = (
            db.session.query(User.id, User.first_name, User.last_name, User.email, User.university)
            .join(PaperCollaborator, User.id == PaperCollaborator.user_id)
            .filter(PaperCollaborator.paper_id == p.id)
            .all()
        )
        paper['collaborators'] = [dict(row._mapping) for row in collaborators]

        # interested companies
        if paper['status'] == 'published':
            interests = (
                db.session.query(Company.id, Company.company_name, Company.email)
                .join(PaperInterest, Company.id == PaperInterest.company_id)
                .filter(PaperInterest.paper_id == p.id)
                .all()
            )
            paper['interested_companies'] = [dict(row._mapping) for row in interests]
        else:
            paper['interested_companies'] = []

        papers.append(paper)

    return render_template('papers/author_dashboard.html', papers=papers)


@papers_bp.route('/company/dashboard')
@company_required
def company_dashboard():
    """Company dashboard showing published papers"""
    user_id = session['user_id']
    search = request.args.get('search', '')

    query = db.session.query(Paper).join(PaperCollaborator).join(User).filter(Paper.status == PaperStatus.published)

    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            db.or_(
                db.func.lower(Paper.title).like(like),
                db.func.lower(User.first_name + ' ' + User.last_name).like(like)
            )
        )

    papers_q = query.order_by(Paper.updated_at.desc()).all()

    papers = []
    for p in papers_q:
        paper = {
            'id': p.id,
            'title': p.title,
            'created_at': p.created_at,
            'updated_at': p.updated_at,
        }

        authors = (
            db.session.query(User.id, User.first_name, User.last_name, User.university)
            .join(PaperCollaborator, User.id == PaperCollaborator.user_id)
            .filter(PaperCollaborator.paper_id == p.id)
            .all()
        )
        paper['authors'] = [dict(row._mapping) for row in authors]

        interest = (
            db.session.query(PaperInterest)
            .filter(PaperInterest.paper_id == p.id, PaperInterest.company_id == user_id)
            .first()
        )
        paper['is_interested'] = interest is not None

        papers.append(paper)

    return render_template('papers/company_dashboard.html', papers=papers, search=search)


@papers_bp.route('/paper/create', methods=['GET', 'POST'])
@author_required
def create_paper():
    """Create a new paper"""
    if request.method == 'POST':
        try:
            title = request.form['title']
            user_id = session['user_id']
            pdf_file = request.files.get('pdf')

            if not pdf_file or not allowed_file(pdf_file.filename):
                flash('Please upload a PDF file.', 'error')
                return redirect(request.url)

            # Create paper record
            paper_id = str(uuid.uuid4())

            # Upload to Supabase Storage (shared cloud storage)
            file_path = upload_paper_pdf(paper_id, pdf_file)

            # Insert paper using SQLAlchemy
            p = Paper(id=paper_id, title=title, status=PaperStatus.draft, file_path=file_path, created_by=user_id)
            db.session.add(p)
            db.session.commit()

            # Add creator as collaborator
            pc = PaperCollaborator(paper_id=paper_id, user_id=user_id)
            db.session.add(pc)
            db.session.commit()

            flash('Paper created successfully!', 'success')
            return redirect(url_for('papers.view_paper', paper_id=paper_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template('papers/create_paper.html')


@papers_bp.route('/paper/<paper_id>')
@login_required
def view_paper(paper_id):
    """View paper details"""
    user_id = session['user_id']
    user_type = session['user_type']

    # Get paper
    p = db.session.query(Paper).filter_by(id=paper_id).first()

    if not p:
        flash('Paper not found.', 'error')
        return redirect(url_for('home'))

    # Check access permissions
    is_collaborator = False
    if user_type == 'author':
        is_coll = db.session.query(PaperCollaborator).filter_by(paper_id=paper_id, user_id=user_id).first()
        if not is_coll:
            flash('You do not have access to this paper.', 'error')
            return redirect(url_for('papers.author_dashboard'))
        is_collaborator = True

    else:  # company
        if p.status != PaperStatus.published:
            flash('This paper is not yet published.', 'error')
            return redirect(url_for('papers.company_dashboard'))

    # Build paper dict
    paper = {
        'id': p.id,
        'title': p.title,
        'status': p.status.value if hasattr(p.status, 'value') else p.status,
        'file_path': p.file_path,
        'created_at': p.created_at,
        'updated_at': p.updated_at,
        'created_by': p.created_by,
    }

    # collaborators
    collaborators = (
        db.session.query(User.id, User.first_name, User.last_name, User.university)
        .join(PaperCollaborator, User.id == PaperCollaborator.user_id)
        .filter(PaperCollaborator.paper_id == paper_id)
        .all()
    )
    paper['collaborators'] = [dict(r._mapping) for r in collaborators]

    # authors (for company view)
    if user_type != 'author':
        authors = (
            db.session.query(User.id, User.first_name, User.last_name, User.university)
            .join(PaperCollaborator, User.id == PaperCollaborator.user_id)
            .filter(PaperCollaborator.paper_id == paper_id)
            .all()
        )
        paper['authors'] = [dict(r._mapping) for r in authors]

    # interested companies
    if paper['status'] == 'published':
        interests = (
            db.session.query(Company.id, Company.company_name)
            .join(PaperInterest, Company.id == PaperInterest.company_id)
            .filter(PaperInterest.paper_id == paper_id)
            .all()
        )
        paper['interested_companies'] = [dict(r._mapping) for r in interests]
    else:
        paper['interested_companies'] = []

    # check if company is interested
    is_interested = False
    if user_type == 'company':
        inter = db.session.query(PaperInterest).filter_by(paper_id=paper_id, company_id=user_id).first()
        is_interested = inter is not None

    # Fetch reviews for this paper
    reviews = []
    if paper['status'] == 'published':
        review_rows = db.session.query(Review).filter_by(paper_id=paper_id).order_by(Review.created_at.desc()).all()
        for r in review_rows:
            review_data = {
                'id': r.id,
                'rating': r.rating,
                'comment': r.comment,
                'created_at': r.created_at,
                'reviewer_type': 'author' if r.user_id else 'company',
            }
            # Get reviewer name
            if r.user_id:
                reviewer = db.session.query(User.first_name, User.last_name).filter_by(id=r.user_id).first()
                if reviewer:
                    review_data['reviewer_name'] = f"{reviewer.first_name} {reviewer.last_name}"
                else:
                    review_data['reviewer_name'] = "Unknown Author"
            else:
                reviewer = db.session.query(Company.company_name).filter_by(id=r.company_id).first()
                if reviewer:
                    review_data['reviewer_name'] = reviewer.company_name
                else:
                    review_data['reviewer_name'] = "Unknown Company"
            reviews.append(review_data)

    # Check if current user has already reviewed this paper
    user_has_reviewed = False
    if paper['status'] == 'published':
        if user_type == 'author':
            existing_review = db.session.query(Review).filter_by(paper_id=paper_id, user_id=user_id).first()
        else:
            existing_review = db.session.query(Review).filter_by(paper_id=paper_id, company_id=user_id).first()
        user_has_reviewed = existing_review is not None

    # Calculate average rating
    avg_rating = None
    if reviews:
        avg_rating = round(sum(r['rating'] for r in reviews) / len(reviews), 1)

    return render_template('papers/view_paper.html', paper=paper, user_type=user_type, is_collaborator=is_collaborator, is_interested=is_interested, reviews=reviews, user_has_reviewed=user_has_reviewed, avg_rating=avg_rating)


@papers_bp.route('/paper/<paper_id>/update', methods=['POST'])
@author_required
def update_paper(paper_id):
    """Update paper title or upload new version"""
    try:
        user_id = session['user_id']

        # Check if user is a collaborator
        is_collaborator = db.session.query(PaperCollaborator).filter_by(paper_id=paper_id, user_id=user_id).first()

        if not is_collaborator:
            flash('You are not a collaborator on this paper.', 'error')
            return redirect(url_for('papers.author_dashboard'))

        # Update title if provided
        title = request.form.get('title')
        if title:
            db.session.query(Paper).filter_by(id=paper_id).update({'title': title, 'updated_at': db.func.now()})
            db.session.commit()
            flash('Title updated successfully!', 'success')

        # Upload new PDF if provided
        pdf_file = request.files.get('pdf')
        if pdf_file and allowed_file(pdf_file.filename):
            # Upload new file to Supabase Storage (replaces old one due to upsert:true)
            file_path = upload_paper_pdf(paper_id, pdf_file)

            # Update database
            db.session.query(Paper).filter_by(id=paper_id).update({'file_path': file_path, 'updated_at': db.func.now()})
            db.session.commit()

            flash('New version uploaded successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('papers.view_paper', paper_id=paper_id))


@papers_bp.route('/paper/<paper_id>/publish', methods=['POST'])
@author_required
def publish_paper(paper_id):
    """Publish a paper"""
    try:
        user_id = session['user_id']

        # Check if user is a collaborator
        is_coll = db.session.query(PaperCollaborator).filter_by(paper_id=paper_id, user_id=user_id).first()

        if not is_coll:
            flash('You are not a collaborator on this paper.', 'error')
            return redirect(url_for('papers.author_dashboard'))

        # Update status to published
        db.session.query(Paper).filter_by(id=paper_id).update({'status': PaperStatus.published, 'updated_at': db.func.now()})
        db.session.commit()

        flash('Paper published successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('papers.view_paper', paper_id=paper_id))


@papers_bp.route('/paper/<paper_id>/download')
@login_required
def download_paper(paper_id):
    """Download paper PDF"""
    user_id = session['user_id']
    user_type = session['user_type']

    # Get paper
    p = db.session.query(Paper).filter_by(id=paper_id).first()

    if not p:
        flash('Paper not found.', 'error')
        return redirect(url_for('home'))

    # Check permissions
    if user_type == 'author':
        # Must be a collaborator
        is_coll = db.session.query(PaperCollaborator).filter_by(paper_id=paper_id, user_id=user_id).first()

        if not is_coll:
            flash('You do not have access to this paper.', 'error')
            return redirect(url_for('papers.author_dashboard'))
    else:
        # Companies can only download published papers
        if p.status != PaperStatus.published:
            flash('This paper is not yet published.', 'error')
            return redirect(url_for('papers.company_dashboard'))

    # Download file from Supabase Storage
    if p.file_path:
        try:
            pdf_content = download_paper_pdf(p.file_path)
            return send_file(
                io.BytesIO(pdf_content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"{p.title}.pdf"
            )
        except Exception as e:
            flash(f'Error downloading file: {str(e)}', 'error')
            return redirect(url_for('papers.view_paper', paper_id=paper_id))
    else:
        flash('Paper file not found.', 'error')
        return redirect(url_for('papers.view_paper', paper_id=paper_id))


@papers_bp.route('/paper/<paper_id>/review', methods=['POST'])
@login_required
def submit_review(paper_id):
    """Submit a review for a paper"""
    user_id = session['user_id']
    user_type = session['user_type']

    try:
        # Check paper exists and is published
        p = db.session.query(Paper).filter_by(id=paper_id).first()
        if not p:
            flash('Paper not found.', 'error')
            return redirect(url_for('home'))

        if p.status != PaperStatus.published:
            flash('You can only review published papers.', 'error')
            return redirect(url_for('papers.view_paper', paper_id=paper_id))

        # Get form data
        rating = request.form.get('rating')
        comment = request.form.get('comment', '').strip()

        if not rating:
            flash('Please select a rating.', 'error')
            return redirect(url_for('papers.view_paper', paper_id=paper_id))

        rating = int(rating)
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5 stars.', 'error')
            return redirect(url_for('papers.view_paper', paper_id=paper_id))

        # Check if user already reviewed this paper
        if user_type == 'author':
            existing = db.session.query(Review).filter_by(paper_id=paper_id, user_id=user_id).first()
        else:
            existing = db.session.query(Review).filter_by(paper_id=paper_id, company_id=user_id).first()

        if existing:
            flash('You have already reviewed this paper.', 'error')
            return redirect(url_for('papers.view_paper', paper_id=paper_id))

        # Create review
        review_id = str(uuid.uuid4())
        if user_type == 'author':
            review = Review(id=review_id, paper_id=paper_id, user_id=user_id, rating=rating, comment=comment if comment else None)
        else:
            review = Review(id=review_id, paper_id=paper_id, company_id=user_id, rating=rating, comment=comment if comment else None)

        db.session.add(review)
        db.session.commit()

        flash('Review submitted successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('papers.view_paper', paper_id=paper_id))
