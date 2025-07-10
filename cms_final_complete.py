import os
import sqlite3
from flask import Flask, send_from_directory, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.ext.automap import automap_base
from urllib.parse import unquote
from sqlalchemy import text
from datetime import datetime

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
ContentPage = None
ContentCategory = None
MeetingType = None
EventCategory = None
Tag = None
CouncillorTag = None

def init_models():
    """Initialize models within application context"""
    global Slide, QuickLink, Councillor, Meeting, Event, ContentPage, ContentCategory, MeetingType, EventCategory, Tag, CouncillorTag
    
    if Slide is not None:
        return
    
    Base = automap_base()
    Base.prepare(db.engine, reflect=True)
    
    Slide = Base.classes.homepage_slide
    QuickLink = Base.classes.quick_link
    Councillor = Base.classes.councillor
    Meeting = Base.classes.meeting
    Event = Base.classes.event
    ContentPage = Base.classes.content_page
    ContentCategory = Base.classes.content_category
    MeetingType = Base.classes.meeting_type
    EventCategory = Base.classes.event_category
    Tag = Base.classes.tag
    CouncillorTag = Base.classes.councillor_tag

def safe_string(value):
    """Safely convert value to string, handling None values"""
    if value is None:
        return ""
    return str(value)

# === HOMEPAGE API Routes ===
@app.route('/api/homepage/slides')
def get_homepage_slides():
    try:
        init_models()
        # FIXED: Filter for active slides and order by sort_order
        slides = db.session.query(Slide).filter(Slide.is_active == True).order_by(Slide.sort_order).all()
        return jsonify([{
            "id": s.id,
            "title": safe_string(s.title),
            "introduction": safe_string(s.introduction),
            "image": safe_string(s.image_filename),  # FIXED: Just filename, not full path
            "button_text": safe_string(s.button_name),  # FIXED: Use button_name field
            "button_url": safe_string(s.button_url),
            "open_method": safe_string(s.open_method),
            "is_featured": s.is_featured,
            "sort_order": s.sort_order,
            "is_active": s.is_active
        } for s in slides])
    except Exception as e:
        return jsonify({"error": f"Failed to load slides: {e}"}), 500

@app.route('/api/homepage/quick-links')
def get_homepage_quick_links():
    try:
        init_models()
        quick_links = db.session.query(QuickLink).all()
        return jsonify([{
            "id": ql.id,
            "title": safe_string(ql.title),
            "description": safe_string(ql.description),
            "button_text": safe_string(ql.button_text),
            "button_url": safe_string(ql.button_url),
            "open_method": safe_string(ql.open_method),
            "sort_order": ql.sort_order,
            "is_active": ql.is_active
        } for ql in quick_links])
    except Exception as e:
        return jsonify({"error": f"Failed to load quick links: {e}"}), 500

@app.route('/api/homepage/meetings')
def get_homepage_meetings():
    try:
        init_models()
        meetings = db.session.query(Meeting).all()
        return jsonify([{
            "id": m.id,
            "title": safe_string(m.title),
            "date": m.date.isoformat() if m.date else None,
            "document_url": safe_string(m.document_url),
            "sort_order": m.sort_order,
            "is_active": m.is_active,
            "created": m.created,
            "updated": m.updated
        } for m in meetings])
    except Exception as e:
        return jsonify({"error": f"Failed to load meetings: {e}"}), 500

@app.route('/api/homepage/events')
def get_homepage_events():
    try:
        init_models()
        events = db.session.query(Event).all()
        return jsonify([{
            "id": e.id,
            "title": safe_string(e.title),
            "description": safe_string(e.description),
            "start_date": e.start_date.isoformat() if e.start_date else None,
            "end_date": e.end_date.isoformat() if e.end_date else None,
            "start_time": safe_string(e.start_time),
            "end_time": safe_string(e.end_time),
            "location_name": safe_string(e.location_name),
            "location_address": safe_string(e.location_address),
            "location_postcode": safe_string(e.location_postcode),
            "contact_name": safe_string(e.contact_name),
            "contact_email": safe_string(e.contact_email),
            "contact_phone": safe_string(e.contact_phone),
            "booking_link": safe_string(e.booking_link),
            "is_active": e.is_active,
            "created": e.created,
            "updated": e.updated
        } for e in events])
    except Exception as e:
        return jsonify({"error": f"Failed to load events: {e}"}), 500

# === COUNCILLORS API Routes ===
@app.route('/api/councillors')
def get_councillors():
    try:
        init_models()
        councillors = db.session.query(Councillor).all()
        return jsonify([{
            "id": c.id,
            "name": safe_string(c.name),
            "title": safe_string(c.title),
            "bio": safe_string(c.bio),
            "email": safe_string(c.email),
            "phone": safe_string(c.phone),
            "image_filename": safe_string(c.image_filename),
            "is_active": c.is_active,
            "sort_order": c.sort_order,
            "created": c.created,
            "updated": c.updated
        } for c in councillors])
    except Exception as e:
        return jsonify({"error": f"Failed to load councillors: {e}"}), 500

@app.route('/api/councillors/<int:councillor_id>')
def get_councillor(councillor_id):
    try:
        init_models()
        councillor = db.session.query(Councillor).filter(Councillor.id == councillor_id).first()
        if not councillor:
            return jsonify({"error": "Councillor not found"}), 404
        
        return jsonify({
            "id": councillor.id,
            "name": safe_string(councillor.name),
            "title": safe_string(councillor.title),
            "bio": safe_string(councillor.bio),
            "email": safe_string(councillor.email),
            "phone": safe_string(councillor.phone),
            "image_filename": safe_string(councillor.image_filename),
            "is_active": councillor.is_active,
            "sort_order": councillor.sort_order,
            "created": councillor.created,
            "updated": councillor.updated
        })
    except Exception as e:
        return jsonify({"error": f"Failed to load councillor: {e}"}), 500

# === EVENTS API Routes ===
@app.route('/api/events')
def get_events():
    try:
        init_models()
        events = db.session.query(Event).all()
        return jsonify([{
            "id": e.id,
            "title": safe_string(e.title),
            "description": safe_string(e.description),
            "start_date": e.start_date.isoformat() if e.start_date else None,
            "end_date": e.end_date.isoformat() if e.end_date else None,
            "start_time": safe_string(e.start_time),
            "end_time": safe_string(e.end_time),
            "location_name": safe_string(e.location_name),
            "location_address": safe_string(e.location_address),
            "location_postcode": safe_string(e.location_postcode),
            "contact_name": safe_string(e.contact_name),
            "contact_email": safe_string(e.contact_email),
            "contact_phone": safe_string(e.contact_phone),
            "booking_link": safe_string(e.booking_link),
            "is_active": e.is_active,
            "created": e.created,
            "updated": e.updated
        } for e in events])
    except Exception as e:
        return jsonify({"error": f"Failed to load events: {e}"}), 500

@app.route('/api/events/<int:event_id>')
def get_event(event_id):
    try:
        init_models()
        event = db.session.query(Event).filter(Event.id == event_id).first()
        if not event:
            return jsonify({"error": "Event not found"}), 404
        
        return jsonify({
            "id": event.id,
            "title": safe_string(event.title),
            "description": safe_string(event.description),
            "start_date": event.start_date.isoformat() if event.start_date else None,
            "end_date": event.end_date.isoformat() if event.end_date else None,
            "start_time": safe_string(event.start_time),
            "end_time": safe_string(event.end_time),
            "location_name": safe_string(event.location_name),
            "location_address": safe_string(event.location_address),
            "location_postcode": safe_string(event.location_postcode),
            "contact_name": safe_string(event.contact_name),
            "contact_email": safe_string(event.contact_email),
            "contact_phone": safe_string(event.contact_phone),
            "booking_link": safe_string(event.booking_link),
            "is_active": event.is_active,
            "created": event.created,
            "updated": event.updated
        })
    except Exception as e:
        return jsonify({"error": f"Failed to load event: {e}"}), 500

# === MEETINGS API Routes ===
@app.route('/api/meetings')
def get_meetings():
    try:
        init_models()
        meetings = db.session.query(Meeting).all()
        return jsonify([{
            "id": m.id,
            "title": safe_string(m.title),
            "date": m.date.isoformat() if m.date else None,
            "document_url": safe_string(m.document_url),
            "sort_order": m.sort_order,
            "is_active": m.is_active,
            "created": m.created,
            "updated": m.updated
        } for m in meetings])
    except Exception as e:
        return jsonify({"error": f"Failed to load meetings: {e}"}), 500

# === CONTENT API Routes ===
@app.route('/api/content')
def get_content():
    try:
        init_models()
        pages = db.session.query(ContentPage).all()
        return jsonify([{
            "id": p.id,
            "title": safe_string(p.title),
            "content": safe_string(p.content),
            "category_id": p.category_id,
            "slug": safe_string(p.slug),
            "is_active": p.is_active,
            "created": p.created,
            "updated": p.updated
        } for p in pages])
    except Exception as e:
        return jsonify({"error": f"Failed to load content: {e}"}), 500

@app.route('/api/content/categories')
def get_content_categories():
    try:
        init_models()
        categories = db.session.query(ContentCategory).all()
        return jsonify([{
            "id": c.id,
            "name": safe_string(c.name),
            "slug": safe_string(c.slug),
            "description": safe_string(c.description),
            "is_active": c.is_active,
            "sort_order": c.sort_order,
            "created": c.created,
            "updated": c.updated
        } for c in categories])
    except Exception as e:
        return jsonify({"error": f"Failed to load categories: {e}"}), 500

@app.route('/api/content/<category_slug>/<page_slug>')
def get_content_page(category_slug, page_slug):
    try:
        init_models()
        
        # First get the category
        category = db.session.query(ContentCategory).filter(ContentCategory.slug == category_slug).first()
        if not category:
            return jsonify({"error": "Category not found"}), 404
        
        # Then get the page
        page = db.session.query(ContentPage).filter(
            ContentPage.category_id == category.id,
            ContentPage.slug == page_slug
        ).first()
        
        if not page:
            return jsonify({"error": "Page not found"}), 404
        
        return jsonify({
            "id": page.id,
            "title": safe_string(page.title),
            "content": safe_string(page.content),
            "category_id": page.category_id,
            "category_name": safe_string(category.name),
            "category_slug": safe_string(category.slug),
            "slug": safe_string(page.slug),
            "is_active": page.is_active,
            "created": page.created,
            "updated": page.updated
        })
    except Exception as e:
        return jsonify({"error": f"Failed to load page: {e}"}), 500

# === Frontend Serving ===
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
