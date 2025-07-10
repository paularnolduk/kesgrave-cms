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

try:
    conn = sqlite3.connect(db_path)
    print("\u2705 Database connected successfully")
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    print("\ud83d\udccb Tables in DB:", tables)
    conn.close()
except Exception as e:
    print("\u274C Failed to connect to DB:", e)

# === Reflect Models ===
Base = automap_base()
Base.prepare(db.engine, reflect=True)

Slide = Base.classes.homepage_slide
QuickLink = Base.classes.homepage_quicklink
Councillor = Base.classes.councillor
Meeting = Base.classes.meeting
Event = Base.classes.event

# === API Routes ===
@app.route('/api/homepage/slides')
def get_homepage_slides():
    try:
        slides = db.session.query(Slide).all()
        return jsonify([{
            "id": s.id,
            "title": s.title,
            "introduction": s.introduction,
            "image": s.filename,
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
        links = db.session.query(QuickLink).all()
        return jsonify([{
            "id": l.id,
            "label": l.name,
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
        councillors = db.session.query(Councillor).all()
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
        meetings = db.session.query(Meeting).all()
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
        events = db.session.query(Event).all()
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
