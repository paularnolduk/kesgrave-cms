import os
import sqlite3
from flask import Flask, send_from_directory, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__, static_folder="dist/assets", template_folder="dist")
CORS(app)

# Use the correct SQLite DB in the instance folder with absolute path
basedir = os.path.abspath(os.path.dirname(__file__))

# === Render fix: use /tmp for write access ===
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

# Debug DB connection
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
    title = db.Column(db.String(200))
    introduction = db.Column(db.Text)
    image_filename = db.Column(db.String(255))
    button_name = db.Column(db.String(100))
    button_url = db.Column(db.String(500))
    open_method = db.Column(db.String(20))
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

class Councillor(db.Model):
    __tablename__ = 'councillor'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    role = db.Column(db.String(100))
    contact = db.Column(db.String(200))

class Meeting(db.Model):
    __tablename__ = 'meeting'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    date = db.Column(db.String(100))
    document_url = db.Column(db.String(200))

class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    date = db.Column(db.String(100))

class ContentBlock(db.Model):
    __tablename__ = 'content_page'
    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(100))
    title = db.Column(db.String(100))
    content = db.Column(db.Text)

# === API Routes ===
@app.route('/api/homepage/slides')
def get_homepage_slides():
    try:
        slides = Slide.query.all()
        print(f"\u2705 Slides found: {len(slides)}")
        return jsonify([
            {
                "id": s.id,
                "title": s.title,
                "introduction": s.introduction,
                "image_filename": s.image_filename,
                "button_name": s.button_name,
                "button_url": s.button_url,
                "open_method": s.open_method,
                "is_featured": s.is_featured,
                "sort_order": s.sort_order,
                "is_active": s.is_active,
                "created_at": s.created_at,
                "updated_at": s.updated_at
            } for s in slides])
    except Exception as e:
        print("\u274C Error loading slides:", e)
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to load slides"}), 500

@app.route('/api/councillors')
def get_councillors():
    councillors = Councillor.query.all()
    return jsonify([{"id": c.id, "name": c.name, "role": c.role, "contact": c.contact} for c in councillors])

@app.route('/api/meetings')
def get_meetings():
    meetings = Meeting.query.all()
    return jsonify([{"id": m.id, "title": m.title, "date": m.date, "document_url": m.document_url} for m in meetings])

@app.route('/api/events')
def get_events():
    events = Event.query.all()
    return jsonify([{"id": e.id, "title": e.title, "description": e.description, "date": e.date} for e in events])

@app.route('/api/content/<section>')
def get_content_section(section):
    blocks = ContentBlock.query.filter_by(section=section).all()
    return jsonify([{"id": b.id, "title": b.title, "content": b.content} for b in blocks])

@app.route('/api/debug/counts')
def debug_counts():
    return jsonify({
        "slides": Slide.query.count(),
        "councillors": Councillor.query.count(),
        "meetings": Meeting.query.count(),
        "events": Event.query.count(),
        "content_blocks": ContentBlock.query.count()
    })

@app.route('/api/councillor-tags')
def get_councillor_tags():
    # Placeholder route until tag model is created
    return jsonify([])

# === Admin/CMS Routes ===
@app.route("/admin")
def admin_root():
    return redirect("/admin/login")

@app.route("/admin/<path:path>")
def serve_admin(path):
    return send_from_directory("dist", "index.html")

@app.route("/login")
def login():
    return send_from_directory("dist", "index.html")

# === Serve Static Assets ===
@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(os.path.join(app.static_folder), filename)

# === Frontend Pages ===
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
