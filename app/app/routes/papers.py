"""
Paper management routes.
Handles paper creation, viewing, updating, and file uploads.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from routes.auth import login_required, author_required, company_required
from extensions import db
from models import Paper, User, Company, PaperCollaborator, PaperInterest, PaperStatus, Review
from sqlalchemy import func
from config import Config
from storage import upload_paper_pdf, download_paper_pdf
import uuid
import io

papers_bp = Blueprint('papers', __name__)


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def calculate_business_relevance_score(paper_id, company_id):
    """
    Calculate business relevance score for a paper.
    
    Factors:
    - How many other companies are interested (popularity)
    - If any company marked it as business critical
    - Industry trend indicator
    
    Returns:
        float: Score between 0.0 and 1.0
    """
    # Count total interested companies
    total_interested = (
        db.session.query(PaperInterest)
        .filter(PaperInterest.paper_id == paper_id)
        .count()
    )
    
    # Count companies that marked as business critical
    business_critical_count = (
        db.session.query(PaperInterest)
        .filter(
            PaperInterest.paper_id == paper_id,
            PaperInterest.is_business_critical == True
        )
        .count()
    )
    
    # Popularity score (0-0.4)
    # Normalized by assuming papers with 10+ interested companies are highly popular
    popularity_score = min(0.4, (total_interested / 10) * 0.4)
    
    # Business critical score (0-0.6)
    # If any company marked as critical, boost the score
    business_critical_score = 0.0
    if business_critical_count > 0:
        business_critical_score = min(0.6, (business_critical_count / 3) * 0.6)
    
    business_relevance = popularity_score + business_critical_score
    
    return min(1.0, business_relevance)


def calculate_relevance_score(paper_id, company_id):
    """
    Calculate relevance score between a paper and a company.
    
    Weighting:
    - Paper subject match: 50% (primary factor)
    - Author field match: 35% (secondary factor - increased)
    - Researcher experience: 5% (minor factor - decreased)
    - Boost: +30% if company interested in other papers by same authors (increased)
    
    Returns:
        float: Score between 0.0 and 1.0
    """
    # Get company interests
    company = db.session.query(Company).filter_by(id=company_id).first()
    if not company or not company.research_interests:
        return 0.0
    
    company_interests = [i.strip().lower() for i in company.research_interests.split(',')]
    
    # Get paper with subject
    paper = db.session.query(Paper).filter_by(id=paper_id).first()
    if not paper:
        return 0.0
    
    # Get paper authors
    authors = (
        db.session.query(User)
        .join(PaperCollaborator, User.id == PaperCollaborator.user_id)
        .filter(PaperCollaborator.paper_id == paper_id)
        .all()
    )
    
    # Calculate paper subject match score (50% weight) - PRIMARY FACTOR
    subject_score = 0.0
    if paper.subject:
        paper_subjects = [s.strip().lower() for s in paper.subject.split(',')]
        
        for subject in paper_subjects:
            subject_words = set(subject.replace('-', ' ').split())
            
            for interest in company_interests:
                interest_words = set(interest.replace('-', ' ').split())
                
                # Check for substring match OR word overlap
                if (interest in subject or 
                    subject in interest or 
                    len(subject_words & interest_words) > 0):
                    subject_score = 0.5  # Full 50% if any subject matches
                    break
            if subject_score > 0:
                break
    
    # Calculate author field match score (35% weight) - SECONDARY FACTOR (INCREASED)
    field_score = 0.0
    if authors:
        field_matches = 0
        for author in authors:
            if author.field_of_research:
                author_field = author.field_of_research.lower()
                author_words = set(author_field.replace(',', ' ').replace('-', ' ').split())
                
                for interest in company_interests:
                    interest_words = set(interest.replace('-', ' ').split())
                    
                    if (interest in author_field or 
                        author_field in interest or 
                        len(author_words & interest_words) > 0):
                        field_matches += 1
                        break
        
        field_score = (field_matches / len(authors)) * 0.35  # 35% weight (increased)
    
    # Calculate experience match score (5% weight) - MINOR FACTOR (DECREASED)
    experience_score = 0.0
    if authors:
        avg_experience = sum(
            author.years_of_experience or 0 for author in authors
        ) / len(authors)
        experience_score = min(1.0, (avg_experience / 20)) * 0.05  # 5% weight (decreased)
    
    # Base score (0.0 to 1.0)
    base_score = subject_score + field_score + experience_score
    
    # Debug output (can be removed later)
    print(f"=== RELEVANCE SCORE DEBUG ===")
    print(f"Paper ID: {paper_id}")
    print(f"Paper Subject: {paper.subject}")
    print(f"Company Interests: {company_interests}")
    print(f"Authors found: {len(authors) if authors else 0}")
    if authors:
        for a in authors:
            print(f"  - Author: {a.first_name} {a.last_name}, Field: '{a.field_of_research}', Experience: {a.years_of_experience}")
    print(f"Subject Score: {subject_score} (50% max)")
    print(f"Field Score: {field_score} (35% max)")
    print(f"Experience Score: {experience_score} (5% max)")
    print(f"Base Score: {base_score}")
    print(f"=============================")
    
    # Check if company is interested in other papers by any of these authors
    if authors:
        author_ids = [author.id for author in authors]
        
        interested_count = (
            db.session.query(PaperInterest)
            .join(PaperCollaborator, PaperInterest.paper_id == PaperCollaborator.paper_id)
            .filter(
                PaperInterest.company_id == company_id,
                PaperCollaborator.user_id.in_(author_ids),
                PaperInterest.paper_id != paper_id
            )
            .distinct(PaperInterest.paper_id)
            .count()
        )
        
        # Apply boost if company is interested in other papers by these authors (INCREASED)
        if interested_count > 0:
            base_score *= 1.3  # 30% boost (increased from 20%)
    
    return min(1.0, base_score)


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

    # Get company's research interests
    company = db.session.query(Company).filter_by(id=user_id).first()
    company_interests = company.research_interests if company else None

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

    return render_template('papers/company_dashboard.html', papers=papers, search=search, company_interests=company_interests)


@papers_bp.route('/company/update-interests', methods=['POST'])
@company_required
def update_research_interests():
    """Update company's research interests"""
    user_id = session['user_id']
    research_interests = request.form.get('research_interests', '').strip()
    
    try:
        db.session.query(Company).filter_by(id=user_id).update({
            'research_interests': research_interests if research_interests else None
        })
        db.session.commit()
        flash('Research interests updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating interests: {str(e)}', 'error')
    
    return redirect(url_for('papers.company_dashboard'))


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
            subject = request.form.get('subject', '').strip()
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
            p = Paper(id=paper_id, title=title, subject=subject if subject else None, status=PaperStatus.draft, file_path=file_path, created_by=user_id)
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
        'subject': p.subject,
        'status': p.status.value if hasattr(p.status, 'value') else p.status,
        'file_path': p.file_path,
        'download_count': p.download_count or 0,
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

    # check if company is interested and get business relevance data
    is_interested = False
    if user_type == 'company':
        inter = db.session.query(PaperInterest).filter_by(paper_id=paper_id, company_id=user_id).first()
        is_interested = inter is not None
        paper['is_interested'] = is_interested  # Add to paper dict for template
        
        # Always calculate and show the relevance score (same as in recommendations)
        business_score = calculate_business_relevance_score(paper_id, user_id)
        relevance_score = calculate_relevance_score(paper_id, user_id)
        paper['business_relevance_score'] = round(relevance_score * 100, 1)
        paper['is_business_critical'] = inter.is_business_critical if inter else False

    # Reviews - only for published papers
    reviews = []
    avg_rating = None
    user_has_reviewed = False
    
    if paper['status'] == 'published':
        review_rows = db.session.query(Review).filter_by(paper_id=paper_id).order_by(Review.created_at.desc()).all()
        
        for r in review_rows:
            review = {
                'id': r.id,
                'rating': r.rating,
                'comment': r.comment,
                'created_at': r.created_at,
                'reviewer_type': 'author' if r.user_id else 'company',
            }
            if r.user_id:
                reviewer = db.session.query(User).filter_by(id=r.user_id).first()
                review['reviewer_name'] = f"{reviewer.first_name} {reviewer.last_name}" if reviewer else "Unknown Author"
            else:
                reviewer = db.session.query(Company).filter_by(id=r.company_id).first()
                review['reviewer_name'] = reviewer.company_name if reviewer else "Unknown Company"
            reviews.append(review)
        
        avg = db.session.query(func.avg(Review.rating)).filter_by(paper_id=paper_id).scalar()
        avg_rating = round(float(avg), 1) if avg else None
        
        if user_type == 'author':
            user_has_reviewed = db.session.query(Review).filter_by(paper_id=paper_id, user_id=user_id).first() is not None
        elif user_type == 'company':
            user_has_reviewed = db.session.query(Review).filter_by(paper_id=paper_id, company_id=user_id).first() is not None

    return render_template('papers/view_paper.html', paper=paper, user_type=user_type, is_collaborator=is_collaborator, is_interested=is_interested, reviews=reviews, avg_rating=avg_rating, user_has_reviewed=user_has_reviewed)


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

        # Update subject if provided
        subject = request.form.get('subject')
        if subject is not None:  # Allow empty string to clear subject
            db.session.query(Paper).filter_by(id=paper_id).update({'subject': subject.strip() if subject.strip() else None, 'updated_at': db.func.now()})
            db.session.commit()
            flash('Subject updated successfully!', 'success')

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
        # Increment download count for company downloads (not author downloads)
        if user_type == 'company':
            try:
                db.session.execute(
                    db.text("UPDATE papers SET download_count = COALESCE(download_count, 0) + 1 WHERE id = :paper_id"),
                    {"paper_id": paper_id}
                )
                db.session.commit()
            except Exception as e:
                print(f"Error updating download count: {e}")
                db.session.rollback()
        
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
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()

    if not rating or not (1 <= rating <= 5):
        flash('Please provide a rating between 1 and 5 stars.', 'error')
        return redirect(url_for('papers.view_paper', paper_id=paper_id))

    paper = db.session.query(Paper).filter_by(id=paper_id).first()
    if not paper or paper.status != PaperStatus.published:
        flash('Paper not found or not published.', 'error')
        return redirect(url_for('papers.company_dashboard' if user_type == 'company' else 'papers.author_dashboard'))

    # Authors cannot review their own papers (if they are collaborators)
    if user_type == 'author':
        is_collaborator = db.session.query(PaperCollaborator).filter_by(paper_id=paper_id, user_id=user_id).first()
        if is_collaborator:
            flash('You cannot review your own paper.', 'error')
            return redirect(url_for('papers.view_paper', paper_id=paper_id))

    try:
        existing_review = None
        if user_type == 'author':
            existing_review = db.session.query(Review).filter_by(paper_id=paper_id, user_id=user_id).first()
        elif user_type == 'company':
            existing_review = db.session.query(Review).filter_by(paper_id=paper_id, company_id=user_id).first()

        if existing_review:
            flash('You have already submitted a review for this paper.', 'error')
            return redirect(url_for('papers.view_paper', paper_id=paper_id))

        new_review = Review(
            paper_id=paper_id,
            rating=rating,
            comment=comment if comment else None
        )
        if user_type == 'author':
            new_review.user_id = user_id
        else:
            new_review.company_id = user_id

        db.session.add(new_review)
        db.session.commit()
        flash('Review submitted successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting review: {str(e)}', 'error')

    return redirect(url_for('papers.view_paper', paper_id=paper_id))


@papers_bp.route('/paper/<paper_id>/toggle_business_critical', methods=['POST'])
@company_required
def toggle_business_critical(paper_id):
    """Toggle business critical status for a paper"""
    user_id = session['user_id']
    
    try:
        interest = db.session.query(PaperInterest).filter_by(
            paper_id=paper_id, 
            company_id=user_id
        ).first()
        
        if not interest:
            flash('You must first mark interest in this paper.', 'error')
            return redirect(url_for('papers.view_paper', paper_id=paper_id))
        
        interest.is_business_critical = not interest.is_business_critical
        new_score = calculate_business_relevance_score(paper_id, user_id)
        interest.business_relevance_score = new_score
        
        db.session.commit()
        
        if interest.is_business_critical:
            flash('Paper marked as business critical!', 'success')
        else:
            flash('Paper unmarked as business critical.', 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('papers.view_paper', paper_id=paper_id))


