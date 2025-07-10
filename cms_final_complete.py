import os
import sqlite3
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from datetime import datetime, date, time
import secrets

# Configure Flask to serve static files from dist directory
base_dir = os.path.dirname(os.path.abspath(__file__))
dist_dir = os.path.join(base_dir, 'dist')

app = Flask(__name__, 
            static_folder=dist_dir,
            static_url_path='',
            template_folder=dist_dir)

app.config['SECRET_KEY'] = secrets.token_hex(16)

# Database configuration
db_path = os.path.join(base_dir, 'instance', 'kesgrave_working.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Global variables for models
Base = None
HomepageSlide = None
HomepageQuicklink = None
Meeting = None
MeetingType = None
Event = None
EventCategory = None
Councillor = None
Tag = None
CouncillorTag = None
ContentPage = None
ContentCategory = None

def safe_string(value):
    """Convert None values to empty strings"""
    return value if value is not None else ""

def safe_getattr(obj, attr, default=""):
    """Safely get attribute with default value"""
    return getattr(obj, attr, default) if hasattr(obj, attr) else default

def init_models():
    """Initialize database models using automap"""
    global Base, HomepageSlide, HomepageQuicklink, Meeting, MeetingType, Event, EventCategory, Councillor, Tag, CouncillorTag, ContentPage, ContentCategory
    
    if Base is not None:
        return  # Already initialized
    
    Base = automap_base()
    Base.prepare(db.engine, reflect=True)
    
    # Map tables to classes
    HomepageSlide = Base.classes.homepage_slide
    HomepageQuicklink = Base.classes.homepage_quicklink
    Meeting = Base.classes.meeting
    MeetingType = Base.classes.meeting_type
    Event = Base.classes.event
    EventCategory = Base.classes.event_category
    Councillor = Base.classes.councillor
    Tag = Base.classes.tag
    CouncillorTag = Base.classes.councillor_tag
    ContentPage = Base.classes.content_page
    ContentCategory = Base.classes.content_category

# Initialize models at startup
try:
    with app.app_context():
        # Test database connection using modern SQLAlchemy syntax
        with db.engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        print("✅ Database connected successfully")
        
        # Get table names using modern syntax
        with db.engine.connect() as connection:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
        print(f"📋 Tables in DB: {tables}")
        
        # Initialize models
        init_models()
        print("✅ Database models initialized")
        
except Exception as e:
    print(f"❌ Database initialization failed: {e}")

# Static file serving routes
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve assets from dist/assets directory"""
    return send_from_directory(os.path.join(dist_dir, 'assets'), filename)

@app.route('/static/uploads/<path:filename>')
def serve_uploads(filename):
    """Serve uploaded files"""
    uploads_dir = os.path.join(base_dir, 'static', 'uploads')
    return send_from_directory(uploads_dir, filename)

# Homepage API Routes

@app.route('/api/homepage/slides')
def get_slides():
    """Get homepage slides with full image URLs"""
    try:
        if not HomepageSlide:
            init_models()
        
        slides = db.session.query(HomepageSlide).filter_by(is_active=True).order_by(HomepageSlide.sort_order).all()
        
        return jsonify([{
            "id": s.id,
            "title": safe_string(s.title),
            "introduction": safe_string(s.introduction),
            "image": f"/static/uploads/{safe_string(s.image_filename)}" if s.image_filename else "",  # Full image URL
            "button_text": safe_string(s.button_name),  # Fixed field name
            "button_url": safe_string(s.button_url),
            "open_method": safe_string(s.open_method),
            "is_featured": bool(s.is_featured),
            "sort_order": s.sort_order,
            "is_active": bool(s.is_active)
        } for s in slides])
        
    except Exception as e:
        return jsonify({"error": f"Failed to load slides: {str(e)}"}), 500

@app.route('/api/homepage/events')
def get_homepage_events():
    """Get next 6 upcoming events with images and categories"""
    try:
        if not Event or not EventCategory:
            init_models()
        
        # Get current datetime
        now = datetime.now()
        
        # Query events with categories, filter future events, limit to 6, order by date
        events = db.session.query(Event, EventCategory).join(
            EventCategory, Event.category_id == EventCategory.id
        ).filter(
            Event.start_date >= now,
            Event.is_published == True
        ).order_by(Event.start_date.asc()).limit(6).all()
        
        return jsonify([{
            "id": e.id,
            "title": safe_string(e.title),
            "description": safe_string(e.description or e.short_description),
            "date": e.start_date.isoformat() if e.start_date else "",
            "location": safe_string(e.location_name),
            "image": f"/static/uploads/{safe_string(e.image_filename)}" if e.image_filename else "",  # Full image URL
            "category": {
                "name": safe_string(ec.name),
                "color": safe_string(ec.color),
                "icon": safe_string(ec.icon)
            }
        } for e, ec in events])
        
    except Exception as e:
        return jsonify({"error": f"Failed to load events: {str(e)}"}), 500

@app.route('/api/homepage/meetings')
def get_meetings():
    """Get next meeting for each meeting type"""
    try:
        if not Meeting or not MeetingType:
            init_models()
        
        # Get current date
        today = date.today()
        
        # Get next meeting for each meeting type
        meeting_types = db.session.query(MeetingType).all()
        next_meetings = []
        
        for mt in meeting_types:
            next_meeting = db.session.query(Meeting).filter(
                Meeting.meeting_type_id == mt.id,
                Meeting.meeting_date >= today,
                Meeting.is_published == True
            ).order_by(Meeting.meeting_date.asc(), Meeting.meeting_time.asc()).first()
            
            if next_meeting:
                next_meetings.append((next_meeting, mt))
        
        return jsonify([{
            "id": m.id,
            "title": safe_string(m.title),
            "date": m.meeting_date.isoformat() if m.meeting_date else "",
            "time": m.meeting_time.strftime('%H:%M') if m.meeting_time else "",  # Added time field
            "document_url": safe_string(m.agenda_filename or m.minutes_filename or m.draft_minutes_filename),
            "type": safe_string(mt.name)
        } for m, mt in next_meetings])
        
    except Exception as e:
        return jsonify({"error": f"Failed to load meetings: {str(e)}"}), 500

@app.route('/api/homepage/quick-links')
def get_quick_links():
    """Get homepage quick links with correct field names"""
    try:
        if not HomepageQuicklink:
            init_models()
        
        quicklinks = db.session.query(HomepageQuicklink).filter_by(is_active=True).order_by(HomepageQuicklink.sort_order).all()
        
        return jsonify([{
            "id": ql.id,
            "title": safe_string(ql.title),  # Fixed: was missing
            "description": safe_string(ql.description),  # Fixed: was missing  
            "button_text": safe_string(ql.button_name),  # Fixed: was missing
            "url": safe_string(ql.button_url),
            "open_method": safe_string(ql.open_method),
            "sort_order": ql.sort_order,
            "is_active": bool(ql.is_active)
        } for ql in quicklinks])
        
    except Exception as e:
        return jsonify({"error": f"Failed to load quick links: {str(e)}"}), 500

# Other API Routes (keeping all existing functionality)

@app.route('/api/councillors')
def get_councillors():
    """Get all councillors"""
    try:
        if not Councillor:
            init_models()
        
        councillors = db.session.query(Councillor).filter_by(is_active=True).all()
        
        return jsonify([{
            "id": c.id,
            "name": safe_string(c.name),
            "role": safe_string(c.title),  # Fixed: was c.role, now c.title
            "phone": safe_string(c.phone),
            "email": safe_string(c.email),
            "bio": safe_string(c.bio),
            "image": safe_string(c.image_filename),
            "is_active": bool(c.is_active)
        } for c in councillors])
        
    except Exception as e:
        return jsonify({"error": f"Failed to load councillors: {str(e)}"}), 500

@app.route('/api/councillors/<int:councillor_id>')
def get_councillor_detail(councillor_id):
    """Get individual councillor details with tags"""
    try:
        if not Councillor or not Tag or not CouncillorTag:
            init_models()
        
        councillor = db.session.query(Councillor).filter_by(id=councillor_id).first()
        if not councillor:
            return jsonify({"error": "Councillor not found"}), 404
        
        # Get councillor tags
        tags = db.session.query(Tag).join(CouncillorTag).filter(CouncillorTag.councillor_id == councillor_id).all()
        
        return jsonify({
            "id": councillor.id,
            "name": safe_string(councillor.name),
            "role": safe_string(councillor.title),
            "phone": safe_string(councillor.phone),
            "email": safe_string(councillor.email),
            "bio": safe_string(councillor.bio),
            "image": safe_string(councillor.image_filename),
            "is_active": bool(councillor.is_active),
            "tags": [{
                "id": t.id,
                "name": safe_string(t.name),
                "color": safe_string(t.color),
                "description": safe_string(t.description)
            } for t in tags]
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to load councillor: {str(e)}"}), 500

@app.route('/api/councillor-tags')
def get_councillor_tags():
    """Get all councillor tags"""
    try:
        if not Tag:
            init_models()
        
        tags = db.session.query(Tag).all()
        
        return jsonify([{
            "id": t.id,
            "name": safe_string(t.name),
            "color": safe_string(t.color),
            "description": safe_string(t.description)
        } for t in tags])
        
    except Exception as e:
        return jsonify({"error": f"Failed to load tags: {str(e)}"}), 500

@app.route('/api/events/<int:event_id>')
def get_event_detail(event_id):
    """Get individual event details"""
    try:
        if not Event or not EventCategory:
            init_models()
        
        event = db.session.query(Event, EventCategory).join(
            EventCategory, Event.category_id == EventCategory.id
        ).filter(Event.id == event_id).first()
        
        if not event:
            return jsonify({"error": "Event not found"}), 404
        
        e, ec = event
        
        return jsonify({
            "id": e.id,
            "title": safe_string(e.title),
            "short_description": safe_string(e.short_description),
            "description": safe_string(e.description),
            "start_date": e.start_date.isoformat() if e.start_date else "",
            "end_date": e.end_date.isoformat() if e.end_date else "",
            "all_day": bool(e.all_day),
            "location_name": safe_string(e.location_name),
            "location_address": safe_string(e.location_address),
            "location_url": safe_string(e.location_url),
            "contact_name": safe_string(e.contact_name),
            "contact_email": safe_string(e.contact_email),
            "contact_phone": safe_string(e.contact_phone),
            "booking_required": bool(e.booking_required),
            "booking_url": safe_string(e.booking_url),
            "max_attendees": e.max_attendees,
            "is_free": bool(e.is_free),
            "price": safe_string(e.price),
            "image_filename": safe_string(e.image_filename),
            "featured": bool(e.featured),
            "status": safe_string(e.status),
            "category": {
                "id": ec.id,
                "name": safe_string(ec.name),
                "color": safe_string(ec.color),
                "icon": safe_string(ec.icon),
                "description": safe_string(ec.description)
            }
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to load event: {str(e)}"}), 500

@app.route('/api/event-categories')
def get_event_categories():
    """Get all event categories"""
    try:
        if not EventCategory:
            init_models()
        
        categories = db.session.query(EventCategory).all()
        
        return jsonify([{
            "id": c.id,
            "name": safe_string(c.name),
            "color": safe_string(c.color),
            "icon": safe_string(c.icon),
            "description": safe_string(c.description)
        } for c in categories])
        
    except Exception as e:
        return jsonify({"error": f"Failed to load event categories: {str(e)}"}), 500

@app.route('/api/content/pages')
def get_content_pages():
    """Get all content pages"""
    try:
        if not ContentPage or not ContentCategory:
            init_models()
        
        pages = db.session.query(ContentPage, ContentCategory).join(
            ContentCategory, ContentPage.category_id == ContentCategory.id
        ).filter(ContentPage.is_published == True).all()
        
        return jsonify([{
            "id": p.id,
            "title": safe_string(p.title),
            "description": safe_string(p.description),
            "content": safe_string(p.content),
            "category": {
                "id": c.id,
                "name": safe_string(c.name),
                "color": safe_string(c.color),
                "url_path": safe_string(c.url_path)
            }
        } for p, c in pages])
        
    except Exception as e:
        return jsonify({"error": f"Failed to load content pages: {str(e)}"}), 500

@app.route('/api/content/categories')
def get_content_categories():
    """Get all content categories"""
    try:
        if not ContentCategory:
            init_models()
        
        categories = db.session.query(ContentCategory).all()
        
        return jsonify([{
            "id": c.id,
            "name": safe_string(c.name),
            "color": safe_string(c.color),
            "url_path": safe_string(c.url_path),
            "description": safe_string(c.description)
        } for c in categories])
        
    except Exception as e:
        return jsonify({"error": f"Failed to load content categories: {str(e)}"}), 500

@app.route('/api/meeting-types')
def get_meeting_types():
    """Get all meeting types"""
    try:
        if not MeetingType:
            init_models()
        
        meeting_types = db.session.query(MeetingType).all()
        
        return jsonify([{
            "id": mt.id,
            "name": safe_string(mt.name),
            "description": safe_string(mt.description),
            "color": safe_string(mt.color)
        } for mt in meeting_types])
        
    except Exception as e:
        return jsonify({"error": f"Failed to load meeting types: {str(e)}"}), 500

@app.route('/api/meetings/type/<type_name>')
def get_meetings_by_type(type_name):
    """Get meetings by meeting type name"""
    try:
        if not Meeting or not MeetingType:
            init_models()
        
        # URL decode the type name
        import urllib.parse
        decoded_type_name = urllib.parse.unquote(type_name)
        
        meetings = db.session.query(Meeting, MeetingType).join(
            MeetingType, Meeting.meeting_type_id == MeetingType.id
        ).filter(MeetingType.name == decoded_type_name).all()
        
        return jsonify([{
            "id": m.id,
            "title": safe_string(m.title),
            "date": m.meeting_date.isoformat() if m.meeting_date else "",
            "time": m.meeting_time.strftime('%H:%M') if m.meeting_time else "",
            "location": safe_string(m.location),
            "agenda_filename": safe_string(m.agenda_filename),
            "minutes_filename": safe_string(m.minutes_filename),
            "draft_minutes_filename": safe_string(m.draft_minutes_filename),
            "status": safe_string(m.status),
            "type": safe_string(mt.name)
        } for m, mt in meetings])
        
    except Exception as e:
        return jsonify({"error": f"Failed to load meetings: {str(e)}"}), 500

# Frontend routes
@app.route('/')
def index():
    return render_template('index.html')

# Smart catch-all route for SPA routing
@app.route('/<path:path>')
def catch_all(path):
    """
    Handle SPA routing while avoiding conflicts with static files
    """
    # Check if this looks like a file request (has file extension)
    if '.' in path.split('/')[-1]:
        # This looks like a file request, let Flask handle it normally
        # If file doesn't exist, Flask will return 404
        return "Not Found", 404
    
    # This looks like a page route, serve the SPA
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)