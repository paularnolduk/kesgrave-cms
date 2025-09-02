import os
from flask import Flask, render_template_string, redirect, url_for, request, flash, jsonify, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re
import json
import uuid
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)

# Configuration - ADAPTED FOR RENDER
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'kesgrave-cms-secret-key-2025')

# Database configuration - FIXED for Render deployment
if os.environ.get("RENDER"):
    # On Render, use a persistent SQLite database in /opt/render/project/src
    db_path = "/opt/render/project/src/kesgrave_working.db"
    uploads_path = "/opt/render/project/src/uploads"
    print(f"📁 Render environment detected, using database: {db_path}")
else:
    # Local development
    db_path = "kesgrave_working.db"
    uploads_path = "uploads"
    print(f"📁 Local environment, using database: {db_path}")

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = uploads_path
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Create upload directories
upload_dirs = ['councillors', 'content/images', 'content/downloads', 'events', 'meetings', 'homepage/logo', 'homepage/slides']
for upload_dir in upload_dirs:
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], upload_dir), exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Enable CORS for API endpoints
CORS(app, origins=[
    os.environ.get('FRONTEND_URL', 'http://localhost:3000'),
    'https://kesgrave-cms.onrender.com',
    'https://kesgravetowncouncil.onrender.com'
])

# User class for authentication
class AdminUser(UserMixin):
    def __init__(self, id, username='admin'):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    return AdminUser(user_id)

# Helper functions
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

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def allowed_image_file(filename):
    return allowed_file(filename, {'png', 'jpg', 'jpeg', 'gif', 'webp'})

def allowed_document_file(filename):
    return allowed_file(filename, {'pdf', 'doc', 'docx', 'txt'})

def save_uploaded_file(file, subfolder, file_type='image'):
    """Save uploaded file and return filename"""
    try:
        if file and file.filename:
            # Generate unique filename
            timestamp = int(datetime.now().timestamp())
            original_filename = secure_filename(file.filename)
            name, ext = os.path.splitext(original_filename)
            filename = f"{name}_{timestamp}{ext}"
            
            # Create full path
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
            os.makedirs(upload_path, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            
            print(f"✅ File saved: {file_path}")
            return filename
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        flash(f'Error uploading file: {str(e)}', 'error')
    return None

# Database Models
class Councillor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    image_filename = db.Column(db.String(255))
    is_published = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    twitter_url = db.Column(db.String(255))
    linkedin_url = db.Column(db.String(255))
    facebook_url = db.Column(db.String(255))
    instagram_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tags = db.relationship('Tag', secondary='councillor_tags', back_populates='councillors')

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(7), default='#007bff')  # Hex color
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    councillors = db.relationship('Councillor', secondary='councillor_tags', back_populates='tags')

# Association table for many-to-many relationship
councillor_tags = db.Table('councillor_tags',
    db.Column('councillor_id', db.Integer, db.ForeignKey('councillor.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    location = db.Column(db.String(200))
    image = db.Column(db.String(500))
    category_id = db.Column(db.Integer, db.ForeignKey('event_category.id'))
    is_featured = db.Column(db.Boolean, default=False)
    website_url = db.Column(db.String(500))
    booking_url = db.Column(db.String(500))
    price = db.Column(db.String(50))
    capacity = db.Column(db.Integer)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = db.relationship('EventCategory', back_populates='events')

class EventCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    color = db.Column(db.String(7), default='#007bff')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    events = db.relationship('Event', back_populates='category')

class MeetingType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    meetings = db.relationship('Meeting', back_populates='meeting_type')

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    meeting_date = db.Column(db.Date, nullable=False)
    meeting_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    meeting_type_id = db.Column(db.Integer, db.ForeignKey('meeting_type.id'), nullable=False)
    
    # File attachments
    agenda_filename = db.Column(db.String(255))
    minutes_filename = db.Column(db.String(255))
    draft_minutes_filename = db.Column(db.String(255))
    schedule_applications_filename = db.Column(db.String(255))
    
    # Boolean flags for frontend compatibility
    has_agenda = db.Column(db.Boolean, default=False)
    has_minutes = db.Column(db.Boolean, default=False)
    has_draft_minutes = db.Column(db.Boolean, default=False)
    has_schedule_applications = db.Column(db.Boolean, default=False)
    
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    meeting_type = db.relationship('MeetingType', back_populates='meetings')

class ContentCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    pages = db.relationship('ContentPage', back_populates='category')

class ContentPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('content_category.id'), nullable=False)
    is_published = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = db.relationship('ContentCategory', back_populates='pages')

class HomepageSlide(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    introduction = db.Column(db.Text)
    button_text = db.Column(db.String(100))
    button_url = db.Column(db.String(500))
    open_method = db.Column(db.String(20), default='same_tab')  # same_tab, new_tab
    image = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Sidebar CSS for admin interface
sidebar_css = '''
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

.sidebar .logo {
    padding: 1.5rem;
    text-align: center;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

.sidebar .nav-item {
    margin: 0.25rem 0;
}

.sidebar .nav-link {
    color: rgba(255,255,255,0.8);
    padding: 0.75rem 1.5rem;
    display: flex;
    align-items: center;
    text-decoration: none;
    transition: all 0.3s ease;
}

.sidebar .nav-link:hover {
    background: rgba(255,255,255,0.1);
    color: white;
}

.sidebar .nav-link.active {
    background: rgba(255,255,255,0.2);
    color: white;
}

.sidebar .nav-link i {
    margin-right: 0.75rem;
    width: 20px;
}

.main-content {
    margin-left: 260px;
    padding: 2rem;
    min-height: 100vh;
    background: #f8f9fa;
}

@media (max-width: 768px) {
    .sidebar {
        transform: translateX(-100%);
        transition: transform 0.3s ease;
    }
    
    .sidebar.show {
        transform: translateX(0);
    }
    
    .main-content {
        margin-left: 0;
    }
}
'''

# Common sidebar navigation
def get_sidebar_nav():
    return '''
    <div class="sidebar">
        <div class="logo">
            <h4>🏛️ Kesgrave CMS</h4>
            <small>Content Management</small>
        </div>
        <nav class="nav flex-column">
            <a class="nav-link" href="/dashboard">
                <i class="fas fa-tachometer-alt"></i>
                Dashboard
            </a>
            <a class="nav-link" href="/homepage">
                <i class="fas fa-home"></i>
                Homepage
            </a>
            <a class="nav-link" href="/councillors">
                <i class="fas fa-users"></i>
                Councillors
            </a>
            <a class="nav-link" href="/events">
                <i class="fas fa-calendar-alt"></i>
                Events
            </a>
            <a class="nav-link" href="/meetings">
                <i class="fas fa-gavel"></i>
                Meetings
            </a>
            <a class="nav-link" href="/content">
                <i class="fas fa-file-alt"></i>
                Content Pages
            </a>
            <div class="nav-item mt-4">
                <a class="nav-link" href="/logout">
                    <i class="fas fa-sign-out-alt"></i>
                    Logout
                </a>
            </div>
        </nav>
    </div>
    '''

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple authentication - admin/admin
        if username == 'admin' and password == 'admin':
            user = AdminUser(1)
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
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
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Username</label>
                        <input type="text" class="form-control" name="username" required value="admin">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" class="form-control" name="password" required value="admin">
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Login</button>
                </form>
                
                <div class="text-center mt-3">
                    <small class="text-muted">Default: admin / admin</small>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    total_councillors = Councillor.query.count()
    published_councillors = Councillor.query.filter_by(is_published=True).count()
    total_events = Event.query.count()
    total_meetings = Meeting.query.count()
    total_content_pages = ContentPage.query.count()
    total_slides = HomepageSlide.query.count()
    
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
            {{ sidebar_css|safe }}
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
        {{ sidebar_nav|safe }}
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>Dashboard</h1>
                <div class="text-muted">
                    <i class="fas fa-user"></i> Welcome, {{ current_user.username }}
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-4 mb-4">
                    <div class="stat-card p-4">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h3 class="text-primary mb-0">{{ total_councillors }}</h3>
                                <p class="text-muted mb-0">Councillors</p>
                                <small class="text-success">{{ published_councillors }} published</small>
                            </div>
                            <div class="text-primary">
                                <i class="fas fa-users fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="stat-card p-4">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h3 class="text-success mb-0">{{ total_events }}</h3>
                                <p class="text-muted mb-0">Events</p>
                            </div>
                            <div class="text-success">
                                <i class="fas fa-calendar-alt fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="stat-card p-4">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h3 class="text-info mb-0">{{ total_meetings }}</h3>
                                <p class="text-muted mb-0">Meetings</p>
                            </div>
                            <div class="text-info">
                                <i class="fas fa-gavel fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="stat-card p-4">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h3 class="text-warning mb-0">{{ total_content_pages }}</h3>
                                <p class="text-muted mb-0">Content Pages</p>
                            </div>
                            <div class="text-warning">
                                <i class="fas fa-file-alt fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="stat-card p-4">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h3 class="text-danger mb-0">{{ total_slides }}</h3>
                                <p class="text-muted mb-0">Homepage Slides</p>
                            </div>
                            <div class="text-danger">
                                <i class="fas fa-images fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Quick Actions</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3 mb-3">
                                    <a href="/homepage" class="btn btn-outline-primary w-100">
                                        <i class="fas fa-home"></i> Manage Homepage
                                    </a>
                                </div>
                                <div class="col-md-3 mb-3">
                                    <a href="/councillors/add" class="btn btn-outline-success w-100">
                                        <i class="fas fa-user-plus"></i> Add Councillor
                                    </a>
                                </div>
                                <div class="col-md-3 mb-3">
                                    <a href="/events/add" class="btn btn-outline-info w-100">
                                        <i class="fas fa-calendar-plus"></i> Add Event
                                    </a>
                                </div>
                                <div class="col-md-3 mb-3">
                                    <a href="/meetings/add" class="btn btn-outline-warning w-100">
                                        <i class="fas fa-plus"></i> Add Meeting
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', 
    sidebar_css=sidebar_css,
    sidebar_nav=get_sidebar_nav(),
    total_councillors=total_councillors,
    published_councillors=published_councillors,
    total_events=total_events,
    total_meetings=total_meetings,
    total_content_pages=total_content_pages,
    total_slides=total_slides)

# Health check endpoint
@app.route('/health')
def health_check():
    try:
        # Test database connection
        councillor_count = Councillor.query.count()
        event_count = Event.query.count()
        meeting_count = Meeting.query.count()
        slide_count = HomepageSlide.query.count()
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "database_path": db_path,
            "counts": {
                "councillors": councillor_count,
                "events": event_count,
                "meetings": meeting_count,
                "slides": slide_count
            },
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "database_path": db_path,
            "timestamp": datetime.utcnow().isoformat()
        }), 500

# API Endpoints for Frontend
@app.route('/api/homepage/slides', methods=['GET', 'OPTIONS'])
def api_homepage_slides():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response
    
    try:
        slides = HomepageSlide.query.filter_by(is_active=True).order_by(HomepageSlide.sort_order).all()
        
        slides_data = []
        for slide in slides:
            slides_data.append({
                "id": slide.id,
                "title": slide.title,
                "introduction": slide.introduction,
                "button_text": slide.button_text,
                "button_url": slide.button_url,
                "open_method": slide.open_method,
                "image": slide.image,
                "is_active": slide.is_active,
                "is_featured": slide.is_featured,
                "sort_order": slide.sort_order
            })
        
        response = make_response(jsonify(slides_data))
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
        
    except Exception as e:
        response = make_response(jsonify({"error": str(e)}), 500)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

@app.route('/api/events', methods=['GET'])
def api_events():
    try:
        # Get query parameters
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        include_past = request.args.get('include_past', 'false').lower() == 'true'
        
        # Build query
        query = Event.query.join(EventCategory, isouter=True)
        
        # Filter by month/year if provided
        if month and year:
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            query = query.filter(Event.date >= start_date, Event.date < end_date)
        
        # Filter past events unless specifically requested
        if not include_past:
            query = query.filter(Event.date >= datetime.now())
        
        events = query.order_by(Event.date).all()
        
        events_data = []
        current_date = datetime.now()
        
        for event in events:
            # Determine if event is in the past
            is_past = event.date < current_date
            
            event_data = {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "date": event.date.isoformat() if event.date else None,
                "end_date": event.end_date.isoformat() if event.end_date else None,
                "location": event.location,
                "image": event.image,
                "is_featured": event.is_featured,
                "is_past": is_past,
                "website_url": event.website_url,
                "booking_url": event.booking_url,
                "price": event.price,
                "capacity": event.capacity,
                "status": event.status,
                "category": {
                    "id": event.category.id,
                    "name": event.category.name,
                    "color": event.category.color
                } if event.category else None
            }
            events_data.append(event_data)
        
        return jsonify({"events": events_data})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to serve uploaded files
@app.route("/uploads/<path:filename>")
def serve_uploads(filename):
    """Serve uploaded files from the uploads directory"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Route to serve slider fix script
@app.route("/slider-fix.js")
def serve_slider_fix():
    return send_from_directory(os.path.dirname(__file__), "slider-fix.js")

# Route to serve events fix script
@app.route("/events-fix.js")
def serve_events_fix():
    return send_from_directory(os.path.dirname(__file__), "events-fix.js")

# Create tables and initialize database
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables created/verified successfully")
        
        # Create default data if needed
        if not EventCategory.query.first():
            default_categories = [
                EventCategory(name="Community Events", color="#28a745"),
                EventCategory(name="Sports & Recreation", color="#007bff"),
                EventCategory(name="Council Meetings", color="#6c757d"),
                EventCategory(name="Cultural Events", color="#fd7e14")
            ]
            for category in default_categories:
                db.session.add(category)
        
        if not MeetingType.query.first():
            default_meeting_types = [
                MeetingType(name="Full Council", description="Full Council meetings"),
                MeetingType(name="Planning and Development", description="Planning and Development Committee"),
                MeetingType(name="Finance and Governance", description="Finance and Governance Committee")
            ]
            for meeting_type in default_meeting_types:
                db.session.add(meeting_type)
        
        db.session.commit()
        print("✅ Default data created successfully")
        
        # Test database connection
        councillor_count = Councillor.query.count()
        event_count = Event.query.count()
        meeting_count = Meeting.query.count()
        slide_count = HomepageSlide.query.count()
        print(f"📊 Database stats - Councillors: {councillor_count}, Events: {event_count}, Meetings: {meeting_count}, Slides: {slide_count}")
        
    except Exception as e:
        print(f"❌ Error with database: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

