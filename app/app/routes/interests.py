"""
Interest management routes.
Handles companies marking papers as interesting.
"""

from flask import Blueprint, request, redirect, url_for, flash, session, render_template
from routes.auth import company_required
from extensions import db
from models import Paper, PaperInterest, User

interests_bp = Blueprint('interests', __name__)


@interests_bp.route('/paper/<paper_id>/toggle-interest', methods=['POST'])
@company_required
def toggle_interest(paper_id):
    """Toggle company interest in a paper"""
    try:
        user_id = session['user_id']

        # Check if paper is published
        paper = db.session.query(Paper).filter_by(id=paper_id).first()

        if not paper or (hasattr(paper, 'status') and getattr(paper.status, 'value', paper.status) != 'published'):
            flash('Can only mark interest in published papers.', 'error')
            return redirect(url_for('papers.company_dashboard'))

        # Check if already interested
        existing = db.session.query(PaperInterest).filter_by(paper_id=paper_id, company_id=user_id).first()

        if existing:
            # Remove interest
            db.session.delete(existing)
            db.session.commit()
            flash('Removed from your interests.', 'success')
        else:
            # Add interest
            pi = PaperInterest(paper_id=paper_id, company_id=user_id)
            db.session.add(pi)
            db.session.commit()
            flash('Added to your interests!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')

    # Redirect back to previous page or dashboard
    return redirect(request.referrer or url_for('papers.company_dashboard'))


@interests_bp.route('/interests')
@company_required
def my_interests():
    """View company's list of interested papers"""
    user_id = session['user_id']

    papers_q = (
        db.session.query(Paper)
        .join(PaperInterest, Paper.id == PaperInterest.paper_id)
        .filter(PaperInterest.company_id == user_id)
        .order_by(PaperInterest.added_at.desc())
        .all()
    )

    papers = []
    for p in papers_q:
        paper = {
            'id': p.id,
            'title': p.title,
            'status': p.status.value if hasattr(p.status, 'value') else p.status,
            'file_path': p.file_path,
            'created_at': p.created_at,
            'updated_at': p.updated_at,
        }

        authors = (
            db.session.query(User.id, User.first_name, User.last_name, User.university)
            .join('paper_collaborators', User.id == None)
        )

        # Instead, fetch authors via PaperCollaborator simple query
        authors = (
            db.session.query(User.id, User.first_name, User.last_name, User.university)
            .join('paper_collaborators', User.id == None)
        )

        # To keep it simple, use a separate query matching the previous behavior:
        from models import PaperCollaborator
        authors = (
            db.session.query(User.id, User.first_name, User.last_name, User.university)
            .join(PaperCollaborator, User.id == PaperCollaborator.user_id)
            .filter(PaperCollaborator.paper_id == p.id)
            .all()
        )

        paper['authors'] = [dict(r._mapping) for r in authors]
        papers.append(paper)

    return render_template('interests/my_interests.html', papers=papers)
