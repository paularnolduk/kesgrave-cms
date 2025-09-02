import os
import sqlite3
import json
import re
from flask import Flask, send_from_directory, jsonify, request, redirect, url_for, render_template_string, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy.ext.automap import automap_base
from urllib.parse import unquote
from datetime import datetime, date
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder="dist/assets", template_folder="dist")
CORS(app)

# Configuration for Flask-Login
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'kesgrave-cms-secret-key-2025')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

# User class for authentication
class AdminUser(UserMixin):
    def __init__(self, id, username='admin'):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    return AdminUser(user_id)

basedir = os.path.abspath(os.path.dirname(__file__))

# ORIGINAL DATABASE LOGIC (PRESERVED FROM WORKING FILE)
if os.environ.get("RENDER"):
    tmp_db_path = "/tmp/kesgrave_working.db"
    original_path = os.path.join(basedir, "instance", "kesgrave_working.db")
    if not os.path.exists(tmp_db_path):
        import shutil
        shutil.copyfile(original_path, tmp_db_path)
    db_path = tmp_db_path
else:
    db_path = os.path.join(basedir, "instance", "kesgrave_working.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Upload configuration
if os.environ.get("RENDER"):
    upload_path = "/tmp/uploads"
else:
    upload_path = os.path.join(basedir, "uploads")

app.config['UPLOAD_FOLDER'] = upload_path
os.makedirs(upload_path, exist_ok=True)

# Create upload subdirectories
upload_dirs = ['slides', 'councillors', 'events', 'meetings', 'content']
for upload_dir in upload_dirs:
    os.makedirs(os.path.join(upload_path, upload_dir), exist_ok=True)

db = SQLAlchemy(app)

# Global variables for models
Slide = None
QuickLink = None
Councillor = None
Meeting = None
Event = None
ContentPage = None
ContentCategory = None
ContentGallery = None
ContentDownload = None
ContentLink = None
MeetingType = None
EventCategory = None
Tag = None
CouncillorTag = None

def init_models():
    """Initialize models within application context"""
    global Slide, QuickLink, Councillor, Meeting, Event, ContentPage, ContentCategory, ContentGallery, ContentDownload, ContentLink, MeetingType, EventCategory, Tag, CouncillorTag
    
    try:
        # Use automap to reflect existing database structure
        Base = automap_base()
        Base.prepare(autoload_with=db.engine)
        
        # Map existing tables
        Slide = Base.classes.get('slide')
        QuickLink = Base.classes.get('quick_link')
        Councillor = Base.classes.get('councillor')
        Meeting = Base.classes.get('meeting')
        Event = Base.classes.get('event')
        ContentPage = Base.classes.get('content_page')
        ContentCategory = Base.classes.get('content_category')
        ContentGallery = Base.classes.get('content_gallery')
        ContentDownload = Base.classes.get('content_download')
        ContentLink = Base.classes.get('content_link')
        MeetingType = Base.classes.get('meeting_type')
        EventCategory = Base.classes.get('event_category')
        Tag = Base.classes.get('tag')
        CouncillorTag = Base.classes.get('councillor_tag')
        
        print("✅ Models initialized successfully")
        
    except Exception as e:
        print(f"❌ Error initializing models: {e}")

# Initialize models
with app.app_context():
    init_models()

# Helper functions
def safe_getattr(obj, attr, default=None):
    """Safely get attribute from object"""
    try:
        return getattr(obj, attr, default)
    except:
        return default

def safe_string(value):
    """Safely convert value to string"""
    if value is None:
        return ""
    return str(value)

def safe_int(value):
    """Safely convert value to int"""
    try:
        return int(value) if value is not None else 0
    except:
        return 0

def safe_bool(value):
    """Safely convert value to boolean"""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def allowed_image_file(filename):
    return allowed_file(filename, {'png', 'jpg', 'jpeg', 'gif', 'webp'})

def save_uploaded_file(file, subfolder):
    """Save uploaded file and return filename"""
    try:
        if file and file.filename:
            # Generate unique filename
            timestamp = int(datetime.now().timestamp())
            original_filename = secure_filename(file.filename)
            name, ext = os.path.splitext(original_filename)
            filename = f"{name}_{timestamp}{ext}"
            
            # Create full path
            upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            print(f"✅ File saved: {file_path}")
            return filename
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        flash(f'Error uploading file: {str(e)}', 'error')
    return None

# === CMS ADMIN INTERFACE ===

@app.route('/cms/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple authentication - admin/admin
        if username == 'admin' and password == 'admin':
            user = AdminUser(1)
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CMS Login - Kesgrave Town Council</title>
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
                    <button type="submit" class="btn btn-primary w-100">Login to CMS</button>
                </form>
                
                <div class="text-center mt-3">
                    <small class="text-muted">Default: admin / admin</small><br>
                    <a href="/" class="btn btn-link btn-sm">← Back to Website</a>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''')

@app.route('/cms/logout')
@login_required
def admin_logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('admin_login'))

# Common admin layout
def get_admin_layout(title, content):
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
        <style>
            .sidebar {{
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }}
            .sidebar .nav-link {{
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: flex;
                align-items: center;
                text-decoration: none;
                transition: all 0.3s ease;
            }}
            .sidebar .nav-link:hover {{
                background: rgba(255,255,255,0.1);
                color: white;
            }}
            .sidebar .nav-link.active {{
                background: rgba(255,255,255,0.2);
                color: white;
            }}
            .sidebar .nav-link i {{
                margin-right: 0.75rem;
                width: 20px;
            }}
            .main-content {{
                margin-left: 260px;
                padding: 2rem;
                min-height: 100vh;
                background: #f8f9fa;
            }}
            .card {{
                border: none;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            @media (max-width: 768px) {{
                .sidebar {{
                    transform: translateX(-100%);
                }}
                .main-content {{
                    margin-left: 0;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
                <small>Content Management</small>
            </div>
            <nav class="nav flex-column">
                <a class="nav-link" href="/cms/dashboard">
                    <i class="fas fa-tachometer-alt"></i>
                    Dashboard
                </a>
                <a class="nav-link" href="/cms/slides">
                    <i class="fas fa-images"></i>
                    Homepage Slides
                </a>
                <a class="nav-link" href="/cms/councillors">
                    <i class="fas fa-users"></i>
                    Councillors
                </a>
                <a class="nav-link" href="/cms/events">
                    <i class="fas fa-calendar-alt"></i>
                    Events
                </a>
                <a class="nav-link" href="/cms/meetings">
                    <i class="fas fa-gavel"></i>
                    Meetings
                </a>
                <a class="nav-link" href="/cms/content">
                    <i class="fas fa-file-alt"></i>
                    Content Pages
                </a>
                <div class="mt-4">
                    <a class="nav-link" href="/" target="_blank">
                        <i class="fas fa-external-link-alt"></i>
                        View Website
                    </a>
                    <a class="nav-link" href="/cms/logout">
                        <i class="fas fa-sign-out-alt"></i>
                        Logout
                    </a>
                </div>
            </nav>
        </div>
        
        <div class="main-content">
            {content}
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script src="https://cdn.quilljs.com/1.3.6/quill.min.js"></script>
    </body>
    </html>
    '''

@app.route('/cms')
@app.route('/cms/dashboard')
@login_required
def admin_dashboard():
    try:
        # Get statistics
        slide_count = db.session.query(Slide).count() if Slide else 0
        councillor_count = db.session.query(Councillor).count() if Councillor else 0
        event_count = db.session.query(Event).count() if Event else 0
        meeting_count = db.session.query(Meeting).count() if Meeting else 0
        
        content = f'''
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>CMS Dashboard</h1>
            <div class="text-muted">
                <i class="fas fa-user"></i> Welcome, {current_user.username}
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-3 mb-4">
                <div class="card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h3 class="text-primary mb-0">{slide_count}</h3>
                                <p class="text-muted mb-0">Homepage Slides</p>
                            </div>
                            <div class="text-primary">
                                <i class="fas fa-images fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3 mb-4">
                <div class="card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h3 class="text-success mb-0">{councillor_count}</h3>
                                <p class="text-muted mb-0">Councillors</p>
                            </div>
                            <div class="text-success">
                                <i class="fas fa-users fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3 mb-4">
                <div class="card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h3 class="text-info mb-0">{event_count}</h3>
                                <p class="text-muted mb-0">Events</p>
                            </div>
                            <div class="text-info">
                                <i class="fas fa-calendar-alt fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3 mb-4">
                <div class="card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="flex-grow-1">
                                <h3 class="text-warning mb-0">{meeting_count}</h3>
                                <p class="text-muted mb-0">Meetings</p>
                            </div>
                            <div class="text-warning">
                                <i class="fas fa-gavel fa-2x"></i>
                            </div>
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
                                <a href="/cms/slides/add" class="btn btn-outline-primary w-100">
                                    <i class="fas fa-plus"></i> Add Slide
                                </a>
                            </div>
                            <div class="col-md-3 mb-3">
                                <a href="/cms/councillors/add" class="btn btn-outline-success w-100">
                                    <i class="fas fa-user-plus"></i> Add Councillor
                                </a>
                            </div>
                            <div class="col-md-3 mb-3">
                                <a href="/cms/events/add" class="btn btn-outline-info w-100">
                                    <i class="fas fa-calendar-plus"></i> Add Event
                                </a>
                            </div>
                            <div class="col-md-3 mb-3">
                                <a href="/cms/meetings/add" class="btn btn-outline-warning w-100">
                                    <i class="fas fa-plus"></i> Add Meeting
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">System Status</h5>
                    </div>
                    <div class="card-body">
                        <p><strong>Database:</strong> {db_path}</p>
                        <p><strong>Environment:</strong> {'Render' if os.environ.get("RENDER") else 'Local'}</p>
                        <p><strong>Status:</strong> <span class="badge bg-success">Online</span></p>
                        <a href="/health" class="btn btn-sm btn-outline-secondary" target="_blank">
                            <i class="fas fa-heartbeat"></i> Health Check
                        </a>
                    </div>
                </div>
            </div>
        </div>
        '''
        
        return get_admin_layout("Dashboard", content)
        
    except Exception as e:
        return f"Error loading dashboard: {str(e)}", 500

# === SLIDES MANAGEMENT ===
@app.route('/cms/slides')
@login_required
def admin_slides():
    try:
        slides = []
        if Slide:
            slides = db.session.query(Slide).order_by(Slide.sort_order).all()
        
        slides_html = ""
        for slide in slides:
            image_html = ""
            if safe_getattr(slide, 'image'):
                image_html = f'<img src="/uploads/slides/{slide.image}" class="img-thumbnail" style="width: 60px; height: 40px; object-fit: cover;">'
            else:
                image_html = '<div class="bg-light d-flex align-items-center justify-content-center" style="width: 60px; height: 40px;"><i class="fas fa-image text-muted"></i></div>'
            
            status_badge = '<span class="badge bg-success">Active</span>' if safe_getattr(slide, 'is_active') else '<span class="badge bg-secondary">Inactive</span>'
            button_text = safe_getattr(slide, 'button_text') or 'No button'
            
            slides_html += f'''
            <tr>
                <td>{image_html}</td>
                <td>{safe_string(safe_getattr(slide, 'title'))}</td>
                <td>{safe_string(safe_getattr(slide, 'introduction', ''))[:50]}{'...' if len(safe_string(safe_getattr(slide, 'introduction', ''))) > 50 else ''}</td>
                <td><span class="badge bg-primary">{button_text}</span></td>
                <td>{status_badge}</td>
                <td>{safe_getattr(slide, 'sort_order', 0)}</td>
                <td>
                    <a href="/cms/slides/edit/{safe_getattr(slide, 'id')}" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteSlide({safe_getattr(slide, 'id')})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
            '''
        
        content = f'''
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>Homepage Slides</h1>
            <a href="/cms/slides/add" class="btn btn-primary">
                <i class="fas fa-plus"></i> Add New Slide
            </a>
        </div>
        
        <div class="card">
            <div class="card-body">
                {'<div class="table-responsive"><table class="table table-hover"><thead><tr><th>Image</th><th>Title</th><th>Introduction</th><th>Button</th><th>Status</th><th>Order</th><th>Actions</th></tr></thead><tbody>' + slides_html + '</tbody></table></div>' if slides else '<div class="text-center py-5"><i class="fas fa-images fa-3x text-muted mb-3"></i><h5>No slides found</h5><p class="text-muted">Create your first homepage slide to get started.</p><a href="/cms/slides/add" class="btn btn-primary"><i class="fas fa-plus"></i> Add First Slide</a></div>'}
            </div>
        </div>
        
        <script>
            function deleteSlide(id) {{
                if (confirm('Are you sure you want to delete this slide?')) {{
                    fetch('/cms/slides/delete/' + id, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }}
                    }}).then(response => {{
                        if (response.ok) {{
                            location.reload();
                        }} else {{
                            alert('Error deleting slide');
                        }}
                    }});
                }}
            }}
        </script>
        '''
        
        return get_admin_layout("Manage Slides", content)
        
    except Exception as e:
        return f"Error loading slides: {str(e)}", 500

@app.route('/cms/slides/add', methods=['GET', 'POST'])
@login_required
def admin_slides_add():
    if request.method == 'POST':
        try:
            # Handle form submission
            title = request.form.get('title')
            introduction = request.form.get('introduction')
            button_text = request.form.get('button_text')
            button_url = request.form.get('button_url')
            open_method = request.form.get('open_method', 'same_tab')
            is_active = bool(request.form.get('is_active'))
            is_featured = bool(request.form.get('is_featured'))
            sort_order = int(request.form.get('sort_order', 0))
            
            # Handle image upload
            image_filename = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_image_file(file.filename):
                    image_filename = save_uploaded_file(file, 'slides')
            
            # Create new slide using raw SQL (since we're using automap)
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO slide (title, introduction, button_text, button_url, open_method, image, is_active, is_featured, sort_order, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, introduction, button_text, button_url, open_method, image_filename, is_active, is_featured, sort_order, datetime.now(), datetime.now()))
            
            conn.commit()
            conn.close()
            
            flash('Slide created successfully!', 'success')
            return redirect(url_for('admin_slides'))
            
        except Exception as e:
            flash(f'Error creating slide: {str(e)}', 'error')
    
    content = '''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Add New Slide</h1>
        <a href="/cms/slides" class="btn btn-secondary">
            <i class="fas fa-arrow-left"></i> Back to Slides
        </a>
    </div>
    
    <div class="card">
        <div class="card-body">
            <form method="POST" enctype="multipart/form-data">
                <div class="row">
                    <div class="col-md-8">
                        <div class="mb-3">
                            <label class="form-label">Title *</label>
                            <input type="text" class="form-control" name="title" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Introduction</label>
                            <textarea class="form-control" name="introduction" rows="3"></textarea>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Button Text</label>
                                    <input type="text" class="form-control" name="button_text">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Button URL</label>
                                    <input type="url" class="form-control" name="button_url">
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Open Method</label>
                                    <select class="form-control" name="open_method">
                                        <option value="same_tab">Same Tab</option>
                                        <option value="new_tab">New Tab</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Sort Order</label>
                                    <input type="number" class="form-control" name="sort_order" value="0">
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="mb-3">
                            <label class="form-label">Slide Image</label>
                            <input type="file" class="form-control" name="image" accept="image/*">
                            <small class="text-muted">Recommended: 1920x1080px</small>
                        </div>
                        
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_active" id="is_active" checked>
                                <label class="form-check-label" for="is_active">
                                    Active
                                </label>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_featured" id="is_featured">
                                <label class="form-check-label" for="is_featured">
                                    Featured
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="d-flex justify-content-end">
                    <a href="/cms/slides" class="btn btn-secondary me-2">Cancel</a>
                    <button type="submit" class="btn btn-primary">Create Slide</button>
                </div>
            </form>
        </div>
    </div>
    '''
    
    return get_admin_layout("Add Slide", content)

# === COUNCILLORS MANAGEMENT ===
@app.route('/cms/councillors')
@login_required
def admin_councillors():
    try:
        councillors = []
        if Councillor:
            councillors = db.session.query(Councillor).order_by(Councillor.name).all()
        
        councillors_html = ""
        for councillor in councillors:
            image_html = ""
            if safe_getattr(councillor, 'image_filename'):
                image_html = f'<img src="/uploads/councillors/{councillor.image_filename}" class="rounded-circle" style="width: 40px; height: 40px; object-fit: cover;">'
            else:
                image_html = '<div class="bg-secondary rounded-circle d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;"><i class="fas fa-user text-white"></i></div>'
            
            status_badge = '<span class="badge bg-success">Published</span>' if safe_getattr(councillor, 'is_published') else '<span class="badge bg-secondary">Draft</span>'
            
            councillors_html += f'''
            <tr>
                <td>
                    <div class="d-flex align-items-center">
                        {image_html}
                        <div class="ms-2">
                            <strong>{safe_string(safe_getattr(councillor, 'name'))}</strong><br>
                            <small class="text-muted">{safe_string(safe_getattr(councillor, 'title', ''))}</small>
                        </div>
                    </div>
                </td>
                <td>{safe_string(safe_getattr(councillor, 'email', ''))}</td>
                <td>{safe_string(safe_getattr(councillor, 'phone', ''))}</td>
                <td>{status_badge}</td>
                <td>
                    <a href="/cms/councillors/edit/{safe_getattr(councillor, 'id')}" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteCouncillor({safe_getattr(councillor, 'id')})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
            '''
        
        content = f'''
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>Councillors</h1>
            <a href="/cms/councillors/add" class="btn btn-primary">
                <i class="fas fa-plus"></i> Add New Councillor
            </a>
        </div>
        
        <div class="card">
            <div class="card-body">
                {'<div class="table-responsive"><table class="table table-hover"><thead><tr><th>Councillor</th><th>Email</th><th>Phone</th><th>Status</th><th>Actions</th></tr></thead><tbody>' + councillors_html + '</tbody></table></div>' if councillors else '<div class="text-center py-5"><i class="fas fa-users fa-3x text-muted mb-3"></i><h5>No councillors found</h5><p class="text-muted">Add your first councillor to get started.</p><a href="/cms/councillors/add" class="btn btn-primary"><i class="fas fa-plus"></i> Add First Councillor</a></div>'}
            </div>
        </div>
        
        <script>
            function deleteCouncillor(id) {{
                if (confirm('Are you sure you want to delete this councillor?')) {{
                    fetch('/cms/councillors/delete/' + id, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }}
                    }}).then(response => {{
                        if (response.ok) {{
                            location.reload();
                        }} else {{
                            alert('Error deleting councillor');
                        }}
                    }});
                }}
            }}
        </script>
        '''
        
        return get_admin_layout("Manage Councillors", content)
        
    except Exception as e:
        return f"Error loading councillors: {str(e)}", 500

# === EVENTS MANAGEMENT ===
@app.route('/cms/events')
@login_required
def admin_events():
    try:
        events = []
        if Event:
            events = db.session.query(Event).order_by(Event.date.desc()).all()
        
        events_html = ""
        for event in events:
            event_date = safe_getattr(event, 'date')
            date_str = event_date.strftime('%d/%m/%Y') if event_date else 'No date'
            
            status_badge = '<span class="badge bg-success">Active</span>' if safe_getattr(event, 'status') == 'active' else '<span class="badge bg-secondary">Inactive</span>'
            featured_badge = '<span class="badge bg-warning">Featured</span>' if safe_getattr(event, 'is_featured') else ''
            
            events_html += f'''
            <tr>
                <td>
                    <strong>{safe_string(safe_getattr(event, 'title'))}</strong><br>
                    <small class="text-muted">{safe_string(safe_getattr(event, 'location', ''))}</small>
                </td>
                <td>{date_str}</td>
                <td>{status_badge} {featured_badge}</td>
                <td>
                    <a href="/cms/events/edit/{safe_getattr(event, 'id')}" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteEvent({safe_getattr(event, 'id')})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
            '''
        
        content = f'''
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>Events</h1>
            <a href="/cms/events/add" class="btn btn-primary">
                <i class="fas fa-plus"></i> Add New Event
            </a>
        </div>
        
        <div class="card">
            <div class="card-body">
                {'<div class="table-responsive"><table class="table table-hover"><thead><tr><th>Event</th><th>Date</th><th>Status</th><th>Actions</th></tr></thead><tbody>' + events_html + '</tbody></table></div>' if events else '<div class="text-center py-5"><i class="fas fa-calendar-alt fa-3x text-muted mb-3"></i><h5>No events found</h5><p class="text-muted">Create your first event to get started.</p><a href="/cms/events/add" class="btn btn-primary"><i class="fas fa-plus"></i> Add First Event</a></div>'}
            </div>
        </div>
        
        <script>
            function deleteEvent(id) {{
                if (confirm('Are you sure you want to delete this event?')) {{
                    fetch('/cms/events/delete/' + id, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }}
                    }}).then(response => {{
                        if (response.ok) {{
                            location.reload();
                        }} else {{
                            alert('Error deleting event');
                        }}
                    }});
                }}
            }}
        </script>
        '''
        
        return get_admin_layout("Manage Events", content)
        
    except Exception as e:
        return f"Error loading events: {str(e)}", 500

# === MEETINGS MANAGEMENT ===
@app.route('/cms/meetings')
@login_required
def admin_meetings():
    try:
        meetings = []
        if Meeting:
            meetings = db.session.query(Meeting).order_by(Meeting.meeting_date.desc()).all()
        
        meetings_html = ""
        for meeting in meetings:
            meeting_date = safe_getattr(meeting, 'meeting_date')
            date_str = meeting_date.strftime('%d/%m/%Y') if meeting_date else 'No date'
            
            status_badge = '<span class="badge bg-success">Published</span>' if safe_getattr(meeting, 'is_published') else '<span class="badge bg-secondary">Draft</span>'
            
            meetings_html += f'''
            <tr>
                <td>
                    <strong>{safe_string(safe_getattr(meeting, 'title'))}</strong><br>
                    <small class="text-muted">{safe_string(safe_getattr(meeting, 'location', ''))}</small>
                </td>
                <td>{date_str}</td>
                <td>{status_badge}</td>
                <td>
                    <a href="/cms/meetings/edit/{safe_getattr(meeting, 'id')}" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteMeeting({safe_getattr(meeting, 'id')})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
            '''
        
        content = f'''
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>Meetings</h1>
            <a href="/cms/meetings/add" class="btn btn-primary">
                <i class="fas fa-plus"></i> Add New Meeting
            </a>
        </div>
        
        <div class="card">
            <div class="card-body">
                {'<div class="table-responsive"><table class="table table-hover"><thead><tr><th>Meeting</th><th>Date</th><th>Status</th><th>Actions</th></tr></thead><tbody>' + meetings_html + '</tbody></table></div>' if meetings else '<div class="text-center py-5"><i class="fas fa-gavel fa-3x text-muted mb-3"></i><h5>No meetings found</h5><p class="text-muted">Schedule your first meeting to get started.</p><a href="/cms/meetings/add" class="btn btn-primary"><i class="fas fa-plus"></i> Add First Meeting</a></div>'}
            </div>
        </div>
        
        <script>
            function deleteMeeting(id) {{
                if (confirm('Are you sure you want to delete this meeting?')) {{
                    fetch('/cms/meetings/delete/' + id, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }}
                    }}).then(response => {{
                        if (response.ok) {{
                            location.reload();
                        }} else {{
                            alert('Error deleting meeting');
                        }}
                    }});
                }}
            }}
        </script>
        '''
        
        return get_admin_layout("Manage Meetings", content)
        
    except Exception as e:
        return f"Error loading meetings: {str(e)}", 500

# === CONTENT PAGES MANAGEMENT ===
@app.route('/cms/content')
@login_required
def admin_content():
    try:
        content_pages = []
        if ContentPage:
            content_pages = db.session.query(ContentPage).order_by(ContentPage.title).all()
        
        pages_html = ""
        for page in content_pages:
            status_badge = '<span class="badge bg-success">Published</span>' if safe_getattr(page, 'is_published') else '<span class="badge bg-secondary">Draft</span>'
            featured_badge = '<span class="badge bg-warning">Featured</span>' if safe_getattr(page, 'is_featured') else ''
            
            pages_html += f'''
            <tr>
                <td>
                    <strong>{safe_string(safe_getattr(page, 'title'))}</strong><br>
                    <small class="text-muted">{safe_string(safe_getattr(page, 'slug', ''))}</small>
                </td>
                <td>{safe_string(safe_getattr(page, 'excerpt', ''))[:100]}{'...' if len(safe_string(safe_getattr(page, 'excerpt', ''))) > 100 else ''}</td>
                <td>{status_badge} {featured_badge}</td>
                <td>
                    <a href="/cms/content/edit/{safe_getattr(page, 'id')}" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button class="btn btn-sm btn-outline-danger" onclick="deletePage({safe_getattr(page, 'id')})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
            '''
        
        content = f'''
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>Content Pages</h1>
            <a href="/cms/content/add" class="btn btn-primary">
                <i class="fas fa-plus"></i> Add New Page
            </a>
        </div>
        
        <div class="card">
            <div class="card-body">
                {'<div class="table-responsive"><table class="table table-hover"><thead><tr><th>Page</th><th>Excerpt</th><th>Status</th><th>Actions</th></tr></thead><tbody>' + pages_html + '</tbody></table></div>' if content_pages else '<div class="text-center py-5"><i class="fas fa-file-alt fa-3x text-muted mb-3"></i><h5>No content pages found</h5><p class="text-muted">Create your first content page to get started.</p><a href="/cms/content/add" class="btn btn-primary"><i class="fas fa-plus"></i> Add First Page</a></div>'}
            </div>
        </div>
        
        <script>
            function deletePage(id) {{
                if (confirm('Are you sure you want to delete this page?')) {{
                    fetch('/cms/content/delete/' + id, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }}
                    }}).then(response => {{
                        if (response.ok) {{
                            location.reload();
                        }} else {{
                            alert('Error deleting page');
                        }}
                    }});
                }}
            }}
        </script>
        '''
        
        return get_admin_layout("Manage Content", content)
        
    except Exception as e:
        return f"Error loading content pages: {str(e)}", 500

# === ORIGINAL API ROUTES (PRESERVED FROM WORKING FILE) ===

@app.route('/api/homepage/slides', methods=['GET', 'OPTIONS'])
def get_homepage_slides():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response
    
    try:
        if not Slide:
            return jsonify([])
        
        slides = db.session.query(Slide).filter_by(is_active=True).order_by(Slide.sort_order).all()
        
        slides_data = []
        for slide in slides:
            slides_data.append({
                "id": safe_getattr(slide, 'id'),
                "title": safe_string(safe_getattr(slide, 'title')),
                "introduction": safe_string(safe_getattr(slide, 'introduction')),
                "button_text": safe_string(safe_getattr(slide, 'button_text')),
                "button_url": safe_string(safe_getattr(slide, 'button_url')),
                "open_method": safe_string(safe_getattr(slide, 'open_method', 'same_tab')),
                "image": safe_string(safe_getattr(slide, 'image')),
                "is_active": safe_bool(safe_getattr(slide, 'is_active')),
                "is_featured": safe_bool(safe_getattr(slide, 'is_featured')),
                "sort_order": safe_int(safe_getattr(slide, 'sort_order'))
            })
        
        response = jsonify(slides_data)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
        
    except Exception as e:
        response = jsonify({"error": str(e)})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 500

@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        if not Event:
            return jsonify({"events": []})
        
        # Get query parameters
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        include_past = request.args.get('include_past', 'false').lower() == 'true'
        
        # Build base query
        query = db.session.query(Event)
        
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
            event_date = safe_getattr(event, 'date')
            is_past = event_date < current_date if event_date else False
            
            # Get category info
            category_data = None
            if EventCategory:
                try:
                    category_id = safe_getattr(event, 'category_id')
                    if category_id:
                        category = db.session.query(EventCategory).filter_by(id=category_id).first()
                        if category:
                            category_data = {
                                "id": safe_getattr(category, 'id'),
                                "name": safe_string(safe_getattr(category, 'name')),
                                "color": safe_string(safe_getattr(category, 'color', '#007bff'))
                            }
                except:
                    pass
            
            event_data = {
                "id": safe_getattr(event, 'id'),
                "title": safe_string(safe_getattr(event, 'title')),
                "description": safe_string(safe_getattr(event, 'description')),
                "date": event_date.isoformat() if event_date else None,
                "end_date": safe_getattr(event, 'end_date').isoformat() if safe_getattr(event, 'end_date') else None,
                "location": safe_string(safe_getattr(event, 'location')),
                "image": safe_string(safe_getattr(event, 'image')),
                "is_featured": safe_bool(safe_getattr(event, 'is_featured')),
                "is_past": is_past,
                "website_url": safe_string(safe_getattr(event, 'website_url')),
                "booking_url": safe_string(safe_getattr(event, 'booking_url')),
                "price": safe_string(safe_getattr(event, 'price')),
                "capacity": safe_getattr(event, 'capacity'),
                "status": safe_string(safe_getattr(event, 'status')),
                "category": category_data
            }
            events_data.append(event_data)
        
        return jsonify({"events": events_data})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route('/health')
def health_check():
    try:
        # Test database connection
        slide_count = db.session.query(Slide).count() if Slide else 0
        councillor_count = db.session.query(Councillor).count() if Councillor else 0
        event_count = db.session.query(Event).count() if Event else 0
        meeting_count = db.session.query(Meeting).count() if Meeting else 0
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "database_path": db_path,
            "counts": {
                "slides": slide_count,
                "councillors": councillor_count,
                "events": event_count,
                "meetings": meeting_count
            },
            "admin_interface": "available at /cms/login",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "database_path": db_path,
            "timestamp": datetime.utcnow().isoformat()
        }), 500

# === ORIGINAL FRONTEND SERVING ROUTES (PRESERVED FROM WORKING FILE) ===

@app.route("/admin")
def admin_root():
    # Redirect old admin route to new CMS
    return redirect("/cms/login")

@app.route("/admin/<path:path>")
def serve_admin(path):
    # Redirect old admin routes to new CMS
    return redirect("/cms/login")

@app.route("/login")
def login():
    # Redirect old login to new CMS login
    return redirect("/cms/login")

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(os.path.join(app.static_folder), filename)

# Route to serve uploaded images
@app.route("/uploads/<path:filename>")
def serve_uploads(filename):
    """Serve uploaded files from the uploads directory"""
    uploads_dir = os.path.join(basedir, "uploads")
    return send_from_directory(uploads_dir, filename)

# Route to serve slider fix script
@app.route("/slider-fix.js")
def serve_slider_fix():
    return send_from_directory(basedir, "slider-fix.js")

# Route to serve events fix script
@app.route("/events-fix.js")
def serve_events_fix():
    return send_from_directory(basedir, "events-fix.js")

# FRONTEND SERVING ROUTES (CRITICAL - PRESERVED FROM WORKING FILE)
@app.route("/")
def serve_frontend():
    return send_from_directory("dist", "index.html")

@app.route("/<path:path>")
def serve_frontend_paths(path):
    # Exclude API, CMS, assets, and uploads from frontend serving
    if path.startswith("api/") or path.startswith("cms/") or path.startswith("admin/") or path.startswith("assets/") or path.startswith("uploads/"):
        return "Not Found", 404
    return send_from_directory("dist", "index.html")

if __name__ == '__main__':
    app.run(debug=True)
