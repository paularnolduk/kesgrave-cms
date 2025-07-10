import os
import sqlite3
from flask import Flask, send_from_directory, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.ext.automap import automap_base

app = Flask(__name__, static_folder="dist/assets", template_folder="dist")
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))

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

db = SQLAlchemy(app)

# Global variables for models
Slide = None
QuickLink = None
Councillor = None
Meeting = None
Event = None

def init_models():
    """Initialize models within application context"""
    global Slide, QuickLink, Councillor, Meeting, Event
    
    if Slide is None:  # Only initialize once
        with app.app_context():
            Base = automap_base()
            Base.prepare(db.engine, reflect=True)
            
            Slide = Base.classes.homepage_slide
            QuickLink = Base.classes.homepage_quicklink
            Councillor = Base.classes.councillor
            Meeting = Base.classes.meeting
            Event = Base.classes.event

def safe_string(value):
    """Convert None/null values to empty string"""
    return value if value is not None else ""

# Test database connection
try:
    with app.app_context():
        conn = sqlite3.connect(db_path)
        print("✅ Database connected successfully")
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        print("📋 Tables in DB:", tables)
        conn.close()
except Exception as e:
    print("❌ Failed to connect to DB:", e)

# === API Routes ===
@app.route('/api/homepage/slides')
def get_homepage_slides():
    try:
        init_models()  # Ensure models are initialized
        slides = db.session.query(Slide).all()
        return jsonify([{
            "id": s.id,
            "title": safe_string(s.title),
            "introduction": safe_string(s.introduction),
            "image": safe_string(s.image_filename),  # FIXED: was s.filename, now s.image_filename
            "button_text": safe_string(s.button_name),  # FIXED: was s.button_text, now s.button_name
            "button_url": safe_string(s.button_url),
            "open_method": safe_string(s.open_method),
            "is_featured": s.is_featured,
            "sort_order": s.sort_order,
            "is_active": s.is_active
        } for s in slides])
    except Exception as e:
        return jsonify({"error": f"Failed to load slides: {str(e)}"}), 500

@app.route('/api/homepage/quick-links')
def get_quick_links():
    try:
        init_models()  # Ensure models are initialized
        links = db.session.query(QuickLink).all()
        return jsonify([{
            "id": l.id,
            "label": safe_string(l.title),  # FIXED: was l.name, now l.title
            "icon": safe_string(getattr(l, 'icon', '')),  # Handle missing icon column gracefully
            "url": safe_string(l.button_url),  # FIXED: was l.url, now l.button_url
            "sort_order": l.sort_order,
            "is_active": l.is_active
        } for l in links])
    except Exception as e:
        return jsonify({"error": f"Failed to load quick links: {str(e)}"}), 500

@app.route('/api/councillors')
def get_councillors():
    try:
        init_models()  # Ensure models are initialized
        councillors = db.session.query(Councillor).all()
        return jsonify([{
            "id": c.id,
            "name": safe_string(c.name),
            "role": safe_string(c.role),
            "phone": safe_string(c.phone),
            "email": safe_string(c.email)
        } for c in councillors])
    except Exception as e:
        return jsonify({"error": f"Failed to load councillors: {str(e)}"}), 500

@app.route('/api/homepage/meetings')
def get_meetings():
    try:
        init_models()  # Ensure models are initialized
        meetings = db.session.query(Meeting).all()
        return jsonify([{
            "id": m.id,
            "title": safe_string(m.title),
            "date": m.meeting_date,  # FIXED: This was already correct
            "document_url": safe_string(m.agenda_filename or m.minutes_filename or m.draft_minutes_filename)  # FIXED: Use available document fields + null safety
        } for m in meetings])
    except Exception as e:
        return jsonify({"error": f"Failed to load meetings: {str(e)}"}), 500

@app.route('/api/homepage/events')
def get_events():
    try:
        init_models()  # Ensure models are initialized
        events = db.session.query(Event).all()
        return jsonify([{
            "id": e.id,
            "title": safe_string(e.title),
            "description": safe_string(e.description),
            "date": e.start_date,  # FIXED: was e.event_date, now e.start_date
            "location": safe_string(e.location_name)  # FIXED: was e.location, now e.location_name
        } for e in events])
    except Exception as e:
        return jsonify({"error": f"Failed to load events: {str(e)}"}), 500

# === Static and Admin Routing ===
@app.route("/admin")
def admin_root():
    return redirect("/admin/login")

@app.route("/admin/<path:path>")
def serve_admin(path):
    return send_from_directory("dist", "index.html")

@app.route("/login")
def login():
    return send_from_directory("dist", "index.html")

@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(os.path.join(app.static_folder), filename)

@app.route("/")
def serve_frontend():
    return send_from_directory("dist", "index.html")

@app.route("/<path:path>")
def serve_frontend_paths(path):
    if path.startswith("api/") or path.startswith("admin/") or path.startswith("assets/"):
        return "Not Found", 404
    return send_from_directory("dist", "index.html")

if __name__ == '__main__':
    app.run(debug=True)