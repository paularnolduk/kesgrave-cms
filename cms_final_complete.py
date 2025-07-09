from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

# App configuration
app = Flask(__name__, static_folder="dist", static_url_path="")
CORS(app)
app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///cms.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join("static", "uploads")

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Database setup
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# ----------- MODELS ----------- #

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class HeaderLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100))
    url = db.Column(db.String(200))

class FooterLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100))
    url = db.Column(db.String(200))

class Councillor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    ward = db.Column(db.String(100))
    position = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(100))
    image_url = db.Column(db.String(200))
    status = db.Column(db.String(50))

class ContentPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100))
    title = db.Column(db.String(200))
    slug = db.Column(db.String(100))
    content = db.Column(db.Text)

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meeting_type = db.Column(db.String(100))
    title = db.Column(db.String(200))
    date = db.Column(db.String(100))
    link = db.Column(db.String(300))

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    date = db.Column(db.String(100))
    description = db.Column(db.Text)
    location = db.Column(db.String(200))

# ----------- LOGIN SETUP ----------- #

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----------- API ROUTES ----------- #

@app.route('/api/header-links')
def get_header_links():
    links = HeaderLink.query.all()
    return jsonify([{ 'text': l.text, 'url': l.url } for l in links])

@app.route('/api/footer-links')
def get_footer_links():
    links = FooterLink.query.all()
    return jsonify([{ 'text': l.text, 'url': l.url } for l in links])

@app.route('/api/councillors')
def get_councillors():
    councillors = Councillor.query.filter_by(status='published').all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'ward': c.ward,
        'position': c.position,
        'email': c.email,
        'phone': c.phone,
        'image_url': c.image_url
    } for c in councillors])

@app.route('/api/content/<category>/<slug>')
def get_content_page(category, slug):
    page = ContentPage.query.filter_by(category=category, slug=slug).first()
    if page:
        return jsonify({
            'title': page.title,
            'slug': page.slug,
            'content': page.content
        })
    return jsonify({'error': 'Page not found'}), 404

@app.route('/api/events')
def get_events():
    events = Event.query.all()
    return jsonify([{
        'title': e.title,
        'date': e.date,
        'description': e.description,
        'location': e.location
    } for e in events])

@app.route('/api/meetings/<meeting_type>')
def get_meetings(meeting_type):
    meetings = Meeting.query.filter_by(meeting_type=meeting_type).all()
    return jsonify([{
        'title': m.title,
        'date': m.date,
        'link': m.link
    } for m in meetings])

# ----------- STATIC FRONTEND ROUTES ----------- #

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("admin") or path.startswith("api") or path.startswith("static"):
        return "Not Found", 404
    full_path = os.path.join(app.static_folder, path)
    if path != "" and os.path.exists(full_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

# ----------- MAIN ----------- #

if __name__ == "__main__":
    app.run(debug=True)
