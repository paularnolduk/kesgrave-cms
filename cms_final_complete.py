import os
import sqlite3
from flask import Flask, send_from_directory, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.ext.automap import automap_base
from urllib.parse import unquote

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

def safe_string(value):
    """Convert None/null values to empty string"""
    return value if value is not None else ""

def safe_getattr(obj, attr, default=""):
    """Safely get attribute with default value"""
    return getattr(obj, attr, default) if hasattr(obj, attr) else default

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

# === HOMEPAGE API Routes ===
@app.route('/api/homepage/slides')
def get_homepage_slides():
    try:
        init_models()
        slides = db.session.query(Slide).all()
        return jsonify([{
            "id": s.id,
            "title": safe_string(s.title),
            "introduction": safe_string(s.introduction),
            "image": safe_string(s.image_filename),
            "button_text": safe_string(s.button_name),
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
        init_models()
        links = db.session.query(QuickLink).all()
        return jsonify([{
            "id": l.id,
            "label": safe_string(l.title),
            "icon": safe_string(safe_getattr(l, 'icon', '')),
            "url": safe_string(l.button_url),
            "sort_order": l.sort_order,
            "is_active": l.is_active
        } for l in links])
    except Exception as e:
        return jsonify({"error": f"Failed to load quick links: {str(e)}"}), 500

@app.route('/api/homepage/meetings')
def get_meetings():
    try:
        init_models()
        # Join meetings with meeting_type to get the type name
        meetings = db.session.query(Meeting, MeetingType).join(MeetingType, Meeting.meeting_type_id == MeetingType.id).all()
        
        return jsonify([{
            "id": m.id,
            "title": safe_string(m.title),
            "date": m.meeting_date,
            "document_url": safe_string(m.agenda_filename or m.minutes_filename or m.draft_minutes_filename),
            "type": safe_string(mt.name)  # Add the missing type field
        } for m, mt in meetings])
    except Exception as e:
        return jsonify({"error": f"Failed to load meetings: {str(e)}"}), 500

@app.route('/api/homepage/events')
def get_events():
    try:
        init_models()
        events = db.session.query(Event).all()
        return jsonify([{
            "id": e.id,
            "title": safe_string(e.title),
            "description": safe_string(e.description),
            "date": e.start_date,
            "location": safe_string(e.location_name)
        } for e in events])
    except Exception as e:
        return jsonify({"error": f"Failed to load events: {str(e)}"}), 500

# === COUNCILLOR API Routes ===
@app.route('/api/councillors')
def get_councillors():
    try:
        init_models()
        councillors = db.session.query(Councillor).all()
        return jsonify([{
            "id": c.id,
            "name": safe_string(c.name),
            "role": safe_string(c.title),
            "phone": safe_string(c.phone),
            "email": safe_string(c.email)
        } for c in councillors])
    except Exception as e:
        return jsonify({"error": f"Failed to load councillors: {str(e)}"}), 500

@app.route('/api/councillors/<int:councillor_id>')
def get_councillor_detail(councillor_id):
    try:
        init_models()
        councillor = db.session.query(Councillor).filter(Councillor.id == councillor_id).first()
        
        if not councillor:
            return jsonify({"error": "Councillor not found"}), 404
        
        # Get councillor tags
        councillor_tags = db.session.query(Tag).join(CouncillorTag, Tag.id == CouncillorTag.tag_id).filter(CouncillorTag.councillor_id == councillor_id).all()
        
        return jsonify({
            "id": councillor.id,
            "name": safe_string(councillor.name),
            "role": safe_string(councillor.title),
            "phone": safe_string(councillor.phone),
            "email": safe_string(councillor.email),
            "bio": safe_string(safe_getattr(councillor, 'bio', '')),
            "image": safe_string(safe_getattr(councillor, 'image', '')),
            "tags": [{
                "id": tag.id,
                "name": safe_string(tag.name),
                "color": safe_string(tag.color),
                "description": safe_string(tag.description)
            } for tag in councillor_tags]
        })
    except Exception as e:
        return jsonify({"error": f"Failed to load councillor details: {str(e)}"}), 500

@app.route('/api/councillor-tags')
def get_councillor_tags():
    try:
        init_models()
        tags = db.session.query(Tag).all()
        return jsonify([{
            "id": t.id,
            "name": safe_string(t.name),
            "color": safe_string(t.color),
            "description": safe_string(t.description),
            "is_active": t.is_active
        } for t in tags])
    except Exception as e:
        return jsonify({"error": f"Failed to load councillor tags: {str(e)}"}), 500

# === CONTENT API Routes ===
@app.route('/api/content/pages')
def get_content_pages():
    try:
        init_models()
        pages = db.session.query(ContentPage).all()
        return jsonify([{
            "id": p.id,
            "title": safe_string(p.title),
            "slug": safe_string(p.slug),
            "short_description": safe_string(p.short_description),
            "long_description": safe_string(p.long_description),
            "category_id": p.category_id,
            "subcategory_id": p.subcategory_id,
            "status": safe_string(p.status),
            "is_featured": p.is_featured,
            "creation_date": p.creation_date,
            "approval_date": p.approval_date,
            "last_reviewed": p.last_reviewed,
            "next_review_date": p.next_review_date
        } for p in pages])
    except Exception as e:
        return jsonify({"error": f"Failed to load content pages: {str(e)}"}), 500

@app.route('/api/content/categories')
def get_content_categories():
    try:
        init_models()
        categories = db.session.query(ContentCategory).all()
        return jsonify([{
            "id": c.id,
            "name": safe_string(c.name),
            "description": safe_string(c.description),
            "color": safe_string(c.color),
            "is_active": c.is_active,
            "is_predefined": c.is_predefined,
            "url_path": safe_string(c.url_path)
        } for c in categories])
    except Exception as e:
        return jsonify({"error": f"Failed to load content categories: {str(e)}"}), 500

# === MEETING API Routes ===
@app.route('/api/meeting-types')
def get_meeting_types():
    try:
        init_models()
        meeting_types = db.session.query(MeetingType).all()
        return jsonify([{
            "id": mt.id,
            "name": safe_string(mt.name),
            "description": safe_string(mt.description),
            "color": safe_string(mt.color),
            "is_predefined": mt.is_predefined,
            "is_active": mt.is_active,
            "show_schedule_applications": mt.show_schedule_applications
        } for mt in meeting_types])
    except Exception as e:
        return jsonify({"error": f"Failed to load meeting types: {str(e)}"}), 500

@app.route('/api/meetings/type/<type_name>')
def get_meetings_by_type(type_name):
    try:
        init_models()
        # URL decode the type name
        decoded_type_name = unquote(type_name)
        
        # Join meetings with meeting_type to filter by type name
        meetings = db.session.query(Meeting).join(MeetingType, Meeting.meeting_type_id == MeetingType.id).filter(MeetingType.name == decoded_type_name).all()
        
        return jsonify([{
            "id": m.id,
            "title": safe_string(m.title),
            "date": m.meeting_date,
            "time": safe_string(str(m.meeting_time)) if m.meeting_time else "",
            "location": safe_string(m.location),
            "agenda_filename": safe_string(m.agenda_filename),
            "minutes_filename": safe_string(m.minutes_filename),
            "draft_minutes_filename": safe_string(m.draft_minutes_filename),
            "schedule_applications_filename": safe_string(m.schedule_applications_filename),
            "audio_filename": safe_string(m.audio_filename),
            "status": safe_string(m.status),
            "is_published": m.is_published,
            "notes": safe_string(m.notes),
            "agenda_title": safe_string(m.agenda_title),
            "agenda_description": safe_string(m.agenda_description),
            "minutes_title": safe_string(m.minutes_title),
            "minutes_description": safe_string(m.minutes_description),
            "draft_minutes_title": safe_string(m.draft_minutes_title),
            "draft_minutes_description": safe_string(m.draft_minutes_description),
            "schedule_applications_title": safe_string(m.schedule_applications_title),
            "schedule_applications_description": safe_string(m.schedule_applications_description),
            "audio_title": safe_string(m.audio_title),
            "audio_description": safe_string(m.audio_description),
            "summary_url": safe_string(m.summary_url)
        } for m in meetings])
    except Exception as e:
        return jsonify({"error": f"Failed to load meetings for type '{type_name}': {str(e)}"}), 500

# === EVENT API Routes ===
@app.route('/api/event-categories')
def get_event_categories():
    try:
        init_models()
        categories = db.session.query(EventCategory).all()
        return jsonify([{
            "id": c.id,
            "name": safe_string(c.name),
            "description": safe_string(c.description),
            "color": safe_string(c.color),
            "icon": safe_string(c.icon),
            "is_active": c.is_active
        } for c in categories])
    except Exception as e:
        return jsonify({"error": f"Failed to load event categories: {str(e)}"}), 500

@app.route('/api/events/<int:event_id>')
def get_event_detail(event_id):
    try:
        init_models()
        event = db.session.query(Event).filter(Event.id == event_id).first()
        
        if not event:
            return jsonify({"error": "Event not found"}), 404
        
        return jsonify({
            "id": event.id,
            "title": safe_string(event.title),
            "description": safe_string(event.description),
            "long_description": safe_string(safe_getattr(event, 'long_description', '')),
            "start_date": event.start_date,
            "end_date": safe_getattr(event, 'end_date', None),
            "start_time": safe_string(str(event.start_time)) if safe_getattr(event, 'start_time', None) else "",
            "end_time": safe_string(str(safe_getattr(event, 'end_time', ''))) if safe_getattr(event, 'end_time', None) else "",
            "location_name": safe_string(event.location_name),
            "location_address": safe_string(safe_getattr(event, 'location_address', '')),
            "contact_email": safe_string(safe_getattr(event, 'contact_email', '')),
            "contact_phone": safe_string(safe_getattr(event, 'contact_phone', '')),
            "website_url": safe_string(safe_getattr(event, 'website_url', '')),
            "booking_url": safe_string(safe_getattr(event, 'booking_url', '')),
            "price": safe_string(safe_getattr(event, 'price', '')),
            "capacity": safe_getattr(event, 'capacity', None),
            "is_featured": safe_getattr(event, 'is_featured', False),
            "status": safe_string(safe_getattr(event, 'status', '')),
            "image": safe_string(safe_getattr(event, 'image', ''))
        })
    except Exception as e:
        return jsonify({"error": f"Failed to load event details: {str(e)}"}), 500

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