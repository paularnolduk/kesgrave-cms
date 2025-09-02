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
    if not os.path.exists(tmp_db_path) and os.path.exists(original_path):
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

# Helper functions for database operations
def execute_query(query, params=None):
    """Execute a query directly on the database"""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # This allows dict-like access
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if query.strip().upper().startswith('SELECT'):
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.rowcount
        
        conn.close()
        return result
    except Exception as e:
        print(f"Database error: {e}")
        return None

def get_table_info(table_name):
    """Get column information for a table"""
    try:
        result = execute_query(f"PRAGMA table_info({table_name})")
        return [row['name'] for row in result] if result else []
    except:
        return []

# Helper functions
def safe_getattr(obj, attr, default=None):
    """Safely get attribute from object or dict"""
    if isinstance(obj, dict):
        return obj.get(attr, default)
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
def get_admin_layout(title, content, active_page=""):
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
            .alert {{
                border: none;
                border-radius: 10px;
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
                <a class="nav-link {'active' if active_page == 'dashboard' else ''}" href="/cms/dashboard">
                    <i class="fas fa-tachometer-alt"></i>
                    Dashboard
                </a>
                <a class="nav-link {'active' if active_page == 'slides' else ''}" href="/cms/slides">
                    <i class="fas fa-images"></i>
                    Homepage Slides
                </a>
                <a class="nav-link {'active' if active_page == 'councillors' else ''}" href="/cms/councillors">
                    <i class="fas fa-users"></i>
                    Councillors
                </a>
                <a class="nav-link {'active' if active_page == 'events' else ''}" href="/cms/events">
                    <i class="fas fa-calendar-alt"></i>
                    Events
                </a>
                <a class="nav-link {'active' if active_page == 'meetings' else ''}" href="/cms/meetings">
                    <i class="fas fa-gavel"></i>
                    Meetings
                </a>
                <a class="nav-link {'active' if active_page == 'content' else ''}" href="/cms/content">
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
        # Get statistics using direct SQL queries
        slide_count = len(execute_query("SELECT * FROM slide") or [])
        councillor_count = len(execute_query("SELECT * FROM councillor") or [])
        event_count = len(execute_query("SELECT * FROM event") or [])
        meeting_count = len(execute_query("SELECT * FROM meeting") or [])
        content_count = len(execute_query("SELECT * FROM content_page") or [])
        
        # Get recent activity
        recent_events = execute_query("SELECT * FROM event ORDER BY created_at DESC LIMIT 5") or []
        recent_meetings = execute_query("SELECT * FROM meeting ORDER BY created_at DESC LIMIT 5") or []
        
        # Content status overview
        published_content = len(execute_query("SELECT * FROM content_page WHERE is_published = 1") or [])
        draft_content = content_count - published_content
        
        content = f'''
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>CMS Dashboard</h1>
            <div class="text-muted">
                <i class="fas fa-user"></i> Welcome, {current_user.username}
            </div>
        </div>
        
        <!-- Statistics Cards -->
        <div class="row mb-4">
            <div class="col-md-2 mb-3">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="fas fa-images fa-2x text-primary mb-2"></i>
                        <h3 class="text-primary">{slide_count}</h3>
                        <p class="mb-0">Slides</p>
                    </div>
                </div>
            </div>
            <div class="col-md-2 mb-3">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="fas fa-users fa-2x text-success mb-2"></i>
                        <h3 class="text-success">{councillor_count}</h3>
                        <p class="mb-0">Councillors</p>
                    </div>
                </div>
            </div>
            <div class="col-md-2 mb-3">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="fas fa-calendar-alt fa-2x text-info mb-2"></i>
                        <h3 class="text-info">{event_count}</h3>
                        <p class="mb-0">Events</p>
                    </div>
                </div>
            </div>
            <div class="col-md-2 mb-3">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="fas fa-gavel fa-2x text-warning mb-2"></i>
                        <h3 class="text-warning">{meeting_count}</h3>
                        <p class="mb-0">Meetings</p>
                    </div>
                </div>
            </div>
            <div class="col-md-2 mb-3">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="fas fa-file-alt fa-2x text-secondary mb-2"></i>
                        <h3 class="text-secondary">{content_count}</h3>
                        <p class="mb-0">Pages</p>
                    </div>
                </div>
            </div>
            <div class="col-md-2 mb-3">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="fas fa-check-circle fa-2x text-success mb-2"></i>
                        <h3 class="text-success">{published_content}</h3>
                        <p class="mb-0">Published</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Content Status Overview -->
        <div class="row mb-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">Content Status</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6">
                                <div class="text-center">
                                    <h4 class="text-success">{published_content}</h4>
                                    <p class="text-muted">Published Pages</p>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="text-center">
                                    <h4 class="text-warning">{draft_content}</h4>
                                    <p class="text-muted">Draft Pages</p>
                                </div>
                            </div>
                        </div>
                        <div class="progress">
                            <div class="progress-bar bg-success" style="width: {(published_content / max(content_count, 1)) * 100}%"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">Quick Actions</h5>
                    </div>
                    <div class="card-body">
                        <div class="d-grid gap-2">
                            <a href="/cms/slides/add" class="btn btn-outline-primary">
                                <i class="fas fa-plus"></i> Add Homepage Slide
                            </a>
                            <a href="/cms/events/add" class="btn btn-outline-info">
                                <i class="fas fa-calendar-plus"></i> Create Event
                            </a>
                            <a href="/cms/meetings/add" class="btn btn-outline-warning">
                                <i class="fas fa-plus"></i> Schedule Meeting
                            </a>
                            <a href="/cms/content/add" class="btn btn-outline-secondary">
                                <i class="fas fa-file-plus"></i> New Content Page
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Recent Activity -->
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">Recent Events</h5>
                    </div>
                    <div class="card-body">
                        {'<p class="text-muted">No recent events</p>' if not recent_events else ''.join([f'<div class="d-flex justify-content-between align-items-center mb-2"><span>{event["title"] if "title" in event.keys() else "Event"}</span><small class="text-muted">{event["date"] if "date" in event.keys() else ""}</small></div>' for event in recent_events[:3]])}
                        <a href="/cms/events" class="btn btn-sm btn-outline-primary">View All Events</a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">Recent Meetings</h5>
                    </div>
                    <div class="card-body">
                        {'<p class="text-muted">No recent meetings</p>' if not recent_meetings else ''.join([f'<div class="d-flex justify-content-between align-items-center mb-2"><span>{meeting["title"] if "title" in meeting.keys() else "Meeting"}</span><small class="text-muted">{meeting["meeting_date"] if "meeting_date" in meeting.keys() else ""}</small></div>' for meeting in recent_meetings[:3]])}
                        <a href="/cms/meetings" class="btn btn-sm btn-outline-warning">View All Meetings</a>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- System Status -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0">System Status</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-4">
                                <p><strong>Database:</strong> {db_path}</p>
                                <p><strong>Status:</strong> <span class="badge bg-success">Online</span></p>
                            </div>
                            <div class="col-md-4">
                                <p><strong>Environment:</strong> {'Render' if os.environ.get("RENDER") else 'Local'}</p>
                                <p><strong>Upload Path:</strong> {upload_path}</p>
                            </div>
                            <div class="col-md-4">
                                <a href="/health" class="btn btn-sm btn-outline-secondary" target="_blank">
                                    <i class="fas fa-heartbeat"></i> Health Check
                                </a>
                                <a href="/api/homepage/slides" class="btn btn-sm btn-outline-info" target="_blank">
                                    <i class="fas fa-code"></i> Test API
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''
        
        return render_template_string(get_admin_layout("Dashboard", content, "dashboard"))
        
    except Exception as e:
        return f"Error loading dashboard: {str(e)}", 500

# === SLIDES MANAGEMENT ===
@app.route('/cms/slides')
@login_required
def admin_slides():
    try:
        slides = execute_query("SELECT * FROM slide ORDER BY sort_order") or []
        
        slides_html = ""
        for slide in slides:
            image_html = ""
            if slide.get('image'):
                image_html = f'<img src="/uploads/slides/{slide["image"]}" class="img-thumbnail" style="width: 60px; height: 40px; object-fit: cover;">'
            else:
                image_html = '<div class="bg-light d-flex align-items-center justify-content-center" style="width: 60px; height: 40px;"><i class="fas fa-image text-muted"></i></div>'
            
            status_badge = '<span class="badge bg-success">Active</span>' if slide.get('is_active') else '<span class="badge bg-secondary">Inactive</span>'
            button_text = slide.get('button_text') or 'No button'
            
            slides_html += f'''
            <tr>
                <td>{image_html}</td>
                <td>{slide.get("title", "")}</td>
                <td>{slide.get("introduction", "")[:50]}{'...' if len(slide.get("introduction", "")) > 50 else ''}</td>
                <td><span class="badge bg-primary">{button_text}</span></td>
                <td>{status_badge}</td>
                <td>{slide.get("sort_order", 0)}</td>
                <td>
                    <a href="/cms/slides/edit/{slide.get('id')}" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteSlide({slide.get('id')})">
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
        
        return render_template_string(get_admin_layout("Manage Slides", content, "slides"))
        
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
            is_active = 1 if request.form.get('is_active') else 0
            is_featured = 1 if request.form.get('is_featured') else 0
            sort_order = int(request.form.get('sort_order', 0))
            
            # Handle image upload
            image_filename = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_image_file(file.filename):
                    image_filename = save_uploaded_file(file, 'slides')
            
            # Insert into database
            execute_query('''
                INSERT INTO slide (title, introduction, button_text, button_url, open_method, image, is_active, is_featured, sort_order, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, introduction, button_text, button_url, open_method, image_filename, is_active, is_featured, sort_order, datetime.now(), datetime.now()))
            
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
    
    return render_template_string(get_admin_layout("Add Slide", content, "slides"))

@app.route('/cms/slides/delete/<int:slide_id>', methods=['POST'])
@login_required
def admin_slides_delete(slide_id):
    try:
        execute_query("DELETE FROM slide WHERE id = ?", (slide_id,))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === EVENTS MANAGEMENT ===
@app.route('/cms/events')
@login_required
def admin_events():
    try:
        events = execute_query("SELECT * FROM event ORDER BY date DESC") or []
        
        events_html = ""
        for event in events:
            event_date = event.get('date')
            if event_date:
                try:
                    # Handle different date formats
                    if isinstance(event_date, str):
                        event_date = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                    date_str = event_date.strftime('%d/%m/%Y') if event_date else 'No date'
                except:
                    date_str = str(event_date)
            else:
                date_str = 'No date'
            
            status_badge = '<span class="badge bg-success">Active</span>' if event.get('status') == 'active' else '<span class="badge bg-secondary">Inactive</span>'
            featured_badge = '<span class="badge bg-warning">Featured</span>' if event.get('is_featured') else ''
            
            events_html += f'''
            <tr>
                <td>
                    <strong>{event.get("title", "")}</strong><br>
                    <small class="text-muted">{event.get("location", "")}</small>
                </td>
                <td>{date_str}</td>
                <td>{status_badge} {featured_badge}</td>
                <td>
                    <a href="/cms/events/edit/{event.get('id')}" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteEvent({event.get('id')})">
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
        
        return render_template_string(get_admin_layout("Manage Events", content, "events"))
        
    except Exception as e:
        return f"Error loading events: {str(e)}", 500

@app.route('/cms/events/add', methods=['GET', 'POST'])
@login_required
def admin_events_add():
    if request.method == 'POST':
        try:
            # Handle form submission
            title = request.form.get('title')
            description = request.form.get('description')
            date_str = request.form.get('date')
            end_date_str = request.form.get('end_date')
            location = request.form.get('location')
            website_url = request.form.get('website_url')
            booking_url = request.form.get('booking_url')
            price = request.form.get('price')
            capacity = request.form.get('capacity')
            is_featured = 1 if request.form.get('is_featured') else 0
            status = request.form.get('status', 'active')
            
            # Parse dates
            event_date = None
            end_date = None
            if date_str:
                event_date = datetime.strptime(date_str, '%Y-%m-%d')
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            
            # Handle image upload
            image_filename = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_image_file(file.filename):
                    image_filename = save_uploaded_file(file, 'events')
            
            # Insert into database
            execute_query('''
                INSERT INTO event (title, description, date, end_date, location, image, website_url, booking_url, price, capacity, is_featured, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, event_date, end_date, location, image_filename, website_url, booking_url, price, capacity, is_featured, status, datetime.now(), datetime.now()))
            
            flash('Event created successfully!', 'success')
            return redirect(url_for('admin_events'))
            
        except Exception as e:
            flash(f'Error creating event: {str(e)}', 'error')
    
    content = '''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Add New Event</h1>
        <a href="/cms/events" class="btn btn-secondary">
            <i class="fas fa-arrow-left"></i> Back to Events
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
                            <textarea class="form-control" name="description" rows="4"></textarea>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Start Date *</label>
                                    <input type="date" class="form-control" name="date" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">End Date</label>
                                    <input type="date" class="form-control" name="end_date">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Location</label>
                            <input type="text" class="form-control" name="location">
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Website URL</label>
                                    <input type="url" class="form-control" name="website_url">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Booking URL</label>
                                    <input type="url" class="form-control" name="booking_url">
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Price</label>
                                    <input type="text" class="form-control" name="price" placeholder="e.g. Free, £10, £5-£15">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Capacity</label>
                                    <input type="number" class="form-control" name="capacity">
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="mb-3">
                            <label class="form-label">Event Image</label>
                            <input type="file" class="form-control" name="image" accept="image/*">
                            <small class="text-muted">Recommended: 800x600px</small>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Status</label>
                            <select class="form-control" name="status">
                                <option value="active">Active</option>
                                <option value="inactive">Inactive</option>
                                <option value="cancelled">Cancelled</option>
                            </select>
                        </div>
                        
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_featured" id="is_featured">
                                <label class="form-check-label" for="is_featured">
                                    Featured Event
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="d-flex justify-content-end">
                    <a href="/cms/events" class="btn btn-secondary me-2">Cancel</a>
                    <button type="submit" class="btn btn-primary">Create Event</button>
                </div>
            </form>
        </div>
    </div>
    '''
    
    return render_template_string(get_admin_layout("Add Event", content, "events"))

@app.route('/cms/events/delete/<int:event_id>', methods=['POST'])
@login_required
def admin_events_delete(event_id):
    try:
        execute_query("DELETE FROM event WHERE id = ?", (event_id,))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === COUNCILLORS MANAGEMENT ===
@app.route('/cms/councillors')
@login_required
def admin_councillors():
    try:
        councillors = execute_query("SELECT * FROM councillor ORDER BY name") or []
        
        councillors_html = ""
        for councillor in councillors:
            image_html = ""
            if councillor.get('image_filename'):
                image_html = f'<img src="/uploads/councillors/{councillor["image_filename"]}" class="rounded-circle" style="width: 40px; height: 40px; object-fit: cover;">'
            else:
                image_html = '<div class="bg-secondary rounded-circle d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;"><i class="fas fa-user text-white"></i></div>'
            
            status_badge = '<span class="badge bg-success">Published</span>' if councillor.get('is_published') else '<span class="badge bg-secondary">Draft</span>'
            
            councillors_html += f'''
            <tr>
                <td>
                    <div class="d-flex align-items-center">
                        {image_html}
                        <div class="ms-2">
                            <strong>{councillor.get("name", "")}</strong><br>
                            <small class="text-muted">{councillor.get("title", "")}</small>
                        </div>
                    </div>
                </td>
                <td>{councillor.get("email", "")}</td>
                <td>{councillor.get("phone", "")}</td>
                <td>{status_badge}</td>
                <td>
                    <a href="/cms/councillors/edit/{councillor.get('id')}" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteCouncillor({councillor.get('id')})">
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
        
        return render_template_string(get_admin_layout("Manage Councillors", content, "councillors"))
        
    except Exception as e:
        return f"Error loading councillors: {str(e)}", 500

@app.route('/cms/councillors/add', methods=['GET', 'POST'])
@login_required
def admin_councillors_add():
    if request.method == 'POST':
        try:
            # Handle form submission
            name = request.form.get('name')
            title = request.form.get('title')
            email = request.form.get('email')
            phone = request.form.get('phone')
            biography = request.form.get('biography')
            facebook_url = request.form.get('facebook_url')
            twitter_url = request.form.get('twitter_url')
            linkedin_url = request.form.get('linkedin_url')
            is_published = 1 if request.form.get('is_published') else 0
            
            # Handle image upload
            image_filename = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename and allowed_image_file(file.filename):
                    image_filename = save_uploaded_file(file, 'councillors')
            
            # Insert into database
            execute_query('''
                INSERT INTO councillor (name, title, email, phone, biography, image_filename, facebook_url, twitter_url, linkedin_url, is_published, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, title, email, phone, biography, image_filename, facebook_url, twitter_url, linkedin_url, is_published, datetime.now(), datetime.now()))
            
            flash('Councillor created successfully!', 'success')
            return redirect(url_for('admin_councillors'))
            
        except Exception as e:
            flash(f'Error creating councillor: {str(e)}', 'error')
    
    content = '''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Add New Councillor</h1>
        <a href="/cms/councillors" class="btn btn-secondary">
            <i class="fas fa-arrow-left"></i> Back to Councillors
        </a>
    </div>
    
    <div class="card">
        <div class="card-body">
            <form method="POST" enctype="multipart/form-data">
                <div class="row">
                    <div class="col-md-8">
                        <div class="mb-3">
                            <label class="form-label">Full Name *</label>
                            <input type="text" class="form-control" name="name" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Title/Position</label>
                            <input type="text" class="form-control" name="title" placeholder="e.g. Town Councillor, Mayor">
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Email</label>
                                    <input type="email" class="form-control" name="email">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Phone</label>
                                    <input type="tel" class="form-control" name="phone">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Biography</label>
                            <textarea class="form-control" name="biography" rows="4"></textarea>
                        </div>
                        
                        <h5>Social Media Links</h5>
                        <div class="row">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Facebook URL</label>
                                    <input type="url" class="form-control" name="facebook_url">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Twitter URL</label>
                                    <input type="url" class="form-control" name="twitter_url">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">LinkedIn URL</label>
                                    <input type="url" class="form-control" name="linkedin_url">
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="mb-3">
                            <label class="form-label">Profile Photo</label>
                            <input type="file" class="form-control" name="image" accept="image/*">
                            <small class="text-muted">Recommended: 400x400px</small>
                        </div>
                        
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_published" id="is_published" checked>
                                <label class="form-check-label" for="is_published">
                                    Published
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="d-flex justify-content-end">
                    <a href="/cms/councillors" class="btn btn-secondary me-2">Cancel</a>
                    <button type="submit" class="btn btn-primary">Create Councillor</button>
                </div>
            </form>
        </div>
    </div>
    '''
    
    return render_template_string(get_admin_layout("Add Councillor", content, "councillors"))

@app.route('/cms/councillors/delete/<int:councillor_id>', methods=['POST'])
@login_required
def admin_councillors_delete(councillor_id):
    try:
        execute_query("DELETE FROM councillor WHERE id = ?", (councillor_id,))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === MEETINGS MANAGEMENT ===
@app.route('/cms/meetings')
@login_required
def admin_meetings():
    try:
        meetings = execute_query("SELECT * FROM meeting ORDER BY meeting_date DESC") or []
        
        meetings_html = ""
        for meeting in meetings:
            meeting_date = meeting.get('meeting_date')
            if meeting_date:
                try:
                    if isinstance(meeting_date, str):
                        meeting_date = datetime.fromisoformat(meeting_date.replace('Z', '+00:00'))
                    date_str = meeting_date.strftime('%d/%m/%Y') if meeting_date else 'No date'
                except:
                    date_str = str(meeting_date)
            else:
                date_str = 'No date'
            
            status_badge = '<span class="badge bg-success">Published</span>' if meeting.get('is_published') else '<span class="badge bg-secondary">Draft</span>'
            
            meetings_html += f'''
            <tr>
                <td>
                    <strong>{meeting.get("title", "")}</strong><br>
                    <small class="text-muted">{meeting.get("location", "")}</small>
                </td>
                <td>{date_str}</td>
                <td>{status_badge}</td>
                <td>
                    <a href="/cms/meetings/edit/{meeting.get('id')}" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteMeeting({meeting.get('id')})">
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
        
        return render_template_string(get_admin_layout("Manage Meetings", content, "meetings"))
        
    except Exception as e:
        return f"Error loading meetings: {str(e)}", 500

@app.route('/cms/meetings/add', methods=['GET', 'POST'])
@login_required
def admin_meetings_add():
    if request.method == 'POST':
        try:
            # Handle form submission
            title = request.form.get('title')
            description = request.form.get('description')
            meeting_date_str = request.form.get('meeting_date')
            meeting_time = request.form.get('meeting_time')
            location = request.form.get('location')
            is_published = 1 if request.form.get('is_published') else 0
            
            # Parse date and time
            meeting_datetime = None
            if meeting_date_str:
                if meeting_time:
                    meeting_datetime = datetime.strptime(f"{meeting_date_str} {meeting_time}", '%Y-%m-%d %H:%M')
                else:
                    meeting_datetime = datetime.strptime(meeting_date_str, '%Y-%m-%d')
            
            # Insert into database
            execute_query('''
                INSERT INTO meeting (title, description, meeting_date, location, is_published, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, description, meeting_datetime, location, is_published, datetime.now(), datetime.now()))
            
            flash('Meeting created successfully!', 'success')
            return redirect(url_for('admin_meetings'))
            
        except Exception as e:
            flash(f'Error creating meeting: {str(e)}', 'error')
    
    content = '''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Add New Meeting</h1>
        <a href="/cms/meetings" class="btn btn-secondary">
            <i class="fas fa-arrow-left"></i> Back to Meetings
        </a>
    </div>
    
    <div class="card">
        <div class="card-body">
            <form method="POST" enctype="multipart/form-data">
                <div class="row">
                    <div class="col-md-8">
                        <div class="mb-3">
                            <label class="form-label">Meeting Title *</label>
                            <input type="text" class="form-control" name="title" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Description</label>
                            <textarea class="form-control" name="description" rows="3"></textarea>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Date *</label>
                                    <input type="date" class="form-control" name="meeting_date" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Time</label>
                                    <input type="time" class="form-control" name="meeting_time">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Location</label>
                            <input type="text" class="form-control" name="location" placeholder="e.g. Council Chambers, Town Hall">
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_published" id="is_published" checked>
                                <label class="form-check-label" for="is_published">
                                    Published
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="d-flex justify-content-end">
                    <a href="/cms/meetings" class="btn btn-secondary me-2">Cancel</a>
                    <button type="submit" class="btn btn-primary">Create Meeting</button>
                </div>
            </form>
        </div>
    </div>
    '''
    
    return render_template_string(get_admin_layout("Add Meeting", content, "meetings"))

@app.route('/cms/meetings/delete/<int:meeting_id>', methods=['POST'])
@login_required
def admin_meetings_delete(meeting_id):
    try:
        execute_query("DELETE FROM meeting WHERE id = ?", (meeting_id,))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === CONTENT PAGES MANAGEMENT ===
@app.route('/cms/content')
@login_required
def admin_content():
    try:
        content_pages = execute_query("SELECT * FROM content_page ORDER BY title") or []
        
        pages_html = ""
        for page in content_pages:
            status_badge = '<span class="badge bg-success">Published</span>' if page.get('is_published') else '<span class="badge bg-secondary">Draft</span>'
            featured_badge = '<span class="badge bg-warning">Featured</span>' if page.get('is_featured') else ''
            
            pages_html += f'''
            <tr>
                <td>
                    <strong>{page.get("title", "")}</strong><br>
                    <small class="text-muted">{page.get("slug", "")}</small>
                </td>
                <td>{page.get("excerpt", "")[:100]}{'...' if len(page.get("excerpt", "")) > 100 else ''}</td>
                <td>{status_badge} {featured_badge}</td>
                <td>
                    <a href="/cms/content/edit/{page.get('id')}" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button class="btn btn-sm btn-outline-danger" onclick="deletePage({page.get('id')})">
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
        
        return render_template_string(get_admin_layout("Manage Content", content, "content"))
        
    except Exception as e:
        return f"Error loading content pages: {str(e)}", 500

@app.route('/cms/content/add', methods=['GET', 'POST'])
@login_required
def admin_content_add():
    if request.method == 'POST':
        try:
            # Handle form submission
            title = request.form.get('title')
            slug = request.form.get('slug')
            excerpt = request.form.get('excerpt')
            content_text = request.form.get('content')
            is_published = 1 if request.form.get('is_published') else 0
            is_featured = 1 if request.form.get('is_featured') else 0
            
            # Generate slug if not provided
            if not slug:
                slug = re.sub(r'[^a-zA-Z0-9\s]', '', title.lower())
                slug = re.sub(r'\s+', '-', slug.strip())
            
            # Insert into database
            execute_query('''
                INSERT INTO content_page (title, slug, excerpt, content, is_published, is_featured, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, slug, excerpt, content_text, is_published, is_featured, datetime.now(), datetime.now()))
            
            flash('Content page created successfully!', 'success')
            return redirect(url_for('admin_content'))
            
        except Exception as e:
            flash(f'Error creating content page: {str(e)}', 'error')
    
    content = '''
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1>Add New Content Page</h1>
        <a href="/cms/content" class="btn btn-secondary">
            <i class="fas fa-arrow-left"></i> Back to Content
        </a>
    </div>
    
    <div class="card">
        <div class="card-body">
            <form method="POST">
                <div class="row">
                    <div class="col-md-8">
                        <div class="mb-3">
                            <label class="form-label">Page Title *</label>
                            <input type="text" class="form-control" name="title" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">URL Slug</label>
                            <input type="text" class="form-control" name="slug" placeholder="auto-generated-from-title">
                            <small class="text-muted">Leave blank to auto-generate from title</small>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Excerpt</label>
                            <textarea class="form-control" name="excerpt" rows="2" placeholder="Brief description of the page"></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Content</label>
                            <div id="editor" style="height: 300px;"></div>
                            <textarea name="content" id="content" style="display: none;"></textarea>
                        </div>
                    </div>
                    
                    <div class="col-md-4">
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_published" id="is_published" checked>
                                <label class="form-check-label" for="is_published">
                                    Published
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
                    <a href="/cms/content" class="btn btn-secondary me-2">Cancel</a>
                    <button type="submit" class="btn btn-primary">Create Page</button>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        // Initialize Quill editor
        var quill = new Quill('#editor', {
            theme: 'snow',
            modules: {
                toolbar: [
                    [{ 'header': [1, 2, 3, false] }],
                    ['bold', 'italic', 'underline'],
                    ['link', 'blockquote', 'code-block'],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                    ['clean']
                ]
            }
        });
        
        // Update hidden textarea when form is submitted
        document.querySelector('form').addEventListener('submit', function() {
            document.querySelector('#content').value = quill.root.innerHTML;
        });
    </script>
    '''
    
    return render_template_string(get_admin_layout("Add Content Page", content, "content"))

@app.route('/cms/content/delete/<int:page_id>', methods=['POST'])
@login_required
def admin_content_delete(page_id):
    try:
        execute_query("DELETE FROM content_page WHERE id = ?", (page_id,))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        slides = execute_query("SELECT * FROM slide WHERE is_active = 1 ORDER BY sort_order") or []
        
        slides_data = []
        for slide in slides:
            slides_data.append({
                "id": slide.get('id'),
                "title": slide.get('title', ''),
                "introduction": slide.get('introduction', ''),
                "button_text": slide.get('button_text', ''),
                "button_url": slide.get('button_url', ''),
                "open_method": slide.get('open_method', 'same_tab'),
                "image": slide.get('image', ''),
                "is_active": bool(slide.get('is_active')),
                "is_featured": bool(slide.get('is_featured')),
                "sort_order": slide.get('sort_order', 0)
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
        # Get query parameters
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        include_past = request.args.get('include_past', 'false').lower() == 'true'
        
        # Build query
        query = "SELECT * FROM event"
        params = []
        
        # Filter by month/year if provided
        if month and year:
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)
            
            query += " WHERE date >= ? AND date < ?"
            params.extend([start_date, end_date])
        
        # Filter past events unless specifically requested
        if not include_past:
            if params:
                query += " AND date >= ?"
            else:
                query += " WHERE date >= ?"
            params.append(datetime.now())
        
        query += " ORDER BY date"
        
        events = execute_query(query, params) or []
        
        events_data = []
        current_date = datetime.now()
        
        for event in events:
            # Determine if event is in the past
            event_date = event.get('date')
            is_past = False
            if event_date:
                try:
                    if isinstance(event_date, str):
                        event_date = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                    is_past = event_date < current_date
                except:
                    pass
            
            event_data = {
                "id": event.get('id'),
                "title": event.get('title', ''),
                "description": event.get('description', ''),
                "date": event_date.isoformat() if event_date else None,
                "end_date": event.get('end_date'),
                "location": event.get('location', ''),
                "image": event.get('image', ''),
                "is_featured": bool(event.get('is_featured')),
                "is_past": is_past,
                "website_url": event.get('website_url', ''),
                "booking_url": event.get('booking_url', ''),
                "price": event.get('price', ''),
                "capacity": event.get('capacity'),
                "status": event.get('status', ''),
                "category": None  # Could be enhanced later
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
        slide_count = len(execute_query("SELECT * FROM slide") or [])
        councillor_count = len(execute_query("SELECT * FROM councillor") or [])
        event_count = len(execute_query("SELECT * FROM event") or [])
        meeting_count = len(execute_query("SELECT * FROM meeting") or [])
        
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
