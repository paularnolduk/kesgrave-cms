import os
import sqlite3
import json
import re
from flask import Flask, send_from_directory, jsonify, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.ext.automap import automap_base
from urllib.parse import unquote
from datetime import datetime, date

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

def process_social_links(social_links_str):
    """
    Process social_links JSON string and return valid links only.
    Returns empty list if no valid links found (to hide section).
    """
    if not social_links_str or social_links_str.strip() == '':
        return []
    
    try:
        # Parse JSON string
        links = json.loads(social_links_str)
        
        if not isinstance(links, dict):
            return []
        
        valid_links = []
        
        # Define placeholder URLs that should be filtered out
        placeholder_patterns = [
            r'^https?://twitter\.com/?$',
            r'^https?://x\.com/?$', 
            r'^https?://linkedin\.com/?$',
            r'^https?://www\.linkedin\.com/?$',
            r'^https?://facebook\.com/?$',
            r'^https?://www\.facebook\.com/?$',
            r'^https?://instagram\.com/?$',
            r'^https?://www\.instagram\.com/?$'
        ]
        
        for platform, url in links.items():
            if not url or not isinstance(url, str):
                continue
                
            url = url.strip()
            
            # Skip empty URLs
            if not url:
                continue
            
            # Skip placeholder URLs
            is_placeholder = any(re.match(pattern, url, re.IGNORECASE) for pattern in placeholder_patterns)
            if is_placeholder:
                continue
            
            # Add valid link
            valid_links.append({
                'platform': platform,
                'url': url
            })
        
        return valid_links
        
    except (json.JSONDecodeError, AttributeError, TypeError):
        # If JSON parsing fails, return empty list
        return []

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
        # ONLY CHANGE: Add filtering for active slides and ordering
        slides = db.session.query(Slide).filter(Slide.is_active == True).order_by(Slide.sort_order).all()
        return jsonify([{
            "id": s.id,
            "title": safe_string(s.title),
            "introduction": safe_string(s.introduction),
            "image": f"/uploads/homepage/slides/{safe_string(s.image_filename)}" if s.image_filename else "",
            "button_text": safe_string(s.button_name),
            "button_url": safe_string(s.button_url),
            "open_method": safe_string(s.open_method),
            "is_featured": s.is_featured,
            "sort_order": s.sort_order,
            "is_active": s.is_active
        } for s in slides])
    except Exception as e:
        return jsonify({"error": f"Failed to load slides: {str(e)}"}), 500

# Events Image JS
@app.route("/events-fix.js")
def serve_events_fix():
    return send_from_directory(basedir, "events-fix.js")

@app.route("/events-fix-v2.js")
def serve_events_fix_v2():
    return send_from_directory(basedir, "events-fix-v2.js")

@app.route("/events-fix-v3.js")
def serve_events_fix_v3():
    return send_from_directory(basedir, "events-fix-v3.js")

@app.route("/events-fix-v4.js")
def serve_events_fix_v4():
    return send_from_directory(basedir, "events-fix-v4.js")

@app.route("/event-modal-fix.js")
def serve_event_modal_fix():
    return send_from_directory(basedir, "event-modal-fix.js")

# Meeting Page Fixes JS
@app.route("/meeting-page-dates.js")
def serve_meeting_page_dates():
    return send_from_directory(basedir, "meeting_page_dates.js")

@app.route('/api/homepage/quick-links')
def get_quick_links():
    try:
        init_models()
        links = db.session.query(QuickLink).all()
        return jsonify([{
            "id": l.id,
            "title": safe_string(l.title),                    # ✅ Title (working)
            "description": safe_string(l.description),       # ✅ FIXED: Added description
            "button_text": safe_string(l.button_name),       # ✅ FIXED: Added button text
            "url": safe_string(l.button_url),                # ✅ Button URL
            "icon": safe_string(safe_getattr(l, 'icon', '')), # ✅ Icon (if exists)
            "sort_order": l.sort_order,
            "is_active": l.is_active
        } for l in links])
    except Exception as e:
        return jsonify({"error": f"Failed to load quick links: {str(e)}"}), 500

@app.route('/api/homepage/meetings')
def get_meetings():
    try:
        init_models()
        # Get current date for filtering
        today = datetime.now().date()
        
        # Get all meeting types
        meeting_types = db.session.query(MeetingType).filter(MeetingType.is_active == True).all()
        
        result = []
        for mt in meeting_types:
            # Get the next upcoming meeting for this type
            next_meeting = db.session.query(Meeting).filter(
                Meeting.meeting_type_id == mt.id,
                Meeting.meeting_date >= today
            ).order_by(Meeting.meeting_date.asc()).first()
            
            if next_meeting:
                result.append({
                    "id": next_meeting.id,
                    "title": safe_string(next_meeting.title),
                    "date": next_meeting.meeting_date,
                    "time": safe_string(str(next_meeting.meeting_time)) if next_meeting.meeting_time else "",
                    "location": safe_string(next_meeting.location),
                    "document_url": safe_string(next_meeting.agenda_filename or next_meeting.minutes_filename or next_meeting.draft_minutes_filename),
                    "type": safe_string(mt.name)
                })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Failed to load meetings: {str(e)}"}), 500

@app.route('/api/homepage/events')
def get_events():
    try:
        init_models()
        # Get current datetime for filtering
        now = datetime.now()
        
        # Get all future events
        future_events = db.session.query(Event).filter(Event.start_date >= now).all()
        
        # Sort events: featured first, then by date
        sorted_events = sorted(future_events, key=lambda e: (not getattr(e, 'featured', False), e.start_date))
        
        # Limit to 6 events
        limited_events = sorted_events[:6]
        
        return jsonify([{
            "id": e.id,
            "title": safe_string(e.title),
            "description": safe_string(e.description),
            "date": e.start_date,
            "location": safe_string(e.location_name),
            "image": f"/uploads/events/{safe_string(e.image_filename)}" if e.image_filename else "",
            "featured": bool(getattr(e, 'featured', False))  # ✅ ADDED FEATURED FIELD
        } for e in limited_events])
    except Exception as e:
        return jsonify({"error": f"Failed to load events: {str(e)}"}), 500

# === COUNCILLOR API Routes ===
@app.route('/api/councillors')
def get_councillors():
    try:
        init_models()
        councillors = db.session.query(Councillor).filter(Councillor.is_published == True).all()
        
        result = []
        for c in councillors:
            # Get councillor tags for this councillor
            councillor_tags = db.session.query(Tag).join(
                CouncillorTag, Tag.id == CouncillorTag.tag_id
            ).filter(CouncillorTag.councillor_id == c.id).all()
            
            # Build image URL
            image_url = ""
            if c.image_filename:
                image_url = f"/uploads/councillors/{c.image_filename}"
            
            # Process social links - FIXED
            processed_social_links = process_social_links(safe_getattr(c, 'social_links', ''))
            
            result.append({
                "id": c.id,
                "name": safe_string(c.name),
                "title": safe_string(c.title),
                "role": safe_string(c.title),
                "phone": safe_string(c.phone),
                "email": safe_string(c.email),
                "intro": safe_string(safe_getattr(c, 'intro', '')),
                "bio": safe_string(safe_getattr(c, 'bio', '')),
                "image_url": image_url,
                "social_links": processed_social_links,
                "tags": [{
                    "id": tag.id,
                    "name": safe_string(tag.name),
                    "color": safe_string(tag.color),
                    "description": safe_string(tag.description)
                } for tag in councillor_tags]
            })
        
        return jsonify(result)
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
        
        # Build image URL
        image_url = ""
        if councillor.image_filename:
            image_url = f"/uploads/councillors/{councillor.image_filename}"
        
        # Process social links - FIXED
        processed_social_links = process_social_links(safe_getattr(councillor, 'social_links', ''))
        
        return jsonify({
            "id": councillor.id,
            "name": safe_string(councillor.name),
            "title": safe_string(councillor.title),
            "role": safe_string(councillor.title),
            "phone": safe_string(councillor.phone),
            "email": safe_string(councillor.email),
            "bio": safe_string(safe_getattr(councillor, 'bio', '')),
            "intro": safe_string(safe_getattr(councillor, 'intro', '')),
            "address": safe_string(safe_getattr(councillor, 'address', '')),
            "qualifications": safe_string(safe_getattr(councillor, 'qualifications', '')),
            "image": image_url,
            "image_url": image_url,
            "social_links": processed_social_links,
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
        
        result = []
        for p in pages:
            # Get category and subcategory objects
            category = None
            subcategory = None
            
            if p.category_id:
                cat = db.session.query(ContentCategory).filter(ContentCategory.id == p.category_id).first()
                if cat:
                    category = {
                        "id": cat.id,
                        "name": safe_string(cat.name),
                        "description": safe_string(cat.description),
                        "color": safe_string(cat.color)
                    }
            
            if p.subcategory_id:
                subcat = db.session.query(ContentCategory).filter(ContentCategory.id == p.subcategory_id).first()
                if subcat:
                    subcategory = {
                        "id": subcat.id,
                        "name": safe_string(subcat.name),
                        "description": safe_string(subcat.description),
                        "color": safe_string(subcat.color)
                    }
            
            # Use the most recent date as updated_at
            updated_at = p.last_reviewed or p.approval_date or p.creation_date
            
            result.append({
                "id": p.id,
                "title": safe_string(p.title),
                "slug": safe_string(p.slug),
                "short_description": safe_string(p.short_description),
                "long_description": safe_string(p.long_description),
                "category_id": p.category_id,
                "subcategory_id": p.subcategory_id,
                "category": category,  # Added category object
                "subcategory": subcategory,  # Added subcategory object
                "status": safe_string(p.status),
                "is_featured": p.is_featured,
                "creation_date": p.creation_date,
                "approval_date": p.approval_date,
                "last_reviewed": p.last_reviewed,
                "next_review_date": p.next_review_date,
                "updated_at": updated_at  # Added updated_at field
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Failed to load content pages: {str(e)}"}), 500

@app.route('/api/content/categories')
def get_content_categories():
    try:
        init_models()
        categories = db.session.query(ContentCategory).all()
        
        result = []
        for c in categories:
            # Count pages in this category
            page_count = db.session.query(ContentPage).filter(ContentPage.category_id == c.id).count()
            
            # Get subcategories (if any)
            subcategories = db.session.query(ContentCategory).filter(ContentCategory.parent_id == c.id).all() if hasattr(ContentCategory, 'parent_id') else []
            
            subcategories_data = []
            for sub in subcategories:
                sub_page_count = db.session.query(ContentPage).filter(ContentPage.subcategory_id == sub.id).count()
                subcategories_data.append({
                    "id": sub.id,
                    "name": safe_string(sub.name),
                    "description": safe_string(sub.description),
                    "color": safe_string(sub.color),
                    "page_count": sub_page_count
                })
            
            result.append({
                "id": c.id,
                "name": safe_string(c.name),
                "description": safe_string(c.description),
                "color": safe_string(c.color),
                "is_active": c.is_active,
                "is_predefined": c.is_predefined,
                "url_path": safe_string(c.url_path),
                "page_count": page_count,  # Added page count
                "subcategories": subcategories_data  # Added subcategories
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Failed to load content categories: {str(e)}"}), 500

# === MEETING API Routes ===
@app.route('/api/meeting-types')
def get_meeting_types():
    try:
        init_models()
        
        # Get all active meeting types
        meeting_types = db.session.query(MeetingType).filter(MeetingType.is_active == True).all()
        
        # Filter to only show specific meeting types that should appear on the page
        allowed_meeting_types = [
            'Community and Recreation',
            'Finance and Governance', 
            'Full Council Meetings',
            'Planning and Development',
            'Annual Town Meeting'  # This will be moved to last position
        ]
        
        # Filter meeting types
        filtered_types = [mt for mt in meeting_types if mt.name in allowed_meeting_types]
        
        # Custom ordering: Annual Town Meeting should be last
        def get_sort_order(meeting_type_name):
            order_map = {
                'Community and Recreation': 1,
                'Finance and Governance': 2,
                'Full Council Meetings': 3,
                'Planning and Development': 4,
                'Annual Town Meeting': 5  # Last position
            }
            return order_map.get(meeting_type_name, 999)
        
        # Sort meeting types by custom order
        filtered_types.sort(key=lambda mt: get_sort_order(mt.name))
        
        result = []
        today = date.today()
        
        for mt in filtered_types:
            # Get the next upcoming meeting for this type
            next_meeting = db.session.query(Meeting).filter(
                Meeting.meeting_type_id == mt.id,
                Meeting.meeting_date >= today,
                Meeting.is_published == True
            ).order_by(Meeting.meeting_date.asc()).first()
            
            # Count total meetings for this type
            meeting_count = db.session.query(Meeting).filter(
                Meeting.meeting_type_id == mt.id,
                Meeting.is_published == True
            ).count()
            
            # Build next meeting data if exists
            next_meeting_data = None
            if next_meeting:
                next_meeting_data = {
                    "id": next_meeting.id,
                    "title": safe_string(next_meeting.title),
                    "date": next_meeting.meeting_date.strftime('%d/%m/%Y') if next_meeting.meeting_date else None,
                    "time": str(next_meeting.meeting_time)[:5] if next_meeting.meeting_time else "",  # HH:MM format
                    "location": safe_string(next_meeting.location),
                    "agenda_filename": safe_string(next_meeting.agenda_filename),
                    "schedule_applications_filename": safe_string(next_meeting.schedule_applications_filename),
                    "status": safe_string(next_meeting.status)
                }
            
            result.append({
                "id": mt.id,
                "name": safe_string(mt.name),
                "description": safe_string(mt.description),
                "color": safe_string(mt.color),
                "is_active": mt.is_active,
                "show_schedule_applications": mt.show_schedule_applications,
                "meeting_count": meeting_count,
                "next_meeting": next_meeting_data  # ADDED: Next meeting data
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Failed to load meeting types: {str(e)}"}), 500

@app.route('/api/meetings/type/<type_name>')
def get_meetings_by_type(type_name):
    try:
        init_models()
        # URL decode the type name
        decoded_type_name = unquote(type_name)
        
        # Get pagination parameters from request
        from flask import request
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Join meetings with meeting_type to filter by type name
        meetings = db.session.query(Meeting).join(MeetingType, Meeting.meeting_type_id == MeetingType.id).filter(MeetingType.name == decoded_type_name).order_by(Meeting.meeting_date.desc()).all()
        
        # Get current date for categorization
        today = date.today()
        
        # Categorize meetings
        upcoming_meetings = []
        recent_meetings = []
        historic_meetings = []
        all_meetings = []  # Flat array for backward compatibility
        
        def format_date_with_comma(meeting_date):
            """Format date as 'Monday, 30 June 2025'"""
            if not meeting_date:
                return None
            return meeting_date.strftime('%A, %d %B %Y')
        
        def create_meeting_data(m):
            """Create meeting data object with file availability flags and legacy structure"""
            
            # Create legacy nested file structure for frontend compatibility
            agenda = None
            if m.agenda_filename and m.agenda_filename.strip():
                agenda = {
                    "file_url": f"/uploads/meetings/{m.agenda_filename}",
                    "title": safe_string(m.agenda_title) or "Meeting Agenda",
                    "description": safe_string(m.agenda_description) or ""
                }
            
            minutes = None
            if m.minutes_filename and m.minutes_filename.strip():
                minutes = {
                    "file_url": f"/uploads/meetings/{m.minutes_filename}",
                    "title": safe_string(m.minutes_title) or "Approved Minutes",
                    "description": safe_string(m.minutes_description) or ""
                }
            
            draft_minutes = None
            if m.draft_minutes_filename and m.draft_minutes_filename.strip():
                draft_minutes = {
                    "file_url": f"/uploads/meetings/{m.draft_minutes_filename}",
                    "title": safe_string(m.draft_minutes_title) or "Draft Minutes",
                    "description": safe_string(m.draft_minutes_description) or ""
                }
            
            schedule_applications = None
            if m.schedule_applications_filename and m.schedule_applications_filename.strip():
                schedule_applications = {
                    "file_url": f"/uploads/meetings/{m.schedule_applications_filename}",
                    "title": safe_string(m.schedule_applications_title) or "Schedule of Applications",
                    "description": safe_string(m.schedule_applications_description) or ""
                }
            
            audio = None
            if m.audio_filename and m.audio_filename.strip():
                audio = {
                    "file_url": f"/uploads/meetings/{m.audio_filename}",
                    "title": safe_string(m.audio_title) or "Meeting Audio",
                    "description": safe_string(m.audio_description) or ""
                }
            
            
            summary = None
            if m.summary_url and m.summary_url.strip():
                summary = {
                    "file_url": safe_string(m.summary_url),
                    "title": "Meeting Summary",
                    "description": "",
                    "button_text": "View Summary"
                }
            else:
                # Provide summary object even when no URL, with custom button text
                summary = {
                    "file_url": None,
                    "title": "Meeting Summary",
                    "description": "",
                    "button_text": "Summary Page Unavailable"
                }
            
            return {
                "id": m.id,
                "title": safe_string(m.title),
                "date": m.meeting_date.strftime('%d/%m/%Y') if m.meeting_date else None,  # Revert to DD/MM/YYYY
                "date_formatted": format_date_with_comma(m.meeting_date),  # Keep formatted version
                "date_raw": m.meeting_date.strftime('%d/%m/%Y') if m.meeting_date else None,  # Raw date for processing
                "time": str(m.meeting_time)[:5] if m.meeting_time else "",
                "location": safe_string(m.location),
                "status": safe_string(m.status),
                "is_published": m.is_published,
                "notes": safe_string(m.notes),
                
                # Summary button text (special handling)
                "summary_button_text": "Summary Page Unavailable" if not (m.summary_url and m.summary_url.strip()) else "View Summary",
                
                # LEGACY NESTED STRUCTURE (for frontend compatibility)
                "agenda": agenda,
                "minutes": minutes,
                "draft_minutes": draft_minutes,
                "schedule_applications": schedule_applications,
                "audio": audio,
                "summary": summary,
                
                # Enhanced file fields with URLs
                "agenda_filename": safe_string(m.agenda_filename),
                "agenda_title": safe_string(m.agenda_title),
                "agenda_description": safe_string(m.agenda_description),
                "agenda_url": f"/uploads/meetings/{m.agenda_filename}" if m.agenda_filename else None,
                
                "minutes_filename": safe_string(m.minutes_filename),
                "minutes_title": safe_string(m.minutes_title),
                "minutes_description": safe_string(m.minutes_description),
                "minutes_url": f"/uploads/meetings/{m.minutes_filename}" if m.minutes_filename else None,
                
                "draft_minutes_filename": safe_string(m.draft_minutes_filename),
                "draft_minutes_title": safe_string(m.draft_minutes_title),
                "draft_minutes_description": safe_string(m.draft_minutes_description),
                "draft_minutes_url": f"/uploads/meetings/{m.draft_minutes_filename}" if m.draft_minutes_filename else None,
                
                "schedule_applications_filename": safe_string(m.schedule_applications_filename),
                "schedule_applications_title": safe_string(m.schedule_applications_title),
                "schedule_applications_description": safe_string(m.schedule_applications_description),
                "schedule_applications_url": f"/uploads/meetings/{m.schedule_applications_filename}" if m.schedule_applications_filename else None,
                
                "audio_filename": safe_string(m.audio_filename),
                "audio_title": safe_string(m.audio_title),
                "audio_description": safe_string(m.audio_description),
                "audio_url": f"/uploads/meetings/{m.audio_filename}" if m.audio_filename else None,
                
                "summary_url": safe_string(m.summary_url),
                
                # Boolean flags for file availability (NEW)
                "has_agenda": bool(m.agenda_filename and m.agenda_filename.strip()),
                "has_minutes": bool(m.minutes_filename and m.minutes_filename.strip()),
                "has_draft_minutes": bool(m.draft_minutes_filename and m.draft_minutes_filename.strip()),
                "has_schedule_applications": bool(m.schedule_applications_filename and m.schedule_applications_filename.strip()),
                "has_audio": bool(m.audio_filename and m.audio_filename.strip()),
                "has_summary": bool(m.summary_url and m.summary_url.strip())
            }
        
        for m in meetings:
            meeting_data = create_meeting_data(m)
            
            # Add to flat array for backward compatibility
            all_meetings.append(meeting_data)
            
            # Categorize based on meeting date
            if m.meeting_date:
                if m.meeting_date >= today:
                    upcoming_meetings.append(meeting_data)
                else:
                    historic_meetings.append(meeting_data)
        
        # Recent meetings are the last 6 past meetings
        recent_meetings = historic_meetings[:6] if historic_meetings else []
        
        # Sort upcoming meetings by date (earliest first)
        upcoming_meetings.sort(key=lambda x: x['date'] if x['date'] else '')
        
        # Pagination for historic meetings
        total_historic = len(historic_meetings)
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_historic = historic_meetings[start_index:end_index]
        
        has_more_historic = end_index < total_historic
        show_load_more = total_historic >= 10  # Show Load More if 10+ meetings
        
        # Return enhanced backward compatible format
        return jsonify({
            # OLD FORMAT (for current frontend compatibility)
            "meetings": all_meetings,
            
            # NEW FORMAT (enhanced with pagination and flags)
            "upcoming": upcoming_meetings,
            "recent": recent_meetings,
            "historic": paginated_historic,  # Paginated historic meetings
            
            # PAGINATION INFO
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_historic": total_historic,
                "has_more": has_more_historic,
                "showing": len(paginated_historic),
                "total_pages": (total_historic + per_page - 1) // per_page,
                "show_load_more_button": show_load_more,  # Frontend guidance
                "load_more_enabled": has_more_historic,   # Whether button should be enabled
                "load_more_text": "Load More Meetings" if has_more_historic else "All Meetings Loaded"
            },
            
            # UI GUIDANCE (for frontend implementation)
            "ui_hints": {
                "date_format": "formatted_with_comma",  # Tells frontend to use formatted dates
                "summary_button_text_field": "summary_button_text",  # Custom summary text
                "load_more_position": "left_of_back_button",  # UI positioning hint
                "load_more_threshold": 10  # Show button when >= 10 meetings
            },
            
            # METADATA
            "total_count": len(meetings),
            "format_version": "v3_enhanced",
            "features": ["file_flags", "pagination", "formatted_dates"]
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to load meetings for type '{type_name}': {str(e)}"}), 500



@app.route('/api/meetings/<int:meeting_id>')
def get_meeting_detail(meeting_id):
    try:
        init_models()
        meeting = db.session.query(Meeting).filter(Meeting.id == meeting_id).first()
        
        if not meeting:
            return jsonify({"error": "Meeting not found"}), 404
        
        # Get meeting type info
        meeting_type = db.session.query(MeetingType).filter(MeetingType.id == meeting.meeting_type_id).first()
        
        # Build file URLs
        agenda_url = None
        if meeting.agenda_filename:
            agenda_url = f"/uploads/meetings/{meeting.agenda_filename}"
        
        schedule_applications_url = None
        if meeting.schedule_applications_filename:
            schedule_applications_url = f"/uploads/meetings/{meeting.schedule_applications_filename}"
        
        minutes_url = None
        if meeting.minutes_filename:
            minutes_url = f"/uploads/meetings/{meeting.minutes_filename}"
        
        draft_minutes_url = None
        if meeting.draft_minutes_filename:
            draft_minutes_url = f"/uploads/meetings/{meeting.draft_minutes_filename}"
        
        audio_url = None
        if meeting.audio_filename:
            audio_url = f"/uploads/meetings/{meeting.audio_filename}"
        
        return jsonify({
            "id": meeting.id,
            "title": safe_string(meeting.title),
            "meeting_type": {
                "id": meeting_type.id if meeting_type else None,
                "name": safe_string(meeting_type.name) if meeting_type else "",
                "color": safe_string(meeting_type.color) if meeting_type else "",
                "show_schedule_applications": meeting_type.show_schedule_applications if meeting_type else False
            },
            "date": meeting.meeting_date.strftime('%d/%m/%Y') if meeting.meeting_date else None,
            "time": str(meeting.meeting_time)[:5] if meeting.meeting_time else "",
            "location": safe_string(meeting.location),
            "status": safe_string(meeting.status),
            "is_published": meeting.is_published,
            "notes": safe_string(meeting.notes),
            "agenda": {
                "filename": safe_string(meeting.agenda_filename),
                "file_url": agenda_url,
                "title": safe_string(safe_getattr(meeting, 'agenda_title', '')),
                "description": safe_string(safe_getattr(meeting, 'agenda_description', ''))
            } if meeting.agenda_filename else None,
            "schedule_applications": {
                "filename": safe_string(meeting.schedule_applications_filename),
                "file_url": schedule_applications_url,
                "title": safe_string(safe_getattr(meeting, 'schedule_applications_title', '')),
                "description": safe_string(safe_getattr(meeting, 'schedule_applications_description', ''))
            } if meeting.schedule_applications_filename else None,
            "minutes": {
                "filename": safe_string(meeting.minutes_filename),
                "file_url": minutes_url,
                "title": safe_string(safe_getattr(meeting, 'minutes_title', '')),
                "description": safe_string(safe_getattr(meeting, 'minutes_description', ''))
            } if meeting.minutes_filename else None,
            "draft_minutes": {
                "filename": safe_string(meeting.draft_minutes_filename),
                "file_url": draft_minutes_url,
                "title": safe_string(safe_getattr(meeting, 'draft_minutes_title', '')),
                "description": safe_string(safe_getattr(meeting, 'draft_minutes_description', ''))
            } if meeting.draft_minutes_filename else None,
            "audio": {
                "filename": safe_string(meeting.audio_filename),
                "file_url": audio_url,
                "title": safe_string(safe_getattr(meeting, 'audio_title', '')),
                "description": safe_string(safe_getattr(meeting, 'audio_description', ''))
            } if meeting.audio_filename else None,
            "summary_url": safe_string(safe_getattr(meeting, 'summary_url', ''))
        })
    except Exception as e:
        return jsonify({"error": f"Failed to load meeting details: {str(e)}"}), 500

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

# Route to serve uploaded images
@app.route("/uploads/<path:filename>")
def serve_uploads(filename):
    """Serve uploaded files from the uploads directory"""
    uploads_dir = os.path.join(basedir, "uploads")
    return send_from_directory(uploads_dir, filename)

# Route to serve slider fix script
@app.route("/slider-fix.js")
def serve_slider_fix():
    return send_from_directory(basedir, "slider-fix.js")

@app.route("/")
def serve_frontend():
    return send_from_directory("dist", "index.html")

@app.route("/<path:path>")
def serve_frontend_paths(path):
    if path.startswith("api/") or path.startswith("admin/") or path.startswith("assets/") or path.startswith("uploads/"):
        return "Not Found", 404
    return send_from_directory("dist", "index.html")

if __name__ == '__main__':
    app.run(debug=True)