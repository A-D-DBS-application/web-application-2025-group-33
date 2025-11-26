"""
Collaborator management routes.
Handles adding and removing collaborators from papers.
"""

from flask import Blueprint, request, redirect, url_for, flash, session
from routes.auth import author_required
from extensions import db
from models import User, Paper, PaperCollaborator

collaborators_bp = Blueprint('collaborators', __name__)


@collaborators_bp.route('/paper/<paper_id>/add-collaborator', methods=['POST'])
@author_required
def add_collaborator(paper_id):
    """Add a collaborator to a paper"""
    try:
        user_id = session['user_id']

        # Check if user is a collaborator
        is_collaborator = db.session.query(PaperCollaborator).filter_by(paper_id=paper_id, user_id=user_id).first()

        if not is_collaborator:
            flash('You are not a collaborator on this paper.', 'error')
            return redirect(url_for('papers.author_dashboard'))

        # Get the user email to add
        collaborator_email = request.form.get('collaborator_email')
        if not collaborator_email:
            flash('Please provide an author email.', 'error')
            return redirect(url_for('papers.view_paper', paper_id=paper_id))

        # Verify the user exists (must be an author)
        collaborator = db.session.query(User).filter_by(email=collaborator_email).first()
        if not collaborator:
            flash('Author not found.', 'error')
            return redirect(url_for('papers.view_paper', paper_id=paper_id))

        collaborator_id = str(collaborator.id)

        # Check if already a collaborator
        existing = db.session.query(PaperCollaborator).filter_by(paper_id=paper_id, user_id=collaborator_id).first()

        if existing:
            flash('This author is already a collaborator.', 'error')
            return redirect(url_for('papers.view_paper', paper_id=paper_id))

        # Add as collaborator
        pc = PaperCollaborator(paper_id=paper_id, user_id=collaborator_id)
        db.session.add(pc)
        db.session.commit()

        flash('Collaborator added successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('papers.view_paper', paper_id=paper_id))


@collaborators_bp.route('/paper/<paper_id>/remove-collaborator/<collaborator_id>', methods=['POST'])
@author_required
def remove_collaborator(paper_id, collaborator_id):
    """Remove a collaborator from a paper"""
    try:
        user_id = session['user_id']

        # Check if current user is a collaborator
        is_collaborator = db.session.query(PaperCollaborator).filter_by(paper_id=paper_id, user_id=user_id).first()

        if not is_collaborator:
            flash('You are not a collaborator on this paper.', 'error')
            return redirect(url_for('papers.author_dashboard'))

        # Check if trying to remove the creator
        paper = db.session.query(Paper).filter_by(id=paper_id).first()

        if paper and str(paper.created_by) == str(collaborator_id):
            flash('Cannot remove the paper creator.', 'error')
            return redirect(url_for('papers.view_paper', paper_id=paper_id))

        # Remove collaborator if exists
        existing = db.session.query(PaperCollaborator).filter_by(paper_id=paper_id, user_id=collaborator_id).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            flash('Collaborator removed successfully!', 'success')
        else:
            flash('Collaborator not found.', 'error')

    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('papers.view_paper', paper_id=paper_id))
