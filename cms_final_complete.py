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
    
    if Slide is None:  # Only initialize once
        with app.app_context():
            Base = automap_base()
            Base.prepare(db.engine, reflect=True)
            
            Slide = Base.classes.homepage_slide
            QuickLink = Base.classes.homepage_quicklink
            Councillor = Base.classes.councillor
            Meeting = Base.classes.meeting
            Event = Base.classes.event
            ContentPage = Base.classes.content_page
            ContentCategory = Base.classes.content_category
            MeetingType = Base.classes.meeting_type
            EventCategory = Base.classes.event_category
            Tag = Base.classes.tag
            CouncillorTag = Base.classes.councillor_tag

# Initialize models at startup
with app.app_context():
    try:
        # Test database connection
        with db.engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        print("✅ Database connected successfully")
        
        # Initialize models
        init_models()
        print("✅ Database models initialized")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

def safe_string(value):
    return value if value is not None else ""

def safe_getattr(obj, attr, default=""):
    """Safely get attribute with default value"""
    return getattr(obj, attr, default) if hasattr(obj, attr) else default

# === API Routes ===
@app.route("/api/homepage/slides")
def get_homepage_slides():
    init_models()
    try:
        slides = db.session.query(Slide).filter(Slide.is_active == True).order_by(Slide.sort_order).all()
        return jsonify([
            {
                "id": s.id,
                "title": safe_string(s.title),
                "introduction": safe_string(s.introduction),
                "filename": safe_string(s.image_filename), # Fixed: was s.filename
                "button_text": safe_string(s.button_name), # Fixed: was s.button_text
                "button_url": safe_string(s.button_url),
                "open_method": safe_string(s.open_method),
                "is_featured": s.is_featured,
                "sort_order": s.sort_order,
                "is_active": s.is_active,
                "created": s.created,
                "updated": s.updated,
            }
            for s in slides
        ])
    except Exception as e:
        return jsonify({"error": f"Failed to load slides: {e}"}), 500

@app.route("/api/homepage/meetings")
def get_homepage_meetings():
    init_models()
    try:
        today = datetime.now().date()
        # Join with meeting_type table to get type name
        meetings = db.session.query(Meeting, MeetingType).join(MeetingType, Meeting.meeting_type_id == MeetingType.id).filter(Meeting.meeting_date >= today).order_by(Meeting.meeting_date).all()
        
        # Group meetings by type and get the next one for each type
        next_meetings_by_type = {}
        for m, mt in meetings:
            if mt.name not in next_meetings_by_type:
                next_meetings_by_type[mt.name] = {
                    "id": m.id,
                    "title": safe_string(m.title),
                    "date": m.meeting_date.isoformat() if m.meeting_date else None,
                    "time": safe_string(m.meeting_time), # Added time field
                    "document_url": safe_string(m.agenda_filename or m.minutes_filename or m.draft_minutes_filename),
                    "type": safe_string(mt.name) # Added the missing type field!
                }

        return jsonify(list(next_meetings_by_type.values()))
    except Exception as e:
        return jsonify({"error": f"Failed to load meetings: {e}"}), 500

@app.route("/api/homepage/quick-links")
def get_homepage_quick_links():
    init_models()
    try:
        quick_links = db.session.query(QuickLink).filter(QuickLink.is_active == True).order_by(QuickLink.sort_order).all()
        return jsonify([
            {
                "id": ql.id,
                "title": safe_string(ql.title), # Fixed: was ql.name
                "description": safe_string(ql.description), # Added description
                "button_text": safe_string(ql.button_text), # Fixed: was ql.button_text
                "button_url": safe_string(ql.button_url), # Fixed: was ql.url
                "sort_order": ql.sort_order,
                "is_active": ql.is_active,
                "created": ql.created,
                "updated": ql.updated,
            }
            for ql in quick_links
        ])
    except Exception as e:
        return jsonify({"error": f"Failed to load quick links: {e}"}), 500

@app.route("/api/homepage/events")
def get_homepage_events():
    init_models()
    try:
        today = datetime.now().date()
        events = db.session.query(Event, EventCategory).join(EventCategory, Event.event_category_id == EventCategory.id, isouter=True).filter(Event.start_date >= today).order_by(Event.start_date).limit(6).all()
        return jsonify([
            {
                "id": e.id,
                "title": safe_string(e.title),
                "introduction": safe_string(e.introduction),
                "image": safe_string(e.image_filename), # Added image
                "start_date": e.start_date.isoformat() if e.start_date else None,
                "end_date": e.end_date.isoformat() if e.end_date else None,
                "start_time": safe_string(e.start_time),
                "end_time": safe_string(e.end_time),
                "location_name": safe_string(e.location_name),
                "category": {
                    "name": safe_string(ec.name),
                    "color": safe_string(ec.color),
                    "icon": safe_string(ec.icon)
                } if ec else None,
                "is_active": e.is_active,
                "created": e.created,
                "updated": e.updated,
            }
            for e, ec in events
        ])
    except Exception as e:
        return jsonify({"error": f"Failed to load events: {e}"}), 500

@app.route("/api/councillors")
def get_councillors():
    init_models()
    try:
        councillors = db.session.query(Councillor).filter(Councillor.is_active == True).order_by(Councillor.sort_order).all()
        return jsonify([
            {
                "id": c.id,
                "name": safe_string(c.name),
                "role": safe_string(c.title), # Fixed: was c.role
                "image": safe_string(c.image_filename),
                "is_active": c.is_active,
                "created": c.created,
                "updated": c.updated,
            }
            for c in councillors
        ])
    except Exception as e:
        return jsonify({"error": f"Failed to load councillors: {e}"}), 500

@app.route("/api/councillors/<int:councillor_id>")
def get_councillor(councillor_id):
    init_models()
    try:
        councillor = db.session.query(Councillor).filter(Councillor.id == councillor_id, Councillor.is_active == True).first()
        if not councillor:
            return jsonify({"error": "Councillor not found"}), 404
        
        # Get associated tags
        tags = db.session.query(Tag).join(CouncillorTag, Tag.id == CouncillorTag.tag_id).filter(CouncillorTag.councillor_id == councillor_id).all()

        return jsonify({
            "id": councillor.id,
            "name": safe_string(councillor.name),
            "role": safe_string(councillor.title),
            "image": safe_string(councillor.image_filename),
            "phone": safe_string(councillor.phone),
            "email": safe_string(councillor.email),
            "bio": safe_string(councillor.bio),
            "is_active": councillor.is_active,
            "created": councillor.created,
            "updated": councillor.updated,
            "tags": [{
                "id": t.id,
                "name": safe_string(t.name),
                "color": safe_string(t.color),
                "description": safe_string(t.description)
            } for t in tags]
        })
    except Exception as e:
        return jsonify({"error": f"Failed to load councillor: {e}"}), 500

@app.route("/api/councillor-tags")
def get_councillor_tags():
    init_models()
    try:
        tags = db.session.query(Tag).all()
        return jsonify([
            {
                "id": t.id,
                "name": safe_string(t.name),
                "color": safe_string(t.color),
                "description": safe_string(t.description)
            }
            for t in tags
        ])
    except Exception as e:
        return jsonify({"error": f"Failed to load councillor tags: {e}"}), 500

@app.route("/api/content/pages")
def get_content_pages():
    init_models()
    try:
        pages = db.session.query(ContentPage, ContentCategory).join(ContentCategory, ContentPage.category_id == ContentCategory.id, isouter=True).filter(ContentPage.is_active == True).order_by(ContentPage.sort_order).all()
        return jsonify([
            {
                "id": p.id,
                "title": safe_string(p.title),
                "introduction": safe_string(p.introduction),
                "description": safe_string(p.description),
                "category": {
                    "id": cc.id,
                    "name": safe_string(cc.name),
                    "color": safe_string(cc.color),
                    "url_path": safe_string(cc.url_path)
                } if cc else None,
                "is_active": p.is_active,
                "created": p.created,
                "updated": p.updated,
            }
            for p, cc in pages
        ])
    except Exception as e:
        return jsonify({"error": f"Failed to load content pages: {e}"}), 500

@app.route("/api/content/categories")
def get_content_categories():
    init_models()
    try:
        categories = db.session.query(ContentCategory).filter(ContentCategory.is_active == True).order_by(ContentCategory.sort_order).all()
        return jsonify([
            {
                "id": c.id,
                "name": safe_string(c.name),
                "color": safe_string(c.color),
                "url_path": safe_string(c.url_path),
                "is_active": c.is_active,
                "created": c.created,
                "updated": c.updated,
            }
            for c in categories
        ])
    except Exception as e:
        return jsonify({"error": f"Failed to load content categories: {e}"}), 500

@app.route("/api/meeting-types")
def get_meeting_types():
    init_models()
    try:
        meeting_types = db.session.query(MeetingType).filter(MeetingType.is_active == True).order_by(MeetingType.sort_order).all()
        return jsonify([
            {
                "id": mt.id,
                "name": safe_string(mt.name),
                "description": safe_string(mt.description),
                "color": safe_string(mt.color),
                "is_active": mt.is_active,
                "created": mt.created,
                "updated": mt.updated,
            }
            for mt in meeting_types
        ])
    except Exception as e:
        return jsonify({"error": f"Failed to load meeting types: {e}"}), 500

@app.route("/api/meetings/type/<string:type_name>")
def get_meetings_by_type(type_name):
    init_models()
    try:
        decoded_type_name = unquote(type_name)
        meeting_type = db.session.query(MeetingType).filter(MeetingType.name == decoded_type_name).first()
        if not meeting_type:
            return jsonify({"error": "Meeting type not found"}), 404

        meetings = db.session.query(Meeting).filter(Meeting.meeting_type_id == meeting_type.id).order_by(Meeting.meeting_date.desc()).all()
        return jsonify([
            {
                "id": m.id,
                "title": safe_string(m.title),
                "date": m.meeting_date.isoformat() if m.meeting_date else None,
                "time": safe_string(m.meeting_time),
                "document_url": safe_string(m.agenda_filename or m.minutes_filename or m.draft_minutes_filename),
                "is_active": m.is_active,
                "created": m.created,
                "updated": m.updated,
            }
            for m in meetings
        ])
    except Exception as e:
        return jsonify({"error": f"Failed to load meetings by type: {e}"}), 500

@app.route("/api/event-categories")
def get_event_categories():
    init_models()
    try:
        categories = db.session.query(EventCategory).filter(EventCategory.is_active == True).order_by(EventCategory.sort_order).all()
        return jsonify([
            {
                "id": c.id,
                "name": safe_string(c.name),
                "description": safe_string(c.description),
                "color": safe_string(c.color),
                "icon": safe_string(c.icon),
                "is_active": c.is_active,
                "created": c.created,
                "updated": c.updated,
            }
            for c in categories
        ])
    except Exception as e:
        return jsonify({"error": f"Failed to load event categories: {e}"}), 500

@app.route("/api/events/<int:event_id>")
def get_event(event_id):
    init_models()
    try:
        event = db.session.query(Event).filter(Event.id == event_id, Event.is_active == True).first()
        if not event:
            return jsonify({"error": "Event not found"}), 404
        
        return jsonify({
            "id": event.id,
            "title": safe_string(event.title),
            "introduction": safe_string(event.introduction),
            "description": safe_string(event.description),
            "image": safe_string(event.image_filename),
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
            "updated": event.updated,
        })
    except Exception as e:
        return jsonify({"error": f"Failed to load event: {e}"}), 500

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