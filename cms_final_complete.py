import os
import sqlite3
from flask import Flask, send_from_directory, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

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

try:
    conn = sqlite3.connect(db_path)
    print("\u2705 Database connected successfully")
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    print("\ud83d\udccb Tables in DB:", tables)
    conn.close()
except Exception as e:
    print("\u274C Failed to connect to DB:", e)

# === Models ===
class Slide(db.Model):
    __tablename__ = 'homepage_slide'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    introduction = db.Column(db.Text)
    filename = db.Column(db.Text)  # change from `image`
    button_text = db.Column(db.Text)
    button_url = db.Column(db.Text)
    open_method = db.Column(db.Text)
    is_featured = db.Column(db.Integer)
    sort_order = db.Column(db.Integer)
    is_active = db.Column(db.Integer)
    created = db.Column(db.Text)
    updated = db.Column(db.Text)

class QuickLink(db.Model):
    __tablename__ = 'homepage_quicklink'
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.Text)
    icon = db.Column(db.Text)
    url = db.Column(db.Text)
    sort_order = db.Column(db.Integer)
    is_active = db.Column(db.Integer)
    created = db.Column(db.Text)
    updated = db.Column(db.Text)

class Councillor(db.Model):
    __tablename__ = 'councillor'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    role = db.Column(db.Text)
    phone = db.Column(db.Text)
    email = db.Column(db.Text)
    sort_order = db.Column(db.Integer)
    is_active = db.Column(db.Integer)
    created = db.Column(db.Text)
    updated = db.Column(db.Text)

class Meeting(db.Model):
    __tablename__ = 'meeting'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    meeting_date = db.Column(db.Text)
    document_url = db.Column(db.Text)
    sort_order = db.Column(db.Integer)
    is_active = db.Column(db.Integer)
    created = db.Column(db.Text)
    updated = db.Column(db.Text)

class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    description = db.Column(db.Text)
    event_date = db.Column(db.Text)
    location = db.Column(db.Text)
    sort_order = db.Column(db.Integer)
    is_active = db.Column(db.Integer)
    created = db.Column(db.Text)
    updated = db.Column(db.Text)

# === API Routes ===
@app.route('/api/homepage/slides')
def get_homepage_slides():
    try:
        slides = Slide.query.all()
        return jsonify([{
            "id": s.id,
            "title": s.title,
            "introduction": s.introduction,
            "image": s.image,
            "button_text": s.button_text,
            "button_url": s.button_url,
            "open_method": s.open_method,
            "is_featured": s.is_featured,
            "sort_order": s.sort_order,
            "is_active": s.is_active
        } for s in slides])
    except Exception as e:
        return jsonify({"error": f"Failed to load slides: {str(e)}"}), 500

@app.route('/api/homepage/quick-links')
def get_quick_links():
    try:
        links = QuickLink.query.all()
        return jsonify([{
            "id": l.id,
            "label": l.label,
            "icon": l.icon,
            "url": l.url,
            "sort_order": l.sort_order,
            "is_active": l.is_active
        } for l in links])
    except Exception as e:
        return jsonify({"error": f"Failed to load quick links: {str(e)}"}), 500

@app.route('/api/councillors')
def get_councillors():
    try:
        councillors = Councillor.query.all()
        return jsonify([{
            "id": c.id,
            "name": c.name,
            "role": c.role,
            "phone": c.phone,
            "email": c.email
        } for c in councillors])
    except Exception as e:
        return jsonify({"error": f"Failed to load councillors: {str(e)}"}), 500

@app.route('/api/homepage/meetings')
def get_meetings():
    try:
        meetings = Meeting.query.all()
        return jsonify([{
            "id": m.id,
            "title": m.title,
            "date": m.meeting_date,
            "document_url": m.document_url
        } for m in meetings])
    except Exception as e:
        return jsonify({"error": f"Failed to load meetings: {str(e)}"}), 500

@app.route('/api/homepage/events')
def get_events():
    try:
        events = Event.query.all()
        return jsonify([{
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "date": e.event_date,
            "location": e.location
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
