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

# ORIGINAL DATABASE LOGIC (EXACTLY FROM YOUR WORKING FILE)
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

# Upload configuration (EXACTLY FROM YOUR WORKING FILE)
if os.environ.get("RENDER"):
    upload_path = "/tmp/uploads"
else:
    upload_path = os.path.join(basedir, "uploads")

app.config['UPLOAD_FOLDER'] = upload_path
os.makedirs(upload_path, exist_ok=True)

db = SQLAlchemy(app)

# ORIGINAL AUTOMAP LOGIC (EXACTLY FROM YOUR WORKING FILE)
Base = automap_base()

with app.app_context():
    Base.prepare(db.engine, reflect=True)
    
    # Access tables
    try:
        Slide = Base.classes.slide
    except:
        Slide = None
    
    try:
        Event = Base.classes.event
    except:
        Event = None
    
    try:
        Meeting = Base.classes.meeting
    except:
        Meeting = None
    
    try:
        Councillor = Base.classes.councillor
    except:
        Councillor = None

# === MINIMAL ADMIN INTERFACE (NEW) ===

@app.route('/cms/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin':
            user = AdminUser(1)
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>CMS Login</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container">
            <div class="row justify-content-center mt-5">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h4>CMS Login</h4>
                        </div>
                        <div class="card-body">
                            {% with messages = get_flashed_messages() %}
                                {% if messages %}
                                    {% for message in messages %}
                                        <div class="alert alert-danger">{{ message }}</div>
                                    {% endfor %}
                                {% endif %}
                            {% endwith %}
                            <form method="POST">
                                <div class="mb-3">
                                    <input type="text" class="form-control" name="username" placeholder="Username" value="admin">
                                </div>
                                <div class="mb-3">
                                    <input type="password" class="form-control" name="password" placeholder="Password" value="admin">
                                </div>
                                <button type="submit" class="btn btn-primary w-100">Login</button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/cms/dashboard')
@login_required
def admin_dashboard():
    try:
        # Get basic counts
        slide_count = db.session.query(Slide).count() if Slide else 0
        event_count = db.session.query(Event).count() if Event else 0
        meeting_count = db.session.query(Meeting).count() if Meeting else 0
        councillor_count = db.session.query(Councillor).count() if Councillor else 0
    except:
        slide_count = event_count = meeting_count = councillor_count = 0
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>CMS Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container">
                <span class="navbar-brand">CMS Dashboard</span>
                <a href="/cms/logout" class="btn btn-outline-light btn-sm">Logout</a>
            </div>
        </nav>
        
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3>{{ slide_count }}</h3>
                            <p>Slides</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3>{{ event_count }}</h3>
                            <p>Events</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3>{{ meeting_count }}</h3>
                            <p>Meetings</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3>{{ councillor_count }}</h3>
                            <p>Councillors</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5>Quick Actions</h5>
                        </div>
                        <div class="card-body">
                            <a href="/cms/slides" class="btn btn-primary me-2">Manage Slides</a>
                            <a href="/cms/events" class="btn btn-info me-2">Manage Events</a>
                            <a href="/cms/meetings" class="btn btn-warning me-2">Manage Meetings</a>
                            <a href="/cms/councillors" class="btn btn-success me-2">Manage Councillors</a>
                            <a href="/" class="btn btn-secondary" target="_blank">View Website</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', slide_count=slide_count, event_count=event_count, meeting_count=meeting_count, councillor_count=councillor_count)

@app.route('/cms/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

@app.route('/cms/slides')
@login_required
def admin_slides():
    try:
        slides = db.session.query(Slide).all() if Slide else []
    except:
        slides = []
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage Slides</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container">
                <a href="/cms/dashboard" class="navbar-brand">← Dashboard</a>
                <span class="navbar-text">Manage Slides</span>
            </div>
        </nav>
        
        <div class="container mt-4">
            <div class="card">
                <div class="card-header d-flex justify-content-between">
                    <h5>Homepage Slides</h5>
                    <button class="btn btn-primary btn-sm">Add New Slide</button>
                </div>
                <div class="card-body">
                    {% if slides %}
                        <div class="table-responsive">
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Title</th>
                                        <th>Introduction</th>
                                        <th>Active</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for slide in slides %}
                                    <tr>
                                        <td>{{ slide.title or '' }}</td>
                                        <td>{{ (slide.introduction or '')[:50] }}...</td>
                                        <td>
                                            {% if slide.is_active %}
                                                <span class="badge bg-success">Active</span>
                                            {% else %}
                                                <span class="badge bg-secondary">Inactive</span>
                                            {% endif %}
                                        </td>
                                        <td>
                                            <button class="btn btn-sm btn-outline-primary">Edit</button>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    {% else %}
                        <p class="text-center">No slides found.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', slides=slides)

@app.route('/cms/events')
@login_required
def admin_events():
    try:
        events = db.session.query(Event).all() if Event else []
    except:
        events = []
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage Events</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container">
                <a href="/cms/dashboard" class="navbar-brand">← Dashboard</a>
                <span class="navbar-text">Manage Events</span>
            </div>
        </nav>
        
        <div class="container mt-4">
            <div class="card">
                <div class="card-header d-flex justify-content-between">
                    <h5>Events</h5>
                    <button class="btn btn-primary btn-sm">Add New Event</button>
                </div>
                <div class="card-body">
                    {% if events %}
                        <div class="table-responsive">
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Title</th>
                                        <th>Date</th>
                                        <th>Location</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for event in events %}
                                    <tr>
                                        <td>{{ event.title or '' }}</td>
                                        <td>{{ event.date or '' }}</td>
                                        <td>{{ event.location or '' }}</td>
                                        <td>
                                            <button class="btn btn-sm btn-outline-primary">Edit</button>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    {% else %}
                        <p class="text-center">No events found.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', events=events)

@app.route('/cms/meetings')
@login_required
def admin_meetings():
    try:
        meetings = db.session.query(Meeting).all() if Meeting else []
    except:
        meetings = []
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage Meetings</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container">
                <a href="/cms/dashboard" class="navbar-brand">← Dashboard</a>
                <span class="navbar-text">Manage Meetings</span>
            </div>
        </nav>
        
        <div class="container mt-4">
            <div class="card">
                <div class="card-header d-flex justify-content-between">
                    <h5>Meetings</h5>
                    <button class="btn btn-primary btn-sm">Add New Meeting</button>
                </div>
                <div class="card-body">
                    {% if meetings %}
                        <div class="table-responsive">
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Title</th>
                                        <th>Date</th>
                                        <th>Location</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for meeting in meetings %}
                                    <tr>
                                        <td>{{ meeting.title or '' }}</td>
                                        <td>{{ meeting.meeting_date or '' }}</td>
                                        <td>{{ meeting.location or '' }}</td>
                                        <td>
                                            <button class="btn btn-sm btn-outline-primary">Edit</button>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    {% else %}
                        <p class="text-center">No meetings found.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', meetings=meetings)

@app.route('/cms/councillors')
@login_required
def admin_councillors():
    try:
        councillors = db.session.query(Councillor).all() if Councillor else []
    except:
        councillors = []
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manage Councillors</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <nav class="navbar navbar-dark bg-dark">
            <div class="container">
                <a href="/cms/dashboard" class="navbar-brand">← Dashboard</a>
                <span class="navbar-text">Manage Councillors</span>
            </div>
        </nav>
        
        <div class="container mt-4">
            <div class="card">
                <div class="card-header d-flex justify-content-between">
                    <h5>Councillors</h5>
                    <button class="btn btn-primary btn-sm">Add New Councillor</button>
                </div>
                <div class="card-body">
                    {% if councillors %}
                        <div class="table-responsive">
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Title</th>
                                        <th>Email</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for councillor in councillors %}
                                    <tr>
                                        <td>{{ councillor.name or '' }}</td>
                                        <td>{{ councillor.title or '' }}</td>
                                        <td>{{ councillor.email or '' }}</td>
                                        <td>
                                            <button class="btn btn-sm btn-outline-primary">Edit</button>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    {% else %}
                        <p class="text-center">No councillors found.</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', councillors=councillors)

# === ALL ORIGINAL ROUTES FROM YOUR WORKING FILE (UNCHANGED) ===

@app.route('/api/homepage/slides', methods=['GET', 'OPTIONS'])
def get_homepage_slides():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response
    
    try:
        if Slide:
            slides = db.session.query(Slide).filter_by(is_active=True).order_by(Slide.sort_order).all()
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
        else:
            slides_data = []
        
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
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        include_past = request.args.get('include_past', 'false').lower() == 'true'
        
        if Event:
            query = db.session.query(Event)
            
            if month and year:
                from datetime import datetime
                start_date = datetime(year, month, 1)
                if month == 12:
                    end_date = datetime(year + 1, 1, 1)
                else:
                    end_date = datetime(year, month + 1, 1)
                
                query = query.filter(Event.date >= start_date, Event.date < end_date)
            
            if not include_past:
                from datetime import datetime
                query = query.filter(Event.date >= datetime.now())
            
            events = query.order_by(Event.date).all()
            
            events_data = []
            for event in events:
                events_data.append({
                    "id": event.id,
                    "title": event.title,
                    "description": event.description,
                    "date": event.date.isoformat() if event.date else None,
                    "end_date": event.end_date.isoformat() if event.end_date else None,
                    "location": event.location,
                    "image": event.image,
                    "is_featured": event.is_featured,
                    "website_url": event.website_url,
                    "booking_url": event.booking_url,
                    "price": event.price,
                    "capacity": event.capacity,
                    "status": event.status
                })
        else:
            events_data = []
        
        return jsonify({"events": events_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    try:
        slide_count = db.session.query(Slide).count() if Slide else 0
        event_count = db.session.query(Event).count() if Event else 0
        meeting_count = db.session.query(Meeting).count() if Meeting else 0
        councillor_count = db.session.query(Councillor).count() if Councillor else 0
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "database_path": db_path,
            "slides": slide_count,
            "events": event_count,
            "meetings": meeting_count,
            "councillors": councillor_count,
            "admin_interface": "available at /cms/login"
        }), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route("/admin")
def admin_root():
    return redirect("/cms/login")

@app.route("/admin/<path:path>")
def serve_admin(path):
    return redirect("/cms/login")

@app.route("/login")
def login():
    return redirect("/cms/login")

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(os.path.join(app.static_folder), filename)

@app.route("/uploads/<path:filename>")
def serve_uploads(filename):
    uploads_dir = os.path.join(basedir, "uploads")
    return send_from_directory(uploads_dir, filename)

@app.route("/slider-fix.js")
def serve_slider_fix():
    return send_from_directory(basedir, "slider-fix.js")

@app.route("/events-fix.js")
def serve_events_fix():
    return send_from_directory(basedir, "events-fix.js")

@app.route("/")
def serve_frontend():
    return send_from_directory("dist", "index.html")

@app.route("/<path:path>")
def serve_frontend_paths(path):
    if path.startswith("api/") or path.startswith("cms/") or path.startswith("admin/") or path.startswith("assets/") or path.startswith("uploads/"):
        return "Not Found", 404
    return send_from_directory("dist", "index.html")

if __name__ == '__main__':
    app.run(debug=True)
