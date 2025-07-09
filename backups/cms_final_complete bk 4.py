from flask import Flask, render_template_string, redirect, url_for, request, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os
import re
import json
import uuid
from werkzeug.utils import secure_filename

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kesgrave-cms-secret-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kesgrave_working.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Create upload directories
upload_dirs = ['councillors', 'content/images', 'content/downloads', 'events']
for upload_dir in upload_dirs:
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], upload_dir), exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for authentication
class AdminUser(UserMixin):
    def __init__(self, id, username='admin'):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    return AdminUser(user_id)

# Helper function to format dates in UK format
def format_uk_date(date_obj):
    """Format datetime object to UK format DD/MM/YYYY"""
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%d/%m/%Y')
    return date_obj

def format_uk_datetime(date_obj):
    """Format datetime object to UK format DD/MM/YYYY HH:MM"""
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%d/%m/%Y %H:%M')
    return date_obj

# Add template filters
app.jinja_env.filters['uk_date'] = format_uk_date
app.jinja_env.filters['uk_datetime'] = format_uk_datetime

# Database Models
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(7), default='#3498db')
    description = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CouncillorTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    councillor_id = db.Column(db.Integer, db.ForeignKey('councillor.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=False)

class Councillor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100))
    intro = db.Column(db.Text)  # Short introduction
    bio = db.Column(db.Text)
    address = db.Column(db.Text)  # Contact address
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    qualifications = db.Column(db.Text)  # Qualifications/credentials
    image_filename = db.Column(db.String(255))
    social_links = db.Column(db.Text)  # JSON string for social media links
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to tags through association table
    tags = db.relationship('Tag', secondary='councillor_tag', backref='councillors')

# Content models for Phase 2
class ContentCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#3498db')
    is_active = db.Column(db.Boolean, default=True)
    is_predefined = db.Column(db.Boolean, default=False)  # For predefined categories that can't be deleted
    url_path = db.Column(db.String(200), unique=True)  # URL path for the category
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContentSubcategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('content_category.id'), nullable=False)
    is_predefined = db.Column(db.Boolean, default=False)  # For predefined subcategories that can't be deleted
    url_path = db.Column(db.String(200))  # URL path for the subcategory
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    category = db.relationship('ContentCategory', backref='subcategories')

class ContentPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True)
    short_description = db.Column(db.Text)  # Short description
    long_description = db.Column(db.Text)   # Long description (rich text)
    category_id = db.Column(db.Integer, db.ForeignKey('content_category.id'))
    subcategory_id = db.Column(db.Integer, db.ForeignKey('content_subcategory.id'))
    status = db.Column(db.String(20), default='Draft')  # Draft, Published, Archived
    is_featured = db.Column(db.Boolean, default=False)
    
    # Content dates
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    approval_date = db.Column(db.DateTime)
    last_reviewed = db.Column(db.DateTime)
    next_review_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = db.relationship('ContentCategory', backref='pages')
    subcategory = db.relationship('ContentSubcategory', backref='pages')

# Content Gallery Model for multiple images with metadata
class ContentGallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_page_id = db.Column(db.Integer, db.ForeignKey('content_page.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    alt_text = db.Column(db.String(200))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    content_page = db.relationship('ContentPage', backref='gallery_images')

# Content Links Model for related links
class ContentLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_page_id = db.Column(db.Integer, db.ForeignKey('content_page.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    new_tab = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    content_page = db.relationship('ContentPage', backref='related_links')

# Content Downloads Model for file downloads
class ContentDownload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_page_id = db.Column(db.Integer, db.ForeignKey('content_page.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    alt_text = db.Column(db.String(200))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    content_page = db.relationship('ContentPage', backref='downloads')

# Event models
class EventCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#3498db')
    icon = db.Column(db.String(50), default='fas fa-calendar')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    short_description = db.Column(db.Text)  # New field for event previews
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('event_category.id'))
    
    # Date and time
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    all_day = db.Column(db.Boolean, default=False)
    
    # Location
    location_name = db.Column(db.String(200))
    location_address = db.Column(db.Text)
    location_url = db.Column(db.String(500))  # Google Maps link
    
    # Contact and booking
    contact_name = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    booking_required = db.Column(db.Boolean, default=False)
    booking_url = db.Column(db.String(500))
    max_attendees = db.Column(db.Integer)
    
    # Pricing
    is_free = db.Column(db.Boolean, default=True)
    price = db.Column(db.String(100))  # e.g., "£5 adults, £3 children"
    
    # Media
    image_filename = db.Column(db.String(255))
    featured = db.Column(db.Boolean, default=False)
    
    # Status
    status = db.Column(db.String(20), default='Draft')  # Draft, Published, Cancelled
    is_published = db.Column(db.Boolean, default=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = db.relationship('EventCategory', backref='events')

# Event Gallery Model for multiple images with metadata
class EventGallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    alt_text = db.Column(db.String(200))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    event = db.relationship('Event', backref='gallery_images')

# Event Category Assignment for multiple categories per event
class EventCategoryAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('event_category.id'), nullable=False)
    
    event = db.relationship('Event', backref='category_assignments')
    category = db.relationship('EventCategory', backref='event_assignments')

# Event Links Model for related URLs
class EventLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    new_tab = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    event = db.relationship('Event', backref='related_links')

# Event Downloads Model for file downloads
class EventDownload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    event = db.relationship('Event', backref='downloads')

# Meeting Type Model (predefined, non-editable)
class MeetingType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#3498db')  # Hex color
    is_predefined = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    show_schedule_applications = db.Column(db.Boolean, default=False)  # Show "Schedule of Applications" column
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Meeting Model
class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    meeting_type_id = db.Column(db.Integer, db.ForeignKey('meeting_type.id'), nullable=False)
    meeting_date = db.Column(db.Date, nullable=False)
    meeting_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(200))
    agenda_filename = db.Column(db.String(255))  # PDF file
    minutes_filename = db.Column(db.String(255))  # PDF file
    schedule_applications_filename = db.Column(db.String(255))  # PDF file (conditional)
    status = db.Column(db.String(20), default='Scheduled')  # Scheduled, Completed, Cancelled
    is_published = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    meeting_type = db.relationship('MeetingType', backref='meetings')

# Helper functions for social links
def get_social_links(councillor):
    """Get social links as dictionary"""
    if councillor.social_links:
        try:
            return json.loads(councillor.social_links)
        except:
            return {}
    return {}

def set_social_links(councillor, links_dict):
    """Set social links from dictionary"""
    councillor.social_links = json.dumps(links_dict) if links_dict else None

# File upload helper
def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_download_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 
        'zip', 'rar', 'png', 'jpg', 'jpeg', 'gif', 'webp'
    }

def allowed_file(filename):
    """Legacy function for backward compatibility"""
    return allowed_image_file(filename)

def save_uploaded_file(file, subfolder, file_type='image'):
    """Save uploaded file and return filename"""
    allowed_func = allowed_image_file if file_type == 'image' else allowed_download_file
    
    if file and allowed_func(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)
        file.save(filepath)
        return filename
    return None

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Simple authentication - any username/password works
        user = AdminUser(1)
        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .login-card {
                background: white;
                border-radius: 15px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                overflow: hidden;
                max-width: 400px;
                width: 100%;
            }
            .login-header {
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                color: white;
                padding: 2rem;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="login-card">
            <div class="login-header">
                <h3>🏛️ Kesgrave CMS</h3>
                <p class="mb-0">Content Management System</p>
            </div>
            <div class="p-4">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Username</label>
                        <input type="text" class="form-control" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" class="form-control" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Login</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    total_councillors = Councillor.query.count()
    published_councillors = Councillor.query.filter_by(is_published=True).count()
    total_tags = Tag.query.count()
    active_tags = Tag.query.filter_by(is_active=True).count()
    
    # Get recent councillors
    recent_councillors = Councillor.query.order_by(Councillor.updated_at.desc()).limit(5).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .stat-card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }
            .stat-card:hover {
                transform: translateY(-5px);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link active">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📊 Dashboard</h1>
                <div class="text-muted">{{ datetime.now()|uk_datetime }}</div>
            </div>
            
            <!-- Statistics Cards -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="stat-card p-4 text-center">
                        <div class="text-primary mb-2">
                            <i class="fas fa-users fa-2x"></i>
                        </div>
                        <h3 class="mb-1">{{ total_councillors }}</h3>
                        <p class="text-muted mb-0">Total Councillors</p>
                        <small class="text-success">{{ published_councillors }} published</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card p-4 text-center">
                        <div class="text-info mb-2">
                            <i class="fas fa-tags fa-2x"></i>
                        </div>
                        <h3 class="mb-1">{{ total_tags }}</h3>
                        <p class="text-muted mb-0">Ward Tags</p>
                        <small class="text-success">{{ active_tags }} active</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card p-4 text-center">
                        <div class="text-warning mb-2">
                            <i class="fas fa-file-alt fa-2x"></i>
                        </div>
                        <h3 class="mb-1">6</h3>
                        <p class="text-muted mb-0">Content Categories</p>
                        <small class="text-success">5 pages</small>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card p-4 text-center">
                        <div class="text-success mb-2">
                            <i class="fas fa-calendar fa-2x"></i>
                        </div>
                        <h3 class="mb-1">3</h3>
                        <p class="text-muted mb-0">Upcoming Events</p>
                        <small class="text-info">This month</small>
                    </div>
                </div>
            </div>
            
            <!-- Quick Actions -->
            <div class="row mb-4">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Quick Actions</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3">
                                    <a href="/councillors/add" class="btn btn-primary w-100 mb-2">
                                        <i class="fas fa-user-plus me-2"></i>Add New Councillor
                                    </a>
                                </div>
                                <div class="col-md-3">
                                    <a href="/tags/add" class="btn btn-info w-100 mb-2">
                                        <i class="fas fa-tag me-2"></i>Create Councillor Group Tags
                                    </a>
                                </div>
                                <div class="col-md-3">
                                    <a href="/content/pages" class="btn btn-warning w-100 mb-2">
                                        <i class="fas fa-file-plus me-2"></i>View All Pages
                                    </a>
                                </div>
                                <div class="col-md-3">
                                    <a href="/events/add" class="btn btn-success w-100 mb-2">
                                        <i class="fas fa-calendar-plus me-2"></i>Add New Event
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Recent Activity -->
            <div class="row">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Recent Councillors</h5>
                        </div>
                        <div class="card-body">
                            {% for councillor in recent_councillors %}
                            <div class="d-flex align-items-center mb-3 pb-3 border-bottom">
                                <div class="me-3">
                                    {% if councillor.image_filename %}
                                    <img src="/uploads/councillors/{{ councillor.image_filename }}" 
                                         class="rounded-circle" width="50" height="50" style="object-fit: cover;">
                                    {% else %}
                                    <div class="bg-secondary rounded-circle d-flex align-items-center justify-content-center" 
                                         style="width: 50px; height: 50px;">
                                        <i class="fas fa-user text-white"></i>
                                    </div>
                                    {% endif %}
                                </div>
                                <div class="flex-grow-1">
                                    <h6 class="mb-1">{{ councillor.name }}</h6>
                                    <p class="text-muted mb-1">{{ councillor.title or "Councillor" }}</p>
                                    <small class="text-muted">Updated: {{ councillor.updated_at|uk_datetime }}</small>
                                </div>
                                <div>
                                    <span class="badge bg-{{ 'success' if councillor.is_published else 'warning' }}">
                                        {{ 'Published' if councillor.is_published else 'Draft' }}
                                    </span>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">System Status</h5>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <div class="d-flex justify-content-between">
                                    <span>Database</span>
                                    <span class="badge bg-success">Connected</span>
                                </div>
                            </div>
                            <div class="mb-3">
                                <div class="d-flex justify-content-between">
                                    <span>File Uploads</span>
                                    <span class="badge bg-success">Working</span>
                                </div>
                            </div>
                            <div class="mb-3">
                                <div class="d-flex justify-content-between">
                                    <span>Last Backup</span>
                                    <span class="badge bg-info">{{ datetime.now()|uk_date }}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', total_councillors=total_councillors, published_councillors=published_councillors,
         total_tags=total_tags, active_tags=active_tags, recent_councillors=recent_councillors,
         datetime=datetime)

@app.route('/councillors')
@login_required
def councillors_list():
    councillors = Councillor.query.order_by(Councillor.name).all()
    
    councillors_html = ""
    for councillor in councillors:
        social_links = get_social_links(councillor)
        social_icons = ""
        for platform, url in social_links.items():
            if url:
                icon_map = {
                    'twitter': 'fab fa-twitter',
                    'linkedin': 'fab fa-linkedin',
                    'facebook': 'fab fa-facebook',
                    'instagram': 'fab fa-instagram'
                }
                icon = icon_map.get(platform, 'fas fa-link')
                social_icons += f'<a href="{url}" target="_blank" class="text-primary me-1"><i class="{icon}"></i></a>'
        
        tags_html = ""
        for tag in councillor.tags:
            tags_html += f'<span class="badge me-1" style="background-color: {tag.color}; color: white;">{tag.name}</span>'
        
        image_html = ""
        if councillor.image_filename:
            image_html = f'<img src="/uploads/councillors/{councillor.image_filename}" class="rounded-circle" width="40" height="40" style="object-fit: cover;">'
        else:
            image_html = '<div class="bg-secondary rounded-circle d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;"><i class="fas fa-user text-white"></i></div>'
        
        councillors_html += f'''
        <tr>
            <td>
                <div class="d-flex align-items-center">
                    <div class="me-3">
                        {image_html}
                    </div>
                    <div>
                        <h6 class="mb-1">{councillor.name}</h6>
                        <small class="text-muted">{councillor.title or "Councillor"}</small>
                    </div>
                </div>
            </td>
            <td>{tags_html}</td>
            <td>{councillor.email or "Not provided"}</td>
            <td>{social_icons}</td>
            <td>
                <span class="badge bg-{'success' if councillor.is_published else 'warning'}">
                    {'Published' if councillor.is_published else 'Draft'}
                </span>
            </td>
            <td>{councillor.updated_at.strftime('%d/%m/%Y')}</td>
            <td>
                <a href="/councillors/edit/{councillor.id}" class="btn btn-sm btn-outline-primary me-1">
                    <i class="fas fa-edit"></i>
                </a>
                <a href="/councillors/delete/{councillor.id}" class="btn btn-sm btn-outline-danger" 
                   onclick="return confirm('Delete {councillor.name}?')">
                    <i class="fas fa-trash"></i>
                </a>
            </td>
        </tr>
        '''
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Councillors - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link active">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>👥 Councillors Management</h1>
                <a href="/councillors/add" class="btn btn-primary">
                    <i class="fas fa-plus me-2"></i>Add New Councillor
                </a>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">All Councillors ({{ councillors|length }})</h5>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>Councillor</th>
                                    <th>Ward Tags</th>
                                    <th>Email</th>
                                    <th>Social Links</th>
                                    <th>Status</th>
                                    <th>Updated</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {{ councillors_html|safe }}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', councillors=councillors, councillors_html=councillors_html)


@app.route('/councillors/add', methods=['GET', 'POST'])
@login_required
def add_councillor():
    if request.method == 'POST':
        # Handle form submission
        councillor = Councillor(
            name=request.form['name'],
            title=request.form.get('title'),
            intro=request.form.get('intro'),
            bio=request.form.get('bio'),
            address=request.form.get('address'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            qualifications=request.form.get('qualifications'),
            is_published=bool(request.form.get('is_published'))
        )
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = save_uploaded_file(file, 'councillors')
                councillor.image_filename = filename
        
        # Handle social links
        social_links = {}
        for platform in ['twitter', 'linkedin', 'facebook', 'instagram']:
            url = request.form.get(f'social_{platform}')
            if url:
                social_links[platform] = url
        set_social_links(councillor, social_links)
        
        db.session.add(councillor)
        db.session.commit()
        
        # Handle tags
        tag_ids = request.form.getlist('tags')
        for tag_id in tag_ids:
            if tag_id:
                councillor_tag = CouncillorTag(councillor_id=councillor.id, tag_id=int(tag_id))
                db.session.add(councillor_tag)
        
        db.session.commit()
        flash('Councillor added successfully!', 'success')
        return redirect(url_for('councillors_list'))
    
    # GET request - show form
    tags = Tag.query.filter_by(is_active=True).order_by(Tag.name).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Councillor - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link active">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>➕ Add New Councillor</h1>
                <a href="/councillors" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to List
                </a>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Councillor Information</h5>
                </div>
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Full Name *</label>
                                    <input type="text" class="form-control" name="name" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Title/Position</label>
                                    <input type="text" class="form-control" name="title" placeholder="e.g., Councillor, Mayor">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Short Introduction</label>
                            <textarea class="form-control" name="intro" rows="2" placeholder="Brief introduction for homepage display"></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Biography</label>
                            <textarea class="form-control" name="bio" rows="4" placeholder="Detailed biography"></textarea>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Email Address</label>
                                    <input type="email" class="form-control" name="email">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Phone Number</label>
                                    <input type="tel" class="form-control" name="phone">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Contact Address</label>
                            <textarea class="form-control" name="address" rows="2"></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Qualifications</label>
                            <textarea class="form-control" name="qualifications" rows="2" placeholder="Education, certifications, experience"></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Profile Image</label>
                            <input type="file" class="form-control" name="image" accept="image/*">
                            <small class="text-muted">Recommended: Square image, at least 300x300px</small>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Ward Tags</label>
                            <div class="row">
                                {% for tag in tags %}
                                <div class="col-md-4 mb-2">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="tags" value="{{ tag.id }}" id="tag{{ tag.id }}">
                                        <label class="form-check-label" for="tag{{ tag.id }}">
                                            <span class="badge" style="background-color: {{ tag.color }}; color: white;">{{ tag.name }}</span>
                                        </label>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Social Media Links</label>
                            <div class="row">
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-twitter"></i></span>
                                        <input type="url" class="form-control" name="social_twitter" placeholder="Twitter/X URL">
                                    </div>
                                </div>
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-linkedin"></i></span>
                                        <input type="url" class="form-control" name="social_linkedin" placeholder="LinkedIn URL">
                                    </div>
                                </div>
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-facebook"></i></span>
                                        <input type="url" class="form-control" name="social_facebook" placeholder="Facebook URL">
                                    </div>
                                </div>
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-instagram"></i></span>
                                        <input type="url" class="form-control" name="social_instagram" placeholder="Instagram URL">
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_published" id="is_published" checked>
                                <label class="form-check-label" for="is_published">
                                    Publish immediately
                                </label>
                            </div>
                        </div>
                        
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Save Councillor
                            </button>
                            <a href="/councillors" class="btn btn-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', tags=tags)

@app.route('/councillors/edit/<int:councillor_id>', methods=['GET', 'POST'])
@login_required
def edit_councillor(councillor_id):
    councillor = Councillor.query.get_or_404(councillor_id)
    
    if request.method == 'POST':
        # Update councillor data
        councillor.name = request.form['name']
        councillor.title = request.form.get('title')
        councillor.intro = request.form.get('intro')
        councillor.bio = request.form.get('bio')
        councillor.address = request.form.get('address')
        councillor.email = request.form.get('email')
        councillor.phone = request.form.get('phone')
        councillor.qualifications = request.form.get('qualifications')
        councillor.is_published = bool(request.form.get('is_published'))
        councillor.updated_at = datetime.utcnow()
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = save_uploaded_file(file, 'councillors')
                councillor.image_filename = filename
        
        # Handle social links
        social_links = {}
        for platform in ['twitter', 'linkedin', 'facebook', 'instagram']:
            url = request.form.get(f'social_{platform}')
            if url:
                social_links[platform] = url
        set_social_links(councillor, social_links)
        
        # Update tags - remove existing and add new ones
        CouncillorTag.query.filter_by(councillor_id=councillor.id).delete()
        tag_ids = request.form.getlist('tags')
        for tag_id in tag_ids:
            if tag_id:
                councillor_tag = CouncillorTag(councillor_id=councillor.id, tag_id=int(tag_id))
                db.session.add(councillor_tag)
        
        db.session.commit()
        flash('Councillor updated successfully!', 'success')
        return redirect(url_for('councillors_list'))
    
    # GET request - show form with existing data
    tags = Tag.query.filter_by(is_active=True).order_by(Tag.name).all()
    councillor_tag_ids = [ct.tag_id for ct in CouncillorTag.query.filter_by(councillor_id=councillor.id).all()]
    social_links = get_social_links(councillor)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Councillor - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link active">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>✏️ Edit Councillor: {{ councillor.name }}</h1>
                <a href="/councillors" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to List
                </a>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Councillor Information</h5>
                </div>
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Full Name *</label>
                                    <input type="text" class="form-control" name="name" value="{{ councillor.name }}" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Title/Position</label>
                                    <input type="text" class="form-control" name="title" value="{{ councillor.title or '' }}" placeholder="e.g., Councillor, Mayor">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Short Introduction</label>
                            <textarea class="form-control" name="intro" rows="2" placeholder="Brief introduction for homepage display">{{ councillor.intro or '' }}</textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Biography</label>
                            <textarea class="form-control" name="bio" rows="4" placeholder="Detailed biography">{{ councillor.bio or '' }}</textarea>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Email Address</label>
                                    <input type="email" class="form-control" name="email" value="{{ councillor.email or '' }}">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Phone Number</label>
                                    <input type="tel" class="form-control" name="phone" value="{{ councillor.phone or '' }}">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Contact Address</label>
                            <textarea class="form-control" name="address" rows="2">{{ councillor.address or '' }}</textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Qualifications</label>
                            <textarea class="form-control" name="qualifications" rows="2" placeholder="Education, certifications, experience">{{ councillor.qualifications or '' }}</textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Profile Image</label>
                            {% if councillor.image_filename %}
                            <div class="mb-2">
                                <img src="/uploads/councillors/{{ councillor.image_filename }}" class="rounded" width="100" height="100" style="object-fit: cover;">
                                <small class="text-muted d-block">Current image</small>
                            </div>
                            {% endif %}
                            <input type="file" class="form-control" name="image" accept="image/*">
                            <small class="text-muted">Leave empty to keep current image. Recommended: Square image, at least 300x300px</small>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Ward Tags</label>
                            <div class="row">
                                {% for tag in tags %}
                                <div class="col-md-4 mb-2">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="tags" value="{{ tag.id }}" id="tag{{ tag.id }}" 
                                               {% if tag.id in councillor_tag_ids %}checked{% endif %}>
                                        <label class="form-check-label" for="tag{{ tag.id }}">
                                            <span class="badge" style="background-color: {{ tag.color }}; color: white;">{{ tag.name }}</span>
                                        </label>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Social Media Links</label>
                            <div class="row">
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-twitter"></i></span>
                                        <input type="url" class="form-control" name="social_twitter" value="{{ social_links.get('twitter', '') }}" placeholder="Twitter/X URL">
                                    </div>
                                </div>
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-linkedin"></i></span>
                                        <input type="url" class="form-control" name="social_linkedin" value="{{ social_links.get('linkedin', '') }}" placeholder="LinkedIn URL">
                                    </div>
                                </div>
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-facebook"></i></span>
                                        <input type="url" class="form-control" name="social_facebook" value="{{ social_links.get('facebook', '') }}" placeholder="Facebook URL">
                                    </div>
                                </div>
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-instagram"></i></span>
                                        <input type="url" class="form-control" name="social_instagram" value="{{ social_links.get('instagram', '') }}" placeholder="Instagram URL">
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_published" id="is_published" {% if councillor.is_published %}checked{% endif %}>
                                <label class="form-check-label" for="is_published">
                                    Published
                                </label>
                            </div>
                        </div>
                        
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Update Councillor
                            </button>
                            <a href="/councillors" class="btn btn-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', councillor=councillor, tags=tags, councillor_tag_ids=councillor_tag_ids, social_links=social_links)

@app.route('/councillors/delete/<int:councillor_id>')
@login_required
def delete_councillor(councillor_id):
    councillor = Councillor.query.get_or_404(councillor_id)
    
    # Delete associated tags
    CouncillorTag.query.filter_by(councillor_id=councillor.id).delete()
    
    # Delete the councillor
    db.session.delete(councillor)
    db.session.commit()
    
    flash(f'Councillor {councillor.name} deleted successfully!', 'success')
    return redirect(url_for('councillors_list'))

# Tags management routes
@app.route('/tags')
@login_required
def tags_list():
    tags = Tag.query.order_by(Tag.name).all()
    
    tags_html = ""
    for tag in tags:
        councillor_count = len(tag.councillors)
        
        tags_html += f'''
        <tr>
            <td>
                <span class="badge" style="background-color: {tag.color}; color: white; font-size: 0.9rem;">
                    {tag.name}
                </span>
            </td>
            <td>{tag.description or "No description"}</td>
            <td>{councillor_count} councillor{'s' if councillor_count != 1 else ''}</td>
            <td>
                <span class="badge bg-{'success' if tag.is_active else 'secondary'}">
                    {'Active' if tag.is_active else 'Inactive'}
                </span>
            </td>
            <td>{tag.created_at.strftime('%d/%m/%Y')}</td>
            <td>
                <a href="/tags/edit/{tag.id}" class="btn btn-sm btn-outline-primary me-1">
                    <i class="fas fa-edit"></i>
                </a>
                <a href="/tags/delete/{tag.id}" class="btn btn-sm btn-outline-danger" 
                   onclick="return confirm('Delete tag {tag.name}? This will remove it from all councillors.')">
                    <i class="fas fa-trash"></i>
                </a>
            </td>
        </tr>
        '''
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ward Tags - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link active">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>🏷️ Ward Tags Management</h1>
                <a href="/tags/add" class="btn btn-primary">
                    <i class="fas fa-plus me-2"></i>Add New Tag
                </a>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">All Ward Tags ({{ tags|length }})</h5>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>Tag</th>
                                    <th>Description</th>
                                    <th>Usage</th>
                                    <th>Status</th>
                                    <th>Created</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {{ tags_html|safe }}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', tags=tags, tags_html=tags_html)

@app.route('/tags/add', methods=['GET', 'POST'])
@login_required
def add_tag():
    if request.method == 'POST':
        tag = Tag(
            name=request.form['name'],
            description=request.form.get('description'),
            color=request.form.get('color', '#3498db'),
            is_active=bool(request.form.get('is_active'))
        )
        
        db.session.add(tag)
        db.session.commit()
        
        flash('Tag created successfully!', 'success')
        return redirect(url_for('tags_list'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Tag - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link active">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>➕ Add New Ward Tag</h1>
                <a href="/tags" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to List
                </a>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Tag Information</h5>
                </div>
                <div class="card-body">
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">Tag Name *</label>
                            <input type="text" class="form-control" name="name" required placeholder="e.g., East Ward, Planning Committee">
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Description</label>
                            <textarea class="form-control" name="description" rows="2" placeholder="Brief description of this tag"></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Color</label>
                            <input type="color" class="form-control form-control-color" name="color" value="#3498db">
                            <small class="text-muted">Choose a color for this tag</small>
                        </div>
                        
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_active" id="is_active" checked>
                                <label class="form-check-label" for="is_active">
                                    Active (available for use)
                                </label>
                            </div>
                        </div>
                        
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Create Tag
                            </button>
                            <a href="/tags" class="btn btn-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/tags/edit/<int:tag_id>', methods=['GET', 'POST'])
@login_required
def edit_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    
    if request.method == 'POST':
        tag.name = request.form['name']
        tag.description = request.form.get('description')
        tag.color = request.form.get('color', '#3498db')
        tag.is_active = bool(request.form.get('is_active'))
        
        db.session.commit()
        flash('Tag updated successfully!', 'success')
        return redirect(url_for('tags_list'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Tag - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link active">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>✏️ Edit Tag: {{ tag.name }}</h1>
                <a href="/tags" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to List
                </a>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Tag Information</h5>
                </div>
                <div class="card-body">
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">Tag Name *</label>
                            <input type="text" class="form-control" name="name" value="{{ tag.name }}" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Description</label>
                            <textarea class="form-control" name="description" rows="2">{{ tag.description or '' }}</textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Color</label>
                            <input type="color" class="form-control form-control-color" name="color" value="{{ tag.color }}">
                            <small class="text-muted">Choose a color for this tag</small>
                        </div>
                        
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_active" id="is_active" {% if tag.is_active %}checked{% endif %}>
                                <label class="form-check-label" for="is_active">
                                    Active (available for use)
                                </label>
                            </div>
                        </div>
                        
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Update Tag
                            </button>
                            <a href="/tags" class="btn btn-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', tag=tag)

@app.route('/tags/delete/<int:tag_id>')
@login_required
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    
    # Delete associated councillor tags
    CouncillorTag.query.filter_by(tag_id=tag.id).delete()
    
    # Delete the tag
    db.session.delete(tag)
    db.session.commit()
    
    flash(f'Tag {tag.name} deleted successfully!', 'success')
    return redirect(url_for('tags_list'))


# Content management routes
@app.route('/content')
@login_required
def content_dashboard():
    # Get real categories with page counts
    db_categories = ContentCategory.query.filter_by(is_active=True).all()
    categories = []
    for cat in db_categories:
        page_count = ContentPage.query.filter_by(category_id=cat.id).count()
        categories.append({
            'name': cat.name,
            'count': page_count,
            'color': cat.color or '#3498db'
        })
    
    # Get recent pages from database
    recent_db_pages = ContentPage.query.order_by(ContentPage.updated_at.desc()).limit(5).all()
    recent_pages = []
    for page in recent_db_pages:
        category_name = page.category.name if page.category else 'Uncategorized'
        updated_date = page.updated_at.strftime('%d/%m/%Y') if page.updated_at else page.created_at.strftime('%d/%m/%Y') if page.created_at else ''
        recent_pages.append({
            'title': page.title,
            'category': category_name,
            'status': page.status,
            'updated': updated_date
        })
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Content Management - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .stat-card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
                cursor: pointer;
            }
            .stat-card:hover {
                transform: translateY(-5px);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📄 Content Management</h1>
                <div class="d-flex gap-2">
                    <a href="/content/pages" class="btn btn-info">
                        <i class="fas fa-list me-2"></i>View All Pages
                    </a>
                    <a href="/content/add" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Add New Page
                    </a>
                </div>
            </div>
            
            <!-- Content Categories -->
            <div class="row mb-4">
                <div class="col-12">
                    <h3 class="mb-3">Content Categories</h3>
                </div>
                {% for category in categories %}
                <div class="col-md-4 mb-3">
                    <div class="stat-card p-4" onclick="window.location.href='/content/pages?category={{ category.name|urlencode }}'">
                        <div class="d-flex align-items-center">
                            <div class="me-3">
                                <div class="rounded-circle d-flex align-items-center justify-content-center" 
                                     style="width: 50px; height: 50px; background-color: {{ category.color }};">
                                    <i class="fas fa-folder text-white"></i>
                                </div>
                            </div>
                            <div>
                                <h5 class="mb-1">{{ category.name }}</h5>
                                <p class="text-muted mb-0">{{ category.count }} pages</p>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <!-- Quick Actions -->
            <div class="row mb-4">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Quick Actions</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3">
                                    <a href="/content/pages" class="btn btn-info w-100 mb-2">
                                        <i class="fas fa-list me-2"></i>View All Pages (57)
                                    </a>
                                </div>
                                <div class="col-md-3">
                                    <a href="/content/add" class="btn btn-primary w-100 mb-2">
                                        <i class="fas fa-file-plus me-2"></i>Create New Page
                                    </a>
                                </div>
                                <div class="col-md-3">
                                    <a href="/content/categories" class="btn btn-warning w-100 mb-2">
                                        <i class="fas fa-folder-plus me-2"></i>Manage Categories
                                    </a>
                                </div>
                                <div class="col-md-3">
                                    <a href="/content/categories/add" class="btn btn-success w-100 mb-2">
                                        <i class="fas fa-plus me-2"></i>Add Category
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Recent Pages -->
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Recent Pages</h5>
                        </div>
                        <div class="card-body p-0">
                            <div class="table-responsive">
                                <table class="table table-hover mb-0">
                                    <thead class="table-light">
                                        <tr>
                                            <th>Page Title</th>
                                            <th>Category</th>
                                            <th>Status</th>
                                            <th>Last Updated</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for page in recent_pages %}
                                        <tr>
                                            <td>
                                                <h6 class="mb-1">{{ page.title }}</h6>
                                                <small class="text-muted">{{ page.category }}</small>
                                            </td>
                                            <td>
                                                <span class="badge bg-secondary">{{ page.category }}</span>
                                            </td>
                                            <td>
                                                <span class="badge bg-{{ 'success' if page.status == 'Published' else 'warning' }}">
                                                    {{ page.status }}
                                                </span>
                                            </td>
                                            <td>{{ page.updated }}</td>
                                            <td>
                                                <a href="#" class="btn btn-sm btn-outline-primary me-1">
                                                    <i class="fas fa-edit"></i>
                                                </a>
                                                <a href="#" class="btn btn-sm btn-outline-info me-1">
                                                    <i class="fas fa-eye"></i>
                                                </a>
                                                <a href="#" class="btn btn-sm btn-outline-danger">
                                                    <i class="fas fa-trash"></i>
                                                </a>
                                            </td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', categories=categories, recent_pages=recent_pages)

@app.route('/content/pages')
@login_required
def content_pages_list():
    # Get filter parameters
    category_filter = request.args.get('category')
    status_filter = request.args.get('status')
    search_query = request.args.get('search', '')
    page_num = int(request.args.get('page', 1))
    per_page = 20
    
    # Build database query
    query = ContentPage.query
    
    # Apply filters
    if category_filter:
        # Handle both category ID and category name
        if category_filter.isdigit():
            query = query.filter(ContentPage.category_id == int(category_filter))
        else:
            # Filter by category name
            query = query.join(ContentCategory).filter(ContentCategory.name == category_filter)
    if status_filter:
        query = query.filter(ContentPage.status == status_filter)
    if search_query:
        query = query.filter(ContentPage.title.contains(search_query))
    
    # Get total count for pagination
    total_pages = query.count()
    
    # Apply pagination
    pages_query = query.order_by(ContentPage.created_at.desc()).offset((page_num - 1) * per_page).limit(per_page)
    db_pages = pages_query.all()
    
    # Convert database objects to template-friendly format
    pages = []
    for page in db_pages:
        category_name = page.category.name if page.category else 'Uncategorized'
        pages.append({
            'id': page.id,
            'title': page.title,
            'category': category_name,
            'status': page.status,
            'author': 'Admin User',  # You can add author field to ContentPage model later
            'created': page.created_at.strftime('%d/%m/%Y') if page.created_at else '',
            'updated': page.updated_at.strftime('%d/%m/%Y') if page.updated_at else page.created_at.strftime('%d/%m/%Y') if page.created_at else '',
            'views': 0,  # You can add views field to ContentPage model later
            'summary': page.short_description or 'No description available'
        })
    
    total_page_count = (total_pages + per_page - 1) // per_page
    
    # Generate pagination HTML
    pagination_html = ""
    if total_page_count > 1:
        pagination_html = '<nav><ul class="pagination justify-content-center">'
        
        # Previous button
        if page_num > 1:
            prev_url = f"/content/pages?page={page_num-1}"
            if category_filter:
                prev_url += f"&category={category_filter}"
            if status_filter:
                prev_url += f"&status={status_filter}"
            if search_query:
                prev_url += f"&search={search_query}"
            pagination_html += f'<li class="page-item"><a class="page-link" href="{prev_url}">Previous</a></li>'
        
        # Page numbers (show 5 pages around current)
        start_page = max(1, page_num - 2)
        end_page = min(total_page_count, page_num + 2)
        
        for p in range(start_page, end_page + 1):
            page_url = f"/content/pages?page={p}"
            if category_filter:
                page_url += f"&category={category_filter}"
            if status_filter:
                page_url += f"&status={status_filter}"
            if search_query:
                page_url += f"&search={search_query}"
            
            active_class = "active" if p == page_num else ""
            pagination_html += f'<li class="page-item {active_class}"><a class="page-link" href="{page_url}">{p}</a></li>'
        
        # Next button
        if page_num < total_page_count:
            next_url = f"/content/pages?page={page_num+1}"
            if category_filter:
                next_url += f"&category={category_filter}"
            if status_filter:
                next_url += f"&status={status_filter}"
            if search_query:
                next_url += f"&search={search_query}"
            pagination_html += f'<li class="page-item"><a class="page-link" href="{next_url}">Next</a></li>'
        
        pagination_html += '</ul></nav>'
    
    # Get categories for filter dropdown
    categories = ContentCategory.query.filter_by(is_active=True).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>All Content Pages - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .filter-card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📋 All Content Pages</h1>
                <div class="d-flex gap-2">
                    <a href="/content" class="btn btn-secondary">
                        <i class="fas fa-arrow-left me-2"></i>Back to Content
                    </a>
                    <a href="/content/add" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Add New Page
                    </a>
                </div>
            </div>
            
            <!-- Filters -->
            <div class="filter-card p-3 mb-4">
                <form method="GET" class="row g-3">
                    <div class="col-md-3">
                        <label class="form-label">Search Pages</label>
                        <input type="text" class="form-control" name="search" value="{{ search_query }}" placeholder="Search by title...">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Category</label>
                        <select class="form-select" name="category">
                            <option value="">All Categories</option>
                            {% for category in categories %}
                            <option value="{{ category.id }}" {% if category_filter == category.id|string %}selected{% endif %}>{{ category.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Status</label>
                        <select class="form-select" name="status">
                            <option value="">All Statuses</option>
                            <option value="Published" {% if status_filter == 'Published' %}selected{% endif %}>Published</option>
                            <option value="Draft" {% if status_filter == 'Draft' %}selected{% endif %}>Draft</option>
                            <option value="Archived" {% if status_filter == 'Archived' %}selected{% endif %}>Archived</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">&nbsp;</label>
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-search me-1"></i>Filter
                            </button>
                            <a href="/content/pages" class="btn btn-outline-secondary">
                                <i class="fas fa-times me-1"></i>Clear
                            </a>
                        </div>
                    </div>
                </form>
            </div>
            
            <!-- Results Summary -->
            <div class="d-flex justify-content-between align-items-center mb-3">
                <div>
                    <h5 class="mb-0">
                        Showing {{ pages|length }} of {{ total_pages }} pages
                        {% if category_filter or status_filter or search_query %}
                        <small class="text-muted">(filtered)</small>
                        {% endif %}
                    </h5>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-primary btn-sm">
                        <i class="fas fa-download me-1"></i>Export
                    </button>
                    <button class="btn btn-outline-warning btn-sm">
                        <i class="fas fa-tasks me-1"></i>Bulk Actions
                    </button>
                </div>
            </div>
            
            <!-- Pages Table -->
            <div class="card">
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th width="5%">
                                        <input type="checkbox" class="form-check-input">
                                    </th>
                                    <th width="35%">Page Title</th>
                                    <th width="15%">Category</th>
                                    <th width="10%">Status</th>
                                    <th width="10%">Author</th>
                                    <th width="10%">Updated</th>
                                    <th width="8%">Views</th>
                                    <th width="7%">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for page in pages %}
                                <tr>
                                    <td>
                                        <input type="checkbox" class="form-check-input" value="{{ page.id }}">
                                    </td>
                                    <td>
                                        <div>
                                            <h6 class="mb-1">{{ page.title }}</h6>
                                            <small class="text-muted">{{ page.summary }}</small>
                                        </div>
                                    </td>
                                    <td>
                                        <span class="badge bg-secondary">{{ page.category }}</span>
                                    </td>
                                    <td>
                                        <span class="badge bg-{{ 'success' if page.status == 'Published' else 'warning' if page.status == 'Draft' else 'secondary' }}">
                                            {{ page.status }}
                                        </span>
                                    </td>
                                    <td>{{ page.author }}</td>
                                    <td>{{ page.updated }}</td>
                                    <td>{{ page.views }}</td>
                                    <td>
                                        <div class="btn-group btn-group-sm">
                                            <a href="/content/edit/{{ page.id }}" class="btn btn-outline-primary" title="Edit">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            <a href="/content/view/{{ page.id }}" class="btn btn-outline-info" title="View">
                                                <i class="fas fa-eye"></i>
                                            </a>
                                            <a href="#" class="btn btn-outline-danger" title="Delete">
                                                <i class="fas fa-trash"></i>
                                            </a>
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <!-- Pagination -->
            <div class="mt-4">
                {{ pagination_html|safe }}
            </div>
            
            <!-- Bulk Actions Panel (hidden by default) -->
            <div class="card mt-3" id="bulkActionsPanel" style="display: none;">
                <div class="card-body">
                    <h6>Bulk Actions</h6>
                    <div class="d-flex gap-2">
                        <button class="btn btn-success btn-sm">
                            <i class="fas fa-check me-1"></i>Publish Selected
                        </button>
                        <button class="btn btn-warning btn-sm">
                            <i class="fas fa-edit me-1"></i>Set as Draft
                        </button>
                        <button class="btn btn-secondary btn-sm">
                            <i class="fas fa-archive me-1"></i>Archive Selected
                        </button>
                        <button class="btn btn-danger btn-sm">
                            <i class="fas fa-trash me-1"></i>Delete Selected
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Show/hide bulk actions panel when checkboxes are selected
            document.addEventListener('DOMContentLoaded', function() {
                const checkboxes = document.querySelectorAll('tbody input[type="checkbox"]');
                const bulkPanel = document.getElementById('bulkActionsPanel');
                
                checkboxes.forEach(checkbox => {
                    checkbox.addEventListener('change', function() {
                        const checkedBoxes = document.querySelectorAll('tbody input[type="checkbox"]:checked');
                        bulkPanel.style.display = checkedBoxes.length > 0 ? 'block' : 'none';
                    });
                });
            });
        </script>
    </body>
    </html>
    ''', pages=pages, total_pages=total_pages, category_filter=category_filter, 
         status_filter=status_filter, search_query=search_query, pagination_html=pagination_html, categories=categories)

# Content category management routes
@app.route('/content/categories')
@login_required
def content_categories():
    categories = ContentCategory.query.all()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Manage Categories - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📁 Manage Categories</h1>
                <div class="d-flex gap-2">
                    <a href="/content" class="btn btn-secondary">
                        <i class="fas fa-arrow-left me-2"></i>Back to Content
                    </a>
                    <a href="/content/categories/add" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Add Category
                    </a>
                </div>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>Category Name</th>
                                    <th>URL Path</th>
                                    <th>Subcategories</th>
                                    <th>Pages</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for category in categories %}
                                <tr>
                                    <td>
                                        <div class="d-flex align-items-center">
                                            <div class="rounded-circle me-3" style="width: 20px; height: 20px; background-color: {{ category.color }};"></div>
                                            <div>
                                                <h6 class="mb-0">{{ category.name }}</h6>
                                                {% if category.description %}
                                                <small class="text-muted">{{ category.description }}</small>
                                                {% endif %}
                                            </div>
                                        </div>
                                    </td>
                                    <td><code>{{ category.url_path or '/' + category.name.lower().replace(' ', '-') }}</code></td>
                                    <td>{{ category.subcategories|length }}</td>
                                    <td>{{ category.pages|length }}</td>
                                    <td>
                                        <span class="badge bg-{{ 'success' if category.is_active else 'secondary' }}">
                                            {{ 'Active' if category.is_active else 'Inactive' }}
                                        </span>
                                        {% if category.is_predefined %}
                                        <span class="badge bg-info">Predefined</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <div class="btn-group btn-group-sm">
                                            <a href="/content/categories/edit/{{ category.id }}" class="btn btn-outline-primary" title="Edit">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            {% if not category.is_predefined %}
                                            <button class="btn btn-outline-danger" title="Delete" onclick="deleteCategory({{ category.id }})">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function deleteCategory(id) {
                if (confirm('Are you sure you want to delete this category?')) {
                    fetch('/content/categories/delete/' + id, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    }).then(response => {
                        if (response.ok) {
                            location.reload();
                        } else {
                            alert('Error deleting category');
                        }
                    });
                }
            }
        </script>
    </body>
    </html>
    ''', categories=categories)

@app.route('/content/categories/add', methods=['GET', 'POST'])
@login_required
def add_content_category():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        color = request.form.get('color', '#3498db')
        url_path = request.form.get('url_path')
        
        # Validate reserved paths
        reserved_paths = ['/councillors', '/ktc-meetings', '/contact', '/admin', '/login']
        if url_path in reserved_paths:
            flash('This URL path is reserved and cannot be used.', 'error')
            return redirect(request.url)
        
        # Check if URL path already exists
        existing = ContentCategory.query.filter_by(url_path=url_path).first()
        if existing:
            flash('This URL path is already in use.', 'error')
            return redirect(request.url)
        
        category = ContentCategory(
            name=name,
            description=description,
            color=color,
            url_path=url_path,
            is_active=True
        )
        
        db.session.add(category)
        
        # Add subcategories if provided
        subcategory_names = request.form.getlist('subcategory_name[]')
        subcategory_paths = request.form.getlist('subcategory_path[]')
        
        for i, sub_name in enumerate(subcategory_names):
            if sub_name.strip():
                sub_path = subcategory_paths[i] if i < len(subcategory_paths) else ''
                subcategory = ContentSubcategory(
                    name=sub_name.strip(),
                    url_path=sub_path.strip() if sub_path.strip() else None,
                    category=category,
                    is_active=True
                )
                db.session.add(subcategory)
        
        db.session.commit()
        flash('Category created successfully!', 'success')
        return redirect(url_for('content_categories'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Category - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>➕ Add Category</h1>
                <a href="/content/categories" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Categories
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="card">
                <div class="card-body">
                    <form method="POST">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Category Name *</label>
                                    <input type="text" class="form-control" name="name" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">URL Path *</label>
                                    <input type="text" class="form-control" name="url_path" placeholder="/category-name" required>
                                    <div class="form-text">Must start with / and use lowercase with hyphens</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Description</label>
                                    <textarea class="form-control" name="description" rows="3"></textarea>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Color</label>
                                    <input type="color" class="form-control form-control-color" name="color" value="#3498db">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-4">
                            <h5>Subcategories (Optional)</h5>
                            <div id="subcategories">
                                <div class="row mb-2">
                                    <div class="col-md-6">
                                        <input type="text" class="form-control" name="subcategory_name[]" placeholder="Subcategory name">
                                    </div>
                                    <div class="col-md-5">
                                        <input type="text" class="form-control" name="subcategory_path[]" placeholder="/subcategory-path">
                                    </div>
                                    <div class="col-md-1">
                                        <button type="button" class="btn btn-outline-danger" onclick="removeSubcategory(this)">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <button type="button" class="btn btn-outline-primary btn-sm" onclick="addSubcategory()">
                                <i class="fas fa-plus me-1"></i>Add Subcategory
                            </button>
                        </div>
                        
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Create Category
                            </button>
                            <a href="/content/categories" class="btn btn-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function addSubcategory() {
                const container = document.getElementById('subcategories');
                const div = document.createElement('div');
                div.className = 'row mb-2';
                div.innerHTML = `
                    <div class="col-md-6">
                        <input type="text" class="form-control" name="subcategory_name[]" placeholder="Subcategory name">
                    </div>
                    <div class="col-md-5">
                        <input type="text" class="form-control" name="subcategory_path[]" placeholder="/subcategory-path">
                    </div>
                    <div class="col-md-1">
                        <button type="button" class="btn btn-outline-danger" onclick="removeSubcategory(this)">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                container.appendChild(div);
            }
            
            function removeSubcategory(button) {
                button.closest('.row').remove();
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/content/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_content_category(category_id):
    category = ContentCategory.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        category.color = request.form.get('color', '#3498db')
        
        # Only allow URL path changes for non-predefined categories
        if not category.is_predefined:
            url_path = request.form.get('url_path')
            
            # Validate reserved paths
            reserved_paths = ['/councillors', '/ktc-meetings', '/contact', '/admin', '/login']
            if url_path in reserved_paths:
                flash('This URL path is reserved and cannot be used.', 'error')
                return redirect(request.url)
            
            # Check if URL path already exists (excluding current category)
            existing = ContentCategory.query.filter(
                ContentCategory.url_path == url_path,
                ContentCategory.id != category_id
            ).first()
            if existing:
                flash('This URL path is already in use.', 'error')
                return redirect(request.url)
            
            category.url_path = url_path
        
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('content_categories'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Category - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>✏️ Edit Category</h1>
                <a href="/content/categories" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Categories
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category_msg, message in messages %}
                        <div class="alert alert-{{ 'danger' if category_msg == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="card">
                <div class="card-body">
                    <form method="POST">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Category Name *</label>
                                    <input type="text" class="form-control" name="name" value="{{ category.name }}" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">URL Path *</label>
                                    <input type="text" class="form-control" name="url_path" value="{{ category.url_path }}" 
                                           {% if category.is_predefined %}readonly{% endif %} required>
                                    {% if category.is_predefined %}
                                    <div class="form-text text-warning">URL path cannot be changed for predefined categories</div>
                                    {% else %}
                                    <div class="form-text">Must start with / and use lowercase with hyphens</div>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Description</label>
                                    <textarea class="form-control" name="description" rows="3">{{ category.description or '' }}</textarea>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Color</label>
                                    <input type="color" class="form-control form-control-color" name="color" value="{{ category.color }}">
                                </div>
                            </div>
                        </div>
                        
                        {% if category.is_predefined %}
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle me-2"></i>
                            This is a predefined category. Some fields cannot be modified to maintain system integrity.
                        </div>
                        {% endif %}
                        
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Update Category
                            </button>
                            <a href="/content/categories" class="btn btn-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', category=category)

@app.route('/content/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_content_category(category_id):
    category = ContentCategory.query.get_or_404(category_id)
    
    # Prevent deletion of predefined categories
    if category.is_predefined:
        return jsonify({'error': 'Cannot delete predefined categories'}), 400
    
    # Check if category has pages
    if category.pages:
        return jsonify({'error': 'Cannot delete category with existing pages'}), 400
    
    # Delete subcategories first
    for subcategory in category.subcategories:
        db.session.delete(subcategory)
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'success': True})

# Content page creation and management
@app.route('/content/add', methods=['GET', 'POST'])
@login_required
def add_content_page():
    if request.method == 'POST':
        title = request.form.get('title')
        short_description = request.form.get('short_description')
        long_description = request.form.get('long_description')
        category_id = request.form.get('category_id')
        subcategory_id = request.form.get('subcategory_id') or None
        status = request.form.get('status', 'Draft')
        
        # Generate slug from title
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
        slug = re.sub(r'\s+', '-', slug).strip('-')
        
        # Check if slug already exists
        existing = ContentPage.query.filter_by(slug=slug).first()
        if existing:
            slug = f"{slug}-{int(datetime.now().timestamp())}"
        
        # Create content page
        content_page = ContentPage(
            title=title,
            slug=slug,
            short_description=short_description,
            long_description=long_description,
            category_id=category_id,
            subcategory_id=subcategory_id,
            status=status,
            creation_date=datetime.utcnow()
        )
        
        # Handle date fields
        created_date = request.form.get('created_date')
        if created_date:
            try:
                content_page.creation_date = datetime.strptime(created_date, '%Y-%m-%d')
            except ValueError:
                pass  # Keep default if invalid date
        
        approved_date = request.form.get('approved_date')
        if approved_date:
            try:
                content_page.approval_date = datetime.strptime(approved_date, '%Y-%m-%d')
            except ValueError:
                pass  # Keep None if invalid date
        
        next_review_date = request.form.get('next_review_date')
        if next_review_date:
            try:
                content_page.next_review_date = datetime.strptime(next_review_date, '%Y-%m-%d')
            except ValueError:
                pass  # Keep None if invalid date
        
        db.session.add(content_page)
        db.session.flush()  # Get the ID
        
        # Handle gallery images
        gallery_files = request.files.getlist('gallery_images[]')
        gallery_titles = request.form.getlist('gallery_title[]')
        gallery_descriptions = request.form.getlist('gallery_description[]')
        gallery_alt_texts = request.form.getlist('gallery_alt_text[]')
        
        for i, file in enumerate(gallery_files):
            if file and file.filename:
                filename = save_uploaded_file(file, 'content/images', 'image')
                if filename:
                    gallery_item = ContentGallery(
                        content_page_id=content_page.id,
                        filename=filename,
                        title=gallery_titles[i] if i < len(gallery_titles) else '',
                        description=gallery_descriptions[i] if i < len(gallery_descriptions) else '',
                        alt_text=gallery_alt_texts[i] if i < len(gallery_alt_texts) else '',
                        sort_order=i
                    )
                    db.session.add(gallery_item)
        
        # Handle related links
        link_titles = request.form.getlist('link_title[]')
        link_urls = request.form.getlist('link_url[]')
        
        for i, title in enumerate(link_titles):
            if title.strip() and i < len(link_urls) and link_urls[i].strip():
                # Check if the checkbox for this link is checked
                new_tab_checked = request.form.get(f'link_new_tab_{i}') is not None
                link = ContentLink(
                    content_page_id=content_page.id,
                    title=title.strip(),
                    url=link_urls[i].strip(),
                    new_tab=new_tab_checked,
                    sort_order=i
                )
                db.session.add(link)
        
        # Handle downloads
        download_files = request.files.getlist('download_files[]')
        download_titles = request.form.getlist('download_title[]')
        download_descriptions = request.form.getlist('download_description[]')
        download_alt_texts = request.form.getlist('download_alt_text[]')
        
        for i, file in enumerate(download_files):
            if file and file.filename:
                filename = save_uploaded_file(file, 'content/downloads', 'download')
                if filename:
                    download_item = ContentDownload(
                        content_page_id=content_page.id,
                        filename=filename,
                        title=download_titles[i] if i < len(download_titles) else file.filename,
                        description=download_descriptions[i] if i < len(download_descriptions) else '',
                        alt_text=download_alt_texts[i] if i < len(download_alt_texts) else '',
                        sort_order=i
                    )
                    db.session.add(download_item)
        
        db.session.commit()
        flash('Content page created successfully!', 'success')
        return redirect(url_for('content_pages_list'))
    
    # GET request - show form
    categories = ContentCategory.query.filter_by(is_active=True).all()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Content Page - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <script src="https://cdn.quilljs.com/1.3.6/quill.min.js"></script>
        <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .section-card {
                border: none;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📝 Add New Content Page</h1>
                <a href="/content" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Content
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST" enctype="multipart/form-data">
                <!-- Basic Information -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-info-circle me-2"></i>Basic Information</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Page Title *</label>
                                    <input type="text" class="form-control" name="title" required>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Status</label>
                                    <select class="form-select" name="status">
                                        <option value="Draft">Draft</option>
                                        <option value="Published">Published</option>
                                        <option value="Archived">Archived</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Category *</label>
                                    <select class="form-select" name="category_id" id="categorySelect" required onchange="loadSubcategories()">
                                        <option value="">Select Category</option>
                                        {% for category in categories %}
                                        <option value="{{ category.id }}">{{ category.name }}</option>
                                        {% endfor %}
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Subcategory</label>
                                    <select class="form-select" name="subcategory_id" id="subcategorySelect">
                                        <option value="">Select Subcategory</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Short Description</label>
                            <textarea class="form-control" name="short_description" rows="3" placeholder="Brief summary of the page content"></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Long Description</label>
                            <div id="longDescription" style="height: 300px;"></div>
                            <input type="hidden" name="long_description" id="longDescriptionInput">
                        </div>
                    </div>
                </div>
                
                <!-- Photo Gallery -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-images me-2"></i>Photo Gallery</h5>
                    </div>
                    <div class="card-body">
                        <div id="galleryContainer">
                            <div class="row mb-3 gallery-item">
                                <div class="col-md-3">
                                    <label class="form-label">Image</label>
                                    <input type="file" class="form-control" name="gallery_images[]" accept="image/*">
                                </div>
                                <div class="col-md-3">
                                    <label class="form-label">Title</label>
                                    <input type="text" class="form-control" name="gallery_title[]">
                                </div>
                                <div class="col-md-3">
                                    <label class="form-label">Description</label>
                                    <input type="text" class="form-control" name="gallery_description[]">
                                </div>
                                <div class="col-md-2">
                                    <label class="form-label">Alt Text</label>
                                    <input type="text" class="form-control" name="gallery_alt_text[]">
                                </div>
                                <div class="col-md-1">
                                    <label class="form-label">&nbsp;</label>
                                    <button type="button" class="btn btn-outline-danger d-block" onclick="removeGalleryItem(this)">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="addGalleryItem()">
                            <i class="fas fa-plus me-1"></i>Add Image
                        </button>
                    </div>
                </div>
                
                <!-- Related Links -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-link me-2"></i>Related Links</h5>
                    </div>
                    <div class="card-body">
                        <div id="linksContainer">
                            <div class="row mb-3 link-item">
                                <div class="col-md-4">
                                    <label class="form-label">Title</label>
                                    <input type="text" class="form-control" name="link_title[]">
                                </div>
                                <div class="col-md-5">
                                    <label class="form-label">URL</label>
                                    <input type="url" class="form-control" name="link_url[]">
                                </div>
                                <div class="col-md-2">
                                    <label class="form-label">New Tab</label>
                                    <div class="form-check">
                                        <input type="checkbox" class="form-check-input" name="link_new_tab_0" checked>
                                        <label class="form-check-label">Open in new tab</label>
                                    </div>
                                </div>
                                <div class="col-md-1">
                                    <label class="form-label">&nbsp;</label>
                                    <button type="button" class="btn btn-outline-danger d-block" onclick="removeLinkItem(this)">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="addLinkItem()">
                            <i class="fas fa-plus me-1"></i>Add Link
                        </button>
                    </div>
                </div>
                
                <!-- Downloads -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-download me-2"></i>Downloads</h5>
                    </div>
                    <div class="card-body">
                        <div id="downloadsContainer">
                            <div class="row mb-3 download-item">
                                <div class="col-md-3">
                                    <label class="form-label">File</label>
                                    <input type="file" class="form-control" name="download_files[]">
                                </div>
                                <div class="col-md-3">
                                    <label class="form-label">Title</label>
                                    <input type="text" class="form-control" name="download_title[]">
                                </div>
                                <div class="col-md-3">
                                    <label class="form-label">Description</label>
                                    <input type="text" class="form-control" name="download_description[]">
                                </div>
                                <div class="col-md-2">
                                    <label class="form-label">Alt Text</label>
                                    <input type="text" class="form-control" name="download_alt_text[]">
                                </div>
                                <div class="col-md-1">
                                    <label class="form-label">&nbsp;</label>
                                    <button type="button" class="btn btn-outline-danger d-block" onclick="removeDownloadItem(this)">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="addDownloadItem()">
                            <i class="fas fa-plus me-1"></i>Add Download
                        </button>
                    </div>
                </div>
                
                <!-- Date Information -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5><i class="fas fa-calendar me-2"></i>Date Information</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Created Date</label>
                                    <input type="date" class="form-control" name="created_date">
                                    <div class="form-text">Date when this content was originally created</div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Approved Date</label>
                                    <input type="date" class="form-control" name="approved_date">
                                    <div class="form-text">Date when this content was approved for publication</div>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Next Review Date</label>
                                    <input type="date" class="form-control" name="next_review_date">
                                    <div class="form-text">Set a date when this content should be reviewed for updates</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Submit -->
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save me-2"></i>Create Page
                    </button>
                    <a href="/content" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Initialize Quill.js
            var quill = new Quill('#longDescription', {
                theme: 'snow',
                modules: {
                    toolbar: [
                        [{ 'header': [1, 2, 3, false] }],
                        ['bold', 'italic', 'underline', 'strike'],
                        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                        [{ 'indent': '-1'}, { 'indent': '+1' }],
                        ['link', 'image'],
                        [{ 'align': [] }],
                        ['clean']
                    ]
                }
            });
            
            // Update hidden input when content changes
            quill.on('text-change', function() {
                document.getElementById('longDescriptionInput').value = quill.root.innerHTML;
            });
            
            // Update hidden input before form submission
            document.querySelector('form').addEventListener('submit', function() {
                document.getElementById('longDescriptionInput').value = quill.root.innerHTML;
            });
            
            // Category/Subcategory handling
            const subcategoriesData = {
                {% for category in categories %}
                {{ category.id }}: [
                    {% for subcategory in category.subcategories %}
                    {id: {{ subcategory.id }}, name: "{{ subcategory.name }}"}{{ "," if not loop.last }}
                    {% endfor %}
                ]{{ "," if not loop.last }}
                {% endfor %}
            };
            
            function loadSubcategories() {
                const categoryId = document.getElementById('categorySelect').value;
                const subcategorySelect = document.getElementById('subcategorySelect');
                
                subcategorySelect.innerHTML = '<option value="">Select Subcategory</option>';
                
                if (categoryId && subcategoriesData[categoryId]) {
                    subcategoriesData[categoryId].forEach(sub => {
                        const option = document.createElement('option');
                        option.value = sub.id;
                        option.textContent = sub.name;
                        subcategorySelect.appendChild(option);
                    });
                }
            }
            
            // Gallery management
            function addGalleryItem() {
                const container = document.getElementById('galleryContainer');
                const div = document.createElement('div');
                div.className = 'row mb-3 gallery-item';
                div.innerHTML = `
                    <div class="col-md-3">
                        <label class="form-label">Image</label>
                        <input type="file" class="form-control" name="gallery_images[]" accept="image/*">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Title</label>
                        <input type="text" class="form-control" name="gallery_title[]">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Description</label>
                        <input type="text" class="form-control" name="gallery_description[]">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Alt Text</label>
                        <input type="text" class="form-control" name="gallery_alt_text[]">
                    </div>
                    <div class="col-md-1">
                        <label class="form-label">&nbsp;</label>
                        <button type="button" class="btn btn-outline-danger d-block" onclick="removeGalleryItem(this)">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                container.appendChild(div);
            }
            
            function removeGalleryItem(button) {
                button.closest('.gallery-item').remove();
            }
            
            // Links management
            let linkCounter = 1;
            function addLinkItem() {
                const container = document.getElementById('linksContainer');
                const div = document.createElement('div');
                div.className = 'row mb-3 link-item';
                div.innerHTML = `
                    <div class="col-md-4">
                        <label class="form-label">Title</label>
                        <input type="text" class="form-control" name="link_title[]">
                    </div>
                    <div class="col-md-5">
                        <label class="form-label">URL</label>
                        <input type="url" class="form-control" name="link_url[]">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">New Tab</label>
                        <div class="form-check">
                            <input type="checkbox" class="form-check-input" name="link_new_tab_${linkCounter}" checked>
                            <label class="form-check-label">Open in new tab</label>
                        </div>
                    </div>
                    <div class="col-md-1">
                        <label class="form-label">&nbsp;</label>
                        <button type="button" class="btn btn-outline-danger d-block" onclick="removeLinkItem(this)">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                container.appendChild(div);
                linkCounter++;
            }
            
            function removeLinkItem(button) {
                button.closest('.link-item').remove();
            }
            
            // Downloads management
            function addDownloadItem() {
                const container = document.getElementById('downloadsContainer');
                const div = document.createElement('div');
                div.className = 'row mb-3 download-item';
                div.innerHTML = `
                    <div class="col-md-3">
                        <label class="form-label">File</label>
                        <input type="file" class="form-control" name="download_files[]">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Title</label>
                        <input type="text" class="form-control" name="download_title[]">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Description</label>
                        <input type="text" class="form-control" name="download_description[]">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Alt Text</label>
                        <input type="text" class="form-control" name="download_alt_text[]">
                    </div>
                    <div class="col-md-1">
                        <label class="form-label">&nbsp;</label>
                        <button type="button" class="btn btn-outline-danger d-block" onclick="removeDownloadItem(this)">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                container.appendChild(div);
            }
            
            function removeDownloadItem(button) {
                button.closest('.download-item').remove();
            }
        </script>
    </body>
    </html>
    ''', categories=categories)

@app.route('/content/edit/<int:page_id>', methods=['GET', 'POST'])
@login_required
def edit_content_page(page_id):
    page = ContentPage.query.get_or_404(page_id)
    
    if request.method == 'POST':
        # Update basic information
        page.title = request.form.get('title')
        page.status = request.form.get('status')
        page.category_id = request.form.get('category_id')
        page.subcategory_id = request.form.get('subcategory_id') if request.form.get('subcategory_id') else None
        page.short_description = request.form.get('short_description')
        page.long_description = request.form.get('long_description')
        
        # Handle date fields
        created_date = request.form.get('created_date')
        if created_date:
            try:
                page.creation_date = datetime.strptime(created_date, '%Y-%m-%d')
            except ValueError:
                pass  # Keep existing if invalid date
        
        approved_date = request.form.get('approved_date')
        if approved_date:
            try:
                page.approval_date = datetime.strptime(approved_date, '%Y-%m-%d')
            except ValueError:
                pass  # Keep existing if invalid date
        else:
            page.approval_date = None
        
        next_review_date = request.form.get('next_review_date')
        if next_review_date:
            try:
                page.next_review_date = datetime.strptime(next_review_date, '%Y-%m-%d')
            except ValueError:
                pass  # Keep existing if invalid date
        else:
            page.next_review_date = None
        
        db.session.commit()
        flash('Content page updated successfully!', 'success')
        return redirect(url_for('content_pages_list'))
    
    # GET request - show form with existing data
    categories = ContentCategory.query.filter_by(is_active=True).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Content Page - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <script src="https://cdn.quilljs.com/1.3.6/quill.min.js"></script>
        <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>✏️ Edit Content Page</h1>
                <a href="/content/pages" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Pages
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST" enctype="multipart/form-data">
                <!-- Basic Information -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5><i class="fas fa-info-circle me-2"></i>Basic Information</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Page Title *</label>
                                    <input type="text" class="form-control" name="title" value="{{ page.title }}" required>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Status</label>
                                    <select class="form-select" name="status">
                                        <option value="Draft" {{ 'selected' if page.status == 'Draft' else '' }}>Draft</option>
                                        <option value="Published" {{ 'selected' if page.status == 'Published' else '' }}>Published</option>
                                        <option value="Archived" {{ 'selected' if page.status == 'Archived' else '' }}>Archived</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Category *</label>
                                    <select class="form-select" name="category_id" id="categorySelect" onchange="loadSubcategories()" required>
                                        <option value="">Select Category</option>
                                        {% for category in categories %}
                                        <option value="{{ category.id }}" {{ 'selected' if page.category_id == category.id else '' }}>{{ category.name }}</option>
                                        {% endfor %}
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Subcategory</label>
                                    <select class="form-select" name="subcategory_id" id="subcategorySelect">
                                        <option value="">Select Subcategory</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Short Description</label>
                            <textarea class="form-control" name="short_description" rows="3" placeholder="Brief summary of the page content">{{ page.short_description or '' }}</textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Long Description</label>
                            <div id="longDescription" style="height: 300px;"></div>
                            <input type="hidden" name="long_description" id="longDescriptionInput" value="{{ page.long_description or '' }}">
                        </div>
                    </div>
                </div>
                
                <!-- Date Information -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5><i class="fas fa-calendar me-2"></i>Date Information</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Created Date</label>
                                    <input type="date" class="form-control" name="created_date" value="{{ page.creation_date.strftime('%Y-%m-%d') if page.creation_date else '' }}">
                                    <div class="form-text">Date when this content was originally created</div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Approved Date</label>
                                    <input type="date" class="form-control" name="approved_date" value="{{ page.approval_date.strftime('%Y-%m-%d') if page.approval_date else '' }}">
                                    <div class="form-text">Date when this content was approved for publication</div>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Next Review Date</label>
                                    <input type="date" class="form-control" name="next_review_date" value="{{ page.next_review_date.strftime('%Y-%m-%d') if page.next_review_date else '' }}">
                                    <div class="form-text">Set a date when this content should be reviewed for updates</div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Last Updated</label>
                                    <input type="text" class="form-control" value="{{ page.updated_at.strftime('%Y-%m-%d %H:%M') if page.updated_at else '' }}" readonly>
                                    <div class="form-text">Automatically updated when content is saved</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save me-2"></i>Update Page
                    </button>
                    <a href="/content/pages" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Initialize Quill.js with existing content
            var quill = new Quill('#longDescription', {
                theme: 'snow',
                modules: {
                    toolbar: [
                        [{ 'header': [1, 2, 3, false] }],
                        ['bold', 'italic', 'underline', 'strike'],
                        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                        [{ 'indent': '-1'}, { 'indent': '+1' }],
                        ['link', 'image'],
                        [{ 'align': [] }],
                        ['clean']
                    ]
                }
            });
            
            // Set existing content
            var existingContent = document.getElementById('longDescriptionInput').value;
            if (existingContent) {
                quill.root.innerHTML = existingContent;
            }
            
            // Update hidden input when content changes
            quill.on('text-change', function() {
                document.getElementById('longDescriptionInput').value = quill.root.innerHTML;
            });
            
            // Update hidden input before form submission
            document.querySelector('form').addEventListener('submit', function() {
                document.getElementById('longDescriptionInput').value = quill.root.innerHTML;
            });
            
            // Category/Subcategory handling
            const subcategoriesData = {
                {% for category in categories %}
                {{ category.id }}: [
                    {% for subcategory in category.subcategories %}
                    {id: {{ subcategory.id }}, name: "{{ subcategory.name }}"}{{ "," if not loop.last }}
                    {% endfor %}
                ]{{ "," if not loop.last }}
                {% endfor %}
            };
            
            function loadSubcategories() {
                const categoryId = document.getElementById('categorySelect').value;
                const subcategorySelect = document.getElementById('subcategorySelect');
                
                subcategorySelect.innerHTML = '<option value="">Select Subcategory</option>';
                
                if (categoryId && subcategoriesData[categoryId]) {
                    subcategoriesData[categoryId].forEach(sub => {
                        const option = document.createElement('option');
                        option.value = sub.id;
                        option.textContent = sub.name;
                        {% if page.subcategory_id %}
                        if (sub.id == {{ page.subcategory_id }}) {
                            option.selected = true;
                        }
                        {% endif %}
                        subcategorySelect.appendChild(option);
                    });
                }
            }
            
            // Load subcategories on page load
            loadSubcategories();
        </script>
    </body>
    </html>
    ''', page=page, categories=categories)

@app.route('/content/view/<int:page_id>')
@login_required
def view_content_page(page_id):
    page = ContentPage.query.get_or_404(page_id)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ page.title }} - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .content-view {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 2rem;
            }
            .status-badge {
                font-size: 0.875rem;
                padding: 0.375rem 0.75rem;
            }
            .gallery-item {
                margin-bottom: 1rem;
            }
            .gallery-item img {
                max-width: 200px;
                height: auto;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
            </div>
            <div class="mt-auto p-3 border-top">
                <a href="/logout" class="nav-link text-danger">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>

        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h2><i class="fas fa-eye me-2"></i>View Content Page</h2>
                    <nav aria-label="breadcrumb">
                        <ol class="breadcrumb">
                            <li class="breadcrumb-item"><a href="/content">Content</a></li>
                            <li class="breadcrumb-item"><a href="/content/pages">All Pages</a></li>
                            <li class="breadcrumb-item active">{{ page.title }}</li>
                        </ol>
                    </nav>
                </div>
                <div>
                    <a href="/content/edit/{{ page.id }}" class="btn btn-primary">
                        <i class="fas fa-edit me-2"></i>Edit Page
                    </a>
                    <a href="/content/pages" class="btn btn-secondary">
                        <i class="fas fa-arrow-left me-2"></i>Back to Pages
                    </a>
                </div>
            </div>

            <div class="content-view">
                <!-- Basic Information -->
                <div class="row mb-4">
                    <div class="col-md-8">
                        <h1>{{ page.title }}</h1>
                        <p class="text-muted mb-3">{{ page.short_description or 'No short description provided.' }}</p>
                    </div>
                    <div class="col-md-4 text-end">
                        <span class="badge status-badge {% if page.status == 'Published' %}bg-success{% elif page.status == 'Draft' %}bg-warning{% else %}bg-secondary{% endif %}">
                            {{ page.status }}
                        </span>
                    </div>
                </div>

                <!-- Content -->
                <div class="mb-4">
                    <h3>Content</h3>
                    <div class="border-start border-primary ps-3">
                        {{ page.long_description|safe if page.long_description else '<p class="text-muted">No content provided.</p>'|safe }}
                    </div>
                </div>

                <!-- Metadata -->
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h4>Category Information</h4>
                        <ul class="list-unstyled">
                            <li><strong>Category:</strong> {{ page.category.name if page.category else 'Uncategorized' }}</li>
                            <li><strong>Subcategory:</strong> {{ page.subcategory.name if page.subcategory else 'None' }}</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h4>Date Information</h4>
                        <ul class="list-unstyled">
                            <li><strong>Created:</strong> {{ page.creation_date.strftime('%d/%m/%Y') if page.creation_date else 'Not set' }}</li>
                            <li><strong>Approved:</strong> {{ page.approval_date.strftime('%d/%m/%Y') if page.approval_date else 'Not approved' }}</li>
                            <li><strong>Last Updated:</strong> {{ page.updated_at.strftime('%d/%m/%Y %H:%M') if page.updated_at else 'Never' }}</li>
                            <li><strong>Next Review:</strong> {{ page.next_review_date.strftime('%d/%m/%Y') if page.next_review_date else 'Not scheduled' }}</li>
                        </ul>
                    </div>
                </div>

                <!-- Gallery -->
                {% if page.gallery_images %}
                <div class="mb-4">
                    <h4>Photo Gallery</h4>
                    <div class="row">
                        {% for item in page.gallery_images %}
                        <div class="col-md-4 gallery-item">
                            <div class="card">
                                <img src="/uploads/content/images/{{ item.filename }}" class="card-img-top" alt="{{ item.alt_text or item.title }}">
                                <div class="card-body">
                                    <h6 class="card-title">{{ item.title or 'Untitled' }}</h6>
                                    <p class="card-text small">{{ item.description or '' }}</p>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}

                <!-- Related Links -->
                {% if page.related_links %}
                <div class="mb-4">
                    <h4>Related Links</h4>
                    <ul class="list-group">
                        {% for link in page.related_links %}
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <a href="{{ link.url }}" {% if link.new_tab %}target="_blank"{% endif %} class="fw-bold">
                                    {{ link.title }}
                                    {% if link.new_tab %}<i class="fas fa-external-link-alt ms-1 small"></i>{% endif %}
                                </a>
                            </div>
                        </li>
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}

                <!-- Downloads -->
                {% if page.downloads %}
                <div class="mb-4">
                    <h4>Downloads</h4>
                    <ul class="list-group">
                        {% for download in page.downloads %}
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <a href="/uploads/content/downloads/{{ download.filename }}" class="fw-bold" download>
                                    <i class="fas fa-download me-2"></i>{{ download.title }}
                                </a>
                                {% if download.description %}
                                <div class="text-muted small">{{ download.description }}</div>
                                {% endif %}
                            </div>
                        </li>
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', page=page)

@app.route('/events')
@login_required
def events_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    
    query = Event.query
    
    if search:
        query = query.filter(Event.title.contains(search))
    if category_filter:
        query = query.filter_by(category_id=category_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    events = query.order_by(Event.start_date.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    categories = EventCategory.query.filter_by(is_active=True).all()
    
    # Get statistics
    total_events = Event.query.count()
    upcoming_events = Event.query.filter(Event.start_date > datetime.utcnow(), Event.is_published == True).count()
    published_events = Event.query.filter_by(is_published=True).count()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Events & Things to Do - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .event-card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
                margin-bottom: 1rem;
            }
            .event-card:hover {
                transform: translateY(-2px);
            }
            .stat-card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }
            .stat-card:hover {
                transform: translateY(-5px);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link active">
                    <i class="fas fa-calendar me-2"></i>Events & Things to Do
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📅 Events & Things to Do</h1>
                <div>
                    <a href="/events/categories" class="btn btn-outline-primary me-2">
                        <i class="fas fa-list me-2"></i>Manage Categories
                    </a>
                    <a href="/events/add" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Add New Event
                    </a>
                </div>
            </div>
            
            <!-- Statistics Cards -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="stat-card p-4 text-center">
                        <div class="text-primary mb-2">
                            <i class="fas fa-calendar fa-2x"></i>
                        </div>
                        <h3 class="mb-1">{{ total_events }}</h3>
                        <p class="text-muted mb-0">Total Events</p>
                        <small class="text-success">{{ published_events }} published</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card p-4 text-center">
                        <div class="text-warning mb-2">
                            <i class="fas fa-clock fa-2x"></i>
                        </div>
                        <h3 class="mb-1">{{ upcoming_events }}</h3>
                        <p class="text-muted mb-0">Upcoming Events</p>
                        <small class="text-info">Next 30 days</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card p-4 text-center">
                        <div class="text-info mb-2">
                            <i class="fas fa-list fa-2x"></i>
                        </div>
                        <h3 class="mb-1">{{ categories|length }}</h3>
                        <p class="text-muted mb-0">Event Categories</p>
                        <small class="text-success">Active categories</small>
                    </div>
                </div>
            </div>
            
            <!-- Search and Filters -->
            <div class="card mb-4">
                <div class="card-body">
                    <form method="GET" class="row g-3">
                        <div class="col-md-4">
                            <input type="text" class="form-control" name="search" 
                                   placeholder="Search events..." value="{{ request.args.get('search', '') }}">
                        </div>
                        <div class="col-md-3">
                            <select class="form-select" name="category">
                                <option value="">All Categories</option>
                                {% for category in categories %}
                                <option value="{{ category.id }}" 
                                        {{ 'selected' if request.args.get('category') == category.id|string }}>
                                    {{ category.name }}
                                </option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-3">
                            <select class="form-select" name="status">
                                <option value="">All Status</option>
                                <option value="Draft" {{ 'selected' if request.args.get('status') == 'Draft' }}>Draft</option>
                                <option value="Published" {{ 'selected' if request.args.get('status') == 'Published' }}>Published</option>
                                <option value="Cancelled" {{ 'selected' if request.args.get('status') == 'Cancelled' }}>Cancelled</option>
                            </select>
                        </div>
                        <div class="col-md-2">
                            <button type="submit" class="btn btn-outline-primary w-100">
                                <i class="fas fa-search"></i> Filter
                            </button>
                        </div>
                    </form>
                </div>
            </div>
            
            <!-- Events List -->
            {% if events.items %}
            <div class="row">
                {% for event in events.items %}
                <div class="col-md-6">
                    <div class="event-card">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-3">
                                <h5 class="card-title mb-0">{{ event.title }}</h5>
                                <div class="dropdown">
                                    <button class="btn btn-sm btn-outline-secondary dropdown-toggle" 
                                            data-bs-toggle="dropdown">
                                        <i class="fas fa-ellipsis-v"></i>
                                    </button>
                                    <ul class="dropdown-menu">
                                        <li><a class="dropdown-item" href="/events/edit/{{ event.id }}">
                                            <i class="fas fa-edit me-2"></i>Edit
                                        </a></li>
                                        <li><a class="dropdown-item" href="/events/view/{{ event.id }}">
                                            <i class="fas fa-eye me-2"></i>View
                                        </a></li>
                                        <li><hr class="dropdown-divider"></li>
                                        <li><a class="dropdown-item text-danger" href="/events/delete/{{ event.id }}"
                                               onclick="return confirm('Are you sure?')">
                                            <i class="fas fa-trash me-2"></i>Delete
                                        </a></li>
                                    </ul>
                                </div>
                            </div>
                            
                            <div class="mb-2">
                                <i class="fas fa-calendar me-2 text-primary"></i>
                                <strong>{{ event.start_date|uk_date }}</strong>
                                {% if not event.all_day %}
                                at {{ event.start_date.strftime('%H:%M') }}
                                {% endif %}
                            </div>
                            
                            {% if event.location_name %}
                            <div class="mb-2">
                                <i class="fas fa-map-marker-alt me-2 text-danger"></i>
                                {{ event.location_name }}
                            </div>
                            {% endif %}
                            
                            {% if event.category %}
                            <div class="mb-2">
                                <span class="badge" style="background-color: {{ event.category.color }};">
                                    <i class="{{ event.category.icon }} me-1"></i>
                                    {{ event.category.name }}
                                </span>
                            </div>
                            {% endif %}
                            
                            {% if event.description %}
                            <p class="text-muted mb-3">{{ event.description[:100] }}{% if event.description|length > 100 %}...{% endif %}</p>
                            {% endif %}
                            
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <span class="badge bg-{{ 'success' if event.status == 'Published' else 'warning' if event.status == 'Draft' else 'danger' }}">
                                        {{ event.status }}
                                    </span>
                                    {% if event.featured %}
                                    <span class="badge bg-info">Featured</span>
                                    {% endif %}
                                    {% if event.is_free %}
                                    <span class="badge bg-success">Free</span>
                                    {% endif %}
                                </div>
                                <small class="text-muted">
                                    Updated: {{ event.updated_at|uk_date }}
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <!-- Pagination -->
            {% if events.pages > 1 %}
            <nav aria-label="Events pagination">
                <ul class="pagination justify-content-center">
                    {% if events.has_prev %}
                    <li class="page-item">
                        <a class="page-link" href="{{ url_for('events_list', page=events.prev_num, 
                           search=request.args.get('search', ''), 
                           category=request.args.get('category', ''),
                           status=request.args.get('status', '')) }}">Previous</a>
                    </li>
                    {% endif %}
                    
                    {% for page_num in events.iter_pages() %}
                        {% if page_num %}
                            {% if page_num != events.page %}
                            <li class="page-item">
                                <a class="page-link" href="{{ url_for('events_list', page=page_num,
                                   search=request.args.get('search', ''), 
                                   category=request.args.get('category', ''),
                                   status=request.args.get('status', '')) }}">{{ page_num }}</a>
                            </li>
                            {% else %}
                            <li class="page-item active">
                                <span class="page-link">{{ page_num }}</span>
                            </li>
                            {% endif %}
                        {% else %}
                        <li class="page-item disabled">
                            <span class="page-link">...</span>
                        </li>
                        {% endif %}
                    {% endfor %}
                    
                    {% if events.has_next %}
                    <li class="page-item">
                        <a class="page-link" href="{{ url_for('events_list', page=events.next_num,
                           search=request.args.get('search', ''), 
                           category=request.args.get('category', ''),
                           status=request.args.get('status', '')) }}">Next</a>
                    </li>
                    {% endif %}
                </ul>
            </nav>
            {% endif %}
            
            {% else %}
            <div class="text-center py-5">
                <i class="fas fa-calendar fa-3x text-muted mb-3"></i>
                <h4>No Events Found</h4>
                <p class="text-muted">Start by creating your first event or adjust your search filters.</p>
                <a href="/events/add" class="btn btn-primary">
                    <i class="fas fa-plus me-2"></i>Create First Event
                </a>
            </div>
            {% endif %}
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', events=events, categories=categories, total_events=total_events, 
         upcoming_events=upcoming_events, published_events=published_events)

@app.route('/settings')
@login_required
def settings():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Settings - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link active">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="text-center">
                <div class="card">
                    <div class="card-body py-5">
                        <i class="fas fa-cog fa-3x text-muted mb-3"></i>
                        <h4>System Settings</h4>
                        <p class="text-muted">Settings management will be available in Phase 2</p>
                        <small class="text-muted">This will include site configuration, user management, and system preferences</small>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

# Event Management Routes (moved from after app.run)
@app.route('/events/add', methods=['GET', 'POST'])
@login_required
def add_event():
    if request.method == 'POST':
        # Handle form submission
        event = Event(
            title=request.form['title'],
            short_description=request.form.get('short_description'),
            description=request.form.get('description'),
            category_id=request.form.get('category_id') if request.form.get('category_id') else None,
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%dT%H:%M'),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%dT%H:%M') if request.form.get('end_date') else None,
            all_day=bool(request.form.get('all_day')),
            location_name=request.form.get('location_name'),
            location_address=request.form.get('location_address'),
            location_url=request.form.get('location_url'),
            contact_name=request.form.get('contact_name'),
            contact_email=request.form.get('contact_email'),
            contact_phone=request.form.get('contact_phone'),
            booking_required=bool(request.form.get('booking_required')),
            booking_url=request.form.get('booking_url'),
            max_attendees=int(request.form['max_attendees']) if request.form.get('max_attendees') else None,
            is_free=bool(request.form.get('is_free')),
            price=request.form.get('price'),
            featured=bool(request.form.get('featured')),
            status=request.form.get('status', 'Draft'),
            is_published=bool(request.form.get('is_published'))
        )
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = save_uploaded_file(file, 'events')
                event.image_filename = filename
        
        db.session.add(event)
        db.session.commit()
        
        # Handle multiple category assignments
        selected_categories = request.form.getlist('categories')
        for category_id in selected_categories:
            if category_id:
                assignment = EventCategoryAssignment(
                    event_id=event.id,
                    category_id=int(category_id)
                )
                db.session.add(assignment)
        
        # Handle gallery images
        gallery_files = request.files.getlist('gallery_images')
        gallery_titles = request.form.getlist('gallery_titles')
        gallery_descriptions = request.form.getlist('gallery_descriptions')
        gallery_alt_texts = request.form.getlist('gallery_alt_texts')
        
        for i, file in enumerate(gallery_files):
            if file and file.filename and allowed_file(file.filename):
                filename = save_uploaded_file(file, 'events/gallery')
                gallery_image = EventGallery(
                    event_id=event.id,
                    filename=filename,
                    title=gallery_titles[i] if i < len(gallery_titles) else '',
                    description=gallery_descriptions[i] if i < len(gallery_descriptions) else '',
                    alt_text=gallery_alt_texts[i] if i < len(gallery_alt_texts) else '',
                    sort_order=i
                )
                db.session.add(gallery_image)
        
        # Handle related links
        link_titles = request.form.getlist('link_titles')
        link_urls = request.form.getlist('link_urls')
        link_new_tabs = request.form.getlist('link_new_tabs')
        
        for i, title in enumerate(link_titles):
            if title.strip() and i < len(link_urls) and link_urls[i].strip():
                link = EventLink(
                    event_id=event.id,
                    title=title.strip(),
                    url=link_urls[i].strip(),
                    new_tab=str(i) in link_new_tabs,  # Checkbox values come as indices
                    sort_order=i
                )
                db.session.add(link)
        
        # Handle downloads
        download_files = request.files.getlist('download_files')
        download_titles = request.form.getlist('download_titles')
        download_descriptions = request.form.getlist('download_descriptions')
        
        for i, file in enumerate(download_files):
            if file and file.filename:
                filename = save_uploaded_file(file, 'events/downloads', 'download')
                if filename:
                    download_item = EventDownload(
                        event_id=event.id,
                        filename=filename,
                        title=download_titles[i] if i < len(download_titles) else file.filename,
                        description=download_descriptions[i] if i < len(download_descriptions) else '',
                        sort_order=i
                    )
                    db.session.add(download_item)
        
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('events_list'))
    
    categories = EventCategory.query.filter_by(is_active=True).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Event - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link active">
                    <i class="fas fa-calendar me-2"></i>Events & Things to Do
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📅 Add New Event</h1>
                <a href="/events" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Events
                </a>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Event Title *</label>
                                    <input type="text" class="form-control" name="title" required>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Description</label>
                                    <textarea class="form-control" name="description" rows="4" 
                                              placeholder="Describe the event..."></textarea>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Start Date & Time *</label>
                                            <input type="datetime-local" class="form-control" name="start_date" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">End Date & Time</label>
                                            <input type="datetime-local" class="form-control" name="end_date">
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="all_day" id="all_day">
                                        <label class="form-check-label" for="all_day">
                                            All Day Event
                                        </label>
                                    </div>
                                </div>
                                
                                <h5 class="mt-4 mb-3">📍 Location Details</h5>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Location Name</label>
                                            <input type="text" class="form-control" name="location_name" 
                                                   placeholder="e.g., Kesgrave Community Centre">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Google Maps URL</label>
                                            <input type="url" class="form-control" name="location_url" 
                                                   placeholder="https://maps.google.com/...">
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Location Address</label>
                                    <textarea class="form-control" name="location_address" rows="2" 
                                              placeholder="Full address..."></textarea>
                                </div>
                                
                                <h5 class="mt-4 mb-3">📞 Contact Information</h5>
                                <div class="row">
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Contact Name</label>
                                            <input type="text" class="form-control" name="contact_name">
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Contact Email</label>
                                            <input type="email" class="form-control" name="contact_email">
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Contact Phone</label>
                                            <input type="tel" class="form-control" name="contact_phone">
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Categories</label>
                                    <div class="border rounded p-3" style="max-height: 200px; overflow-y: auto;">
                                        {% for category in categories %}
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" name="categories" 
                                                   value="{{ category.id }}" id="cat_{{ category.id }}">
                                            <label class="form-check-label" for="cat_{{ category.id }}">
                                                {{ category.name }}
                                            </label>
                                        </div>
                                        {% endfor %}
                                    </div>
                                    <small class="text-muted">Select one or more categories</small>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Status</label>
                                    <select class="form-select" name="status">
                                        <option value="Draft">Draft</option>
                                        <option value="Published">Published</option>
                                        <option value="Cancelled">Cancelled</option>
                                    </select>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Event Image</label>
                                    <input type="file" class="form-control" name="image" accept="image/*">
                                    <small class="text-muted">JPG, PNG, GIF up to 16MB</small>
                                </div>
                                
                                <h6 class="mt-4 mb-3">🎫 Booking & Pricing</h6>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="is_free" id="is_free" checked>
                                        <label class="form-check-label" for="is_free">
                                            Free Event
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Price Details</label>
                                    <input type="text" class="form-control" name="price" 
                                           placeholder="e.g., £5 adults, £3 children">
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="booking_required" id="booking_required">
                                        <label class="form-check-label" for="booking_required">
                                            Booking Required
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Booking URL</label>
                                    <input type="url" class="form-control" name="booking_url" 
                                           placeholder="https://...">
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Max Attendees</label>
                                    <input type="number" class="form-control" name="max_attendees" min="1">
                                </div>
                                
                                <h6 class="mt-4 mb-3">⚙️ Options</h6>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="featured" id="featured">
                                        <label class="form-check-label" for="featured">
                                            Featured Event
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="is_published" id="is_published">
                                        <label class="form-check-label" for="is_published">
                                            Publish Immediately
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <hr>
                        <div class="d-flex justify-content-between">
                            <a href="/events" class="btn btn-secondary">Cancel</a>
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Create Event
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', categories=categories)

@app.route('/events/categories')
@login_required
def event_categories():
    categories = EventCategory.query.all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Event Categories - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .sidebar .nav-link { color: rgba(255,255,255,0.8); padding: 12px 20px; margin: 2px 0; border-radius: 8px; }
            .sidebar .nav-link:hover, .sidebar .nav-link.active { background: rgba(255,255,255,0.1); color: white; }
            .main-content { background: #f8f9fa; min-height: 100vh; }
            .category-card { border: none; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); transition: transform 0.2s; }
            .category-card:hover { transform: translateY(-2px); }
            .category-icon { width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <div class="col-md-2 sidebar">
                    <div class="p-3">
                        <h4 class="text-white mb-4"><i class="fas fa-building me-2"></i>Kesgrave CMS</h4>
                        <nav class="nav flex-column">
                            <a class="nav-link" href="/dashboard"><i class="fas fa-tachometer-alt me-2"></i>Dashboard</a>
                            <a class="nav-link" href="/councillors"><i class="fas fa-users me-2"></i>Councillors</a>
                            <a class="nav-link" href="/tags"><i class="fas fa-tags me-2"></i>Ward Tags</a>
                            <a class="nav-link" href="/content"><i class="fas fa-file-alt me-2"></i>Content</a>
                            <a class="nav-link active" href="/events"><i class="fas fa-calendar me-2"></i>Events & Things to Do</a>
                            <a class="nav-link" href="/settings"><i class="fas fa-cog me-2"></i>Settings</a>
                        </nav>
                    </div>
                </div>
                <div class="col-md-10 main-content">
                    <div class="p-4">
                        <div class="d-flex justify-content-between align-items-center mb-4">
                            <h1><i class="fas fa-list-alt me-2"></i>Event Categories</h1>
                            <div>
                                <a href="/events" class="btn btn-secondary me-2">
                                    <i class="fas fa-arrow-left me-2"></i>Back to Events
                                </a>
                                <button class="btn btn-primary">
                                    <i class="fas fa-plus me-2"></i>Add Category
                                </button>
                            </div>
                        </div>
                        
                        <div class="row">
                            {% for category in categories %}
                            <div class="col-md-4 mb-4">
                                <div class="card category-card">
                                    <div class="card-body">
                                        <div class="d-flex align-items-center mb-3">
                                            <div class="category-icon me-3" style="background-color: {{ category.color }};">
                                                <i class="{{ category.icon }}"></i>
                                            </div>
                                            <div>
                                                <h5 class="card-title mb-1">{{ category.name }}</h5>
                                                <small class="text-muted">{{ category.description }}</small>
                                            </div>
                                        </div>
                                        <div class="d-flex justify-content-between align-items-center">
                                            <span class="badge bg-primary">{{ category.events|length }} events</span>
                                            <div class="btn-group btn-group-sm">
                                                <button class="btn btn-outline-primary">
                                                    <i class="fas fa-edit"></i>
                                                </button>
                                                <button class="btn btn-outline-danger">
                                                    <i class="fas fa-trash"></i>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', categories=categories)

# File upload route
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Event Management Routes
@app.route('/events/view/<int:event_id>')
@login_required
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    category = EventCategory.query.get(event.category_id) if event.category_id else None
    
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{event.title} - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh;">
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-8 mx-auto">
                    <div class="card shadow-lg">
                        <div class="card-header bg-primary text-white">
                            <h2><i class="fas fa-calendar-alt me-2"></i>{event.title}</h2>
                            <a href="/events" class="btn btn-light btn-sm">
                                <i class="fas fa-arrow-left me-1"></i>Back to Events
                            </a>
                        </div>
                        <div class="card-body">
                            {f'<img src="/uploads/events/{event.image_filename}" class="img-fluid mb-3" alt="{event.title}">' if event.image_filename else ''}
                            <p><strong>Category:</strong> {category.name if category else 'None'}</p>
                            <p><strong>Date:</strong> {event.start_date.strftime('%d/%m/%Y %H:%M') if event.start_date else 'TBD'}</p>
                            {f'<p><strong>Location:</strong> {event.location_name}</p>' if event.location_name else ''}
                            <div class="mt-3">
                                <h5>Description</h5>
                                <p>{event.description or 'No description available.'}</p>
                            </div>
                            <div class="mt-3">
                                <a href="/events/edit/{event.id}" class="btn btn-warning">
                                    <i class="fas fa-edit me-1"></i>Edit Event
                                </a>
                                <a href="/events" class="btn btn-secondary">
                                    <i class="fas fa-list me-1"></i>All Events
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/events/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    categories = EventCategory.query.all()
    
    if request.method == 'POST':
        # Update event with form data
        event.title = request.form.get('title')
        event.description = request.form.get('description')
        event.category_id = request.form.get('category_id') if request.form.get('category_id') else None
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = str(int(time.time()))
                filename = f"{timestamp}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'events', filename))
                event.image_filename = filename
        
        # Handle dates
        start_date = request.form.get('start_date')
        if start_date:
            event.start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
        
        end_date = request.form.get('end_date')
        if end_date:
            event.end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
        
        event.all_day = 'all_day' in request.form
        event.location_name = request.form.get('location_name')
        event.location_address = request.form.get('location_address')
        event.location_url = request.form.get('location_url')
        event.contact_name = request.form.get('contact_name')
        event.contact_email = request.form.get('contact_email')
        event.contact_phone = request.form.get('contact_phone')
        event.booking_required = 'booking_required' in request.form
        event.booking_url = request.form.get('booking_url')
        event.max_attendees = int(request.form.get('max_attendees')) if request.form.get('max_attendees') else None
        event.is_free = 'is_free' in request.form
        event.price = request.form.get('price')
        event.featured = 'featured' in request.form
        event.status = request.form.get('status', 'draft')
        event.is_published = 'is_published' in request.form
        
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('events_list'))
    
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Event - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh;">
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-10 mx-auto">
                    <div class="card shadow-lg">
                        <div class="card-header bg-warning text-dark">
                            <h2><i class="fas fa-edit me-2"></i>Edit Event: {event.title}</h2>
                            <a href="/events" class="btn btn-dark btn-sm">
                                <i class="fas fa-arrow-left me-1"></i>Back to Events
                            </a>
                        </div>
                        <div class="card-body">
                            <form method="POST" enctype="multipart/form-data">
                                <div class="row">
                                    <div class="col-md-8">
                                        <div class="mb-3">
                                            <label class="form-label">Event Title</label>
                                            <input type="text" class="form-control" name="title" value="{event.title}" required>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Description</label>
                                            <textarea class="form-control" name="description" rows="4">{event.description or ''}</textarea>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Category</label>
                                            <select class="form-select" name="category_id">
                                                <option value="">Select Category</option>
                                                {''.join([f'<option value="{cat.id}" {"selected" if event.category_id == cat.id else ""}>{cat.name}</option>' for cat in categories])}
                                            </select>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Status</label>
                                            <select class="form-select" name="status">
                                                <option value="draft" {"selected" if event.status == "draft" else ""}>Draft</option>
                                                <option value="published" {"selected" if event.status == "published" else ""}>Published</option>
                                            </select>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Event Image</label>
                                            <input type="file" class="form-control" name="image" accept="image/*">
                                            {f'<small class="text-muted">Current: {event.image_filename}</small>' if event.image_filename else ''}
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Start Date & Time</label>
                                            <input type="datetime-local" class="form-control" name="start_date" 
                                                   value="{event.start_date.strftime('%Y-%m-%dT%H:%M') if event.start_date else ''}">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">End Date & Time</label>
                                            <input type="datetime-local" class="form-control" name="end_date"
                                                   value="{event.end_date.strftime('%Y-%m-%dT%H:%M') if event.end_date else ''}">
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="all_day" {"checked" if event.all_day else ""}>
                                        <label class="form-check-label">All Day Event</label>
                                    </div>
                                </div>
                                
                                <h5 class="mt-4">Location Details</h5>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Location Name</label>
                                            <input type="text" class="form-control" name="location_name" value="{event.location_name or ''}">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Google Maps URL</label>
                                            <input type="url" class="form-control" name="location_url" value="{event.location_url or ''}">
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Location Address</label>
                                    <textarea class="form-control" name="location_address" rows="2">{event.location_address or ''}</textarea>
                                </div>
                                
                                <h5 class="mt-4">Contact Information</h5>
                                <div class="row">
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Contact Name</label>
                                            <input type="text" class="form-control" name="contact_name" value="{event.contact_name or ''}">
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Contact Email</label>
                                            <input type="email" class="form-control" name="contact_email" value="{event.contact_email or ''}">
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Contact Phone</label>
                                            <input type="tel" class="form-control" name="contact_phone" value="{event.contact_phone or ''}">
                                        </div>
                                    </div>
                                </div>
                                
                                <h5 class="mt-4">Booking & Pricing</h5>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="form-check mb-3">
                                            <input class="form-check-input" type="checkbox" name="is_free" {"checked" if event.is_free else ""}>
                                            <label class="form-check-label">Free Event</label>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Price Details</label>
                                            <input type="text" class="form-control" name="price" value="{event.price or ''}" placeholder="e.g., £5 adults, £3 children">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="form-check mb-3">
                                            <input class="form-check-input" type="checkbox" name="booking_required" {"checked" if event.booking_required else ""}>
                                            <label class="form-check-label">Booking Required</label>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Booking URL</label>
                                            <input type="url" class="form-control" name="booking_url" value="{event.booking_url or ''}">
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Max Attendees</label>
                                            <input type="number" class="form-control" name="max_attendees" value="{event.max_attendees or ''}">
                                        </div>
                                    </div>
                                </div>
                                
                                <h5 class="mt-4">Options</h5>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="form-check mb-3">
                                            <input class="form-check-input" type="checkbox" name="featured" {"checked" if event.featured else ""}>
                                            <label class="form-check-label">Featured Event</label>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="form-check mb-3">
                                            <input class="form-check-input" type="checkbox" name="is_published" {"checked" if event.is_published else ""}>
                                            <label class="form-check-label">Publish Immediately</label>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mt-4">
                                    <button type="submit" class="btn btn-success btn-lg">
                                        <i class="fas fa-save me-2"></i>Update Event
                                    </button>
                                    <a href="/events" class="btn btn-secondary btn-lg ms-2">
                                        <i class="fas fa-times me-2"></i>Cancel
                                    </a>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/events/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Delete image file if exists
    if event.image_filename:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'events', event.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('events_list'))

@app.route('/events/categories/add', methods=['GET', 'POST'])
@login_required
def add_event_category():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        icon = request.form.get('icon', 'fas fa-calendar')
        color = request.form.get('color', '#007bff')
        
        category = EventCategory(
            name=name,
            description=description,
            icon=icon,
            color=color
        )
        
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully!', 'success')
        return redirect(url_for('event_categories'))
    
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Event Category - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh;">
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-6 mx-auto">
                    <div class="card shadow-lg">
                        <div class="card-header bg-success text-white">
                            <h2><i class="fas fa-plus me-2"></i>Add Event Category</h2>
                            <a href="/events/categories" class="btn btn-light btn-sm">
                                <i class="fas fa-arrow-left me-1"></i>Back to Categories
                            </a>
                        </div>
                        <div class="card-body">
                            <form method="POST">
                                <div class="mb-3">
                                    <label class="form-label">Category Name</label>
                                    <input type="text" class="form-control" name="name" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Description</label>
                                    <textarea class="form-control" name="description" rows="3"></textarea>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Icon (FontAwesome class)</label>
                                    <input type="text" class="form-control" name="icon" value="fas fa-calendar" placeholder="fas fa-calendar">
                                    <small class="text-muted">e.g., fas fa-music, fas fa-sports-ball, fas fa-graduation-cap</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Color</label>
                                    <input type="color" class="form-control" name="color" value="#007bff">
                                </div>
                                <button type="submit" class="btn btn-success">
                                    <i class="fas fa-save me-2"></i>Create Category
                                </button>
                                <a href="/events/categories" class="btn btn-secondary ms-2">
                                    <i class="fas fa-times me-2"></i>Cancel
                                </a>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/events/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_event_category(category_id):
    category = EventCategory.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        category.icon = request.form.get('icon')
        category.color = request.form.get('color')
        
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('event_categories'))
    
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Category - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh;">
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-6 mx-auto">
                    <div class="card shadow-lg">
                        <div class="card-header bg-warning text-dark">
                            <h2><i class="fas fa-edit me-2"></i>Edit Category: {category.name}</h2>
                            <a href="/events/categories" class="btn btn-dark btn-sm">
                                <i class="fas fa-arrow-left me-1"></i>Back to Categories
                            </a>
                        </div>
                        <div class="card-body">
                            <form method="POST">
                                <div class="mb-3">
                                    <label class="form-label">Category Name</label>
                                    <input type="text" class="form-control" name="name" value="{category.name}" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Description</label>
                                    <textarea class="form-control" name="description" rows="3">{category.description or ''}</textarea>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Icon (FontAwesome class)</label>
                                    <input type="text" class="form-control" name="icon" value="{category.icon or 'fas fa-calendar'}">
                                    <small class="text-muted">e.g., fas fa-music, fas fa-sports-ball, fas fa-graduation-cap</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Color</label>
                                    <input type="color" class="form-control" name="color" value="{category.color or '#007bff'}">
                                </div>
                                <button type="submit" class="btn btn-warning">
                                    <i class="fas fa-save me-2"></i>Update Category
                                </button>
                                <a href="/events/categories" class="btn btn-secondary ms-2">
                                    <i class="fas fa-times me-2"></i>Cancel
                                </a>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create sample data if none exists
        if Tag.query.count() == 0:
            sample_tags = [
                {'name': 'East Ward', 'color': '#e74c3c', 'description': 'East Ward representative'},
                {'name': 'West Ward', 'color': '#3498db', 'description': 'West Ward representative'},
                {'name': 'North Ward', 'color': '#27ae60', 'description': 'North Ward representative'},
                {'name': 'South Ward', 'color': '#f39c12', 'description': 'South Ward representative'},
                {'name': 'Planning Committee', 'color': '#9b59b6', 'description': 'Planning Committee member'},
                {'name': 'Finance Committee', 'color': '#34495e', 'description': 'Finance Committee member'},
                {'name': 'Mayor', 'color': '#e67e22', 'description': 'Mayor of Kesgrave'},
                {'name': 'Deputy Mayor', 'color': '#1abc9c', 'description': 'Deputy Mayor'}
            ]
            
            for tag_data in sample_tags:
                tag = Tag(**tag_data)
                db.session.add(tag)
            
            db.session.commit()
        
        # Create sample councillors if none exist
        if Councillor.query.count() == 0:
            sample_councillors = [
                {
                    'name': 'John Smith',
                    'title': 'Mayor',
                    'intro': 'Dedicated to serving the Kesgrave community with transparency and commitment.',
                    'bio': 'John has been serving the Kesgrave community for over 15 years. He is passionate about local development and environmental sustainability.',
                    'email': 'john.smith@kesgrave-tc.gov.uk',
                    'phone': '01473 625180',
                    'address': 'Kesgrave Town Hall, Main Road, Kesgrave, IP5 2BY',
                    'qualifications': 'BA Politics, Local Government Certificate',
                    'is_published': True
                },
                {
                    'name': 'Sarah Johnson',
                    'title': 'Deputy Mayor',
                    'intro': 'Focused on community services and youth development programs.',
                    'bio': 'Sarah brings extensive experience in community development and has been instrumental in establishing youth programs in Kesgrave.',
                    'email': 'sarah.johnson@kesgrave-tc.gov.uk',
                    'phone': '01473 625181',
                    'address': 'Kesgrave Town Hall, Main Road, Kesgrave, IP5 2BY',
                    'qualifications': 'MSc Community Development, Youth Work Diploma',
                    'is_published': True
                },
                {
                    'name': 'Michael Brown',
                    'title': 'Councillor',
                    'intro': 'Specializing in planning and development with focus on sustainable growth.',
                    'bio': 'Michael has a background in urban planning and is committed to ensuring sustainable development in Kesgrave.',
                    'email': 'michael.brown@kesgrave-tc.gov.uk',
                    'phone': '01473 625182',
                    'address': 'Kesgrave Town Hall, Main Road, Kesgrave, IP5 2BY',
                    'qualifications': 'BSc Urban Planning, RTPI Member',
                    'is_published': True
                },
                {
                    'name': 'Emma Wilson',
                    'title': 'Councillor',
                    'intro': 'Advocate for environmental policies and green initiatives.',
                    'bio': 'Emma is passionate about environmental protection and has led several green initiatives in the community.',
                    'email': 'emma.wilson@kesgrave-tc.gov.uk',
                    'phone': '01473 625183',
                    'address': 'Kesgrave Town Hall, Main Road, Kesgrave, IP5 2BY',
                    'qualifications': 'MSc Environmental Science, IEMA Member',
                    'is_published': True
                },
                {
                    'name': 'David Taylor',
                    'title': 'Councillor',
                    'intro': 'Finance committee chair with expertise in budget management.',
                    'bio': 'David brings financial expertise to the council and ensures responsible budget management for the community.',
                    'email': 'david.taylor@kesgrave-tc.gov.uk',
                    'phone': '01473 625184',
                    'address': 'Kesgrave Town Hall, Main Road, Kesgrave, IP5 2BY',
                    'qualifications': 'ACCA Qualified, MBA Finance',
                    'is_published': True
                }
            ]
            
            for councillor_data in sample_councillors:
                councillor = Councillor(**councillor_data)
                db.session.add(councillor)
            
            db.session.commit()
            
            # Assign tags to councillors
            councillors = Councillor.query.all()
            tags = Tag.query.all()
            
            # Assign specific tags to each councillor
            tag_assignments = [
                (0, [6, 0, 4]),  # John Smith: Mayor, East Ward, Planning Committee
                (1, [7, 1]),     # Sarah Johnson: Deputy Mayor, West Ward
                (2, [2, 4]),     # Michael Brown: North Ward, Planning Committee
                (3, [3]),        # Emma Wilson: South Ward
                (4, [0, 5])      # David Taylor: East Ward, Finance Committee
            ]
            
            for councillor_idx, tag_indices in tag_assignments:
                councillor = councillors[councillor_idx]
                for tag_idx in tag_indices:
                    if tag_idx < len(tags):
                        councillor_tag = CouncillorTag(councillor_id=councillor.id, tag_id=tags[tag_idx].id)
                        db.session.add(councillor_tag)
            
            db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=8027)


# Event Categories Management Route

# Initialize predefined meeting types
def init_meeting_types():
    """Initialize predefined meeting types"""
    with app.app_context():
        # Create predefined meeting types if they don't exist
        predefined_types = [
            {
                'name': 'Annual Town Meeting',
                'description': 'Annual meeting open to all residents',
                'color': '#e74c3c',
                'show_schedule_applications': False
            },
            {
                'name': 'Community and Recreation Committee',
                'description': 'Committee meetings for community and recreation matters',
                'color': '#2ecc71',
                'show_schedule_applications': False
            },
            {
                'name': 'Finance and Governance Committee',
                'description': 'Committee meetings for finance and governance matters',
                'color': '#f39c12',
                'show_schedule_applications': False
            },
            {
                'name': 'Full Council Meeting',
                'description': 'Full council meetings with all councillors',
                'color': '#3498db',
                'show_schedule_applications': False
            },
            {
                'name': 'Planning and Development Committee',
                'description': 'Committee meetings for planning and development matters',
                'color': '#9b59b6',
                'show_schedule_applications': True  # This type shows Schedule of Applications
            }
        ]
        
        for type_data in predefined_types:
            # Check if meeting type already exists
            existing_type = MeetingType.query.filter_by(name=type_data['name']).first()
            if not existing_type:
                meeting_type = MeetingType(
                    name=type_data['name'],
                    description=type_data['description'],
                    color=type_data['color'],
                    show_schedule_applications=type_data['show_schedule_applications'],
                    is_predefined=True,
                    is_active=True
                )
                db.session.add(meeting_type)
        
        db.session.commit()

# Initialize predefined content categories and subcategories
def init_content_categories():
    """Initialize predefined content categories and subcategories"""
    with app.app_context():
        # Create predefined categories if they don't exist
        predefined_categories = [
            {
                'name': 'News',
                'url_path': '/news',
                'description': 'Latest news and announcements',
                'color': '#e74c3c',
                'subcategories': []
            },
            {
                'name': 'Council Information',
                'url_path': '/council-information',
                'description': 'Information about the council and its operations',
                'color': '#3498db',
                'subcategories': []
            },
            {
                'name': 'Meetings',
                'url_path': '/meetings',
                'description': 'Meeting information and documents',
                'color': '#9b59b6',
                'subcategories': [
                    {'name': 'Annual Town Meetings', 'url_path': '/annual-town-meetings'},
                    {'name': 'Community and Recreation', 'url_path': '/community-and-recreation'},
                    {'name': 'Finance and Governance', 'url_path': '/finance-and-governance'},
                    {'name': 'Full Council Meetings', 'url_path': '/full-council-meetings'},
                    {'name': 'Planning and Development', 'url_path': '/planning-and-development'}
                ]
            },
            {
                'name': 'Financial Information',
                'url_path': '/financial-information',
                'description': 'Budget, accounts, and financial transparency',
                'color': '#f39c12',
                'subcategories': []
            },
            {
                'name': 'Reporting Problems',
                'url_path': '/reporting-problems',
                'description': 'How to report issues and problems',
                'color': '#e67e22',
                'subcategories': []
            }
        ]
        
        for cat_data in predefined_categories:
            # Check if category already exists
            existing_cat = ContentCategory.query.filter_by(url_path=cat_data['url_path']).first()
            if not existing_cat:
                category = ContentCategory(
                    name=cat_data['name'],
                    url_path=cat_data['url_path'],
                    description=cat_data['description'],
                    color=cat_data['color'],
                    is_predefined=True,
                    is_active=True
                )
                db.session.add(category)
                db.session.flush()  # Get the ID
                
                # Add subcategories
                for sub_data in cat_data['subcategories']:
                    subcategory = ContentSubcategory(
                        name=sub_data['name'],
                        url_path=sub_data['url_path'],
                        category_id=category.id,
                        is_predefined=True,
                        is_active=True
                    )
                    db.session.add(subcategory)
        
        db.session.commit()

# Add sample data initialization for events
def init_sample_events():
    """Initialize sample event categories and events"""
    with app.app_context():
        # Create sample event categories if none exist
        if EventCategory.query.count() == 0:
            categories = [
                EventCategory(name='Community Events', description='Local community gatherings and celebrations', color='#e74c3c', icon='fas fa-users'),
                EventCategory(name='Council Meetings', description='Official council meetings and public sessions', color='#3498db', icon='fas fa-gavel'),
                EventCategory(name='Sports & Recreation', description='Sports events and recreational activities', color='#2ecc71', icon='fas fa-futbol'),
                EventCategory(name='Arts & Culture', description='Cultural events, exhibitions, and performances', color='#9b59b6', icon='fas fa-palette'),
                EventCategory(name='Education & Training', description='Educational workshops and training sessions', color='#f39c12', icon='fas fa-graduation-cap'),
                EventCategory(name='Environment', description='Environmental initiatives and green events', color='#27ae60', icon='fas fa-leaf')
            ]
            
            for category in categories:
                db.session.add(category)
            
            db.session.commit()
            
            # Create sample events
            sample_events = [
                Event(
                    title='Annual Summer Fair',
                    description='Join us for our annual summer fair with stalls, games, and entertainment for all the family.',
                    category_id=1,  # Community Events
                    start_date=datetime(2025, 7, 15, 10, 0),
                    end_date=datetime(2025, 7, 15, 16, 0),
                    location_name='Kesgrave Community Centre',
                    location_address='Main Road, Kesgrave, IP5 2PB',
                    contact_name='Sarah Johnson',
                    contact_email='events@kesgrave.gov.uk',
                    contact_phone='01473 123456',
                    is_free=True,
                    featured=True,
                    status='Published',
                    is_published=True
                ),
                Event(
                    title='Town Council Meeting',
                    description='Monthly town council meeting open to the public.',
                    category_id=2,  # Council Meetings
                    start_date=datetime(2025, 7, 3, 19, 30),
                    end_date=datetime(2025, 7, 3, 21, 0),
                    location_name='Council Chambers',
                    location_address='Kesgrave Town Hall, IP5 2PB',
                    contact_name='Town Clerk',
                    contact_email='clerk@kesgrave.gov.uk',
                    is_free=True,
                    status='Published',
                    is_published=True
                ),
                Event(
                    title='Football Tournament',
                    description='Local football tournament for all age groups.',
                    category_id=3,  # Sports & Recreation
                    start_date=datetime(2025, 8, 10, 9, 0),
                    end_date=datetime(2025, 8, 10, 17, 0),
                    location_name='Kesgrave Sports Ground',
                    booking_required=True,
                    booking_url='https://kesgrave.gov.uk/book-football',
                    max_attendees=100,
                    price='£5 per team',
                    is_free=False,
                    status='Published',
                    is_published=True
                )
            ]
            
            for event in sample_events:
                db.session.add(event)
            
            db.session.commit()


# Main initialization function
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Initialize predefined meeting types
        init_meeting_types()
        
        # Initialize predefined content categories
        init_content_categories()
        
        # Initialize sample data
        init_sample_events()
        
        # Create sample tags if none exist
        if Tag.query.count() == 0:
            tags = [
                Tag(name='East Ward', color='#3498db', description='East Ward representatives'),
                Tag(name='West Ward', color='#e74c3c', description='West Ward representatives'),
                Tag(name='North Ward', color='#2ecc71', description='North Ward representatives'),
                Tag(name='South Ward', color='#f39c12', description='South Ward representatives'),
                Tag(name='Central Ward', color='#9b59b6', description='Central Ward representatives'),
                Tag(name='Mayor', color='#e67e22', description='Mayor of Kesgrave'),
                Tag(name='Deputy Mayor', color='#34495e', description='Deputy Mayor'),
                Tag(name='Planning Committee', color='#16a085', description='Planning Committee members'),
                Tag(name='Finance Committee', color='#8e44ad', description='Finance Committee members'),
                Tag(name='Environment Committee', color='#27ae60', description='Environment Committee members')
            ]
            
            for tag in tags:
                db.session.add(tag)
            
            db.session.commit()
        
        # Create sample councillors if none exist
        if Councillor.query.count() == 0:
            councillors = [
                Councillor(
                    name='Neal Beecroft-Smith',
                    title='Mayor',
                    intro='Serving the community with dedication and transparency.',
                    bio='Neal has been serving Kesgrave for over 10 years, focusing on community development and environmental initiatives.',
                    email='neal.beecroft-smith@kesgrave.gov.uk',
                    phone='01473 123456',
                    qualifications='BSc Environmental Science, Local Government Certificate',
                    is_published=True
                ),
                Councillor(
                    name='Avtar Athwall',
                    title='Deputy Mayor',
                    intro='Committed to improving local services and community engagement.',
                    bio='Avtar brings extensive experience in local governance and community outreach programs.',
                    email='avtar.athwall@kesgrave.gov.uk',
                    phone='01473 123457',
                    qualifications='MA Public Administration',
                    is_published=True
                ),
                Councillor(
                    name='Sarah Johnson',
                    title='Councillor',
                    intro='Passionate about education and youth development.',
                    bio='Sarah has worked in education for 15 years and is dedicated to improving facilities for young people.',
                    email='sarah.johnson@kesgrave.gov.uk',
                    phone='01473 123458',
                    qualifications='MEd Educational Leadership',
                    is_published=True
                ),
                Councillor(
                    name='Michael Thompson',
                    title='Councillor',
                    intro='Focused on sustainable development and planning.',
                    bio='Michael chairs the Planning Committee and has expertise in sustainable urban development.',
                    email='michael.thompson@kesgrave.gov.uk',
                    phone='01473 123459',
                    qualifications='MSc Urban Planning',
                    is_published=True
                ),
                Councillor(
                    name='Emma Wilson',
                    title='Councillor',
                    intro='Advocate for community health and wellbeing.',
                    bio='Emma works to improve health services and promote community wellbeing initiatives.',
                    email='emma.wilson@kesgrave.gov.uk',
                    phone='01473 123460',
                    qualifications='BSc Public Health',
                    is_published=True
                )
            ]
            
            for councillor in councillors:
                db.session.add(councillor)
            
            db.session.commit()
            
            # Assign tags to councillors
            tags = Tag.query.all()
            councillors = Councillor.query.all()
            
            # Assign some sample tags to councillors
            tag_assignments = [
                (0, [0, 5]),  # Neal: East Ward, Mayor
                (1, [1, 6]),  # Avtar: West Ward, Deputy Mayor
                (2, [2, 9]),  # Sarah: North Ward, Environment Committee
                (3, [3, 7]),  # Michael: South Ward, Planning Committee
                (4, [4, 8])   # Emma: Central Ward, Finance Committee
            ]
            
            for councillor_idx, tag_indices in tag_assignments:
                councillor = councillors[councillor_idx]
                for tag_idx in tag_indices:
                    if tag_idx < len(tags):
                        councillor_tag = CouncillorTag(councillor_id=councillor.id, tag_id=tags[tag_idx].id)
                        db.session.add(councillor_tag)
            
            db.session.commit()
        
        # Create sample content categories if none exist
        if ContentCategory.query.count() == 0:
            categories = [
                ContentCategory(name='Planning', description='Planning applications and development', color='#3498db'),
                ContentCategory(name='Environment', description='Environmental policies and initiatives', color='#27ae60'),
                ContentCategory(name='Community', description='Community services and events', color='#e74c3c'),
                ContentCategory(name='Finance', description='Budget and financial information', color='#f39c12'),
                ContentCategory(name='Transport', description='Transport and highways', color='#9b59b6'),
                ContentCategory(name='Housing', description='Housing policies and development', color='#e67e22')
            ]
            
            for category in categories:
                db.session.add(category)
            
            db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=8027)


# Event Edit Route
@app.route('/events/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    if request.method == 'POST':
        # Update event with form data
        event.title = request.form['title']
        event.description = request.form.get('description')
        event.category_id = request.form.get('category_id') if request.form.get('category_id') else None
        event.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%dT%H:%M')
        event.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%dT%H:%M') if request.form.get('end_date') else None
        event.all_day = bool(request.form.get('all_day'))
        event.location_name = request.form.get('location_name')
        event.location_address = request.form.get('location_address')
        event.location_url = request.form.get('location_url')
        event.contact_name = request.form.get('contact_name')
        event.contact_email = request.form.get('contact_email')
        event.contact_phone = request.form.get('contact_phone')
        event.booking_required = bool(request.form.get('booking_required'))
        event.booking_url = request.form.get('booking_url')
        event.max_attendees = int(request.form['max_attendees']) if request.form.get('max_attendees') else None
        event.is_free = bool(request.form.get('is_free'))
        event.price = request.form.get('price')
        event.featured = bool(request.form.get('featured'))
        event.status = request.form.get('status', 'Draft')
        event.is_published = bool(request.form.get('is_published'))
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = save_uploaded_file(file, 'events')
                event.image_filename = filename
        
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('events_list'))
    
    categories = EventCategory.query.filter_by(is_active=True).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Event - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link active">
                    <i class="fas fa-calendar me-2"></i>Events & Things to Do
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>✏️ Edit Event: {{ event.title }}</h1>
                <a href="/events" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Events
                </a>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Event Title *</label>
                                    <input type="text" class="form-control" name="title" value="{{ event.title }}" required>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Description</label>
                                    <textarea class="form-control" name="description" rows="4" 
                                              placeholder="Describe the event...">{{ event.description or '' }}</textarea>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Start Date & Time *</label>
                                            <input type="datetime-local" class="form-control" name="start_date" 
                                                   value="{{ event.start_date.strftime('%Y-%m-%dT%H:%M') }}" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">End Date & Time</label>
                                            <input type="datetime-local" class="form-control" name="end_date"
                                                   value="{{ event.end_date.strftime('%Y-%m-%dT%H:%M') if event.end_date else '' }}">
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="all_day" id="all_day" 
                                               {{ 'checked' if event.all_day else '' }}>
                                        <label class="form-check-label" for="all_day">
                                            All Day Event
                                        </label>
                                    </div>
                                </div>
                                
                                <h5 class="mt-4 mb-3">📍 Location Details</h5>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Location Name</label>
                                            <input type="text" class="form-control" name="location_name" 
                                                   value="{{ event.location_name or '' }}"
                                                   placeholder="e.g., Kesgrave Community Centre">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Google Maps URL</label>
                                            <input type="url" class="form-control" name="location_url" 
                                                   value="{{ event.location_url or '' }}"
                                                   placeholder="https://maps.google.com/...">
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Location Address</label>
                                    <textarea class="form-control" name="location_address" rows="2" 
                                              placeholder="Full address...">{{ event.location_address or '' }}</textarea>
                                </div>
                                
                                <h5 class="mt-4 mb-3">📞 Contact Information</h5>
                                <div class="row">
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Contact Name</label>
                                            <input type="text" class="form-control" name="contact_name" 
                                                   value="{{ event.contact_name or '' }}">
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Contact Email</label>
                                            <input type="email" class="form-control" name="contact_email" 
                                                   value="{{ event.contact_email or '' }}">
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Contact Phone</label>
                                            <input type="tel" class="form-control" name="contact_phone" 
                                                   value="{{ event.contact_phone or '' }}">
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Category</label>
                                    <select class="form-select" name="category_id">
                                        <option value="">Select Category</option>
                                        {% for category in categories %}
                                        <option value="{{ category.id }}" {{ 'selected' if event.category_id == category.id else '' }}>
                                            {{ category.name }}
                                        </option>
                                        {% endfor %}
                                    </select>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Status</label>
                                    <select class="form-select" name="status">
                                        <option value="Draft" {{ 'selected' if event.status == 'Draft' else '' }}>Draft</option>
                                        <option value="Published" {{ 'selected' if event.status == 'Published' else '' }}>Published</option>
                                        <option value="Cancelled" {{ 'selected' if event.status == 'Cancelled' else '' }}>Cancelled</option>
                                    </select>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Event Image</label>
                                    {% if event.image_filename %}
                                    <div class="mb-2">
                                        <img src="/uploads/events/{{ event.image_filename }}" class="img-thumbnail" style="max-width: 200px;">
                                        <small class="d-block text-muted">Current image</small>
                                    </div>
                                    {% endif %}
                                    <input type="file" class="form-control" name="image" accept="image/*">
                                    <small class="text-muted">JPG, PNG, GIF up to 16MB (leave empty to keep current)</small>
                                </div>
                                
                                <h6 class="mt-4 mb-3">🎫 Booking & Pricing</h6>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="is_free" id="is_free" 
                                               {{ 'checked' if event.is_free else '' }}>
                                        <label class="form-check-label" for="is_free">
                                            Free Event
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Price Details</label>
                                    <input type="text" class="form-control" name="price" 
                                           value="{{ event.price or '' }}"
                                           placeholder="e.g., £5 adults, £3 children">
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="booking_required" id="booking_required"
                                               {{ 'checked' if event.booking_required else '' }}>
                                        <label class="form-check-label" for="booking_required">
                                            Booking Required
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Booking URL</label>
                                    <input type="url" class="form-control" name="booking_url" 
                                           value="{{ event.booking_url or '' }}"
                                           placeholder="https://...">
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Max Attendees</label>
                                    <input type="number" class="form-control" name="max_attendees" 
                                           value="{{ event.max_attendees or '' }}" min="1">
                                </div>
                                
                                <h6 class="mt-4 mb-3">⚙️ Options</h6>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="featured" id="featured"
                                               {{ 'checked' if event.featured else '' }}>
                                        <label class="form-check-label" for="featured">
                                            Featured Event
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="is_published" id="is_published"
                                               {{ 'checked' if event.is_published else '' }}>
                                        <label class="form-check-label" for="is_published">
                                            Published
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <hr>
                        <div class="d-flex justify-content-between">
                            <a href="/events" class="btn btn-secondary">Cancel</a>
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Update Event
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', event=event, categories=categories)

# Event Delete Route
@app.route('/events/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Delete associated image file if exists
    if event.image_filename:
        try:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'events', event.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
        except:
            pass  # Continue even if file deletion fails
    
    db.session.delete(event)
    db.session.commit()
    
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('events_list'))

# Event View All Route (enhanced)
@app.route('/events/all')
@login_required
def events_all():
    events = Event.query.order_by(Event.start_date.desc()).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>All Events - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .event-row:hover {
                background-color: #f8f9fa;
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link active">
                    <i class="fas fa-calendar me-2"></i>Events & Things to Do
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📅 All Events</h1>
                <div>
                    <a href="/events" class="btn btn-secondary me-2">
                        <i class="fas fa-arrow-left me-2"></i>Back to Events
                    </a>
                    <a href="/events/add" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Add New Event
                    </a>
                </div>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Event</th>
                                    <th>Date & Time</th>
                                    <th>Category</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for event in events %}
                                <tr class="event-row">
                                    <td>
                                        <div class="d-flex align-items-center">
                                            {% if event.image_filename %}
                                            <img src="/uploads/events/{{ event.image_filename }}" 
                                                 class="rounded me-3" style="width: 50px; height: 50px; object-fit: cover;">
                                            {% else %}
                                            <div class="bg-secondary rounded me-3 d-flex align-items-center justify-content-center" 
                                                 style="width: 50px; height: 50px;">
                                                <i class="fas fa-calendar text-white"></i>
                                            </div>
                                            {% endif %}
                                            <div>
                                                <h6 class="mb-1">{{ event.title }}</h6>
                                                {% if event.location_name %}
                                                <small class="text-muted">
                                                    <i class="fas fa-map-marker-alt me-1"></i>{{ event.location_name }}
                                                </small>
                                                {% endif %}
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        <div>
                                            <strong>{{ event.start_date.strftime('%d/%m/%Y') }}</strong>
                                            {% if not event.all_day %}
                                            <br><small class="text-muted">{{ event.start_date.strftime('%H:%M') }}</small>
                                            {% endif %}
                                        </div>
                                    </td>
                                    <td>
                                        {% if event.category %}
                                        <span class="badge" style="background-color: {{ event.category.color }};">
                                            {{ event.category.name }}
                                        </span>
                                        {% else %}
                                        <span class="badge bg-secondary">Uncategorized</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if event.status == 'Published' %}
                                        <span class="badge bg-success">{{ event.status }}</span>
                                        {% elif event.status == 'Draft' %}
                                        <span class="badge bg-warning">{{ event.status }}</span>
                                        {% else %}
                                        <span class="badge bg-danger">{{ event.status }}</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <div class="btn-group btn-group-sm">
                                            <a href="/events/edit/{{ event.id }}" class="btn btn-outline-primary">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            <button class="btn btn-outline-danger" 
                                                    onclick="deleteEvent({{ event.id }}, '{{ event.title }}')">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                        
                        {% if not events %}
                        <div class="text-center py-5">
                            <i class="fas fa-calendar-times fa-3x text-muted mb-3"></i>
                            <h5 class="text-muted">No events found</h5>
                            <p class="text-muted">Start by creating your first event.</p>
                            <a href="/events/add" class="btn btn-primary">
                                <i class="fas fa-plus me-2"></i>Add New Event
                            </a>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
        function deleteEvent(eventId, eventTitle) {
            if (confirm('Are you sure you want to delete "' + eventTitle + '"? This action cannot be undone.')) {
                fetch('/events/delete/' + eventId, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                }).then(response => {
                    if (response.ok) {
                        location.reload();
                    } else {
                        alert('Error deleting event');
                    }
                });
            }
        }
        </script>
    </body>
    </html>
    ''', events=events)


# ===== MEETINGS SECTION =====

@app.route('/meetings')
@login_required
def meetings_list():
    # Get filter parameters
    meeting_type_filter = request.args.get('type', '')
    
    # Build query
    query = Meeting.query.join(MeetingType)
    
    if meeting_type_filter:
        query = query.filter(Meeting.meeting_type_id == meeting_type_filter)
    
    # Order by date descending (most recent first)
    meetings = query.order_by(Meeting.meeting_date.desc(), Meeting.meeting_time.desc()).all()
    meeting_types = MeetingType.query.filter_by(is_active=True).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Meetings - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .meeting-row:hover {
                background-color: #f8f9fa;
            }
            .meeting-type-badge {
                font-size: 0.8em;
                padding: 0.25rem 0.5rem;
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/meetings" class="nav-link active">
                    <i class="fas fa-handshake me-2"></i>Meetings
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>🤝 Meetings Management</h1>
                <a href="/meetings/add" class="btn btn-primary">
                    <i class="fas fa-plus me-2"></i>Add Meeting
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <!-- Filters -->
            <div class="card mb-4">
                <div class="card-body">
                    <form method="GET" class="row g-3">
                        <div class="col-md-4">
                            <label class="form-label">Filter by Meeting Type</label>
                            <select class="form-select" name="type" onchange="this.form.submit()">
                                <option value="">All Meeting Types</option>
                                {% for type in meeting_types %}
                                <option value="{{ type.id }}" {{ 'selected' if request.args.get('type') == type.id|string else '' }}>
                                    {{ type.name }}
                                </option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-8 d-flex align-items-end">
                            <button type="submit" class="btn btn-outline-primary me-2">Apply Filter</button>
                            <a href="/meetings" class="btn btn-outline-secondary">Clear Filters</a>
                        </div>
                    </form>
                </div>
            </div>
            
            <!-- Meetings Table -->
            <div class="card">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>Meeting</th>
                                    <th>Type</th>
                                    <th>Date & Time</th>
                                    <th>Location</th>
                                    <th>Agenda</th>
                                    <th>Minutes</th>
                                    <th id="schedule-header" style="display: none;">Schedule of Applications</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for meeting in meetings %}
                                <tr class="meeting-row">
                                    <td>
                                        <strong>{{ meeting.title }}</strong>
                                        {% if meeting.notes %}
                                        <br><small class="text-muted">{{ meeting.notes[:100] }}{% if meeting.notes|length > 100 %}...{% endif %}</small>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <span class="badge meeting-type-badge" style="background-color: {{ meeting.meeting_type.color }};">
                                            {{ meeting.meeting_type.name }}
                                        </span>
                                    </td>
                                    <td>
                                        {{ meeting.meeting_date.strftime('%d %b %Y') }}<br>
                                        <small class="text-muted">{{ meeting.meeting_time.strftime('%H:%M') }}</small>
                                    </td>
                                    <td>{{ meeting.location or '-' }}</td>
                                    <td>
                                        {% if meeting.agenda_filename %}
                                        <a href="/uploads/meetings/{{ meeting.agenda_filename }}" target="_blank" class="btn btn-sm btn-outline-primary">
                                            <i class="fas fa-file-pdf me-1"></i>View
                                        </a>
                                        {% else %}
                                        <span class="text-muted">-</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if meeting.minutes_filename %}
                                        <a href="/uploads/meetings/{{ meeting.minutes_filename }}" target="_blank" class="btn btn-sm btn-outline-success">
                                            <i class="fas fa-file-pdf me-1"></i>View
                                        </a>
                                        {% else %}
                                        <span class="text-muted">-</span>
                                        {% endif %}
                                    </td>
                                    <td class="schedule-cell" style="display: none;">
                                        {% if meeting.meeting_type.show_schedule_applications %}
                                            {% if meeting.schedule_applications_filename %}
                                            <a href="/uploads/meetings/{{ meeting.schedule_applications_filename }}" target="_blank" class="btn btn-sm btn-outline-info">
                                                <i class="fas fa-file-pdf me-1"></i>View
                                            </a>
                                            {% else %}
                                            <span class="text-muted">-</span>
                                            {% endif %}
                                        {% else %}
                                        <span class="text-muted">N/A</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if meeting.status == 'Scheduled' %}
                                        <span class="badge bg-primary">{{ meeting.status }}</span>
                                        {% elif meeting.status == 'Completed' %}
                                        <span class="badge bg-success">{{ meeting.status }}</span>
                                        {% elif meeting.status == 'Cancelled' %}
                                        <span class="badge bg-danger">{{ meeting.status }}</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <div class="btn-group btn-group-sm">
                                            <a href="/meetings/edit/{{ meeting.id }}" class="btn btn-outline-primary">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            <button class="btn btn-outline-danger" onclick="deleteMeeting({{ meeting.id }}, '{{ meeting.title }}')">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                        
                        {% if not meetings %}
                        <div class="text-center py-5">
                            <i class="fas fa-handshake fa-3x text-muted mb-3"></i>
                            <h5 class="text-muted">No meetings found</h5>
                            <p class="text-muted">Start by creating your first meeting.</p>
                            <a href="/meetings/add" class="btn btn-primary">
                                <i class="fas fa-plus me-2"></i>Add New Meeting
                            </a>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Show/hide Schedule of Applications column based on meeting types
            function updateScheduleColumn() {
                const meetings = {{ meetings|tojson }};
                const showSchedule = meetings.some(meeting => meeting.meeting_type.show_schedule_applications);
                
                const header = document.getElementById('schedule-header');
                const cells = document.querySelectorAll('.schedule-cell');
                
                if (showSchedule) {
                    header.style.display = '';
                    cells.forEach(cell => cell.style.display = '');
                } else {
                    header.style.display = 'none';
                    cells.forEach(cell => cell.style.display = 'none');
                }
            }
            
            function deleteMeeting(meetingId, meetingTitle) {
                if (confirm('Are you sure you want to delete "' + meetingTitle + '"? This action cannot be undone.')) {
                    fetch('/meetings/delete/' + meetingId, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    }).then(response => {
                        if (response.ok) {
                            location.reload();
                        } else {
                            alert('Error deleting meeting');
                        }
                    });
                }
            }
            
            // Initialize on page load
            updateScheduleColumn();
        </script>
    </body>
    </html>
    ''', meetings=meetings, meeting_types=meeting_types, request=request)

@app.route('/meetings/add', methods=['GET', 'POST'])
@login_required
def add_meeting():
    if request.method == 'POST':
        # Handle form submission
        meeting = Meeting(
            title=request.form['title'],
            meeting_type_id=request.form['meeting_type_id'],
            meeting_date=datetime.strptime(request.form['meeting_date'], '%Y-%m-%d').date(),
            meeting_time=datetime.strptime(request.form['meeting_time'], '%H:%M').time(),
            location=request.form.get('location'),
            status=request.form.get('status', 'Scheduled'),
            is_published=bool(request.form.get('is_published')),
            notes=request.form.get('notes')
        )
        
        # Handle file uploads
        if 'agenda_file' in request.files:
            file = request.files['agenda_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'download')
                meeting.agenda_filename = filename
        
        if 'minutes_file' in request.files:
            file = request.files['minutes_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'download')
                meeting.minutes_filename = filename
        
        if 'schedule_applications_file' in request.files:
            file = request.files['schedule_applications_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'download')
                meeting.schedule_applications_filename = filename
        
        db.session.add(meeting)
        
        # Handle future meetings generation
        if request.form.get('generate_future'):
            frequency = request.form.get('frequency')  # monthly, quarterly, etc.
            count = int(request.form.get('future_count', 1))
            
            base_date = meeting.meeting_date
            for i in range(1, count + 1):
                if frequency == 'monthly':
                    future_date = base_date + relativedelta(months=i)
                elif frequency == 'quarterly':
                    future_date = base_date + relativedelta(months=i*3)
                elif frequency == 'yearly':
                    future_date = base_date + relativedelta(years=i)
                else:
                    continue
                
                future_meeting = Meeting(
                    title=meeting.title,
                    meeting_type_id=meeting.meeting_type_id,
                    meeting_date=future_date,
                    meeting_time=meeting.meeting_time,
                    location=meeting.location,
                    status='Scheduled',
                    is_published=meeting.is_published,
                    notes=meeting.notes
                )
                db.session.add(future_meeting)
        
        db.session.commit()
        flash('Meeting created successfully!', 'success')
        return redirect(url_for('meetings_list'))
    
    meeting_types = MeetingType.query.filter_by(is_active=True).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Meeting - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .section-card {
                border: none;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/meetings" class="nav-link active">
                    <i class="fas fa-handshake me-2"></i>Meetings
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>🤝 Add New Meeting</h1>
                <a href="/meetings" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Meetings
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST" enctype="multipart/form-data">
                <!-- Basic Information -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-info-circle me-2"></i>Basic Information</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Title *</label>
                                    <input type="text" class="form-control" name="title" required>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Status</label>
                                    <select class="form-select" name="status">
                                        <option value="Scheduled">Scheduled</option>
                                        <option value="Completed">Completed</option>
                                        <option value="Cancelled">Cancelled</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Type *</label>
                                    <select class="form-select" name="meeting_type_id" required onchange="updateScheduleField()">
                                        <option value="">Select Meeting Type</option>
                                        {% for type in meeting_types %}
                                        <option value="{{ type.id }}" data-show-schedule="{{ type.show_schedule_applications|lower }}">
                                            {{ type.name }}
                                        </option>
                                        {% endfor %}
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Date *</label>
                                    <input type="date" class="form-control" name="meeting_date" required>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Time *</label>
                                    <input type="time" class="form-control" name="meeting_time" required>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Location</label>
                                    <input type="text" class="form-control" name="location" placeholder="e.g., Council Chambers, Kesgrave Town Hall">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <div class="form-check mt-4">
                                        <input class="form-check-input" type="checkbox" name="is_published" id="is_published" checked>
                                        <label class="form-check-label" for="is_published">
                                            Publish Immediately
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Notes</label>
                            <textarea class="form-control" name="notes" rows="3" placeholder="Additional notes about the meeting"></textarea>
                        </div>
                    </div>
                </div>
                
                <!-- Documents -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-file-pdf me-2"></i>Meeting Documents</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Agenda (PDF)</label>
                                    <input type="file" class="form-control" name="agenda_file" accept=".pdf">
                                    <small class="text-muted">Upload meeting agenda</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Minutes (PDF)</label>
                                    <input type="file" class="form-control" name="minutes_file" accept=".pdf">
                                    <small class="text-muted">Upload meeting minutes</small>
                                </div>
                            </div>
                            <div class="col-md-4" id="schedule-field" style="display: none;">
                                <div class="mb-3">
                                    <label class="form-label">Schedule of Applications (PDF)</label>
                                    <input type="file" class="form-control" name="schedule_applications_file" accept=".pdf">
                                    <small class="text-muted">Upload schedule of applications</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Future Meetings Generator -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-calendar-plus me-2"></i>Generate Future Meetings</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="generate_future" id="generate_future" onchange="toggleFutureOptions()">
                                <label class="form-check-label" for="generate_future">
                                    Generate future meetings based on this one
                                </label>
                            </div>
                        </div>
                        
                        <div id="future-options" style="display: none;">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Frequency</label>
                                        <select class="form-select" name="frequency">
                                            <option value="monthly">Monthly</option>
                                            <option value="quarterly">Quarterly</option>
                                            <option value="yearly">Yearly</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Number of Future Meetings</label>
                                        <input type="number" class="form-control" name="future_count" min="1" max="12" value="3">
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Submit -->
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save me-2"></i>Create Meeting
                    </button>
                    <a href="/meetings" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function updateScheduleField() {
                const select = document.querySelector('select[name="meeting_type_id"]');
                const scheduleField = document.getElementById('schedule-field');
                
                if (select.value) {
                    const option = select.options[select.selectedIndex];
                    const showSchedule = option.getAttribute('data-show-schedule') === 'true';
                    scheduleField.style.display = showSchedule ? 'block' : 'none';
                } else {
                    scheduleField.style.display = 'none';
                }
            }
            
            function toggleFutureOptions() {
                const checkbox = document.getElementById('generate_future');
                const options = document.getElementById('future-options');
                options.style.display = checkbox.checked ? 'block' : 'none';
            }
        </script>
    </body>
    </html>
    ''', meeting_types=meeting_types)




@app.route('/meetings/edit/<int:meeting_id>', methods=['GET', 'POST'])
@login_required
def edit_meeting(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    
    if request.method == 'POST':
        # Update meeting details
        meeting.title = request.form['title']
        meeting.meeting_type_id = request.form['meeting_type_id']
        meeting.meeting_date = datetime.strptime(request.form['meeting_date'], '%Y-%m-%d').date()
        meeting.meeting_time = datetime.strptime(request.form['meeting_time'], '%H:%M').time()
        meeting.location = request.form.get('location')
        meeting.status = request.form.get('status', 'Scheduled')
        meeting.is_published = bool(request.form.get('is_published'))
        meeting.notes = request.form.get('notes')
        meeting.updated_at = datetime.utcnow()
        
        # Handle file uploads
        if 'agenda_file' in request.files:
            file = request.files['agenda_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'download')
                if filename:
                    meeting.agenda_filename = filename
        
        if 'minutes_file' in request.files:
            file = request.files['minutes_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'download')
                if filename:
                    meeting.minutes_filename = filename
        
        if 'schedule_applications_file' in request.files:
            file = request.files['schedule_applications_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'download')
                if filename:
                    meeting.schedule_applications_filename = filename
        
        db.session.commit()
        flash('Meeting updated successfully!', 'success')
        return redirect(url_for('meetings_list'))
    
    meeting_types = MeetingType.query.filter_by(is_active=True).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Meeting - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .section-card {
                border: none;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/meetings" class="nav-link active">
                    <i class="fas fa-handshake me-2"></i>Meetings
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>✏️ Edit Meeting: {{ meeting.title }}</h1>
                <a href="/meetings" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Meetings
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST" enctype="multipart/form-data">
                <!-- Basic Information -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-info-circle me-2"></i>Basic Information</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Title *</label>
                                    <input type="text" class="form-control" name="title" value="{{ meeting.title }}" required>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Status</label>
                                    <select class="form-select" name="status">
                                        <option value="Scheduled" {{ 'selected' if meeting.status == 'Scheduled' else '' }}>Scheduled</option>
                                        <option value="Completed" {{ 'selected' if meeting.status == 'Completed' else '' }}>Completed</option>
                                        <option value="Cancelled" {{ 'selected' if meeting.status == 'Cancelled' else '' }}>Cancelled</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Type *</label>
                                    <select class="form-select" name="meeting_type_id" required onchange="updateScheduleField()">
                                        <option value="">Select Meeting Type</option>
                                        {% for type in meeting_types %}
                                        <option value="{{ type.id }}" data-show-schedule="{{ type.show_schedule_applications|lower }}" {{ 'selected' if meeting.meeting_type_id == type.id else '' }}>
                                            {{ type.name }}
                                        </option>
                                        {% endfor %}
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Date *</label>
                                    <input type="date" class="form-control" name="meeting_date" value="{{ meeting.meeting_date.strftime('%Y-%m-%d') }}" required>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Time *</label>
                                    <input type="time" class="form-control" name="meeting_time" value="{{ meeting.meeting_time.strftime('%H:%M') }}" required>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Location</label>
                                    <input type="text" class="form-control" name="location" value="{{ meeting.location or '' }}" placeholder="e.g., Council Chambers, Kesgrave Town Hall">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <div class="form-check mt-4">
                                        <input class="form-check-input" type="checkbox" name="is_published" id="is_published" {{ 'checked' if meeting.is_published else '' }}>
                                        <label class="form-check-label" for="is_published">
                                            Published
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Notes</label>
                            <textarea class="form-control" name="notes" rows="3" placeholder="Additional notes about the meeting">{{ meeting.notes or '' }}</textarea>
                        </div>
                    </div>
                </div>
                
                <!-- Documents -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-file-pdf me-2"></i>Meeting Documents</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Agenda (PDF)</label>
                                    {% if meeting.agenda_filename %}
                                    <div class="mb-2">
                                        <small class="text-muted">Current: {{ meeting.agenda_filename }}</small>
                                        <a href="/uploads/meetings/{{ meeting.agenda_filename }}" target="_blank" class="btn btn-sm btn-outline-primary ms-2">
                                            <i class="fas fa-eye"></i> View
                                        </a>
                                    </div>
                                    {% endif %}
                                    <input type="file" class="form-control" name="agenda_file" accept=".pdf">
                                    <small class="text-muted">Upload new agenda to replace current</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Minutes (PDF)</label>
                                    {% if meeting.minutes_filename %}
                                    <div class="mb-2">
                                        <small class="text-muted">Current: {{ meeting.minutes_filename }}</small>
                                        <a href="/uploads/meetings/{{ meeting.minutes_filename }}" target="_blank" class="btn btn-sm btn-outline-success ms-2">
                                            <i class="fas fa-eye"></i> View
                                        </a>
                                    </div>
                                    {% endif %}
                                    <input type="file" class="form-control" name="minutes_file" accept=".pdf">
                                    <small class="text-muted">Upload new minutes to replace current</small>
                                </div>
                            </div>
                            <div class="col-md-4" id="schedule-field" style="display: {{ 'block' if meeting.meeting_type.show_schedule_applications else 'none' }};">
                                <div class="mb-3">
                                    <label class="form-label">Schedule of Applications (PDF)</label>
                                    {% if meeting.schedule_applications_filename %}
                                    <div class="mb-2">
                                        <small class="text-muted">Current: {{ meeting.schedule_applications_filename }}</small>
                                        <a href="/uploads/meetings/{{ meeting.schedule_applications_filename }}" target="_blank" class="btn btn-sm btn-outline-info ms-2">
                                            <i class="fas fa-eye"></i> View
                                        </a>
                                    </div>
                                    {% endif %}
                                    <input type="file" class="form-control" name="schedule_applications_file" accept=".pdf">
                                    <small class="text-muted">Upload new schedule to replace current</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Submit -->
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save me-2"></i>Update Meeting
                    </button>
                    <a href="/meetings" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function updateScheduleField() {
                const select = document.querySelector('select[name="meeting_type_id"]');
                const scheduleField = document.getElementById('schedule-field');
                
                if (select.value) {
                    const option = select.options[select.selectedIndex];
                    const showSchedule = option.getAttribute('data-show-schedule') === 'true';
                    scheduleField.style.display = showSchedule ? 'block' : 'none';
                } else {
                    scheduleField.style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    ''', meeting=meeting, meeting_types=meeting_types)

@app.route('/meetings/delete/<int:meeting_id>', methods=['POST'])
@login_required
def delete_meeting(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    
    # Delete associated files
    if meeting.agenda_filename:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'meetings', meeting.agenda_filename))
        except:
            pass
    
    if meeting.minutes_filename:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'meetings', meeting.minutes_filename))
        except:
            pass
    
    if meeting.schedule_applications_filename:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'meetings', meeting.schedule_applications_filename))
        except:
            pass
    
    db.session.delete(meeting)
    db.session.commit()
    
    flash('Meeting deleted successfully!', 'success')
    return redirect(url_for('meetings_list'))


