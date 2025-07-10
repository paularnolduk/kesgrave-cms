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

# Debug DB connection and list tables
try:
    conn = sqlite3.connect(db_path)
    print("✅ Database connected successfully")

    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    print("📋 Tables in DB:", tables)

    conn.close()
except Exception as e:
    print("❌ Failed to connect to or inspect DB:", e)


# === Models ===
class Slide(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    image_url = db.Column(db.String(200))

class Councillor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    role = db.Column(db.String(100))
    contact = db.Column(db.String(200))

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    date = db.Column(db.String(100))
    document_url = db.Column(db.String(200))

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    date = db.Column(db.String(100))

class ContentBlock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section = db.Column(db.String(100))
    title = db.Column(db.String(100))
    content = db.Column(db.Text)

# === API Routes ===
@app.route('/api/homepage/slides')
def get_homepage_slides():
    try:
        slides = Slide.query.all()
        print(f"✅ Slides found: {len(slides)}")
        return jsonify([{"id": s.id, "title": s.title, "image_url": s.image_url} for s in slides])
    except Exception as e:
        print("❌ Error loading slides:", e)
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
