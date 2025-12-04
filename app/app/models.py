from extensions import db
from datetime import datetime
import enum
import uuid


# Author (User) model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    university = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    field_of_research = db.Column(db.String(255))
    years_of_experience = db.Column(db.Integer, default=0)

# Company model
class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(500))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    research_interests = db.Column(db.String(1000))

class PaperStatus(enum.Enum):
    draft = 'draft'
    published = 'published'

class Paper(db.Model):
    __tablename__ = 'papers'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.Text, nullable=False)
    subject = db.Column(db.String(500))  # Paper subject for relevance matching
    status = db.Column(db.Enum(PaperStatus), nullable=False, default=PaperStatus.draft)
    file_path = db.Column(db.String(1000))
    download_count = db.Column(db.Integer, default=0)  # Track number of downloads
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class PaperCollaborator(db.Model):
    __tablename__ = 'paper_collaborators'
    paper_id = db.Column(db.String(36), db.ForeignKey('papers.id'), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    added_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

class PaperInterest(db.Model):
    __tablename__ = 'paper_interests'
    paper_id = db.Column(db.String(36), db.ForeignKey('papers.id'), primary_key=True)
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), primary_key=True)
    added_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    relevance_score = db.Column(db.Float, default=0.0)
    business_relevance_score = db.Column(db.Float, default=0.0)  # ADD THIS
    is_business_critical = db.Column(db.Boolean, default=False)  # ADD THIS


class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    paper_id = db.Column(db.String(36), db.ForeignKey('papers.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    company_id = db.Column(db.String(36), db.ForeignKey('companies.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='rating_check'),
        db.CheckConstraint('(user_id IS NOT NULL AND company_id IS NULL) OR (user_id IS NULL AND company_id IS NOT NULL)', name='review_author_or_company_check'),
        db.UniqueConstraint('paper_id', 'user_id', name='unique_user_review'),
        db.UniqueConstraint('paper_id', 'company_id', name='unique_company_review'),
    )
