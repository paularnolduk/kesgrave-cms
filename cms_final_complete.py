import os
from flask import Flask, send_from_directory, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__, static_folder="dist/assets", template_folder="dist")
CORS(app)

# Use the correct SQLite DB in the instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///instance/kesgrave_working.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

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
    slides = Slide.query.all()
    return jsonify([{"id": s.id, "title": s.title, "image_url": s.image_url} for s in slides])

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