"""
Paper management routes.
Handles paper creation, viewing, updating, and file uploads.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from routes.auth import login_required, author_required, company_required
from extensions import db
from models import Paper, User, Company, PaperCollaborator, PaperInterest, PaperStatus
from config import Config
from storage import upload_paper_pdf, download_paper_pdf
import uuid
import io

papers_bp = Blueprint('papers', __name__)


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def calculate_relevance_score(paper_id, company_id):
    """
    Calculate relevance score between a paper and a company.
    
    Weighting:
    - Research field match: 50%
    - Researcher experience: 50%
    - Boost: +20% if company is interested in other papers by same authors
    
    Returns:
        float: Score between 0.0 and 1.0
    """
    # Get company interests
    company = db.session.query(Company).filter_by(id=company_id).first()
    if not company or not company.research_interests:
        return 0.0
    
    company_interests = [i.strip().lower() for i in company.research_interests.split(',')]
    
    # Get paper authors
    authors = (
        db.session.query(User)
        .join(PaperCollaborator, User.id == PaperCollaborator.user_id)
        .filter(PaperCollaborator.paper_id == paper_id)
        .all()
    )
    
    if not authors:
        return 0.0
    
    # Calculate field match score (50% weight)
    field_matches = 0
    for author in authors:
        if author.field_of_research:
            author_field = author.field_of_research.lower()
            for interest in company_interests:
                if interest in author_field or author_field in interest:
                    field_matches += 1
    
    field_score = (field_matches / len(authors)) * 0.5  # 50% weight
    
    # Calculate experience match score (50% weight)
    avg_experience = sum(
        author.years_of_experience or 0 for author in authors
    ) / len(authors)
    
    experience_score = min(1.0, (avg_experience / 20)) * 0.5  # 50% weight
    
    # Base score (0.0 to 1.0)
    base_score = field_score + experience_score
    
    # Check if company is interested in other papers by any of these authors
    author_ids = [author.id for author in authors]
    
    interested_count = (
        db.session.query(PaperInterest)
        .join(PaperCollaborator, PaperInterest.paper_id == PaperCollaborator.paper_id)
        .filter(
            PaperInterest.company_id == company_id,
            PaperCollaborator.user_id.in_(author_ids),
            PaperInterest.paper_id != paper_id  # Don't count this paper
        )
        .distinct(PaperInterest.paper_id)
        .count()
    )
    
    # Apply boost if company is interested in other papers by these authors
    boost_multiplier = 1.0
    if interested_count > 0:
        boost_multiplier = 1.2  # 20% boost
    
    final_score = min(1.0, base_score * boost_multiplier)
    
    return final_score


def get_recommended_papers(company_id, limit=10):
    """
    Get papers recommended for a company based on relevance.
    
    Args:
        company_id: UUID of the company
        limit: Maximum number of papers to return
        
    Returns:
        List of dicts with 'paper' and 'score' keys, sorted by score descending
    """
    # Get all published papers
    papers = (
        db.session.query(Paper)
        .filter(Paper.status == PaperStatus.published)
        .all()
    )
    
    # Calculate scores
    scored_papers = []
    for paper in papers:
        score = calculate_relevance_score(paper.id, company_id)
        if score > 0:
            scored_papers.append({
                'paper': paper,
                'score': score
            })
    
    # Sort by score descending
    scored_papers.sort(key=lambda x: x['score'], reverse=True)
    
    return scored_papers[:limit]


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
                db.func.lower(User.first_name + ' ' + User.last_name).like(like),
                db.func.lower(User.field_of_research).like(like)
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
            db.session.query(User.id, User.first_name, User.last_name, User.university, User.field_of_research)
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


@papers_bp.route('/company/recommendations')
@company_required
def recommended_papers():
    """Show AI-recommended papers for company based on their interests and researcher experience"""
    user_id = session['user_id']
    
    company = db.session.query(Company).filter_by(id=user_id).first()
    
    if not company or not company.research_interests:
        flash('Please set your research interests first to get recommendations.', 'info')
        return redirect(url_for('papers.company_dashboard'))
    
    recommended = get_recommended_papers(user_id, limit=20)
    
    papers = []
    for item in recommended:
        p = item['paper']
        paper = {
            'id': p.id,
            'title': p.title,
            'relevance_score': round(item['score'] * 100, 1),  # Convert to percentage
            'created_at': p.created_at,
        }
        
        authors = (
            db.session.query(User.id, User.first_name, User.last_name, 
                           User.university, User.years_of_experience, User.field_of_research)
            .join(PaperCollaborator, User.id == PaperCollaborator.user_id)
            .filter(PaperCollaborator.paper_id == p.id)
            .all()
        )
        paper['authors'] = [dict(r._mapping) for r in authors]
        papers.append(paper)
    
    return render_template('papers/recommended_papers.html', papers=papers)


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
            db.session.query(User.id, User.first_name, User.last_name, User.university, User.years_of_experience, User.field_of_research)
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

    return render_template('papers/view_paper.html', paper=paper, user_type=user_type, is_collaborator=is_collaborator, is_interested=is_interested)


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
