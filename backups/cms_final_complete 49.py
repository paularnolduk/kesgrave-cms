from flask import Flask, render_template_string, redirect, url_for, request, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os
import re
import json
import uuid
from werkzeug.utils import secure_filename

from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)

# Footer Links API Endpoint
@app.route('/api/footer-links', methods=['GET'])
def get_footer_links():
    """API endpoint to get footer links for the frontend website"""
    try:
        # You can customize these links or pull from database
        footer_links = [
            {'title': 'Privacy Policy', 'url': '/privacy-policy'},
            {'title': 'Terms of Service', 'url': '/terms'},
            {'title': 'Accessibility Statement', 'url': '/accessibility'},
            {'title': 'Contact Us', 'url': '/contact'},
            {'title': 'Freedom of Information', 'url': '/foi'},
            {'title': 'Complaints Procedure', 'url': '/complaints'}
        ]
        
        return jsonify(footer_links)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Header Links API Endpoint (Optional)
@app.route('/api/header-links', methods=['GET'])
def get_header_links():
    """API endpoint to get header navigation links"""
    try:
        header_links = [
            {'title': 'Home', 'url': '/', 'active': True},
            {'title': 'Councillors', 'url': '/councillors', 'active': True},
            {'title': 'Information', 'url': '/content', 'active': True},
            {'title': 'Meetings', 'url': '/ktc-meetings', 'active': True},
            {'title': 'Things to Do', 'url': '/ktc-events', 'active': True},
            {'title': 'Contact', 'url': '/contact', 'active': True}
        ]
        
        return jsonify(header_links)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Content Pages API Endpoint (Optional - for dynamic content)
@app.route('/api/content/<category>/<page>', methods=['GET'])
def get_content_page(category, page):
    """Get specific content page from CMS"""
    try:
        # Query your ContentPage model
        content_page = ContentPage.query.filter_by(
            category=category.replace('-', ' ').title(),
            slug=page
        ).first()
        
        if not content_page:
            return jsonify({'error': 'Page not found'}), 404
            
        return jsonify({
            'title': content_page.title,
            'content': content_page.content,
            'category': content_page.category,
            'last_updated': content_page.updated_at.isoformat() if content_page.updated_at else None,
            'status': content_page.status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# CORS Support for Local Development
CORS(app, origins=['http://localhost:5173', 'http://127.0.0.1:5173'], supports_credentials=True)

@app.after_request
def after_request(response):
    """Add CORS headers for local development"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Events API Endpoint (Optional - for dynamic events)
@app.route('/api/events', methods=['GET'])
def get_events():
    """Get events for the frontend website"""
    try:
        events = Event.query.filter_by(status='published').order_by(Event.date.desc()).all()
        events_data = []
        
        for event in events:
            events_data.append({
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'date': event.date.isoformat() if event.date else None,
                'time': event.time,
                'location': event.location,
                'category': event.category
            })
        
        return jsonify(events_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Meetings API Endpoint (Optional - for dynamic meetings)
@app.route('/api/meetings/<meeting_type>', methods=['GET'])
def get_meetings(meeting_type):
    """Get meetings by type for the frontend website"""
    try:
        meetings = Meeting.query.filter_by(
            type=meeting_type.replace('-', ' ').title()
        ).order_by(Meeting.date.desc()).all()
        
        meetings_data = []
        for meeting in meetings:
            meetings_data.append({
                'id': meeting.id,
                'title': meeting.title,
                'date': meeting.date.isoformat() if meeting.date else None,
                'time': meeting.time,
                'location': meeting.location,
                'agenda_url': meeting.agenda_url,
                'minutes_url': meeting.minutes_url
            })
        
        return jsonify(meetings_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Event Detail API Endpoint

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kesgrave-cms-secret-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kesgrave_working.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Create upload directories
upload_dirs = ['councillors', 'content/images', 'content/downloads', 'events', 'meetings', 'homepage/logo', 'homepage/slides']
for upload_dir in upload_dirs:
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], upload_dir), exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for authentication
class AdminUser(UserMixin):
    def __init__(self, id, username='admin'):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    return AdminUser(user_id)

# Helper function to format dates in UK format
def format_uk_date(date_obj):
    """Format datetime object to UK format DD/MM/YYYY"""
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%d/%m/%Y')
    return date_obj

def format_uk_datetime(date_obj):
    """Format datetime object to UK format DD/MM/YYYY HH:MM"""
    if isinstance(date_obj, datetime):
        return date_obj.strftime('%d/%m/%Y %H:%M')
    return date_obj

# Add template filters
app.jinja_env.filters['uk_date'] = format_uk_date
app.jinja_env.filters['uk_datetime'] = format_uk_datetime

# Standardized sidebar template for consistent navigation across all CMS pages
def get_sidebar_html(active_page=''):
    """
    Generate standardized sidebar HTML for all CMS pages
    active_page: string indicating which page should be highlighted as active
    """
    return f'''
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link {'active' if active_page == 'dashboard' else ''}">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/homepage" class="nav-link {'active' if active_page == 'homepage' else ''}">
                    <i class="fas fa-home me-2"></i>Homepage
                </a>
                <a href="/content" class="nav-link {'active' if active_page == 'content' else ''}">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/meetings" class="nav-link {'active' if active_page == 'meetings' else ''}">
                    <i class="fas fa-handshake me-2"></i>Meetings
                </a>
                <a href="/events" class="nav-link {'active' if active_page == 'events' else ''}">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/councillors" class="nav-link {'active' if active_page == 'councillors' else ''}">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link {'active' if active_page == 'tags' else ''}">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content-review" class="nav-link {'active' if active_page == 'content-review' else ''}">
                    <i class="fas fa-clipboard-check me-2"></i>Content Review System
                </a>
                <a href="/settings" class="nav-link {'active' if active_page == 'settings' else ''}">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
    '''

# Standardized CSS for sidebar styling
def get_sidebar_css():
    """
    Generate standardized CSS for sidebar styling
    """
    return '''
        .sidebar {
            position: fixed;
            top: 0;
            left: 0;
            height: 100vh;
            width: 260px;
            background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
            color: white;
            z-index: 1000;
            overflow-y: auto;
        }
        .main-content {
            margin-left: 260px;
            padding: 2rem;
            background-color: #f8f9fa;
            min-height: 100vh;
        }
        .nav-link {
            color: rgba(255,255,255,0.8);
            padding: 0.75rem 1.5rem;
            display: block;
            text-decoration: none;
            transition: all 0.3s ease;
        }
        .nav-link:hover, .nav-link.active {
            color: white;
            background: rgba(255,255,255,0.1);
        }
    '''

# Database Models
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(7), default='#3498db')
    description = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CouncillorTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    councillor_id = db.Column(db.Integer, db.ForeignKey('councillor.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=False)

class Councillor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100))
    intro = db.Column(db.Text)  # Short introduction
    bio = db.Column(db.Text)
    address = db.Column(db.Text)  # Contact address
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    qualifications = db.Column(db.Text)  # Qualifications/credentials
    image_filename = db.Column(db.String(255))
    social_links = db.Column(db.Text)  # JSON string for social media links
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to tags through association table
    tags = db.relationship('Tag', secondary='councillor_tag', backref='councillors')

# Content models for Phase 2
class ContentCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#3498db')
    is_active = db.Column(db.Boolean, default=True)
    is_predefined = db.Column(db.Boolean, default=False)  # For predefined categories that can't be deleted
    url_path = db.Column(db.String(200), unique=True)  # URL path for the category
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContentSubcategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('content_category.id'), nullable=False)
    is_predefined = db.Column(db.Boolean, default=False)  # For predefined subcategories that can't be deleted
    url_path = db.Column(db.String(200))  # URL path for the subcategory
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    category = db.relationship('ContentCategory', backref='subcategories')

class ContentPage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True)
    short_description = db.Column(db.Text)  # Short description
    long_description = db.Column(db.Text)   # Long description (rich text)
    category_id = db.Column(db.Integer, db.ForeignKey('content_category.id'))
    subcategory_id = db.Column(db.Integer, db.ForeignKey('content_subcategory.id'))
    status = db.Column(db.String(20), default='Draft')  # Draft, Published, Archived
    is_featured = db.Column(db.Boolean, default=False)
    
    # Content dates
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    approval_date = db.Column(db.DateTime)
    last_reviewed = db.Column(db.DateTime)
    next_review_date = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = db.relationship('ContentCategory', backref='pages')
    subcategory = db.relationship('ContentSubcategory', backref='pages')

# Content Gallery Model for multiple images with metadata
class ContentGallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_page_id = db.Column(db.Integer, db.ForeignKey('content_page.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    alt_text = db.Column(db.String(200))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    content_page = db.relationship('ContentPage', backref='gallery_images')

# Content Links Model for related links
class ContentLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_page_id = db.Column(db.Integer, db.ForeignKey('content_page.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    new_tab = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    content_page = db.relationship('ContentPage', backref='related_links')

# Content Downloads Model for file downloads
class ContentDownload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content_page_id = db.Column(db.Integer, db.ForeignKey('content_page.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    alt_text = db.Column(db.String(200))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    content_page = db.relationship('ContentPage', backref='downloads')

# Event models
class EventCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#3498db')
    icon = db.Column(db.String(50), default='fas fa-calendar')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    short_description = db.Column(db.Text)  # New field for event previews
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('event_category.id'))
    
    # Date and time
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    all_day = db.Column(db.Boolean, default=False)
    
    # Location
    location_name = db.Column(db.String(200))
    location_address = db.Column(db.Text)
    location_url = db.Column(db.String(500))  # Google Maps link
    
    # Contact and booking
    contact_name = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    booking_required = db.Column(db.Boolean, default=False)
    booking_url = db.Column(db.String(500))
    max_attendees = db.Column(db.Integer)
    
    # Pricing
    is_free = db.Column(db.Boolean, default=True)
    price = db.Column(db.String(100))  # e.g., "£5 adults, £3 children"
    
    # Media
    image_filename = db.Column(db.String(255))
    featured = db.Column(db.Boolean, default=False)
    
    # Status
    status = db.Column(db.String(20), default='Draft')  # Draft, Published, Cancelled
    is_published = db.Column(db.Boolean, default=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = db.relationship('EventCategory', backref='events')

# Event Gallery Model for multiple images with metadata
class EventGallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    alt_text = db.Column(db.String(200))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    event = db.relationship('Event', backref='gallery_images')

# Event Category Assignment for multiple categories per event
class EventCategoryAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('event_category.id'), nullable=False)
    
    event = db.relationship('Event', backref='category_assignments')
    category = db.relationship('EventCategory', backref='event_assignments')

# Event Links Model for related URLs
class EventLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    new_tab = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    event = db.relationship('Event', backref='related_links')

# Event Downloads Model for file downloads
class EventDownload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    event = db.relationship('Event', backref='downloads')

# Meeting Type Model (predefined, non-editable)
class MeetingType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#3498db')  # Hex color
    is_predefined = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    show_schedule_applications = db.Column(db.Boolean, default=False)  # Show "Schedule of Applications" column
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Meeting Model
class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    meeting_type_id = db.Column(db.Integer, db.ForeignKey('meeting_type.id'), nullable=False)
    meeting_date = db.Column(db.Date, nullable=False)
    meeting_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(200))
    
    # Document files and metadata
    agenda_filename = db.Column(db.String(255))  # PDF file
    agenda_title = db.Column(db.String(200))
    agenda_description = db.Column(db.Text)
    
    minutes_filename = db.Column(db.String(255))  # PDF file
    minutes_title = db.Column(db.String(200))
    minutes_description = db.Column(db.Text)
    
    draft_minutes_filename = db.Column(db.String(255))  # PDF file
    draft_minutes_title = db.Column(db.String(200))
    draft_minutes_description = db.Column(db.Text)
    
    schedule_applications_filename = db.Column(db.String(255))  # PDF file (conditional)
    schedule_applications_title = db.Column(db.String(200))
    schedule_applications_description = db.Column(db.Text)
    
    audio_filename = db.Column(db.String(255))  # Audio file
    audio_title = db.Column(db.String(200))
    audio_description = db.Column(db.Text)
    
    summary_url = db.Column(db.String(500))  # External URL
    
    status = db.Column(db.String(20), default='Scheduled')  # Scheduled, Completed, Cancelled
    is_published = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    meeting_type = db.relationship('MeetingType', backref='meetings')

# Homepage Models
class HomepageLogo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    logo_image_filename = db.Column(db.String(255))  # Uploaded logo image
    logo_text = db.Column(db.String(200))  # Logo text
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HomepageHeaderLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    link_name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HomepageFooterColumn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    column_number = db.Column(db.Integer, nullable=False)  # 1, 2, or 3
    column_title = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HomepageFooterLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    footer_column_id = db.Column(db.Integer, db.ForeignKey('homepage_footer_column.id'), nullable=False)
    link_name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    footer_column = db.relationship('HomepageFooterColumn', backref='links')

class HomepageSlide(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    introduction = db.Column(db.Text)  # Short text
    image_filename = db.Column(db.String(255))  # Slide image
    button_name = db.Column(db.String(100))  # Action button text
    button_url = db.Column(db.String(500))  # Action button URL
    open_method = db.Column(db.String(20), default='same_tab')  # same_tab, new_tab, new_window
    is_featured = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HomepageQuicklink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    button_name = db.Column(db.String(100))  # Action button text
    button_url = db.Column(db.String(500))  # Action button URL
    open_method = db.Column(db.String(20), default='same_tab')  # same_tab, new_tab, new_window
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Helper functions for social links
def get_social_links(councillor):
    """Get social links as dictionary"""
    if councillor.social_links:
        try:
            return json.loads(councillor.social_links)
        except:
            return {}
    return {}

def set_social_links(councillor, links_dict):
    """Set social links from dictionary"""
    councillor.social_links = json.dumps(links_dict) if links_dict else None

# File upload helper
def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_download_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 
        'zip', 'rar', 'png', 'jpg', 'jpeg', 'gif', 'webp'
    }

def allowed_file(filename):
    """Legacy function for backward compatibility"""
    return allowed_image_file(filename)

def save_uploaded_file(file, subfolder, file_type='image'):
    """Save uploaded file and return filename"""
    allowed_func = allowed_image_file if file_type == 'image' else allowed_download_file
    
    if file and allowed_func(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)
        file.save(filepath)
        return filename
    return None

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Simple authentication - any username/password works
        user = AdminUser(1)
        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .login-card {
                background: white;
                border-radius: 15px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.1);
                overflow: hidden;
                max-width: 400px;
                width: 100%;
            }
            .login-header {
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                color: white;
                padding: 2rem;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="login-card">
            <div class="login-header">
                <h3>🏛️ Kesgrave CMS</h3>
                <p class="mb-0">Content Management System</p>
            </div>
            <div class="p-4">
                <form method="POST">
                    <div class="mb-3">
                        <label class="form-label">Username</label>
                        <input type="text" class="form-control" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" class="form-control" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">Login</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    total_councillors = Councillor.query.count()
    published_councillors = Councillor.query.filter_by(is_published=True).count()
    total_tags = Tag.query.count()
    active_tags = Tag.query.filter_by(is_active=True).count()
    
    # Get recent councillors
    recent_councillors = Councillor.query.order_by(Councillor.updated_at.desc()).limit(5).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            {{ sidebar_css|safe }}
            .stat-card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }
            .stat-card:hover {
                transform: translateY(-5px);
            }
        </style>
    </head>
    <body>
        {{ sidebar_html|safe }}
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📊 Dashboard</h1>
                <div class="text-muted">{{ datetime.now()|uk_datetime }}</div>
            </div>
            
            <!-- Statistics Cards -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="stat-card p-4 text-center">
                        <div class="text-primary mb-2">
                            <i class="fas fa-users fa-2x"></i>
                        </div>
                        <h3 class="text-primary">{{ published_councillors }}/{{ total_councillors }}</h3>
                        <p class="text-muted mb-0">Published Councillors</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card p-4 text-center">
                        <div class="text-success mb-2">
                            <i class="fas fa-tags fa-2x"></i>
                        </div>
                        <h3 class="text-success">{{ active_tags }}/{{ total_tags }}</h3>
                        <p class="text-muted mb-0">Active Ward Tags</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card p-4 text-center">
                        <div class="text-warning mb-2">
                            <i class="fas fa-file-alt fa-2x"></i>
                        </div>
                        <h3 class="text-warning">{{ content_count }}</h3>
                        <p class="text-muted mb-0">Content Pages</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-card p-4 text-center">
                        <div class="text-info mb-2">
                            <i class="fas fa-calendar fa-2x"></i>
                        </div>
                        <h3 class="text-info">{{ events_count }}</h3>
                        <p class="text-muted mb-0">Upcoming Events</p>
                    </div>
                </div>
            </div>
                    <!-- Recent Activity -->
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Recent Councillors</h5>
                        </div>
                        <div class="card-body">
                            {% if recent_councillors %}
                            <div class="list-group list-group-flush">
                                {% for councillor in recent_councillors %}
                                <div class="list-group-item d-flex justify-content-between align-items-center">
                                    <div>
                                        <strong>{{ councillor.name }}</strong>
                                        {% if councillor.title %}
                                        <br><small class="text-muted">{{ councillor.title }}</small>
                                        {% endif %}
                                    </div>
                                    <span class="badge bg-{{ 'success' if councillor.is_published else 'warning' }}">
                                        {{ 'Published' if councillor.is_published else 'Draft' }}
                                    </span>
                                </div>
                                {% endfor %}
                            </div>
                            {% else %}
                            <p class="text-muted">No councillors found.</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Quick Actions</h5>
                        </div>
                        <div class="card-body">
                            <div class="d-grid gap-2">
                                <a href="/councillors/add" class="btn btn-primary">
                                    <i class="fas fa-user-plus me-2"></i>Add New Councillor
                                </a>
                                <a href="/content/pages/add" class="btn btn-success">
                                    <i class="fas fa-file-plus me-2"></i>Add New Content Page
                                </a>
                                <a href="/events/add" class="btn btn-info">
                                    <i class="fas fa-calendar-plus me-2"></i>Add New Event
                                </a>
                                <a href="/content-review" class="btn btn-warning">
                                    <i class="fas fa-clipboard-check me-2"></i>Review Content
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', total_councillors=total_councillors, published_councillors=published_councillors,
         total_tags=total_tags, active_tags=active_tags, recent_councillors=recent_councillors,
         content_count=ContentPage.query.count(),
         events_count=Event.query.filter(Event.start_date >= datetime.now()).count(),
         datetime=datetime, sidebar_html=get_sidebar_html('dashboard'), sidebar_css=get_sidebar_css())

@app.route('/councillors')
@login_required
def councillors_list():
    councillors = Councillor.query.order_by(Councillor.name).all()
    
    councillors_html = ""
    for councillor in councillors:
        social_links = get_social_links(councillor)
        social_icons = ""
        for platform, url in social_links.items():
            if url:
                icon_map = {
                    'twitter': 'fab fa-twitter',
                    'linkedin': 'fab fa-linkedin',
                    'facebook': 'fab fa-facebook',
                    'instagram': 'fab fa-instagram'
                }
                icon = icon_map.get(platform, 'fas fa-link')
                social_icons += f'<a href="{url}" target="_blank" class="text-primary me-1"><i class="{icon}"></i></a>'
        
        tags_html = ""
        for tag in councillor.tags:
            tags_html += f'<span class="badge me-1" style="background-color: {tag.color}; color: white;">{tag.name}</span>'
        
        image_html = ""
        if councillor.image_filename:
            image_html = f'<img src="/uploads/councillors/{councillor.image_filename}" class="rounded-circle" width="40" height="40" style="object-fit: cover;">'
        else:
            image_html = '<div class="bg-secondary rounded-circle d-flex align-items-center justify-content-center" style="width: 40px; height: 40px;"><i class="fas fa-user text-white"></i></div>'
        
        councillors_html += f'''
        <tr>
            <td>
                <div class="d-flex align-items-center">
                    <div class="me-3">
                        {image_html}
                    </div>
                    <div>
                        <h6 class="mb-1">{councillor.name}</h6>
                        <small class="text-muted">{councillor.title or "Councillor"}</small>
                    </div>
                </div>
            </td>
            <td>{tags_html}</td>
            <td>{councillor.email or "Not provided"}</td>
            <td>{social_icons}</td>
            <td>
                <span class="badge bg-{'success' if councillor.is_published else 'warning'}">
                    {'Published' if councillor.is_published else 'Draft'}
                </span>
            </td>
            <td>{councillor.updated_at.strftime('%d/%m/%Y')}</td>
            <td>
                <a href="/councillors/edit/{councillor.id}" class="btn btn-sm btn-outline-primary me-1">
                    <i class="fas fa-edit"></i>
                </a>
                <a href="/councillors/delete/{councillor.id}" class="btn btn-sm btn-outline-danger" 
                   onclick="return confirm('Delete {councillor.name}?')">
                    <i class="fas fa-trash"></i>
                </a>
            </td>
        </tr>
        '''
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Councillors - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link active">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>👥 Councillors Management</h1>
                <a href="/councillors/add" class="btn btn-primary">
                    <i class="fas fa-plus me-2"></i>Add New Councillor
                </a>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">All Councillors ({{ councillors|length }})</h5>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>Councillor</th>
                                    <th>Ward Tags</th>
                                    <th>Email</th>
                                    <th>Social Links</th>
                                    <th>Status</th>
                                    <th>Updated</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {{ councillors_html|safe }}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', councillors=councillors, councillors_html=councillors_html)


@app.route('/councillors/add', methods=['GET', 'POST'])
@login_required
def add_councillor():
    if request.method == 'POST':
        # Handle form submission
        councillor = Councillor(
            name=request.form['name'],
            title=request.form.get('title'),
            intro=request.form.get('intro'),
            bio=request.form.get('bio'),
            address=request.form.get('address'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            qualifications=request.form.get('qualifications'),
            is_published=bool(request.form.get('is_published'))
        )
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = save_uploaded_file(file, 'councillors')
                councillor.image_filename = filename
        
        # Handle social links
        social_links = {}
        for platform in ['twitter', 'linkedin', 'facebook', 'instagram']:
            url = request.form.get(f'social_{platform}')
            if url:
                social_links[platform] = url
        set_social_links(councillor, social_links)
        
        db.session.add(councillor)
        db.session.commit()
        
        # Handle tags
        tag_ids = request.form.getlist('tags')
        for tag_id in tag_ids:
            if tag_id:
                councillor_tag = CouncillorTag(councillor_id=councillor.id, tag_id=int(tag_id))
                db.session.add(councillor_tag)
        
        db.session.commit()
        flash('Councillor added successfully!', 'success')
        return redirect(url_for('councillors_list'))
    
    # GET request - show form
    tags = Tag.query.filter_by(is_active=True).order_by(Tag.name).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Councillor - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link active">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>➕ Add New Councillor</h1>
                <a href="/councillors" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to List
                </a>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Councillor Information</h5>
                </div>
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Full Name *</label>
                                    <input type="text" class="form-control" name="name" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Title/Position</label>
                                    <input type="text" class="form-control" name="title" placeholder="e.g., Councillor, Mayor">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Short Introduction</label>
                            <textarea class="form-control" name="intro" rows="2" placeholder="Brief introduction for homepage display"></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Biography</label>
                            <textarea class="form-control" name="bio" rows="4" placeholder="Detailed biography"></textarea>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Email Address</label>
                                    <input type="email" class="form-control" name="email">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Phone Number</label>
                                    <input type="tel" class="form-control" name="phone">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Contact Address</label>
                            <textarea class="form-control" name="address" rows="2"></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Qualifications</label>
                            <textarea class="form-control" name="qualifications" rows="2" placeholder="Education, certifications, experience"></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Profile Image</label>
                            <input type="file" class="form-control" name="image" accept="image/*">
                            <small class="text-muted">Recommended: Square image, at least 300x300px</small>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Ward Tags</label>
                            <div class="row">
                                {% for tag in tags %}
                                <div class="col-md-4 mb-2">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="tags" value="{{ tag.id }}" id="tag{{ tag.id }}">
                                        <label class="form-check-label" for="tag{{ tag.id }}">
                                            <span class="badge" style="background-color: {{ tag.color }}; color: white;">{{ tag.name }}</span>
                                        </label>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Social Media Links</label>
                            <div class="row">
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-twitter"></i></span>
                                        <input type="url" class="form-control" name="social_twitter" placeholder="Twitter/X URL">
                                    </div>
                                </div>
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-linkedin"></i></span>
                                        <input type="url" class="form-control" name="social_linkedin" placeholder="LinkedIn URL">
                                    </div>
                                </div>
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-facebook"></i></span>
                                        <input type="url" class="form-control" name="social_facebook" placeholder="Facebook URL">
                                    </div>
                                </div>
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-instagram"></i></span>
                                        <input type="url" class="form-control" name="social_instagram" placeholder="Instagram URL">
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_published" id="is_published" checked>
                                <label class="form-check-label" for="is_published">
                                    Publish immediately
                                </label>
                            </div>
                        </div>
                        
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Save Councillor
                            </button>
                            <a href="/councillors" class="btn btn-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', tags=tags)

@app.route('/councillors/edit/<int:councillor_id>', methods=['GET', 'POST'])
@login_required
def edit_councillor(councillor_id):
    councillor = Councillor.query.get_or_404(councillor_id)
    
    if request.method == 'POST':
        # Update councillor data
        councillor.name = request.form['name']
        councillor.title = request.form.get('title')
        councillor.intro = request.form.get('intro')
        councillor.bio = request.form.get('bio')
        councillor.address = request.form.get('address')
        councillor.email = request.form.get('email')
        councillor.phone = request.form.get('phone')
        councillor.qualifications = request.form.get('qualifications')
        councillor.is_published = bool(request.form.get('is_published'))
        councillor.updated_at = datetime.utcnow()
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = save_uploaded_file(file, 'councillors')
                councillor.image_filename = filename
        
        # Handle social links
        social_links = {}
        for platform in ['twitter', 'linkedin', 'facebook', 'instagram']:
            url = request.form.get(f'social_{platform}')
            if url:
                social_links[platform] = url
        set_social_links(councillor, social_links)
        
        # Update tags - remove existing and add new ones
        CouncillorTag.query.filter_by(councillor_id=councillor.id).delete()
        tag_ids = request.form.getlist('tags')
        for tag_id in tag_ids:
            if tag_id:
                councillor_tag = CouncillorTag(councillor_id=councillor.id, tag_id=int(tag_id))
                db.session.add(councillor_tag)
        
        db.session.commit()
        flash('Councillor updated successfully!', 'success')
        return redirect(url_for('councillors_list'))
    
    # GET request - show form with existing data
    tags = Tag.query.filter_by(is_active=True).order_by(Tag.name).all()
    councillor_tag_ids = [ct.tag_id for ct in CouncillorTag.query.filter_by(councillor_id=councillor.id).all()]
    social_links = get_social_links(councillor)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Councillor - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link active">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>✏️ Edit Councillor: {{ councillor.name }}</h1>
                <a href="/councillors" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to List
                </a>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Councillor Information</h5>
                </div>
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Full Name *</label>
                                    <input type="text" class="form-control" name="name" value="{{ councillor.name }}" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Title/Position</label>
                                    <input type="text" class="form-control" name="title" value="{{ councillor.title or '' }}" placeholder="e.g., Councillor, Mayor">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Short Introduction</label>
                            <textarea class="form-control" name="intro" rows="2" placeholder="Brief introduction for homepage display">{{ councillor.intro or '' }}</textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Biography</label>
                            <textarea class="form-control" name="bio" rows="4" placeholder="Detailed biography">{{ councillor.bio or '' }}</textarea>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Email Address</label>
                                    <input type="email" class="form-control" name="email" value="{{ councillor.email or '' }}">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Phone Number</label>
                                    <input type="tel" class="form-control" name="phone" value="{{ councillor.phone or '' }}">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Contact Address</label>
                            <textarea class="form-control" name="address" rows="2">{{ councillor.address or '' }}</textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Qualifications</label>
                            <textarea class="form-control" name="qualifications" rows="2" placeholder="Education, certifications, experience">{{ councillor.qualifications or '' }}</textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Profile Image</label>
                            {% if councillor.image_filename %}
                            <div class="mb-2">
                                <img src="/uploads/councillors/{{ councillor.image_filename }}" class="rounded" width="100" height="100" style="object-fit: cover;">
                                <small class="text-muted d-block">Current image</small>
                            </div>
                            {% endif %}
                            <input type="file" class="form-control" name="image" accept="image/*">
                            <small class="text-muted">Leave empty to keep current image. Recommended: Square image, at least 300x300px</small>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Ward Tags</label>
                            <div class="row">
                                {% for tag in tags %}
                                <div class="col-md-4 mb-2">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="tags" value="{{ tag.id }}" id="tag{{ tag.id }}" 
                                               {% if tag.id in councillor_tag_ids %}checked{% endif %}>
                                        <label class="form-check-label" for="tag{{ tag.id }}">
                                            <span class="badge" style="background-color: {{ tag.color }}; color: white;">{{ tag.name }}</span>
                                        </label>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Social Media Links</label>
                            <div class="row">
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-twitter"></i></span>
                                        <input type="url" class="form-control" name="social_twitter" value="{{ social_links.get('twitter', '') }}" placeholder="Twitter/X URL">
                                    </div>
                                </div>
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-linkedin"></i></span>
                                        <input type="url" class="form-control" name="social_linkedin" value="{{ social_links.get('linkedin', '') }}" placeholder="LinkedIn URL">
                                    </div>
                                </div>
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-facebook"></i></span>
                                        <input type="url" class="form-control" name="social_facebook" value="{{ social_links.get('facebook', '') }}" placeholder="Facebook URL">
                                    </div>
                                </div>
                                <div class="col-md-6 mb-2">
                                    <div class="input-group">
                                        <span class="input-group-text"><i class="fab fa-instagram"></i></span>
                                        <input type="url" class="form-control" name="social_instagram" value="{{ social_links.get('instagram', '') }}" placeholder="Instagram URL">
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_published" id="is_published" {% if councillor.is_published %}checked{% endif %}>
                                <label class="form-check-label" for="is_published">
                                    Published
                                </label>
                            </div>
                        </div>
                        
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Update Councillor
                            </button>
                            <a href="/councillors" class="btn btn-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', councillor=councillor, tags=tags, councillor_tag_ids=councillor_tag_ids, social_links=social_links)

@app.route('/councillors/delete/<int:councillor_id>')
@login_required
def delete_councillor(councillor_id):
    councillor = Councillor.query.get_or_404(councillor_id)
    
    # Delete associated tags
    CouncillorTag.query.filter_by(councillor_id=councillor.id).delete()
    
    # Delete the councillor
    db.session.delete(councillor)
    db.session.commit()
    
    flash(f'Councillor {councillor.name} deleted successfully!', 'success')
    return redirect(url_for('councillors_list'))

# Tags management routes
@app.route('/tags')
@login_required
def tags_list():
    tags = Tag.query.order_by(Tag.name).all()
    
    tags_html = ""
    for tag in tags:
        councillor_count = len(tag.councillors)
        
        tags_html += f'''
        <tr>
            <td>
                <span class="badge" style="background-color: {tag.color}; color: white; font-size: 0.9rem;">
                    {tag.name}
                </span>
            </td>
            <td>{tag.description or "No description"}</td>
            <td>{councillor_count} councillor{'s' if councillor_count != 1 else ''}</td>
            <td>
                <span class="badge bg-{'success' if tag.is_active else 'secondary'}">
                    {'Active' if tag.is_active else 'Inactive'}
                </span>
            </td>
            <td>{tag.created_at.strftime('%d/%m/%Y')}</td>
            <td>
                <a href="/tags/edit/{tag.id}" class="btn btn-sm btn-outline-primary me-1">
                    <i class="fas fa-edit"></i>
                </a>
                <a href="/tags/delete/{tag.id}" class="btn btn-sm btn-outline-danger" 
                   onclick="return confirm('Delete tag {tag.name}? This will remove it from all councillors.')">
                    <i class="fas fa-trash"></i>
                </a>
            </td>
        </tr>
        '''
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ward Tags - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link active">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>🏷️ Ward Tags Management</h1>
                <a href="/tags/add" class="btn btn-primary">
                    <i class="fas fa-plus me-2"></i>Add New Tag
                </a>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">All Ward Tags ({{ tags|length }})</h5>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>Tag</th>
                                    <th>Description</th>
                                    <th>Usage</th>
                                    <th>Status</th>
                                    <th>Created</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {{ tags_html|safe }}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', tags=tags, tags_html=tags_html)

@app.route('/tags/add', methods=['GET', 'POST'])
@login_required
def add_tag():
    if request.method == 'POST':
        tag = Tag(
            name=request.form['name'],
            description=request.form.get('description'),
            color=request.form.get('color', '#3498db'),
            is_active=bool(request.form.get('is_active'))
        )
        
        db.session.add(tag)
        db.session.commit()
        
        flash('Tag created successfully!', 'success')
        return redirect(url_for('tags_list'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Tag - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link active">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>➕ Add New Ward Tag</h1>
                <a href="/tags" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to List
                </a>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Tag Information</h5>
                </div>
                <div class="card-body">
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">Tag Name *</label>
                            <input type="text" class="form-control" name="name" required placeholder="e.g., East Ward, Planning Committee">
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Description</label>
                            <textarea class="form-control" name="description" rows="2" placeholder="Brief description of this tag"></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Color</label>
                            <input type="color" class="form-control form-control-color" name="color" value="#3498db">
                            <small class="text-muted">Choose a color for this tag</small>
                        </div>
                        
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_active" id="is_active" checked>
                                <label class="form-check-label" for="is_active">
                                    Active (available for use)
                                </label>
                            </div>
                        </div>
                        
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Create Tag
                            </button>
                            <a href="/tags" class="btn btn-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route('/tags/edit/<int:tag_id>', methods=['GET', 'POST'])
@login_required
def edit_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    
    if request.method == 'POST':
        tag.name = request.form['name']
        tag.description = request.form.get('description')
        tag.color = request.form.get('color', '#3498db')
        tag.is_active = bool(request.form.get('is_active'))
        
        db.session.commit()
        flash('Tag updated successfully!', 'success')
        return redirect(url_for('tags_list'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Tag - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link active">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>✏️ Edit Tag: {{ tag.name }}</h1>
                <a href="/tags" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to List
                </a>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Tag Information</h5>
                </div>
                <div class="card-body">
                    <form method="POST">
                        <div class="mb-3">
                            <label class="form-label">Tag Name *</label>
                            <input type="text" class="form-control" name="name" value="{{ tag.name }}" required>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Description</label>
                            <textarea class="form-control" name="description" rows="2">{{ tag.description or '' }}</textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Color</label>
                            <input type="color" class="form-control form-control-color" name="color" value="{{ tag.color }}">
                            <small class="text-muted">Choose a color for this tag</small>
                        </div>
                        
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_active" id="is_active" {% if tag.is_active %}checked{% endif %}>
                                <label class="form-check-label" for="is_active">
                                    Active (available for use)
                                </label>
                            </div>
                        </div>
                        
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Update Tag
                            </button>
                            <a href="/tags" class="btn btn-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', tag=tag)

@app.route('/tags/delete/<int:tag_id>')
@login_required
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    
    # Delete associated councillor tags
    CouncillorTag.query.filter_by(tag_id=tag.id).delete()
    
    # Delete the tag
    db.session.delete(tag)
    db.session.commit()
    
    flash(f'Tag {tag.name} deleted successfully!', 'success')
    return redirect(url_for('tags_list'))


# Content management routes
@app.route('/content')
@login_required
def content_dashboard():
    # Get real categories with page counts
    db_categories = ContentCategory.query.filter_by(is_active=True).all()
    categories = []
    for cat in db_categories:
        page_count = ContentPage.query.filter_by(category_id=cat.id).count()
        categories.append({
            'name': cat.name,
            'count': page_count,
            'color': cat.color or '#3498db'
        })
    
    # Get recent pages from database
    recent_db_pages = ContentPage.query.order_by(ContentPage.updated_at.desc()).limit(5).all()
    recent_pages = []
    for page in recent_db_pages:
        category_name = page.category.name if page.category else 'Uncategorized'
        updated_date = page.updated_at.strftime('%d/%m/%Y') if page.updated_at else page.created_at.strftime('%d/%m/%Y') if page.created_at else ''
        recent_pages.append({
            'title': page.title,
            'category': category_name,
            'status': page.status,
            'updated': updated_date
        })
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Content Management - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .stat-card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
                cursor: pointer;
            }
            .stat-card:hover {
                transform: translateY(-5px);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📄 Content Management</h1>
                <div class="d-flex gap-2">
                    <a href="/content/pages" class="btn btn-info">
                        <i class="fas fa-list me-2"></i>View All Pages
                    </a>
                    <a href="/content/add" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Add New Page
                    </a>
                </div>
            </div>
            
            <!-- Content Categories -->
            <div class="row mb-4">
                <div class="col-12">
                    <h3 class="mb-3">Content Categories</h3>
                </div>
                {% for category in categories %}
                <div class="col-md-4 mb-3">
                    <div class="stat-card p-4" onclick="window.location.href='/content/pages?category={{ category.name|urlencode }}'">
                        <div class="d-flex align-items-center">
                            <div class="me-3">
                                <div class="rounded-circle d-flex align-items-center justify-content-center" 
                                     style="width: 50px; height: 50px; background-color: {{ category.color }};">
                                    <i class="fas fa-folder text-white"></i>
                                </div>
                            </div>
                            <div>
                                <h5 class="mb-1">{{ category.name }}</h5>
                                <p class="text-muted mb-0">{{ category.count }} pages</p>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <!-- Quick Actions -->
            <div class="row mb-4">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Quick Actions</h5>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-3">
                                    <a href="/content/pages" class="btn btn-info w-100 mb-2">
                                        <i class="fas fa-list me-2"></i>View All Pages (57)
                                    </a>
                                </div>
                                <div class="col-md-3">
                                    <a href="/content/add" class="btn btn-primary w-100 mb-2">
                                        <i class="fas fa-file-plus me-2"></i>Create New Page
                                    </a>
                                </div>
                                <div class="col-md-3">
                                    <a href="/content/categories" class="btn btn-warning w-100 mb-2">
                                        <i class="fas fa-folder-plus me-2"></i>Manage Categories
                                    </a>
                                </div>
                                <div class="col-md-3">
                                    <a href="/content/categories/add" class="btn btn-success w-100 mb-2">
                                        <i class="fas fa-plus me-2"></i>Add Category
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Recent Pages -->
            <div class="row">
                <div class="col-md-12">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Recent Pages</h5>
                        </div>
                        <div class="card-body p-0">
                            <div class="table-responsive">
                                <table class="table table-hover mb-0">
                                    <thead class="table-light">
                                        <tr>
                                            <th>Page Title</th>
                                            <th>Category</th>
                                            <th>Status</th>
                                            <th>Last Updated</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for page in recent_pages %}
                                        <tr>
                                            <td>
                                                <h6 class="mb-1">{{ page.title }}</h6>
                                                <small class="text-muted">{{ page.category }}</small>
                                            </td>
                                            <td>
                                                <span class="badge bg-secondary">{{ page.category }}</span>
                                            </td>
                                            <td>
                                                <span class="badge bg-{{ 'success' if page.status == 'Published' else 'warning' }}">
                                                    {{ page.status }}
                                                </span>
                                            </td>
                                            <td>{{ page.updated }}</td>
                                            <td>
                                                <a href="#" class="btn btn-sm btn-outline-primary me-1">
                                                    <i class="fas fa-edit"></i>
                                                </a>
                                                <a href="#" class="btn btn-sm btn-outline-info me-1">
                                                    <i class="fas fa-eye"></i>
                                                </a>
                                                <a href="#" class="btn btn-sm btn-outline-danger">
                                                    <i class="fas fa-trash"></i>
                                                </a>
                                            </td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''', categories=categories, recent_pages=recent_pages)

@app.route('/content/pages')
@login_required
def content_pages_list():
    # Get filter parameters
    category_filter = request.args.get('category')
    status_filter = request.args.get('status')
    search_query = request.args.get('search', '')
    page_num = int(request.args.get('page', 1))
    per_page = 20
    
    # Build database query
    query = ContentPage.query
    
    # Apply filters
    if category_filter:
        # Handle both category ID and category name
        if category_filter.isdigit():
            query = query.filter(ContentPage.category_id == int(category_filter))
        else:
            # Filter by category name
            query = query.join(ContentCategory).filter(ContentCategory.name == category_filter)
    if status_filter:
        query = query.filter(ContentPage.status == status_filter)
    if search_query:
        query = query.filter(ContentPage.title.contains(search_query))
    
    # Get total count for pagination
    total_pages = query.count()
    
    # Apply pagination
    pages_query = query.order_by(ContentPage.created_at.desc()).offset((page_num - 1) * per_page).limit(per_page)
    db_pages = pages_query.all()
    
    # Convert database objects to template-friendly format
    pages = []
    for page in db_pages:
        category_name = page.category.name if page.category else 'Uncategorized'
        pages.append({
            'id': page.id,
            'title': page.title,
            'category': category_name,
            'status': page.status,
            'author': 'Admin User',  # You can add author field to ContentPage model later
            'created': page.created_at.strftime('%d/%m/%Y') if page.created_at else '',
            'updated': page.updated_at.strftime('%d/%m/%Y') if page.updated_at else page.created_at.strftime('%d/%m/%Y') if page.created_at else '',
            'views': 0,  # You can add views field to ContentPage model later
            'summary': page.short_description or 'No description available'
        })
    
    total_page_count = (total_pages + per_page - 1) // per_page
    
    # Generate pagination HTML
    pagination_html = ""
    if total_page_count > 1:
        pagination_html = '<nav><ul class="pagination justify-content-center">'
        
        # Previous button
        if page_num > 1:
            prev_url = f"/content/pages?page={page_num-1}"
            if category_filter:
                prev_url += f"&category={category_filter}"
            if status_filter:
                prev_url += f"&status={status_filter}"
            if search_query:
                prev_url += f"&search={search_query}"
            pagination_html += f'<li class="page-item"><a class="page-link" href="{prev_url}">Previous</a></li>'
        
        # Page numbers (show 5 pages around current)
        start_page = max(1, page_num - 2)
        end_page = min(total_page_count, page_num + 2)
        
        for p in range(start_page, end_page + 1):
            page_url = f"/content/pages?page={p}"
            if category_filter:
                page_url += f"&category={category_filter}"
            if status_filter:
                page_url += f"&status={status_filter}"
            if search_query:
                page_url += f"&search={search_query}"
            
            active_class = "active" if p == page_num else ""
            pagination_html += f'<li class="page-item {active_class}"><a class="page-link" href="{page_url}">{p}</a></li>'
        
        # Next button
        if page_num < total_page_count:
            next_url = f"/content/pages?page={page_num+1}"
            if category_filter:
                next_url += f"&category={category_filter}"
            if status_filter:
                next_url += f"&status={status_filter}"
            if search_query:
                next_url += f"&search={search_query}"
            pagination_html += f'<li class="page-item"><a class="page-link" href="{next_url}">Next</a></li>'
        
        pagination_html += '</ul></nav>'
    
    # Get categories for filter dropdown
    categories = ContentCategory.query.filter_by(is_active=True).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>All Content Pages - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .filter-card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📋 All Content Pages</h1>
                <div class="d-flex gap-2">
                    <a href="/content" class="btn btn-secondary">
                        <i class="fas fa-arrow-left me-2"></i>Back to Content
                    </a>
                    <a href="/content/add" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Add New Page
                    </a>
                </div>
            </div>
            
            <!-- Filters -->
            <div class="filter-card p-3 mb-4">
                <form method="GET" class="row g-3">
                    <div class="col-md-3">
                        <label class="form-label">Search Pages</label>
                        <input type="text" class="form-control" name="search" value="{{ search_query }}" placeholder="Search by title...">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Category</label>
                        <select class="form-select" name="category">
                            <option value="">All Categories</option>
                            {% for category in categories %}
                            <option value="{{ category.id }}" {% if category_filter == category.id|string %}selected{% endif %}>{{ category.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Status</label>
                        <select class="form-select" name="status">
                            <option value="">All Statuses</option>
                            <option value="Published" {% if status_filter == 'Published' %}selected{% endif %}>Published</option>
                            <option value="Draft" {% if status_filter == 'Draft' %}selected{% endif %}>Draft</option>
                            <option value="Archived" {% if status_filter == 'Archived' %}selected{% endif %}>Archived</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">&nbsp;</label>
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-search me-1"></i>Filter
                            </button>
                            <a href="/content/pages" class="btn btn-outline-secondary">
                                <i class="fas fa-times me-1"></i>Clear
                            </a>
                        </div>
                    </div>
                </form>
            </div>
            
            <!-- Results Summary -->
            <div class="d-flex justify-content-between align-items-center mb-3">
                <div>
                    <h5 class="mb-0">
                        Showing {{ pages|length }} of {{ total_pages }} pages
                        {% if category_filter or status_filter or search_query %}
                        <small class="text-muted">(filtered)</small>
                        {% endif %}
                    </h5>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-primary btn-sm">
                        <i class="fas fa-download me-1"></i>Export
                    </button>
                    <button class="btn btn-outline-warning btn-sm">
                        <i class="fas fa-tasks me-1"></i>Bulk Actions
                    </button>
                </div>
            </div>
            
            <!-- Pages Table -->
            <div class="card">
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th width="5%">
                                        <input type="checkbox" class="form-check-input">
                                    </th>
                                    <th width="35%">Page Title</th>
                                    <th width="15%">Category</th>
                                    <th width="10%">Status</th>
                                    <th width="10%">Author</th>
                                    <th width="10%">Updated</th>
                                    <th width="8%">Views</th>
                                    <th width="7%">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for page in pages %}
                                <tr>
                                    <td>
                                        <input type="checkbox" class="form-check-input" value="{{ page.id }}">
                                    </td>
                                    <td>
                                        <div>
                                            <h6 class="mb-1">{{ page.title }}</h6>
                                            <small class="text-muted">{{ page.summary }}</small>
                                        </div>
                                    </td>
                                    <td>
                                        <span class="badge bg-secondary">{{ page.category }}</span>
                                    </td>
                                    <td>
                                        <span class="badge bg-{{ 'success' if page.status == 'Published' else 'warning' if page.status == 'Draft' else 'secondary' }}">
                                            {{ page.status }}
                                        </span>
                                    </td>
                                    <td>{{ page.author }}</td>
                                    <td>{{ page.updated }}</td>
                                    <td>{{ page.views }}</td>
                                    <td>
                                        <div class="btn-group btn-group-sm">
                                            <a href="/content/edit/{{ page.id }}" class="btn btn-outline-primary" title="Edit">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            <a href="/content/view/{{ page.id }}" class="btn btn-outline-info" title="View">
                                                <i class="fas fa-eye"></i>
                                            </a>
                                            <a href="#" class="btn btn-outline-danger" title="Delete">
                                                <i class="fas fa-trash"></i>
                                            </a>
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <!-- Pagination -->
            <div class="mt-4">
                {{ pagination_html|safe }}
            </div>
            
            <!-- Bulk Actions Panel (hidden by default) -->
            <div class="card mt-3" id="bulkActionsPanel" style="display: none;">
                <div class="card-body">
                    <h6>Bulk Actions</h6>
                    <div class="d-flex gap-2">
                        <button class="btn btn-success btn-sm">
                            <i class="fas fa-check me-1"></i>Publish Selected
                        </button>
                        <button class="btn btn-warning btn-sm">
                            <i class="fas fa-edit me-1"></i>Set as Draft
                        </button>
                        <button class="btn btn-secondary btn-sm">
                            <i class="fas fa-archive me-1"></i>Archive Selected
                        </button>
                        <button class="btn btn-danger btn-sm">
                            <i class="fas fa-trash me-1"></i>Delete Selected
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Show/hide bulk actions panel when checkboxes are selected
            document.addEventListener('DOMContentLoaded', function() {
                const checkboxes = document.querySelectorAll('tbody input[type="checkbox"]');
                const bulkPanel = document.getElementById('bulkActionsPanel');
                
                checkboxes.forEach(checkbox => {
                    checkbox.addEventListener('change', function() {
                        const checkedBoxes = document.querySelectorAll('tbody input[type="checkbox"]:checked');
                        bulkPanel.style.display = checkedBoxes.length > 0 ? 'block' : 'none';
                    });
                });
            });
        </script>
    </body>
    </html>
    ''', pages=pages, total_pages=total_pages, category_filter=category_filter, 
         status_filter=status_filter, search_query=search_query, pagination_html=pagination_html, categories=categories)

# Content category management routes
@app.route('/content/categories')
@login_required
def content_categories():
    categories = ContentCategory.query.all()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Manage Categories - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📁 Manage Categories</h1>
                <div class="d-flex gap-2">
                    <a href="/content" class="btn btn-secondary">
                        <i class="fas fa-arrow-left me-2"></i>Back to Content
                    </a>
                    <a href="/content/categories/add" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Add Category
                    </a>
                </div>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>Category Name</th>
                                    <th>URL Path</th>
                                    <th>Subcategories</th>
                                    <th>Pages</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for category in categories %}
                                <tr>
                                    <td>
                                        <div class="d-flex align-items-center">
                                            <div class="rounded-circle me-3" style="width: 20px; height: 20px; background-color: {{ category.color }};"></div>
                                            <div>
                                                <h6 class="mb-0">{{ category.name }}</h6>
                                                {% if category.description %}
                                                <small class="text-muted">{{ category.description }}</small>
                                                {% endif %}
                                            </div>
                                        </div>
                                    </td>
                                    <td><code>{{ category.url_path or '/' + category.name.lower().replace(' ', '-') }}</code></td>
                                    <td>{{ category.subcategories|length }}</td>
                                    <td>{{ category.pages|length }}</td>
                                    <td>
                                        <span class="badge bg-{{ 'success' if category.is_active else 'secondary' }}">
                                            {{ 'Active' if category.is_active else 'Inactive' }}
                                        </span>
                                        {% if category.is_predefined %}
                                        <span class="badge bg-info">Predefined</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <div class="btn-group btn-group-sm">
                                            <a href="/content/categories/edit/{{ category.id }}" class="btn btn-outline-primary" title="Edit">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            {% if not category.is_predefined %}
                                            <button class="btn btn-outline-danger" title="Delete" onclick="deleteCategory({{ category.id }})">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function deleteCategory(id) {
                if (confirm('Are you sure you want to delete this category?')) {
                    fetch('/content/categories/delete/' + id, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    }).then(response => {
                        if (response.ok) {
                            location.reload();
                        } else {
                            alert('Error deleting category');
                        }
                    });
                }
            }
        </script>
    </body>
    </html>
    ''', categories=categories)

@app.route('/content/categories/add', methods=['GET', 'POST'])
@login_required
def add_content_category():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        color = request.form.get('color', '#3498db')
        url_path = request.form.get('url_path')
        
        # Validate reserved paths
        reserved_paths = ['/councillors', '/ktc-meetings', '/contact', '/admin', '/login']
        if url_path in reserved_paths:
            flash('This URL path is reserved and cannot be used.', 'error')
            return redirect(request.url)
        
        # Check if URL path already exists
        existing = ContentCategory.query.filter_by(url_path=url_path).first()
        if existing:
            flash('This URL path is already in use.', 'error')
            return redirect(request.url)
        
        category = ContentCategory(
            name=name,
            description=description,
            color=color,
            url_path=url_path,
            is_active=True
        )
        
        db.session.add(category)
        
        # Add subcategories if provided
        subcategory_names = request.form.getlist('subcategory_name[]')
        subcategory_paths = request.form.getlist('subcategory_path[]')
        
        for i, sub_name in enumerate(subcategory_names):
            if sub_name.strip():
                sub_path = subcategory_paths[i] if i < len(subcategory_paths) else ''
                subcategory = ContentSubcategory(
                    name=sub_name.strip(),
                    url_path=sub_path.strip() if sub_path.strip() else None,
                    category=category,
                    is_active=True
                )
                db.session.add(subcategory)
        
        db.session.commit()
        flash('Category created successfully!', 'success')
        return redirect(url_for('content_categories'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Category - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>➕ Add Category</h1>
                <a href="/content/categories" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Categories
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="card">
                <div class="card-body">
                    <form method="POST">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Category Name *</label>
                                    <input type="text" class="form-control" name="name" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">URL Path *</label>
                                    <input type="text" class="form-control" name="url_path" placeholder="/category-name" required>
                                    <div class="form-text">Must start with / and use lowercase with hyphens</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Description</label>
                                    <textarea class="form-control" name="description" rows="3"></textarea>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Color</label>
                                    <input type="color" class="form-control form-control-color" name="color" value="#3498db">
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-4">
                            <h5>Subcategories (Optional)</h5>
                            <div id="subcategories">
                                <div class="row mb-2">
                                    <div class="col-md-6">
                                        <input type="text" class="form-control" name="subcategory_name[]" placeholder="Subcategory name">
                                    </div>
                                    <div class="col-md-5">
                                        <input type="text" class="form-control" name="subcategory_path[]" placeholder="/subcategory-path">
                                    </div>
                                    <div class="col-md-1">
                                        <button type="button" class="btn btn-outline-danger" onclick="removeSubcategory(this)">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <button type="button" class="btn btn-outline-primary btn-sm" onclick="addSubcategory()">
                                <i class="fas fa-plus me-1"></i>Add Subcategory
                            </button>
                        </div>
                        
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Create Category
                            </button>
                            <a href="/content/categories" class="btn btn-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function addSubcategory() {
                const container = document.getElementById('subcategories');
                const div = document.createElement('div');
                div.className = 'row mb-2';
                div.innerHTML = `
                    <div class="col-md-6">
                        <input type="text" class="form-control" name="subcategory_name[]" placeholder="Subcategory name">
                    </div>
                    <div class="col-md-5">
                        <input type="text" class="form-control" name="subcategory_path[]" placeholder="/subcategory-path">
                    </div>
                    <div class="col-md-1">
                        <button type="button" class="btn btn-outline-danger" onclick="removeSubcategory(this)">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                container.appendChild(div);
            }
            
            function removeSubcategory(button) {
                button.closest('.row').remove();
            }
        </script>
    </body>
    </html>
    ''')

@app.route('/content/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_content_category(category_id):
    category = ContentCategory.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        category.color = request.form.get('color', '#3498db')
        
        # Only allow URL path changes for non-predefined categories
        if not category.is_predefined:
            url_path = request.form.get('url_path')
            
            # Validate reserved paths
            reserved_paths = ['/councillors', '/ktc-meetings', '/contact', '/admin', '/login']
            if url_path in reserved_paths:
                flash('This URL path is reserved and cannot be used.', 'error')
                return redirect(request.url)
            
            # Check if URL path already exists (excluding current category)
            existing = ContentCategory.query.filter(
                ContentCategory.url_path == url_path,
                ContentCategory.id != category_id
            ).first()
            if existing:
                flash('This URL path is already in use.', 'error')
                return redirect(request.url)
            
            category.url_path = url_path
        
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('content_categories'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Category - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>✏️ Edit Category</h1>
                <a href="/content/categories" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Categories
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category_msg, message in messages %}
                        <div class="alert alert-{{ 'danger' if category_msg == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <div class="card">
                <div class="card-body">
                    <form method="POST">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Category Name *</label>
                                    <input type="text" class="form-control" name="name" value="{{ category.name }}" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">URL Path *</label>
                                    <input type="text" class="form-control" name="url_path" value="{{ category.url_path }}" 
                                           {% if category.is_predefined %}readonly{% endif %} required>
                                    {% if category.is_predefined %}
                                    <div class="form-text text-warning">URL path cannot be changed for predefined categories</div>
                                    {% else %}
                                    <div class="form-text">Must start with / and use lowercase with hyphens</div>
                                    {% endif %}
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Description</label>
                                    <textarea class="form-control" name="description" rows="3">{{ category.description or '' }}</textarea>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Color</label>
                                    <input type="color" class="form-control form-control-color" name="color" value="{{ category.color }}">
                                </div>
                            </div>
                        </div>
                        
                        {% if category.is_predefined %}
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle me-2"></i>
                            This is a predefined category. Some fields cannot be modified to maintain system integrity.
                        </div>
                        {% endif %}
                        
                        <div class="d-flex gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Update Category
                            </button>
                            <a href="/content/categories" class="btn btn-secondary">Cancel</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', category=category)

@app.route('/content/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_content_category(category_id):
    category = ContentCategory.query.get_or_404(category_id)
    
    # Prevent deletion of predefined categories
    if category.is_predefined:
        return jsonify({'error': 'Cannot delete predefined categories'}), 400
    
    # Check if category has pages
    if category.pages:
        return jsonify({'error': 'Cannot delete category with existing pages'}), 400
    
    # Delete subcategories first
    for subcategory in category.subcategories:
        db.session.delete(subcategory)
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'success': True})

# Content page creation and management
@app.route('/content/add', methods=['GET', 'POST'])
@login_required
def add_content_page():
    if request.method == 'POST':
        title = request.form.get('title')
        short_description = request.form.get('short_description')
        long_description = request.form.get('long_description')
        category_id = request.form.get('category_id')
        subcategory_id = request.form.get('subcategory_id') or None
        status = request.form.get('status', 'Draft')
        
        # Generate slug from title
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
        slug = re.sub(r'\s+', '-', slug).strip('-')
        
        # Check if slug already exists
        existing = ContentPage.query.filter_by(slug=slug).first()
        if existing:
            slug = f"{slug}-{int(datetime.now().timestamp())}"
        
        # Create content page
        content_page = ContentPage(
            title=title,
            slug=slug,
            short_description=short_description,
            long_description=long_description,
            category_id=category_id,
            subcategory_id=subcategory_id,
            status=status,
            creation_date=datetime.utcnow()
        )
        
        # Handle date fields
        created_date = request.form.get('created_date')
        if created_date:
            try:
                content_page.creation_date = datetime.strptime(created_date, '%Y-%m-%d')
            except ValueError:
                pass  # Keep default if invalid date
        
        approved_date = request.form.get('approved_date')
        if approved_date:
            try:
                content_page.approval_date = datetime.strptime(approved_date, '%Y-%m-%d')
            except ValueError:
                pass  # Keep None if invalid date
        
        next_review_date = request.form.get('next_review_date')
        if next_review_date:
            try:
                content_page.next_review_date = datetime.strptime(next_review_date, '%Y-%m-%d')
            except ValueError:
                pass  # Keep None if invalid date
        
        db.session.add(content_page)
        db.session.flush()  # Get the ID
        
        # Handle gallery images
        gallery_files = request.files.getlist('gallery_images[]')
        gallery_titles = request.form.getlist('gallery_title[]')
        gallery_descriptions = request.form.getlist('gallery_description[]')
        gallery_alt_texts = request.form.getlist('gallery_alt_text[]')
        
        for i, file in enumerate(gallery_files):
            if file and file.filename:
                filename = save_uploaded_file(file, 'content/images', 'image')
                if filename:
                    gallery_item = ContentGallery(
                        content_page_id=content_page.id,
                        filename=filename,
                        title=gallery_titles[i] if i < len(gallery_titles) else '',
                        description=gallery_descriptions[i] if i < len(gallery_descriptions) else '',
                        alt_text=gallery_alt_texts[i] if i < len(gallery_alt_texts) else '',
                        sort_order=i
                    )
                    db.session.add(gallery_item)
        
        # Handle related links
        link_titles = request.form.getlist('link_title[]')
        link_urls = request.form.getlist('link_url[]')
        
        for i, title in enumerate(link_titles):
            if title.strip() and i < len(link_urls) and link_urls[i].strip():
                # Check if the checkbox for this link is checked
                new_tab_checked = request.form.get(f'link_new_tab_{i}') is not None
                link = ContentLink(
                    content_page_id=content_page.id,
                    title=title.strip(),
                    url=link_urls[i].strip(),
                    new_tab=new_tab_checked,
                    sort_order=i
                )
                db.session.add(link)
        
        # Handle downloads
        download_files = request.files.getlist('download_files[]')
        download_titles = request.form.getlist('download_title[]')
        download_descriptions = request.form.getlist('download_description[]')
        download_alt_texts = request.form.getlist('download_alt_text[]')
        
        for i, file in enumerate(download_files):
            if file and file.filename:
                filename = save_uploaded_file(file, 'content/downloads', 'download')
                if filename:
                    download_item = ContentDownload(
                        content_page_id=content_page.id,
                        filename=filename,
                        title=download_titles[i] if i < len(download_titles) else file.filename,
                        description=download_descriptions[i] if i < len(download_descriptions) else '',
                        alt_text=download_alt_texts[i] if i < len(download_alt_texts) else '',
                        sort_order=i
                    )
                    db.session.add(download_item)
        
        db.session.commit()
        flash('Content page created successfully!', 'success')
        return redirect(url_for('content_pages_list'))
    
    # GET request - show form
    categories = ContentCategory.query.filter_by(is_active=True).all()
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Content Page - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <script src="https://cdn.quilljs.com/1.3.6/quill.min.js"></script>
        <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .section-card {
                border: none;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📝 Add New Content Page</h1>
                <a href="/content" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Content
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST" enctype="multipart/form-data">
                <!-- Basic Information -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-info-circle me-2"></i>Basic Information</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Page Title *</label>
                                    <input type="text" class="form-control" name="title" required>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Status</label>
                                    <select class="form-select" name="status">
                                        <option value="Draft">Draft</option>
                                        <option value="Published">Published</option>
                                        <option value="Archived">Archived</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Category *</label>
                                    <select class="form-select" name="category_id" id="categorySelect" required onchange="loadSubcategories()">
                                        <option value="">Select Category</option>
                                        {% for category in categories %}
                                        <option value="{{ category.id }}">{{ category.name }}</option>
                                        {% endfor %}
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Subcategory</label>
                                    <select class="form-select" name="subcategory_id" id="subcategorySelect">
                                        <option value="">Select Subcategory</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Short Description</label>
                            <textarea class="form-control" name="short_description" rows="3" placeholder="Brief summary of the page content"></textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Long Description</label>
                            <div id="longDescription" style="height: 300px;"></div>
                            <input type="hidden" name="long_description" id="longDescriptionInput">
                        </div>
                    </div>
                </div>
                
                <!-- Photo Gallery -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-images me-2"></i>Photo Gallery</h5>
                    </div>
                    <div class="card-body">
                        <div id="galleryContainer">
                            <div class="row mb-3 gallery-item">
                                <div class="col-md-3">
                                    <label class="form-label">Image</label>
                                    <input type="file" class="form-control" name="gallery_images[]" accept="image/*">
                                </div>
                                <div class="col-md-3">
                                    <label class="form-label">Title</label>
                                    <input type="text" class="form-control" name="gallery_title[]">
                                </div>
                                <div class="col-md-3">
                                    <label class="form-label">Description</label>
                                    <input type="text" class="form-control" name="gallery_description[]">
                                </div>
                                <div class="col-md-2">
                                    <label class="form-label">Alt Text</label>
                                    <input type="text" class="form-control" name="gallery_alt_text[]">
                                </div>
                                <div class="col-md-1">
                                    <label class="form-label">&nbsp;</label>
                                    <button type="button" class="btn btn-outline-danger d-block" onclick="removeGalleryItem(this)">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="addGalleryItem()">
                            <i class="fas fa-plus me-1"></i>Add Image
                        </button>
                    </div>
                </div>
                
                <!-- Related Links -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-link me-2"></i>Related Links</h5>
                    </div>
                    <div class="card-body">
                        <div id="linksContainer">
                            <div class="row mb-3 link-item">
                                <div class="col-md-4">
                                    <label class="form-label">Title</label>
                                    <input type="text" class="form-control" name="link_title[]">
                                </div>
                                <div class="col-md-5">
                                    <label class="form-label">URL</label>
                                    <input type="url" class="form-control" name="link_url[]">
                                </div>
                                <div class="col-md-2">
                                    <label class="form-label">New Tab</label>
                                    <div class="form-check">
                                        <input type="checkbox" class="form-check-input" name="link_new_tab_0" checked>
                                        <label class="form-check-label">Open in new tab</label>
                                    </div>
                                </div>
                                <div class="col-md-1">
                                    <label class="form-label">&nbsp;</label>
                                    <button type="button" class="btn btn-outline-danger d-block" onclick="removeLinkItem(this)">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="addLinkItem()">
                            <i class="fas fa-plus me-1"></i>Add Link
                        </button>
                    </div>
                </div>
                
                <!-- Downloads -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-download me-2"></i>Downloads</h5>
                    </div>
                    <div class="card-body">
                        <div id="downloadsContainer">
                            <div class="row mb-3 download-item">
                                <div class="col-md-3">
                                    <label class="form-label">File</label>
                                    <input type="file" class="form-control" name="download_files[]">
                                </div>
                                <div class="col-md-3">
                                    <label class="form-label">Title</label>
                                    <input type="text" class="form-control" name="download_title[]">
                                </div>
                                <div class="col-md-3">
                                    <label class="form-label">Description</label>
                                    <input type="text" class="form-control" name="download_description[]">
                                </div>
                                <div class="col-md-2">
                                    <label class="form-label">Alt Text</label>
                                    <input type="text" class="form-control" name="download_alt_text[]">
                                </div>
                                <div class="col-md-1">
                                    <label class="form-label">&nbsp;</label>
                                    <button type="button" class="btn btn-outline-danger d-block" onclick="removeDownloadItem(this)">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="addDownloadItem()">
                            <i class="fas fa-plus me-1"></i>Add Download
                        </button>
                    </div>
                </div>
                
                <!-- Date Information -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5><i class="fas fa-calendar me-2"></i>Date Information</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Created Date</label>
                                    <input type="date" class="form-control" name="created_date">
                                    <div class="form-text">Date when this content was originally created</div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Approved Date</label>
                                    <input type="date" class="form-control" name="approved_date">
                                    <div class="form-text">Date when this content was approved for publication</div>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Next Review Date</label>
                                    <input type="date" class="form-control" name="next_review_date">
                                    <div class="form-text">Set a date when this content should be reviewed for updates</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Submit -->
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save me-2"></i>Create Page
                    </button>
                    <a href="/content" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Initialize Quill.js
            var quill = new Quill('#longDescription', {
                theme: 'snow',
                modules: {
                    toolbar: [
                        [{ 'header': [1, 2, 3, false] }],
                        ['bold', 'italic', 'underline', 'strike'],
                        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                        [{ 'indent': '-1'}, { 'indent': '+1' }],
                        ['link', 'image'],
                        [{ 'align': [] }],
                        ['clean']
                    ]
                }
            });
            
            // Update hidden input when content changes
            quill.on('text-change', function() {
                document.getElementById('longDescriptionInput').value = quill.root.innerHTML;
            });
            
            // Update hidden input before form submission
            document.querySelector('form').addEventListener('submit', function() {
                document.getElementById('longDescriptionInput').value = quill.root.innerHTML;
            });
            
            // Category/Subcategory handling
            const subcategoriesData = {
                {% for category in categories %}
                {{ category.id }}: [
                    {% for subcategory in category.subcategories %}
                    {id: {{ subcategory.id }}, name: "{{ subcategory.name }}"}{{ "," if not loop.last }}
                    {% endfor %}
                ]{{ "," if not loop.last }}
                {% endfor %}
            };
            
            function loadSubcategories() {
                const categoryId = document.getElementById('categorySelect').value;
                const subcategorySelect = document.getElementById('subcategorySelect');
                
                subcategorySelect.innerHTML = '<option value="">Select Subcategory</option>';
                
                if (categoryId && subcategoriesData[categoryId]) {
                    subcategoriesData[categoryId].forEach(sub => {
                        const option = document.createElement('option');
                        option.value = sub.id;
                        option.textContent = sub.name;
                        subcategorySelect.appendChild(option);
                    });
                }
            }
            
            // Gallery management
            function addGalleryItem() {
                const container = document.getElementById('galleryContainer');
                const div = document.createElement('div');
                div.className = 'row mb-3 gallery-item';
                div.innerHTML = `
                    <div class="col-md-3">
                        <label class="form-label">Image</label>
                        <input type="file" class="form-control" name="gallery_images[]" accept="image/*">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Title</label>
                        <input type="text" class="form-control" name="gallery_title[]">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Description</label>
                        <input type="text" class="form-control" name="gallery_description[]">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Alt Text</label>
                        <input type="text" class="form-control" name="gallery_alt_text[]">
                    </div>
                    <div class="col-md-1">
                        <label class="form-label">&nbsp;</label>
                        <button type="button" class="btn btn-outline-danger d-block" onclick="removeGalleryItem(this)">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                container.appendChild(div);
            }
            
            function removeGalleryItem(button) {
                button.closest('.gallery-item').remove();
            }
            
            // Links management
            let linkCounter = 1;
            function addLinkItem() {
                const container = document.getElementById('linksContainer');
                const div = document.createElement('div');
                div.className = 'row mb-3 link-item';
                div.innerHTML = `
                    <div class="col-md-4">
                        <label class="form-label">Title</label>
                        <input type="text" class="form-control" name="link_title[]">
                    </div>
                    <div class="col-md-5">
                        <label class="form-label">URL</label>
                        <input type="url" class="form-control" name="link_url[]">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">New Tab</label>
                        <div class="form-check">
                            <input type="checkbox" class="form-check-input" name="link_new_tab_${linkCounter}" checked>
                            <label class="form-check-label">Open in new tab</label>
                        </div>
                    </div>
                    <div class="col-md-1">
                        <label class="form-label">&nbsp;</label>
                        <button type="button" class="btn btn-outline-danger d-block" onclick="removeLinkItem(this)">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                container.appendChild(div);
                linkCounter++;
            }
            
            function removeLinkItem(button) {
                button.closest('.link-item').remove();
            }
            
            // Downloads management
            function addDownloadItem() {
                const container = document.getElementById('downloadsContainer');
                const div = document.createElement('div');
                div.className = 'row mb-3 download-item';
                div.innerHTML = `
                    <div class="col-md-3">
                        <label class="form-label">File</label>
                        <input type="file" class="form-control" name="download_files[]">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Title</label>
                        <input type="text" class="form-control" name="download_title[]">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label">Description</label>
                        <input type="text" class="form-control" name="download_description[]">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Alt Text</label>
                        <input type="text" class="form-control" name="download_alt_text[]">
                    </div>
                    <div class="col-md-1">
                        <label class="form-label">&nbsp;</label>
                        <button type="button" class="btn btn-outline-danger d-block" onclick="removeDownloadItem(this)">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                container.appendChild(div);
            }
            
            function removeDownloadItem(button) {
                button.closest('.download-item').remove();
            }
        </script>
    </body>
    </html>
    ''', categories=categories)

@app.route('/content/edit/<int:page_id>', methods=['GET', 'POST'])
@login_required
def edit_content_page(page_id):
    page = ContentPage.query.get_or_404(page_id)
    
    if request.method == 'POST':
        # Update basic information
        page.title = request.form.get('title')
        page.status = request.form.get('status')
        page.category_id = request.form.get('category_id')
        page.subcategory_id = request.form.get('subcategory_id') if request.form.get('subcategory_id') else None
        page.short_description = request.form.get('short_description')
        page.long_description = request.form.get('long_description')
        
        # Handle date fields
        created_date = request.form.get('created_date')
        if created_date:
            try:
                page.creation_date = datetime.strptime(created_date, '%Y-%m-%d')
            except ValueError:
                pass  # Keep existing if invalid date
        
        approved_date = request.form.get('approved_date')
        if approved_date:
            try:
                page.approval_date = datetime.strptime(approved_date, '%Y-%m-%d')
            except ValueError:
                pass  # Keep existing if invalid date
        else:
            page.approval_date = None
        
        next_review_date = request.form.get('next_review_date')
        if next_review_date:
            try:
                page.next_review_date = datetime.strptime(next_review_date, '%Y-%m-%d')
            except ValueError:
                pass  # Keep existing if invalid date
        else:
            page.next_review_date = None
        
        # Handle gallery updates
        existing_gallery_ids = request.form.getlist('existing_gallery_ids[]')
        gallery_files = request.files.getlist('gallery_files[]')
        gallery_titles = request.form.getlist('gallery_title[]')
        gallery_descriptions = request.form.getlist('gallery_description[]')
        gallery_alt_texts = request.form.getlist('gallery_alt_text[]')
        
        # Remove gallery items not in the form (deleted items)
        current_gallery_ids = [str(item.id) for item in page.gallery_images]
        for gallery_id in current_gallery_ids:
            if gallery_id not in existing_gallery_ids:
                gallery_item = ContentGallery.query.get(gallery_id)
                if gallery_item:
                    db.session.delete(gallery_item)
        
        # Update existing and add new gallery items
        for i, title in enumerate(gallery_titles):
            if i < len(existing_gallery_ids) and existing_gallery_ids[i]:
                # Update existing gallery item
                gallery_item = ContentGallery.query.get(existing_gallery_ids[i])
                if gallery_item:
                    gallery_item.title = title.strip() if title else None
                    gallery_item.description = gallery_descriptions[i].strip() if i < len(gallery_descriptions) and gallery_descriptions[i] else None
                    gallery_item.alt_text = gallery_alt_texts[i].strip() if i < len(gallery_alt_texts) and gallery_alt_texts[i] else None
                    
                    # Update file if new one uploaded
                    if i < len(gallery_files) and gallery_files[i] and gallery_files[i].filename:
                        filename = save_uploaded_file(gallery_files[i], 'content/images', 'gallery')
                        if filename:
                            gallery_item.filename = filename
            else:
                # Add new gallery item
                if i < len(gallery_files) and gallery_files[i] and gallery_files[i].filename:
                    filename = save_uploaded_file(gallery_files[i], 'content/images', 'gallery')
                    if filename:
                        gallery_item = ContentGallery(
                            content_page_id=page.id,
                            filename=filename,
                            title=title.strip() if title else None,
                            description=gallery_descriptions[i].strip() if i < len(gallery_descriptions) and gallery_descriptions[i] else None,
                            alt_text=gallery_alt_texts[i].strip() if i < len(gallery_alt_texts) and gallery_alt_texts[i] else None
                        )
                        db.session.add(gallery_item)
        
        # Handle links updates
        existing_link_ids = request.form.getlist('existing_link_ids[]')
        link_titles = request.form.getlist('link_title[]')
        link_urls = request.form.getlist('link_url[]')
        
        # Remove links not in the form (deleted items)
        current_link_ids = [str(link.id) for link in page.related_links]
        for link_id in current_link_ids:
            if link_id not in existing_link_ids:
                link_item = ContentLink.query.get(link_id)
                if link_item:
                    db.session.delete(link_item)
        
        # Update existing and add new links
        for i, title in enumerate(link_titles):
            if title.strip() and i < len(link_urls) and link_urls[i].strip():
                new_tab_checked = request.form.get(f'link_new_tab_{i}') is not None
                
                if i < len(existing_link_ids) and existing_link_ids[i]:
                    # Update existing link
                    link_item = ContentLink.query.get(existing_link_ids[i])
                    if link_item:
                        link_item.title = title.strip()
                        link_item.url = link_urls[i].strip()
                        link_item.new_tab = new_tab_checked
                        link_item.sort_order = i
                else:
                    # Add new link
                    link_item = ContentLink(
                        content_page_id=page.id,
                        title=title.strip(),
                        url=link_urls[i].strip(),
                        new_tab=new_tab_checked,
                        sort_order=i
                    )
                    db.session.add(link_item)
        
        # Handle downloads updates
        existing_download_ids = request.form.getlist('existing_download_ids[]')
        download_files = request.files.getlist('download_files[]')
        download_titles = request.form.getlist('download_title[]')
        download_descriptions = request.form.getlist('download_description[]')
        
        # Remove downloads not in the form (deleted items)
        current_download_ids = [str(download.id) for download in page.downloads]
        for download_id in current_download_ids:
            if download_id not in existing_download_ids:
                download_item = ContentDownload.query.get(download_id)
                if download_item:
                    db.session.delete(download_item)
        
        # Update existing and add new downloads
        for i, title in enumerate(download_titles):
            if title.strip():
                if i < len(existing_download_ids) and existing_download_ids[i]:
                    # Update existing download
                    download_item = ContentDownload.query.get(existing_download_ids[i])
                    if download_item:
                        download_item.title = title.strip()
                        download_item.description = download_descriptions[i].strip() if i < len(download_descriptions) and download_descriptions[i] else None
                        
                        # Update file if new one uploaded
                        if i < len(download_files) and download_files[i] and download_files[i].filename:
                            filename = save_uploaded_file(download_files[i], 'content/downloads', 'download')
                            if filename:
                                download_item.filename = filename
                else:
                    # Add new download
                    if i < len(download_files) and download_files[i] and download_files[i].filename:
                        filename = save_uploaded_file(download_files[i], 'content/downloads', 'download')
                        if filename:
                            download_item = ContentDownload(
                                content_page_id=page.id,
                                filename=filename,
                                title=title.strip(),
                                description=download_descriptions[i].strip() if i < len(download_descriptions) and download_descriptions[i] else None
                            )
                            db.session.add(download_item)
        
        # Set updated timestamp
        page.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Content page updated successfully!', 'success')
        return redirect(url_for('content_pages_list'))
    
    # GET request - show form with existing data
    categories = ContentCategory.query.filter_by(is_active=True).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Content Page - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <script src="https://cdn.quilljs.com/1.3.6/quill.min.js"></script>
        <link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>✏️ Edit Content Page</h1>
                <a href="/content/pages" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Pages
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST" enctype="multipart/form-data">
                <!-- Basic Information -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5><i class="fas fa-info-circle me-2"></i>Basic Information</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Page Title *</label>
                                    <input type="text" class="form-control" name="title" value="{{ page.title }}" required>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Status</label>
                                    <select class="form-select" name="status">
                                        <option value="Draft" {{ 'selected' if page.status == 'Draft' else '' }}>Draft</option>
                                        <option value="Published" {{ 'selected' if page.status == 'Published' else '' }}>Published</option>
                                        <option value="Archived" {{ 'selected' if page.status == 'Archived' else '' }}>Archived</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Category *</label>
                                    <select class="form-select" name="category_id" id="categorySelect" onchange="loadSubcategories()" required>
                                        <option value="">Select Category</option>
                                        {% for category in categories %}
                                        <option value="{{ category.id }}" {{ 'selected' if page.category_id == category.id else '' }}>{{ category.name }}</option>
                                        {% endfor %}
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Subcategory</label>
                                    <select class="form-select" name="subcategory_id" id="subcategorySelect">
                                        <option value="">Select Subcategory</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Short Description</label>
                            <textarea class="form-control" name="short_description" rows="3" placeholder="Brief summary of the page content">{{ page.short_description or '' }}</textarea>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Long Description</label>
                            <div id="longDescription" style="height: 300px;"></div>
                            <input type="hidden" name="long_description" id="longDescriptionInput" value="{{ page.long_description or '' }}">
                        </div>
                    </div>
                </div>
                
                <!-- Date Information -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5><i class="fas fa-calendar me-2"></i>Date Information</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Created Date</label>
                                    <input type="date" class="form-control" name="created_date" value="{{ page.creation_date.strftime('%Y-%m-%d') if page.creation_date else '' }}">
                                    <div class="form-text">Date when this content was originally created</div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Approved Date</label>
                                    <input type="date" class="form-control" name="approved_date" value="{{ page.approval_date.strftime('%Y-%m-%d') if page.approval_date else '' }}">
                                    <div class="form-text">Date when this content was approved for publication</div>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Next Review Date</label>
                                    <input type="date" class="form-control" name="next_review_date" value="{{ page.next_review_date.strftime('%Y-%m-%d') if page.next_review_date else '' }}">
                                    <div class="form-text">Set a date when this content should be reviewed for updates</div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Last Updated</label>
                                    <input type="text" class="form-control" value="{{ page.updated_at.strftime('%Y-%m-%d %H:%M') if page.updated_at else '' }}" readonly>
                                    <div class="form-text">Automatically updated when content is saved</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Photo Gallery Section -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-images me-2"></i>Photo Gallery</h5>
                    </div>
                    <div class="card-body">
                        <div id="gallery-container">
                            {% for item in page.gallery_images %}
                            <div class="gallery-item border rounded p-3 mb-3">
                                <div class="row">
                                    <div class="col-md-3">
                                        <label class="form-label">Image</label>
                                        <input type="file" class="form-control" name="gallery_files[]" accept="image/*">
                                        <input type="hidden" name="existing_gallery_ids[]" value="{{ item.id }}">
                                        {% if item.filename %}
                                        <div class="mt-2">
                                            <img src="/uploads/content/images/{{ item.filename }}" class="img-thumbnail" style="max-height: 100px;">
                                            <div class="small text-muted">Current: {{ item.filename }}</div>
                                        </div>
                                        {% endif %}
                                    </div>
                                    <div class="col-md-3">
                                        <label class="form-label">Title</label>
                                        <input type="text" class="form-control" name="gallery_title[]" value="{{ item.title or '' }}">
                                    </div>
                                    <div class="col-md-3">
                                        <label class="form-label">Description</label>
                                        <textarea class="form-control" name="gallery_description[]" rows="2">{{ item.description or '' }}</textarea>
                                    </div>
                                    <div class="col-md-2">
                                        <label class="form-label">Alt Text</label>
                                        <input type="text" class="form-control" name="gallery_alt_text[]" value="{{ item.alt_text or '' }}">
                                    </div>
                                    <div class="col-md-1">
                                        <label class="form-label">&nbsp;</label>
                                        <button type="button" class="btn btn-outline-danger d-block" onclick="removeGalleryItem(this)">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                        <button type="button" class="btn btn-outline-primary" onclick="addGalleryItem()">
                            <i class="fas fa-plus me-2"></i>Add Gallery Item
                        </button>
                    </div>
                </div>

                <!-- Related Links Section -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-link me-2"></i>Related Links</h5>
                    </div>
                    <div class="card-body">
                        <div id="links-container">
                            {% for link in page.related_links %}
                            <div class="link-item border rounded p-3 mb-3">
                                <div class="row">
                                    <div class="col-md-4">
                                        <label class="form-label">Link Title</label>
                                        <input type="text" class="form-control" name="link_title[]" value="{{ link.title or '' }}" required>
                                        <input type="hidden" name="existing_link_ids[]" value="{{ link.id }}">
                                    </div>
                                    <div class="col-md-4">
                                        <label class="form-label">URL</label>
                                        <input type="url" class="form-control" name="link_url[]" value="{{ link.url or '' }}" required>
                                    </div>
                                    <div class="col-md-2">
                                        <label class="form-label">Open in New Tab</label>
                                        <div class="form-check">
                                            <input type="checkbox" class="form-check-input" name="link_new_tab_{{ loop.index0 }}" {% if link.new_tab %}checked{% endif %}>
                                            <label class="form-check-label">New Tab</label>
                                        </div>
                                    </div>
                                    <div class="col-md-2">
                                        <label class="form-label">&nbsp;</label>
                                        <button type="button" class="btn btn-outline-danger d-block" onclick="removeLinkItem(this)">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                        <button type="button" class="btn btn-outline-primary" onclick="addLinkItem()">
                            <i class="fas fa-plus me-2"></i>Add Related Link
                        </button>
                    </div>
                </div>

                <!-- Downloads Section -->
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-download me-2"></i>Downloads</h5>
                    </div>
                    <div class="card-body">
                        <div id="downloads-container">
                            {% for download in page.downloads %}
                            <div class="download-item border rounded p-3 mb-3">
                                <div class="row">
                                    <div class="col-md-3">
                                        <label class="form-label">File</label>
                                        <input type="file" class="form-control" name="download_files[]">
                                        <input type="hidden" name="existing_download_ids[]" value="{{ download.id }}">
                                        {% if download.filename %}
                                        <div class="mt-2">
                                            <a href="/uploads/content/downloads/{{ download.filename }}" class="btn btn-sm btn-outline-info" target="_blank">
                                                <i class="fas fa-download me-1"></i>{{ download.filename }}
                                            </a>
                                        </div>
                                        {% endif %}
                                    </div>
                                    <div class="col-md-3">
                                        <label class="form-label">Title</label>
                                        <input type="text" class="form-control" name="download_title[]" value="{{ download.title or '' }}" required>
                                    </div>
                                    <div class="col-md-4">
                                        <label class="form-label">Description</label>
                                        <textarea class="form-control" name="download_description[]" rows="2">{{ download.description or '' }}</textarea>
                                    </div>
                                    <div class="col-md-1">
                                        <label class="form-label">&nbsp;</label>
                                        <button type="button" class="btn btn-outline-danger d-block" onclick="removeDownloadItem(this)">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                        <button type="button" class="btn btn-outline-primary" onclick="addDownloadItem()">
                            <i class="fas fa-plus me-2"></i>Add Download
                        </button>
                    </div>
                </div>
                
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save me-2"></i>Update Page
                    </button>
                    <a href="/content/pages" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Initialize Quill.js with existing content
            var quill = new Quill('#longDescription', {
                theme: 'snow',
                modules: {
                    toolbar: [
                        [{ 'header': [1, 2, 3, false] }],
                        ['bold', 'italic', 'underline', 'strike'],
                        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                        [{ 'indent': '-1'}, { 'indent': '+1' }],
                        ['link', 'image'],
                        [{ 'align': [] }],
                        ['clean']
                    ]
                }
            });
            
            // Set existing content
            var existingContent = document.getElementById('longDescriptionInput').value;
            if (existingContent) {
                quill.root.innerHTML = existingContent;
            }
            
            // Update hidden input when content changes
            quill.on('text-change', function() {
                document.getElementById('longDescriptionInput').value = quill.root.innerHTML;
            });
            
            // Update hidden input before form submission
            document.querySelector('form').addEventListener('submit', function() {
                document.getElementById('longDescriptionInput').value = quill.root.innerHTML;
            });
            
            // Category/Subcategory handling
            const subcategoriesData = {
                {% for category in categories %}
                {{ category.id }}: [
                    {% for subcategory in category.subcategories %}
                    {id: {{ subcategory.id }}, name: "{{ subcategory.name }}"}{{ "," if not loop.last }}
                    {% endfor %}
                ]{{ "," if not loop.last }}
                {% endfor %}
            };
            
            function loadSubcategories() {
                const categoryId = document.getElementById('categorySelect').value;
                const subcategorySelect = document.getElementById('subcategorySelect');
                
                subcategorySelect.innerHTML = '<option value="">Select Subcategory</option>';
                
                if (categoryId && subcategoriesData[categoryId]) {
                    subcategoriesData[categoryId].forEach(sub => {
                        const option = document.createElement('option');
                        option.value = sub.id;
                        option.textContent = sub.name;
                        {% if page.subcategory_id %}
                        if (sub.id == {{ page.subcategory_id }}) {
                            option.selected = true;
                        }
                        {% endif %}
                        subcategorySelect.appendChild(option);
                    });
                }
            }
            
            // Load subcategories on page load
            loadSubcategories();
            
            // Gallery management
            let galleryCounter = {{ page.gallery_images|length }};
            
            function addGalleryItem() {
                const container = document.getElementById('gallery-container');
                const newItem = document.createElement('div');
                newItem.className = 'gallery-item border rounded p-3 mb-3';
                newItem.innerHTML = `
                    <div class="row">
                        <div class="col-md-3">
                            <label class="form-label">Image</label>
                            <input type="file" class="form-control" name="gallery_files[]" accept="image/*" required>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Title</label>
                            <input type="text" class="form-control" name="gallery_title[]">
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Description</label>
                            <textarea class="form-control" name="gallery_description[]" rows="2"></textarea>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Alt Text</label>
                            <input type="text" class="form-control" name="gallery_alt_text[]">
                        </div>
                        <div class="col-md-1">
                            <label class="form-label">&nbsp;</label>
                            <button type="button" class="btn btn-outline-danger d-block" onclick="removeGalleryItem(this)">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `;
                container.appendChild(newItem);
                galleryCounter++;
            }
            
            function removeGalleryItem(button) {
                button.closest('.gallery-item').remove();
            }
            
            // Links management
            let linkCounter = {{ page.related_links|length }};
            
            function addLinkItem() {
                const container = document.getElementById('links-container');
                const newItem = document.createElement('div');
                newItem.className = 'link-item border rounded p-3 mb-3';
                newItem.innerHTML = `
                    <div class="row">
                        <div class="col-md-4">
                            <label class="form-label">Link Title</label>
                            <input type="text" class="form-control" name="link_title[]" required>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">URL</label>
                            <input type="url" class="form-control" name="link_url[]" required>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">Open in New Tab</label>
                            <div class="form-check">
                                <input type="checkbox" class="form-check-input" name="link_new_tab_${linkCounter}">
                                <label class="form-check-label">New Tab</label>
                            </div>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">&nbsp;</label>
                            <button type="button" class="btn btn-outline-danger d-block" onclick="removeLinkItem(this)">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `;
                container.appendChild(newItem);
                linkCounter++;
            }
            
            function removeLinkItem(button) {
                button.closest('.link-item').remove();
            }
            
            // Downloads management
            let downloadCounter = {{ page.downloads|length }};
            
            function addDownloadItem() {
                const container = document.getElementById('downloads-container');
                const newItem = document.createElement('div');
                newItem.className = 'download-item border rounded p-3 mb-3';
                newItem.innerHTML = `
                    <div class="row">
                        <div class="col-md-3">
                            <label class="form-label">File</label>
                            <input type="file" class="form-control" name="download_files[]" required>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Title</label>
                            <input type="text" class="form-control" name="download_title[]" required>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Description</label>
                            <textarea class="form-control" name="download_description[]" rows="2"></textarea>
                        </div>
                        <div class="col-md-1">
                            <label class="form-label">&nbsp;</label>
                            <button type="button" class="btn btn-outline-danger d-block" onclick="removeDownloadItem(this)">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                `;
                container.appendChild(newItem);
                downloadCounter++;
            }
            
            function removeDownloadItem(button) {
                button.closest('.download-item').remove();
            }
        </script>
    </body>
    </html>
    ''', page=page, categories=categories)

@app.route('/content/view/<int:page_id>')
@login_required
def view_content_page(page_id):
    page = ContentPage.query.get_or_404(page_id)
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ page.title }} - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .content-view {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 2rem;
            }
            .status-badge {
                font-size: 0.875rem;
                padding: 0.375rem 0.75rem;
            }
            .gallery-item {
                margin-bottom: 1rem;
            }
            .gallery-item img {
                max-width: 200px;
                height: auto;
                border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link active">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
            </div>
            <div class="mt-auto p-3 border-top">
                <a href="/logout" class="nav-link text-danger">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>

        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h2><i class="fas fa-eye me-2"></i>View Content Page</h2>
                    <nav aria-label="breadcrumb">
                        <ol class="breadcrumb">
                            <li class="breadcrumb-item"><a href="/content">Content</a></li>
                            <li class="breadcrumb-item"><a href="/content/pages">All Pages</a></li>
                            <li class="breadcrumb-item active">{{ page.title }}</li>
                        </ol>
                    </nav>
                </div>
                <div>
                    <a href="/content/edit/{{ page.id }}" class="btn btn-primary">
                        <i class="fas fa-edit me-2"></i>Edit Page
                    </a>
                    <a href="/content/pages" class="btn btn-secondary">
                        <i class="fas fa-arrow-left me-2"></i>Back to Pages
                    </a>
                </div>
            </div>

            <div class="content-view">
                <!-- Basic Information -->
                <div class="row mb-4">
                    <div class="col-md-8">
                        <h1>{{ page.title }}</h1>
                        <p class="text-muted mb-3">{{ page.short_description or 'No short description provided.' }}</p>
                    </div>
                    <div class="col-md-4 text-end">
                        <span class="badge status-badge {% if page.status == 'Published' %}bg-success{% elif page.status == 'Draft' %}bg-warning{% else %}bg-secondary{% endif %}">
                            {{ page.status }}
                        </span>
                    </div>
                </div>

                <!-- Content -->
                <div class="mb-4">
                    <h3>Content</h3>
                    <div class="border-start border-primary ps-3">
                        {{ page.long_description|safe if page.long_description else '<p class="text-muted">No content provided.</p>'|safe }}
                    </div>
                </div>

                <!-- Metadata -->
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h4>Category Information</h4>
                        <ul class="list-unstyled">
                            <li><strong>Category:</strong> {{ page.category.name if page.category else 'Uncategorized' }}</li>
                            <li><strong>Subcategory:</strong> {{ page.subcategory.name if page.subcategory else 'None' }}</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h4>Date Information</h4>
                        <ul class="list-unstyled">
                            <li><strong>Created:</strong> {{ page.creation_date.strftime('%d/%m/%Y') if page.creation_date else 'Not set' }}</li>
                            <li><strong>Approved:</strong> {{ page.approval_date.strftime('%d/%m/%Y') if page.approval_date else 'Not approved' }}</li>
                            <li><strong>Last Updated:</strong> {{ page.updated_at.strftime('%d/%m/%Y %H:%M') if page.updated_at else 'Never' }}</li>
                            <li><strong>Next Review:</strong> {{ page.next_review_date.strftime('%d/%m/%Y') if page.next_review_date else 'Not scheduled' }}</li>
                        </ul>
                    </div>
                </div>

                <!-- Gallery -->
                {% if page.gallery_images %}
                <div class="mb-4">
                    <h4>Photo Gallery</h4>
                    <div class="row">
                        {% for item in page.gallery_images %}
                        <div class="col-md-4 gallery-item">
                            <div class="card">
                                <img src="/uploads/content/images/{{ item.filename }}" class="card-img-top" alt="{{ item.alt_text or item.title }}">
                                <div class="card-body">
                                    <h6 class="card-title">{{ item.title or 'Untitled' }}</h6>
                                    <p class="card-text small">{{ item.description or '' }}</p>
                                </div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}

                <!-- Related Links -->
                {% if page.related_links %}
                <div class="mb-4">
                    <h4>Related Links</h4>
                    <ul class="list-group">
                        {% for link in page.related_links %}
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <a href="{{ link.url }}" {% if link.new_tab %}target="_blank"{% endif %} class="fw-bold">
                                    {{ link.title }}
                                    {% if link.new_tab %}<i class="fas fa-external-link-alt ms-1 small"></i>{% endif %}
                                </a>
                            </div>
                        </li>
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}

                <!-- Downloads -->
                {% if page.downloads %}
                <div class="mb-4">
                    <h4>Downloads</h4>
                    <ul class="list-group">
                        {% for download in page.downloads %}
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <a href="/uploads/content/downloads/{{ download.filename }}" class="fw-bold" download>
                                    <i class="fas fa-download me-2"></i>{{ download.title }}
                                </a>
                                {% if download.description %}
                                <div class="text-muted small">{{ download.description }}</div>
                                {% endif %}
                            </div>
                        </li>
                        {% endfor %}
                    </ul>
                </div>
                {% endif %}
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', page=page)

@app.route('/events')
@login_required
def events_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    
    query = Event.query
    
    if search:
        query = query.filter(Event.title.contains(search))
    if category_filter:
        query = query.filter_by(category_id=category_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    events = query.order_by(Event.start_date.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    categories = EventCategory.query.filter_by(is_active=True).all()
    
    # Get statistics
    total_events = Event.query.count()
    upcoming_events = Event.query.filter(Event.start_date > datetime.utcnow(), Event.is_published == True).count()
    published_events = Event.query.filter_by(is_published=True).count()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Events & Things to Do - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .event-card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
                margin-bottom: 1rem;
            }
            .event-card:hover {
                transform: translateY(-2px);
            }
            .stat-card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.3s ease;
            }
            .stat-card:hover {
                transform: translateY(-5px);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link active">
                    <i class="fas fa-calendar me-2"></i>Events & Things to Do
                </a>
                <a href="/meetings" class="nav-link">
                    <i class="fas fa-handshake me-2"></i>Meetings
                </a>
                <a href="/homepage" class="nav-link">
                    <i class="fas fa-home me-2"></i>Homepage
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📅 Events & Things to Do</h1>
                <div>
                    <a href="/events/categories" class="btn btn-outline-primary me-2">
                        <i class="fas fa-list me-2"></i>Manage Categories
                    </a>
                    <a href="/events/add" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Add New Event
                    </a>
                </div>
            </div>
            
            <!-- Statistics Cards -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="stat-card p-4 text-center">
                        <div class="text-primary mb-2">
                            <i class="fas fa-calendar fa-2x"></i>
                        </div>
                        <h3 class="mb-1">{{ total_events }}</h3>
                        <p class="text-muted mb-0">Total Events</p>
                        <small class="text-success">{{ published_events }} published</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card p-4 text-center">
                        <div class="text-warning mb-2">
                            <i class="fas fa-clock fa-2x"></i>
                        </div>
                        <h3 class="mb-1">{{ upcoming_events }}</h3>
                        <p class="text-muted mb-0">Upcoming Events</p>
                        <small class="text-info">Next 30 days</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stat-card p-4 text-center">
                        <div class="text-info mb-2">
                            <i class="fas fa-list fa-2x"></i>
                        </div>
                        <h3 class="mb-1">{{ categories|length }}</h3>
                        <p class="text-muted mb-0">Event Categories</p>
                        <small class="text-success">Active categories</small>
                    </div>
                </div>
            </div>
            
            <!-- Search and Filters -->
            <div class="card mb-4">
                <div class="card-body">
                    <form method="GET" class="row g-3">
                        <div class="col-md-4">
                            <input type="text" class="form-control" name="search" 
                                   placeholder="Search events..." value="{{ request.args.get('search', '') }}">
                        </div>
                        <div class="col-md-3">
                            <select class="form-select" name="category">
                                <option value="">All Categories</option>
                                {% for category in categories %}
                                <option value="{{ category.id }}" 
                                        {{ 'selected' if request.args.get('category') == category.id|string }}>
                                    {{ category.name }}
                                </option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-3">
                            <select class="form-select" name="status">
                                <option value="">All Status</option>
                                <option value="Draft" {{ 'selected' if request.args.get('status') == 'Draft' }}>Draft</option>
                                <option value="Published" {{ 'selected' if request.args.get('status') == 'Published' }}>Published</option>
                                <option value="Cancelled" {{ 'selected' if request.args.get('status') == 'Cancelled' }}>Cancelled</option>
                            </select>
                        </div>
                        <div class="col-md-2">
                            <button type="submit" class="btn btn-outline-primary w-100">
                                <i class="fas fa-search"></i> Filter
                            </button>
                        </div>
                    </form>
                </div>
            </div>
            
            <!-- Events List -->
            {% if events.items %}
            <div class="row">
                {% for event in events.items %}
                <div class="col-md-6">
                    <div class="event-card">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-3">
                                <h5 class="card-title mb-0">{{ event.title }}</h5>
                                <div class="dropdown">
                                    <button class="btn btn-sm btn-outline-secondary dropdown-toggle" 
                                            data-bs-toggle="dropdown">
                                        <i class="fas fa-ellipsis-v"></i>
                                    </button>
                                    <ul class="dropdown-menu">
                                        <li><a class="dropdown-item" href="/events/edit/{{ event.id }}">
                                            <i class="fas fa-edit me-2"></i>Edit
                                        </a></li>
                                        <li><a class="dropdown-item" href="/events/view/{{ event.id }}">
                                            <i class="fas fa-eye me-2"></i>View
                                        </a></li>
                                        <li><hr class="dropdown-divider"></li>
                                        <li><a class="dropdown-item text-danger" href="/events/delete/{{ event.id }}"
                                               onclick="return confirm('Are you sure?')">
                                            <i class="fas fa-trash me-2"></i>Delete
                                        </a></li>
                                    </ul>
                                </div>
                            </div>
                            
                            <div class="mb-2">
                                <i class="fas fa-calendar me-2 text-primary"></i>
                                <strong>{{ event.start_date|uk_date }}</strong>
                                {% if not event.all_day %}
                                at {{ event.start_date.strftime('%H:%M') }}
                                {% endif %}
                            </div>
                            
                            {% if event.location_name %}
                            <div class="mb-2">
                                <i class="fas fa-map-marker-alt me-2 text-danger"></i>
                                {{ event.location_name }}
                            </div>
                            {% endif %}
                            
                            {% if event.category %}
                            <div class="mb-2">
                                <span class="badge" style="background-color: {{ event.category.color }};">
                                    <i class="{{ event.category.icon }} me-1"></i>
                                    {{ event.category.name }}
                                </span>
                            </div>
                            {% endif %}
                            
                            {% if event.description %}
                            <p class="text-muted mb-3">{{ event.description[:100] }}{% if event.description|length > 100 %}...{% endif %}</p>
                            {% endif %}
                            
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <span class="badge bg-{{ 'success' if event.status == 'Published' else 'warning' if event.status == 'Draft' else 'danger' }}">
                                        {{ event.status }}
                                    </span>
                                    {% if event.featured %}
                                    <span class="badge bg-info">Featured</span>
                                    {% endif %}
                                    {% if event.is_free %}
                                    <span class="badge bg-success">Free</span>
                                    {% endif %}
                                </div>
                                <small class="text-muted">
                                    Updated: {{ event.updated_at|uk_date }}
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            
            <!-- Pagination -->
            {% if events.pages > 1 %}
            <nav aria-label="Events pagination">
                <ul class="pagination justify-content-center">
                    {% if events.has_prev %}
                    <li class="page-item">
                        <a class="page-link" href="{{ url_for('events_list', page=events.prev_num, 
                           search=request.args.get('search', ''), 
                           category=request.args.get('category', ''),
                           status=request.args.get('status', '')) }}">Previous</a>
                    </li>
                    {% endif %}
                    
                    {% for page_num in events.iter_pages() %}
                        {% if page_num %}
                            {% if page_num != events.page %}
                            <li class="page-item">
                                <a class="page-link" href="{{ url_for('events_list', page=page_num,
                                   search=request.args.get('search', ''), 
                                   category=request.args.get('category', ''),
                                   status=request.args.get('status', '')) }}">{{ page_num }}</a>
                            </li>
                            {% else %}
                            <li class="page-item active">
                                <span class="page-link">{{ page_num }}</span>
                            </li>
                            {% endif %}
                        {% else %}
                        <li class="page-item disabled">
                            <span class="page-link">...</span>
                        </li>
                        {% endif %}
                    {% endfor %}
                    
                    {% if events.has_next %}
                    <li class="page-item">
                        <a class="page-link" href="{{ url_for('events_list', page=events.next_num,
                           search=request.args.get('search', ''), 
                           category=request.args.get('category', ''),
                           status=request.args.get('status', '')) }}">Next</a>
                    </li>
                    {% endif %}
                </ul>
            </nav>
            {% endif %}
            
            {% else %}
            <div class="text-center py-5">
                <i class="fas fa-calendar fa-3x text-muted mb-3"></i>
                <h4>No Events Found</h4>
                <p class="text-muted">Start by creating your first event or adjust your search filters.</p>
                <a href="/events/add" class="btn btn-primary">
                    <i class="fas fa-plus me-2"></i>Create First Event
                </a>
            </div>
            {% endif %}
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', events=events, categories=categories, total_events=total_events, 
         upcoming_events=upcoming_events, published_events=published_events)

@app.route('/settings')
@login_required
def settings():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Settings - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/settings" class="nav-link active">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="text-center">
                <div class="card">
                    <div class="card-body py-5">
                        <i class="fas fa-cog fa-3x text-muted mb-3"></i>
                        <h4>System Settings</h4>
                        <p class="text-muted">Settings management will be available in Phase 2</p>
                        <small class="text-muted">This will include site configuration, user management, and system preferences</small>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    ''')

# Event Management Routes (moved from after app.run)
@app.route('/events/add', methods=['GET', 'POST'])
@login_required
def add_event():
    if request.method == 'POST':
        # Handle form submission
        event = Event(
            title=request.form['title'],
            short_description=request.form.get('short_description'),
            description=request.form.get('description'),
            category_id=request.form.get('category_id') if request.form.get('category_id') else None,
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%dT%H:%M'),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%dT%H:%M') if request.form.get('end_date') else None,
            all_day=bool(request.form.get('all_day')),
            location_name=request.form.get('location_name'),
            location_address=request.form.get('location_address'),
            location_url=request.form.get('location_url'),
            contact_name=request.form.get('contact_name'),
            contact_email=request.form.get('contact_email'),
            contact_phone=request.form.get('contact_phone'),
            booking_required=bool(request.form.get('booking_required')),
            booking_url=request.form.get('booking_url'),
            max_attendees=int(request.form['max_attendees']) if request.form.get('max_attendees') else None,
            is_free=bool(request.form.get('is_free')),
            price=request.form.get('price'),
            featured=bool(request.form.get('featured')),
            status=request.form.get('status', 'Draft'),
            is_published=bool(request.form.get('is_published'))
        )
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = save_uploaded_file(file, 'events')
                event.image_filename = filename
        
        db.session.add(event)
        db.session.commit()
        
        # Handle multiple category assignments
        selected_categories = request.form.getlist('categories')
        for category_id in selected_categories:
            if category_id:
                assignment = EventCategoryAssignment(
                    event_id=event.id,
                    category_id=int(category_id)
                )
                db.session.add(assignment)
        
        # Handle gallery images
        gallery_files = request.files.getlist('gallery_images')
        gallery_titles = request.form.getlist('gallery_titles')
        gallery_descriptions = request.form.getlist('gallery_descriptions')
        gallery_alt_texts = request.form.getlist('gallery_alt_texts')
        
        for i, file in enumerate(gallery_files):
            if file and file.filename and allowed_file(file.filename):
                filename = save_uploaded_file(file, 'events/gallery')
                gallery_image = EventGallery(
                    event_id=event.id,
                    filename=filename,
                    title=gallery_titles[i] if i < len(gallery_titles) else '',
                    description=gallery_descriptions[i] if i < len(gallery_descriptions) else '',
                    alt_text=gallery_alt_texts[i] if i < len(gallery_alt_texts) else '',
                    sort_order=i
                )
                db.session.add(gallery_image)
        
        # Handle related links
        link_titles = request.form.getlist('link_titles')
        link_urls = request.form.getlist('link_urls')
        link_new_tabs = request.form.getlist('link_new_tabs')
        
        for i, title in enumerate(link_titles):
            if title.strip() and i < len(link_urls) and link_urls[i].strip():
                link = EventLink(
                    event_id=event.id,
                    title=title.strip(),
                    url=link_urls[i].strip(),
                    new_tab=str(i) in link_new_tabs,  # Checkbox values come as indices
                    sort_order=i
                )
                db.session.add(link)
        
        # Handle downloads
        download_files = request.files.getlist('download_files')
        download_titles = request.form.getlist('download_titles')
        download_descriptions = request.form.getlist('download_descriptions')
        
        for i, file in enumerate(download_files):
            if file and file.filename:
                filename = save_uploaded_file(file, 'events/downloads', 'download')
                if filename:
                    download_item = EventDownload(
                        event_id=event.id,
                        filename=filename,
                        title=download_titles[i] if i < len(download_titles) else file.filename,
                        description=download_descriptions[i] if i < len(download_descriptions) else '',
                        sort_order=i
                    )
                    db.session.add(download_item)
        
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('events_list'))
    
    categories = EventCategory.query.filter_by(is_active=True).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Event - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link active">
                    <i class="fas fa-calendar me-2"></i>Events & Things to Do
                </a>
                <a href="/meetings" class="nav-link">
                    <i class="fas fa-handshake me-2"></i>Meetings
                </a>
                <a href="/homepage" class="nav-link">
                    <i class="fas fa-home me-2"></i>Homepage
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📅 Add New Event</h1>
                <a href="/events" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Events
                </a>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Event Title *</label>
                                    <input type="text" class="form-control" name="title" required>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Description</label>
                                    <textarea class="form-control" name="description" rows="4" 
                                              placeholder="Describe the event..."></textarea>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Start Date & Time *</label>
                                            <input type="datetime-local" class="form-control" name="start_date" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">End Date & Time</label>
                                            <input type="datetime-local" class="form-control" name="end_date">
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="all_day" id="all_day">
                                        <label class="form-check-label" for="all_day">
                                            All Day Event
                                        </label>
                                    </div>
                                </div>
                                
                                <h5 class="mt-4 mb-3">📍 Location Details</h5>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Location Name</label>
                                            <input type="text" class="form-control" name="location_name" 
                                                   placeholder="e.g., Kesgrave Community Centre">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Google Maps URL</label>
                                            <input type="url" class="form-control" name="location_url" 
                                                   placeholder="https://maps.google.com/...">
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Location Address</label>
                                    <textarea class="form-control" name="location_address" rows="2" 
                                              placeholder="Full address..."></textarea>
                                </div>
                                
                                <h5 class="mt-4 mb-3">📞 Contact Information</h5>
                                <div class="row">
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Contact Name</label>
                                            <input type="text" class="form-control" name="contact_name">
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Contact Email</label>
                                            <input type="email" class="form-control" name="contact_email">
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Contact Phone</label>
                                            <input type="tel" class="form-control" name="contact_phone">
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Categories</label>
                                    <div class="border rounded p-3" style="max-height: 200px; overflow-y: auto;">
                                        {% for category in categories %}
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" name="categories" 
                                                   value="{{ category.id }}" id="cat_{{ category.id }}">
                                            <label class="form-check-label" for="cat_{{ category.id }}">
                                                {{ category.name }}
                                            </label>
                                        </div>
                                        {% endfor %}
                                    </div>
                                    <small class="text-muted">Select one or more categories</small>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Status</label>
                                    <select class="form-select" name="status">
                                        <option value="Draft">Draft</option>
                                        <option value="Published">Published</option>
                                        <option value="Cancelled">Cancelled</option>
                                    </select>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Event Image</label>
                                    <input type="file" class="form-control" name="image" accept="image/*">
                                    <small class="text-muted">JPG, PNG, GIF up to 16MB</small>
                                </div>
                                
                                <h6 class="mt-4 mb-3">🎫 Booking & Pricing</h6>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="is_free" id="is_free" checked>
                                        <label class="form-check-label" for="is_free">
                                            Free Event
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Price Details</label>
                                    <input type="text" class="form-control" name="price" 
                                           placeholder="e.g., £5 adults, £3 children">
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="booking_required" id="booking_required">
                                        <label class="form-check-label" for="booking_required">
                                            Booking Required
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Booking URL</label>
                                    <input type="url" class="form-control" name="booking_url" 
                                           placeholder="https://...">
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Max Attendees</label>
                                    <input type="number" class="form-control" name="max_attendees" min="1">
                                </div>
                                
                                <h6 class="mt-4 mb-3">⚙️ Options</h6>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="featured" id="featured">
                                        <label class="form-check-label" for="featured">
                                            Featured Event
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="is_published" id="is_published">
                                        <label class="form-check-label" for="is_published">
                                            Publish Immediately
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <hr>
                        
                        <!-- Related Links Section -->
                        <h5 class="mb-3">🔗 Related Links</h5>
                        <div id="links-container">
                            <div class="row mb-2 link-row">
                                <div class="col-md-4">
                                    <input type="text" class="form-control" name="link_titles" placeholder="Link Title">
                                </div>
                                <div class="col-md-6">
                                    <input type="url" class="form-control" name="link_urls" placeholder="https://...">
                                </div>
                                <div class="col-md-2">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="link_new_tabs" value="0" checked>
                                        <label class="form-check-label">New Tab</label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <button type="button" class="btn btn-sm btn-outline-primary" onclick="addLinkRow()">
                            <i class="fas fa-plus me-1"></i>Add Another Link
                        </button>
                        
                        <hr>
                        
                        <!-- Downloads Section -->
                        <h5 class="mb-3">📁 Related Downloads</h5>
                        <div id="downloads-container">
                            <div class="row mb-2 download-row">
                                <div class="col-md-4">
                                    <input type="text" class="form-control" name="download_titles" placeholder="Download Title">
                                </div>
                                <div class="col-md-4">
                                    <input type="text" class="form-control" name="download_descriptions" placeholder="Description (optional)">
                                </div>
                                <div class="col-md-4">
                                    <input type="file" class="form-control" name="download_files">
                                </div>
                            </div>
                        </div>
                        <button type="button" class="btn btn-sm btn-outline-primary" onclick="addDownloadRow()">
                            <i class="fas fa-plus me-1"></i>Add Another Download
                        </button>
                        
                        <hr>
                        <div class="d-flex justify-content-between">
                            <a href="/events" class="btn btn-secondary">Cancel</a>
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Create Event
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function addLinkRow() {
                const container = document.getElementById('links-container');
                const linkCount = container.querySelectorAll('.link-row').length;
                const newRow = document.createElement('div');
                newRow.className = 'row mb-2 link-row';
                newRow.innerHTML = `
                    <div class="col-md-4">
                        <input type="text" class="form-control" name="link_titles" placeholder="Link Title">
                    </div>
                    <div class="col-md-6">
                        <input type="url" class="form-control" name="link_urls" placeholder="https://...">
                    </div>
                    <div class="col-md-2">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" name="link_new_tabs" value="${linkCount}" checked>
                            <label class="form-check-label">New Tab</label>
                        </div>
                    </div>
                `;
                container.appendChild(newRow);
            }
            
            function addDownloadRow() {
                const container = document.getElementById('downloads-container');
                const newRow = document.createElement('div');
                newRow.className = 'row mb-2 download-row';
                newRow.innerHTML = `
                    <div class="col-md-4">
                        <input type="text" class="form-control" name="download_titles" placeholder="Download Title">
                    </div>
                    <div class="col-md-4">
                        <input type="text" class="form-control" name="download_descriptions" placeholder="Description (optional)">
                    </div>
                    <div class="col-md-4">
                        <input type="file" class="form-control" name="download_files">
                    </div>
                `;
                container.appendChild(newRow);
            }
        </script>
    </body>
    </html>
    ''', categories=categories)

@app.route('/events/categories')
@login_required
def event_categories():
    categories = EventCategory.query.all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Event Categories - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .category-card { border: none; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); transition: transform 0.2s; }
            .category-card:hover { transform: translateY(-2px); }
            .category-icon { width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px; }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link active">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/meetings" class="nav-link">
                    <i class="fas fa-handshake me-2"></i>Meetings
                </a>
                <a href="/homepage" class="nav-link">
                    <i class="fas fa-home me-2"></i>Homepage
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1><i class="fas fa-list-alt me-2"></i>Event Categories</h1>
                <div>
                    <a href="/events" class="btn btn-secondary me-2">
                        <i class="fas fa-arrow-left me-2"></i>Back to Events
                    </a>
                    <a href="/events/categories/add" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Add Category
                    </a>
                </div>
            </div>
            
            <div class="row">
                {% for category in categories %}
                <div class="col-md-4 mb-4">
                    <div class="card category-card">
                        <div class="card-body">
                            <div class="d-flex align-items-center mb-3">
                                <div class="category-icon me-3" style="background-color: {{ category.color }};">
                                    <i class="{{ category.icon }}"></i>
                                </div>
                                <div>
                                    <h5 class="card-title mb-1">{{ category.name }}</h5>
                                    <small class="text-muted">{{ category.description }}</small>
                                </div>
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="badge bg-primary">{{ category.events|length }} events</span>
                                <div class="btn-group btn-group-sm">
                                    <a href="/events/categories/edit/{{ category.id }}" class="btn btn-outline-primary">
                                        <i class="fas fa-edit"></i>
                                    </a>
                                    <button class="btn btn-outline-danger">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', categories=categories)

# File upload route
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Event Management Routes
@app.route('/events/view/<int:event_id>')
@login_required
def view_event(event_id):
    event = Event.query.get_or_404(event_id)
    category = EventCategory.query.get(event.category_id) if event.category_id else None
    
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{event.title} - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh;">
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-8 mx-auto">
                    <div class="card shadow-lg">
                        <div class="card-header bg-primary text-white">
                            <h2><i class="fas fa-calendar-alt me-2"></i>{event.title}</h2>
                            <a href="/events" class="btn btn-light btn-sm">
                                <i class="fas fa-arrow-left me-1"></i>Back to Events
                            </a>
                        </div>
                        <div class="card-body">
                            {f'<img src="/uploads/events/{event.image_filename}" class="img-fluid mb-3" alt="{event.title}">' if event.image_filename else ''}
                            <p><strong>Category:</strong> {category.name if category else 'None'}</p>
                            <p><strong>Date:</strong> {event.start_date.strftime('%d/%m/%Y %H:%M') if event.start_date else 'TBD'}</p>
                            {f'<p><strong>Location:</strong> {event.location_name}</p>' if event.location_name else ''}
                            <div class="mt-3">
                                <h5>Description</h5>
                                <p>{event.description or 'No description available.'}</p>
                            </div>
                            <div class="mt-3">
                                <a href="/events/edit/{event.id}" class="btn btn-warning">
                                    <i class="fas fa-edit me-1"></i>Edit Event
                                </a>
                                <a href="/events" class="btn btn-secondary">
                                    <i class="fas fa-list me-1"></i>All Events
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/events/edit/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    categories = EventCategory.query.filter_by(is_active=True).all()
    
    # Get current category assignments
    current_category_ids = [assignment.category_id for assignment in event.category_assignments]
    
    if request.method == 'POST':
        # Update event with form data
        event.title = request.form.get('title')
        event.short_description = request.form.get('short_description')
        event.description = request.form.get('description')
        
        # Handle dates
        start_date = request.form.get('start_date')
        if start_date:
            event.start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
        
        end_date = request.form.get('end_date')
        if end_date:
            event.end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
        
        event.all_day = bool(request.form.get('all_day'))
        event.location_name = request.form.get('location_name')
        event.location_address = request.form.get('location_address')
        event.location_url = request.form.get('location_url')
        event.contact_name = request.form.get('contact_name')
        event.contact_email = request.form.get('contact_email')
        event.contact_phone = request.form.get('contact_phone')
        event.booking_required = bool(request.form.get('booking_required'))
        event.booking_url = request.form.get('booking_url')
        event.max_attendees = int(request.form.get('max_attendees')) if request.form.get('max_attendees') else None
        event.is_free = bool(request.form.get('is_free'))
        event.price = request.form.get('price')
        event.featured = bool(request.form.get('featured'))
        event.status = request.form.get('status', 'Draft')
        event.is_published = bool(request.form.get('is_published'))
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = save_uploaded_file(file, 'events')
                event.image_filename = filename
        
        # Handle multiple category assignments
        # Clear existing assignments
        EventCategoryAssignment.query.filter_by(event_id=event.id).delete()
        
        selected_categories = request.form.getlist('categories')
        for category_id in selected_categories:
            if category_id:
                assignment = EventCategoryAssignment(
                    event_id=event.id,
                    category_id=int(category_id)
                )
                db.session.add(assignment)
        
        # Handle related links
        link_titles = request.form.getlist('link_titles')
        link_urls = request.form.getlist('link_urls')
        link_new_tabs = request.form.getlist('link_new_tabs')
        
        # Check if any new links are provided
        if any(title.strip() for title in link_titles) and any(url.strip() for url in link_urls):
            # Clear existing links only if new ones are provided
            EventLink.query.filter_by(event_id=event.id).delete()
        
        for i, title in enumerate(link_titles):
            if title.strip() and i < len(link_urls) and link_urls[i].strip():
                link = EventLink(
                    event_id=event.id,
                    title=title.strip(),
                    url=link_urls[i].strip(),
                    new_tab=str(i) in link_new_tabs,
                    sort_order=i
                )
                db.session.add(link)
        
        # Handle downloads
        download_files = request.files.getlist('download_files')
        download_titles = request.form.getlist('download_titles')
        download_descriptions = request.form.getlist('download_descriptions')
        
        # Only clear existing downloads if new files are being uploaded
        if any(file and file.filename for file in download_files):
            # Clear existing downloads only if new ones are provided
            EventDownload.query.filter_by(event_id=event.id).delete()
        
        for i, file in enumerate(download_files):
            if file and file.filename:
                filename = save_uploaded_file(file, 'events/downloads', 'download')
                if filename:
                    download_item = EventDownload(
                        event_id=event.id,
                        filename=filename,
                        title=download_titles[i] if i < len(download_titles) else file.filename,
                        description=download_descriptions[i] if i < len(download_descriptions) else '',
                        sort_order=i
                    )
                    db.session.add(download_item)
        
        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('events_list'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Event - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link active">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/meetings" class="nav-link">
                    <i class="fas fa-handshake me-2"></i>Meetings
                </a>
                <a href="/homepage" class="nav-link">
                    <i class="fas fa-home me-2"></i>Homepage
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📅 Edit Event: {{ event.title }}</h1>
                <a href="/events" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Events
                </a>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Event Title *</label>
                                    <input type="text" class="form-control" name="title" value="{{ event.title }}" required>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Short Description</label>
                                    <textarea class="form-control" name="short_description" rows="2" 
                                              placeholder="Brief summary for event previews...">{{ event.short_description or '' }}</textarea>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Description</label>
                                    <textarea class="form-control" name="description" rows="4" 
                                              placeholder="Describe the event...">{{ event.description or '' }}</textarea>
                                </div>
                                
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Start Date & Time *</label>
                                            <input type="datetime-local" class="form-control" name="start_date" 
                                                   value="{{ event.start_date.strftime('%Y-%m-%dT%H:%M') if event.start_date else '' }}" required>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">End Date & Time</label>
                                            <input type="datetime-local" class="form-control" name="end_date"
                                                   value="{{ event.end_date.strftime('%Y-%m-%dT%H:%M') if event.end_date else '' }}">
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="all_day" id="all_day" {{ 'checked' if event.all_day else '' }}>
                                        <label class="form-check-label" for="all_day">
                                            All Day Event
                                        </label>
                                    </div>
                                </div>
                                
                                <h5 class="mt-4 mb-3">📍 Location Details</h5>
                                <div class="row">
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Location Name</label>
                                            <input type="text" class="form-control" name="location_name" 
                                                   value="{{ event.location_name or '' }}" placeholder="e.g., Kesgrave Community Centre">
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="mb-3">
                                            <label class="form-label">Google Maps URL</label>
                                            <input type="url" class="form-control" name="location_url" 
                                                   value="{{ event.location_url or '' }}" placeholder="https://maps.google.com/...">
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Location Address</label>
                                    <textarea class="form-control" name="location_address" rows="2" 
                                              placeholder="Full address...">{{ event.location_address or '' }}</textarea>
                                </div>
                                
                                <h5 class="mt-4 mb-3">📞 Contact Information</h5>
                                <div class="row">
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Contact Name</label>
                                            <input type="text" class="form-control" name="contact_name" value="{{ event.contact_name or '' }}">
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Contact Email</label>
                                            <input type="email" class="form-control" name="contact_email" value="{{ event.contact_email or '' }}">
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="mb-3">
                                            <label class="form-label">Contact Phone</label>
                                            <input type="tel" class="form-control" name="contact_phone" value="{{ event.contact_phone or '' }}">
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Categories</label>
                                    <div class="border rounded p-3" style="max-height: 200px; overflow-y: auto;">
                                        {% for category in categories %}
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" name="categories" 
                                                   value="{{ category.id }}" id="cat_{{ category.id }}"
                                                   {{ 'checked' if category.id in current_category_ids else '' }}>
                                            <label class="form-check-label" for="cat_{{ category.id }}">
                                                {{ category.name }}
                                            </label>
                                        </div>
                                        {% endfor %}
                                    </div>
                                    <small class="text-muted">Select one or more categories</small>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Status</label>
                                    <select class="form-select" name="status">
                                        <option value="Draft" {{ 'selected' if event.status == 'Draft' else '' }}>Draft</option>
                                        <option value="Published" {{ 'selected' if event.status == 'Published' else '' }}>Published</option>
                                        <option value="Cancelled" {{ 'selected' if event.status == 'Cancelled' else '' }}>Cancelled</option>
                                    </select>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Event Image</label>
                                    <input type="file" class="form-control" name="image" accept="image/*">
                                    {% if event.image_filename %}
                                    <small class="text-muted">Current: {{ event.image_filename }}</small>
                                    {% endif %}
                                </div>
                                
                                <h6 class="mt-4 mb-3">🎫 Booking & Pricing</h6>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="is_free" id="is_free" {{ 'checked' if event.is_free else '' }}>
                                        <label class="form-check-label" for="is_free">
                                            Free Event
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Price Details</label>
                                    <input type="text" class="form-control" name="price" value="{{ event.price or '' }}"
                                           placeholder="e.g., £5 adults, £3 children">
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="booking_required" id="booking_required" {{ 'checked' if event.booking_required else '' }}>
                                        <label class="form-check-label" for="booking_required">
                                            Booking Required
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Booking URL</label>
                                    <input type="url" class="form-control" name="booking_url" value="{{ event.booking_url or '' }}"
                                           placeholder="https://...">
                                </div>
                                
                                <div class="mb-3">
                                    <label class="form-label">Max Attendees</label>
                                    <input type="number" class="form-control" name="max_attendees" value="{{ event.max_attendees or '' }}" min="1">
                                </div>
                                
                                <h6 class="mt-4 mb-3">⚙️ Options</h6>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="featured" id="featured" {{ 'checked' if event.featured else '' }}>
                                        <label class="form-check-label" for="featured">
                                            Featured Event
                                        </label>
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="is_published" id="is_published" {{ 'checked' if event.is_published else '' }}>
                                        <label class="form-check-label" for="is_published">
                                            Published
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <hr>
                        
                        <!-- Related Links Section -->
                        <h5 class="mb-3">🔗 Related Links</h5>
                        <div id="links-container">
                            {% for link in event.related_links %}
                            <div class="row mb-2 link-row">
                                <div class="col-md-4">
                                    <input type="text" class="form-control" name="link_titles" value="{{ link.title }}" placeholder="Link Title">
                                </div>
                                <div class="col-md-6">
                                    <input type="url" class="form-control" name="link_urls" value="{{ link.url }}" placeholder="https://...">
                                </div>
                                <div class="col-md-2">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="link_new_tabs" value="{{ loop.index0 }}" {{ 'checked' if link.new_tab else '' }}>
                                        <label class="form-check-label">New Tab</label>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                            <div class="row mb-2 link-row">
                                <div class="col-md-4">
                                    <input type="text" class="form-control" name="link_titles" placeholder="Link Title">
                                </div>
                                <div class="col-md-6">
                                    <input type="url" class="form-control" name="link_urls" placeholder="https://...">
                                </div>
                                <div class="col-md-2">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" name="link_new_tabs" value="0">
                                        <label class="form-check-label">New Tab</label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <button type="button" class="btn btn-sm btn-outline-primary" onclick="addLinkRow()">
                            <i class="fas fa-plus me-1"></i>Add Another Link
                        </button>
                        
                        <hr>
                        
                        <!-- Downloads Section -->
                        <h5 class="mb-3">📁 Related Downloads</h5>
                        <div id="downloads-container">
                            {% for download in event.downloads %}
                            <div class="row mb-2 download-row">
                                <div class="col-md-4">
                                    <input type="text" class="form-control" name="download_titles" value="{{ download.title }}" placeholder="Download Title">
                                </div>
                                <div class="col-md-6">
                                    <input type="text" class="form-control" name="download_descriptions" value="{{ download.description or '' }}" placeholder="Description (optional)">
                                </div>
                                <div class="col-md-2">
                                    <small class="text-muted">{{ download.filename }}</small>
                                </div>
                            </div>
                            {% endfor %}
                            <div class="row mb-2 download-row">
                                <div class="col-md-4">
                                    <input type="text" class="form-control" name="download_titles" placeholder="Download Title">
                                </div>
                                <div class="col-md-4">
                                    <input type="text" class="form-control" name="download_descriptions" placeholder="Description (optional)">
                                </div>
                                <div class="col-md-4">
                                    <input type="file" class="form-control" name="download_files">
                                </div>
                            </div>
                        </div>
                        <button type="button" class="btn btn-sm btn-outline-primary" onclick="addDownloadRow()">
                            <i class="fas fa-plus me-1"></i>Add Another Download
                        </button>
                        
                        <hr>
                        <div class="d-flex justify-content-between">
                            <a href="/events" class="btn btn-secondary">Cancel</a>
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-2"></i>Update Event
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function addLinkRow() {
                const container = document.getElementById('links-container');
                const linkCount = container.querySelectorAll('.link-row').length;
                const newRow = document.createElement('div');
                newRow.className = 'row mb-2 link-row';
                newRow.innerHTML = `
                    <div class="col-md-4">
                        <input type="text" class="form-control" name="link_titles" placeholder="Link Title">
                    </div>
                    <div class="col-md-6">
                        <input type="url" class="form-control" name="link_urls" placeholder="https://...">
                    </div>
                    <div class="col-md-2">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" name="link_new_tabs" value="${linkCount}">
                            <label class="form-check-label">New Tab</label>
                        </div>
                    </div>
                `;
                container.appendChild(newRow);
            }
            
            function addDownloadRow() {
                const container = document.getElementById('downloads-container');
                const newRow = document.createElement('div');
                newRow.className = 'row mb-2 download-row';
                newRow.innerHTML = `
                    <div class="col-md-4">
                        <input type="text" class="form-control" name="download_titles" placeholder="Download Title">
                    </div>
                    <div class="col-md-4">
                        <input type="text" class="form-control" name="download_descriptions" placeholder="Description (optional)">
                    </div>
                    <div class="col-md-4">
                        <input type="file" class="form-control" name="download_files">
                    </div>
                `;
                container.appendChild(newRow);
            }
        </script>
    </body>
    </html>
    ''', event=event, categories=categories, current_category_ids=current_category_ids)

@app.route('/events/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Delete image file if exists
    if event.image_filename:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'events', event.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('events_list'))

@app.route('/events/categories/add', methods=['GET', 'POST'])
@login_required
def add_event_category():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        icon = request.form.get('icon', 'fas fa-calendar')
        color = request.form.get('color', '#007bff')
        
        category = EventCategory(
            name=name,
            description=description,
            icon=icon,
            color=color
        )
        
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully!', 'success')
        return redirect(url_for('event_categories'))
    
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Event Category - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh;">
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-6 mx-auto">
                    <div class="card shadow-lg">
                        <div class="card-header bg-success text-white">
                            <h2><i class="fas fa-plus me-2"></i>Add Event Category</h2>
                            <a href="/events/categories" class="btn btn-light btn-sm">
                                <i class="fas fa-arrow-left me-1"></i>Back to Categories
                            </a>
                        </div>
                        <div class="card-body">
                            <form method="POST">
                                <div class="mb-3">
                                    <label class="form-label">Category Name</label>
                                    <input type="text" class="form-control" name="name" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Description</label>
                                    <textarea class="form-control" name="description" rows="3"></textarea>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Icon (FontAwesome class)</label>
                                    <input type="text" class="form-control" name="icon" value="fas fa-calendar" placeholder="fas fa-calendar">
                                    <small class="text-muted">e.g., fas fa-music, fas fa-sports-ball, fas fa-graduation-cap</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Color</label>
                                    <input type="color" class="form-control" name="color" value="#007bff">
                                </div>
                                <button type="submit" class="btn btn-success">
                                    <i class="fas fa-save me-2"></i>Create Category
                                </button>
                                <a href="/events/categories" class="btn btn-secondary ms-2">
                                    <i class="fas fa-times me-2"></i>Cancel
                                </a>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/events/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_event_category(category_id):
    category = EventCategory.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        category.icon = request.form.get('icon')
        category.color = request.form.get('color')
        
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('event_categories'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Category - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link active">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/meetings" class="nav-link">
                    <i class="fas fa-handshake me-2"></i>Meetings
                </a>
                <a href="/homepage" class="nav-link">
                    <i class="fas fa-home me-2"></i>Homepage
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1><i class="fas fa-edit me-2"></i>Edit Category: {{ category.name }}</h1>
                <a href="/events/categories" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Categories
                </a>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <form method="POST">
                                <div class="mb-3">
                                    <label class="form-label">Category Name</label>
                                    <input type="text" class="form-control" name="name" value="{{ category.name }}" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Description</label>
                                    <textarea class="form-control" name="description" rows="3">{{ category.description or '' }}</textarea>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Icon (FontAwesome class)</label>
                                    <input type="text" class="form-control" name="icon" value="{{ category.icon or 'fas fa-calendar' }}">
                                    <small class="text-muted">e.g., fas fa-music, fas fa-sports-ball, fas fa-graduation-cap</small>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Color</label>
                                    <input type="color" class="form-control" name="color" value="{{ category.color or '#007bff' }}">
                                </div>
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-save me-2"></i>Update Category
                                </button>
                                <a href="/events/categories" class="btn btn-secondary ms-2">
                                    <i class="fas fa-times me-2"></i>Cancel
                                </a>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    ''', category=category)

# Homepage Settings Route
@app.route('/homepage', methods=['GET', 'POST'])
@login_required
def homepage_settings():
    if request.method == 'POST':
        # Handle form submission
        action = request.form.get('action')
        
        if action == 'save_logo':
            # Handle logo settings
            logo = HomepageLogo.query.first()
            if not logo:
                logo = HomepageLogo()
                db.session.add(logo)
            
            logo.logo_text = request.form.get('logo_text', '')
            
            # Handle logo image upload
            if 'logo_image' in request.files:
                file = request.files['logo_image']
                if file and file.filename and allowed_image_file(file.filename):
                    filename = save_uploaded_file(file, 'homepage/logo', 'image')
                    if filename:
                        logo.logo_image_filename = filename
            
            db.session.commit()
            flash('Logo settings saved successfully!', 'success')
        
        elif action == 'save_header_links':
            # Clear existing header links
            HomepageHeaderLink.query.delete()
            
            # Add new header links (max 5)
            for i in range(5):
                link_name = request.form.get(f'header_link_name_{i}')
                link_url = request.form.get(f'header_link_url_{i}')
                
                if link_name and link_url:
                    header_link = HomepageHeaderLink(
                        link_name=link_name,
                        url=link_url,
                        sort_order=i
                    )
                    db.session.add(header_link)
            
            db.session.commit()
            flash('Header links saved successfully!', 'success')
        
        elif action == 'save_footer':
            # Handle footer columns and links
            for col_num in range(1, 4):  # 3 columns
                column_title = request.form.get(f'footer_col_{col_num}_title')
                
                if column_title:
                    # Find or create column
                    column = HomepageFooterColumn.query.filter_by(column_number=col_num).first()
                    if not column:
                        column = HomepageFooterColumn(column_number=col_num)
                        db.session.add(column)
                    
                    column.column_title = column_title
                    
                    # Clear existing links for this column
                    HomepageFooterLink.query.filter_by(footer_column_id=column.id).delete()
                    
                    # Add new links (max 4 per column)
                    for i in range(4):
                        link_name = request.form.get(f'footer_col_{col_num}_link_name_{i}')
                        link_url = request.form.get(f'footer_col_{col_num}_link_url_{i}')
                        
                        if link_name and link_url:
                            footer_link = HomepageFooterLink(
                                footer_column_id=column.id,
                                link_name=link_name,
                                url=link_url,
                                sort_order=i
                            )
                            db.session.add(footer_link)
            
            db.session.commit()
            flash('Footer settings saved successfully!', 'success')
        
        elif action == 'save_slides':
            # FIXED: Update existing slides individually instead of deleting all
            for i in range(5):
                title = request.form.get(f'slide_title_{i}')
                introduction = request.form.get(f'slide_intro_{i}')
                button_name = request.form.get(f'slide_button_name_{i}')
                button_url = request.form.get(f'slide_button_url_{i}')
                open_method = request.form.get(f'slide_open_method_{i}', 'same_tab')
                is_featured = bool(request.form.get(f'slide_featured_{i}'))
                
                if title:
                    # Try to find existing slide by sort_order
                    existing_slide = HomepageSlide.query.filter_by(sort_order=i).first()
                    
                    if existing_slide:
                        # Update existing slide
                        existing_slide.title = title
                        existing_slide.introduction = introduction
                        existing_slide.button_name = button_name
                        existing_slide.button_url = button_url
                        existing_slide.open_method = open_method
                        existing_slide.is_featured = is_featured
                        existing_slide.is_active = True
                        slide = existing_slide
                    else:
                        # Create new slide
                        slide = HomepageSlide(
                            title=title,
                            introduction=introduction,
                            button_name=button_name,
                            button_url=button_url,
                            open_method=open_method,
                            is_featured=is_featured,
                            sort_order=i,
                            is_active=True
                        )
                        db.session.add(slide)
                    
                    # Handle slide image upload (only update if new image uploaded)
                    if f'slide_image_{i}' in request.files:
                        file = request.files[f'slide_image_{i}']
                        if file and file.filename and allowed_image_file(file.filename):
                            filename = save_uploaded_file(file, 'homepage/slides', 'image')
                            if filename:
                                slide.image_filename = filename
                else:
                    # If no title provided, deactivate the slide but don't delete it
                    existing_slide = HomepageSlide.query.filter_by(sort_order=i).first()
                    if existing_slide:
                        existing_slide.is_active = False
            
            db.session.commit()
            flash('Slider settings saved successfully!', 'success')
        
        elif action == 'save_quicklinks':
            # Clear existing quicklinks
            HomepageQuicklink.query.delete()
            
            # Add new quicklinks
            quicklink_count = int(request.form.get('quicklink_count', 0))
            for i in range(quicklink_count):
                title = request.form.get(f'quicklink_title_{i}')
                description = request.form.get(f'quicklink_description_{i}')
                button_name = request.form.get(f'quicklink_button_name_{i}')
                button_url = request.form.get(f'quicklink_button_url_{i}')
                open_method = request.form.get(f'quicklink_open_method_{i}', 'same_tab')
                
                if title:
                    quicklink = HomepageQuicklink(
                        title=title,
                        description=description,
                        button_name=button_name,
                        button_url=button_url,
                        open_method=open_method,
                        sort_order=i
                    )
                    db.session.add(quicklink)
            
            db.session.commit()
            flash('Quicklinks saved successfully!', 'success')
        
        return redirect(url_for('homepage_settings'))
    
    # Get existing data
    logo = HomepageLogo.query.first()
    header_links = HomepageHeaderLink.query.order_by(HomepageHeaderLink.sort_order).all()
    footer_columns = HomepageFooterColumn.query.order_by(HomepageFooterColumn.column_number).all()
    slides = HomepageSlide.query.order_by(HomepageSlide.sort_order).all()
    quicklinks = HomepageQuicklink.query.order_by(HomepageQuicklink.sort_order).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Homepage Settings - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .section-card {
                border: none;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
            .section-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px 10px 0 0;
            }
            .dynamic-form-group {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1rem;
                background-color: #f8f9fa;
            }
            .remove-btn {
                position: absolute;
                top: 10px;
                right: 10px;
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/meetings" class="nav-link">
                    <i class="fas fa-handshake me-2"></i>Meetings
                </a>
                <a href="/homepage" class="nav-link active">
                    <i class="fas fa-home me-2"></i>Homepage
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1><i class="fas fa-home me-2 text-primary"></i>Homepage Settings</h1>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <!-- Logo Settings -->
            <div class="card section-card">
                <div class="card-header section-header">
                    <h5 class="mb-0"><i class="fas fa-image me-2"></i>Logo Settings</h5>
                </div>
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        <input type="hidden" name="action" value="save_logo">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Logo Image</label>
                                    <input type="file" class="form-control" name="logo_image" accept="image/*">
                                    {% if logo and logo.logo_image_filename %}
                                    <small class="text-muted">Current: {{ logo.logo_image_filename }}</small>
                                    {% endif %}
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Logo Text</label>
                                    <input type="text" class="form-control" name="logo_text" value="{{ logo.logo_text if logo else '' }}" placeholder="Enter logo text">
                                </div>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save me-2"></i>Save Logo Settings
                        </button>
                    </form>
                </div>
            </div>
            
            <!-- Header Links -->
            <div class="card section-card">
                <div class="card-header section-header">
                    <h5 class="mb-0"><i class="fas fa-link me-2"></i>Header Bar Links (Max 5)</h5>
                </div>
                <div class="card-body">
                    <form method="POST">
                        <input type="hidden" name="action" value="save_header_links">
                        {% for i in range(5) %}
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <label class="form-label">Link {{ i + 1 }} Name</label>
                                <input type="text" class="form-control" name="header_link_name_{{ i }}" 
                                       value="{{ header_links[i].link_name if header_links and i < header_links|length else '' }}" 
                                       placeholder="Link name">
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Link {{ i + 1 }} URL</label>
                                <input type="url" class="form-control" name="header_link_url_{{ i }}" 
                                       value="{{ header_links[i].url if header_links and i < header_links|length else '' }}" 
                                       placeholder="https://example.com">
                            </div>
                        </div>
                        {% endfor %}
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save me-2"></i>Save Header Links
                        </button>
                    </form>
                </div>
            </div>
            
            <!-- Footer Columns -->
            <div class="card section-card">
                <div class="card-header section-header">
                    <h5 class="mb-0"><i class="fas fa-columns me-2"></i>Footer Bar Columns (3 Columns)</h5>
                </div>
                <div class="card-body">
                    <form method="POST">
                        <input type="hidden" name="action" value="save_footer">
                        {% for col_num in range(1, 4) %}
                        <div class="mb-4">
                            <h6 class="text-primary">Column {{ col_num }}</h6>
                            <div class="mb-3">
                                <label class="form-label">Column Title</label>
                                <input type="text" class="form-control" name="footer_col_{{ col_num }}_title" 
                                       value="{% for col in footer_columns %}{% if col.column_number == col_num %}{{ col.column_title }}{% endif %}{% endfor %}" 
                                       placeholder="Column title">
                            </div>
                            {% for i in range(4) %}
                            <div class="row mb-2">
                                <div class="col-md-6">
                                    <input type="text" class="form-control" name="footer_col_{{ col_num }}_link_name_{{ i }}" 
                                           value="{% for col in footer_columns %}{% if col.column_number == col_num %}{% for link in col.links %}{% if loop.index0 == i %}{{ link.link_name }}{% endif %}{% endfor %}{% endif %}{% endfor %}" 
                                           placeholder="Link {{ i + 1 }} name">
                                </div>
                                <div class="col-md-6">
                                    <input type="url" class="form-control" name="footer_col_{{ col_num }}_link_url_{{ i }}" 
                                           value="{% for col in footer_columns %}{% if col.column_number == col_num %}{% for link in col.links %}{% if loop.index0 == i %}{{ link.url }}{% endif %}{% endfor %}{% endif %}{% endfor %}" 
                                           placeholder="https://example.com">
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                        {% endfor %}
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save me-2"></i>Save Footer Settings
                        </button>
                    </form>
                </div>
            </div>
            
            <!-- Slider Section -->
            <div class="card section-card">
                <div class="card-header section-header">
                    <h5 class="mb-0"><i class="fas fa-images me-2"></i>Slider Section (Max 5 Slides)</h5>
                </div>
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data">
                        <input type="hidden" name="action" value="save_slides">
                        {% for i in range(5) %}
                        <div class="dynamic-form-group">
                            <h6 class="text-primary">Slide {{ i + 1 }}</h6>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Title</label>
                                        <input type="text" class="form-control" name="slide_title_{{ i }}" 
                                               value="{{ slides[i].title if slides and i < slides|length else '' }}" 
                                               placeholder="Slide title">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Image</label>
                                        <input type="file" class="form-control" name="slide_image_{{ i }}" accept="image/*">
                                        {% if slides and i < slides|length and slides[i].image_filename %}
                                        <small class="text-muted">Current: {{ slides[i].image_filename }}</small>
                                        {% endif %}
                                    </div>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Introduction</label>
                                <textarea class="form-control" name="slide_intro_{{ i }}" rows="2" 
                                          placeholder="Short introduction text">{{ slides[i].introduction if slides and i < slides|length else '' }}</textarea>
                            </div>
                            <div class="row">
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label class="form-label">Button Name</label>
                                        <input type="text" class="form-control" name="slide_button_name_{{ i }}" 
                                               value="{{ slides[i].button_name if slides and i < slides|length else '' }}" 
                                               placeholder="Button text">
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label class="form-label">Button URL</label>
                                        <input type="url" class="form-control" name="slide_button_url_{{ i }}" 
                                               value="{{ slides[i].button_url if slides and i < slides|length else '' }}" 
                                               placeholder="https://example.com">
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label class="form-label">Open Method</label>
                                        <select class="form-select" name="slide_open_method_{{ i }}">
                                            <option value="same_tab" {{ 'selected' if slides and i < slides|length and slides[i].open_method == 'same_tab' else '' }}>Same Tab</option>
                                            <option value="new_tab" {{ 'selected' if slides and i < slides|length and slides[i].open_method == 'new_tab' else '' }}>New Tab</option>
                                            <option value="new_window" {{ 'selected' if slides and i < slides|length and slides[i].open_method == 'new_window' else '' }}>New Window</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="slide_featured_{{ i }}" 
                                       {{ 'checked' if slides and i < slides|length and slides[i].is_featured else '' }}>
                                <label class="form-check-label">Featured Slide</label>
                            </div>
                        </div>
                        {% endfor %}
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save me-2"></i>Save Slider Settings
                        </button>
                    </form>
                </div>
            </div>
            
            <!-- Quicklinks Section -->
            <div class="card section-card">
                <div class="card-header section-header">
                    <h5 class="mb-0"><i class="fas fa-external-link-alt me-2"></i>Quicklink Section</h5>
                </div>
                <div class="card-body">
                    <form method="POST" id="quicklinksForm">
                        <input type="hidden" name="action" value="save_quicklinks">
                        <input type="hidden" name="quicklink_count" id="quicklinkCount" value="{{ quicklinks|length if quicklinks else 0 }}">
                        
                        <div id="quicklinksContainer">
                            {% for quicklink in quicklinks %}
                            <div class="dynamic-form-group" data-index="{{ loop.index0 }}">
                                <div class="position-relative">
                                    <button type="button" class="btn btn-sm btn-outline-danger remove-btn" onclick="removeQuicklink(this)">
                                        <i class="fas fa-times"></i>
                                    </button>
                                    <h6 class="text-primary">Quicklink {{ loop.index }}</h6>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label class="form-label">Title</label>
                                                <input type="text" class="form-control" name="quicklink_title_{{ loop.index0 }}" 
                                                       value="{{ quicklink.title }}" placeholder="Quicklink title">
                                            </div>
                                        </div>
                                        <div class="col-md-6">
                                            <div class="mb-3">
                                                <label class="form-label">Description</label>
                                                <textarea class="form-control" name="quicklink_description_{{ loop.index0 }}" rows="2" 
                                                          placeholder="Description">{{ quicklink.description }}</textarea>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="row">
                                        <div class="col-md-4">
                                            <div class="mb-3">
                                                <label class="form-label">Button Name</label>
                                                <input type="text" class="form-control" name="quicklink_button_name_{{ loop.index0 }}" 
                                                       value="{{ quicklink.button_name }}" placeholder="Button text">
                                            </div>
                                        </div>
                                        <div class="col-md-4">
                                            <div class="mb-3">
                                                <label class="form-label">Button URL</label>
                                                <input type="url" class="form-control" name="quicklink_button_url_{{ loop.index0 }}" 
                                                       value="{{ quicklink.button_url }}" placeholder="https://example.com">
                                            </div>
                                        </div>
                                        <div class="col-md-4">
                                            <div class="mb-3">
                                                <label class="form-label">Open Method</label>
                                                <select class="form-select" name="quicklink_open_method_{{ loop.index0 }}">
                                                    <option value="same_tab" {{ 'selected' if quicklink.open_method == 'same_tab' else '' }}>Same Tab</option>
                                                    <option value="new_tab" {{ 'selected' if quicklink.open_method == 'new_tab' else '' }}>New Tab</option>
                                                    <option value="new_window" {{ 'selected' if quicklink.open_method == 'new_window' else '' }}>New Window</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        </div>
                        
                        <div class="mb-3">
                            <button type="button" class="btn btn-outline-primary" onclick="addQuicklink()">
                                <i class="fas fa-plus me-2"></i>Add Quicklink
                            </button>
                        </div>
                        
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save me-2"></i>Save Quicklinks
                        </button>
                    </form>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            let quicklinkIndex = {{ quicklinks|length if quicklinks else 0 }};
            
            function addQuicklink() {
                const container = document.getElementById('quicklinksContainer');
                const quicklinkHtml = `
                    <div class="dynamic-form-group" data-index="${quicklinkIndex}">
                        <div class="position-relative">
                            <button type="button" class="btn btn-sm btn-outline-danger remove-btn" onclick="removeQuicklink(this)">
                                <i class="fas fa-times"></i>
                            </button>
                            <h6 class="text-primary">Quicklink ${quicklinkIndex + 1}</h6>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Title</label>
                                        <input type="text" class="form-control" name="quicklink_title_${quicklinkIndex}" placeholder="Quicklink title">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Description</label>
                                        <textarea class="form-control" name="quicklink_description_${quicklinkIndex}" rows="2" placeholder="Description"></textarea>
                                    </div>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label class="form-label">Button Name</label>
                                        <input type="text" class="form-control" name="quicklink_button_name_${quicklinkIndex}" placeholder="Button text">
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label class="form-label">Button URL</label>
                                        <input type="url" class="form-control" name="quicklink_button_url_${quicklinkIndex}" placeholder="https://example.com">
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="mb-3">
                                        <label class="form-label">Open Method</label>
                                        <select class="form-select" name="quicklink_open_method_${quicklinkIndex}">
                                            <option value="same_tab">Same Tab</option>
                                            <option value="new_tab">New Tab</option>
                                            <option value="new_window">New Window</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                container.insertAdjacentHTML('beforeend', quicklinkHtml);
                quicklinkIndex++;
                updateQuicklinkCount();
            }
            
            function removeQuicklink(button) {
                button.closest('.dynamic-form-group').remove();
                updateQuicklinkCount();
                updateQuicklinkNumbers();
            }
            
            function updateQuicklinkCount() {
                const count = document.querySelectorAll('#quicklinksContainer .dynamic-form-group').length;
                document.getElementById('quicklinkCount').value = count;
            }
            
            function updateQuicklinkNumbers() {
                const quicklinks = document.querySelectorAll('#quicklinksContainer .dynamic-form-group');
                quicklinks.forEach((quicklink, index) => {
                    const title = quicklink.querySelector('h6');
                    title.textContent = `Quicklink ${index + 1}`;
                });
            }
        </script>
    </body>
    </html>
    ''', logo=logo, header_links=header_links, footer_columns=footer_columns, slides=slides, quicklinks=quicklinks)

# Homepage Slides API Endpoint

# Event Detail API Endpoint - PROPERLY PLACED AFTER DATABASE MODELS
@app.route('/api/events/<int:event_id>', methods=['GET', 'OPTIONS'])
def get_event_details(event_id):
    """Get full details for a specific event including all related data"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        print(f"🔍 DEBUG: Fetching event details for event ID: {event_id}")
        
        # Get the main event data
        event = Event.query.get(event_id)
        if not event:
            print(f"❌ ERROR: Event {event_id} not found")
            error_response = make_response(jsonify({
                'error': 'Event not found',
                'message': f'No event found with ID {event_id}'
            }), 404)
            error_response.headers['Access-Control-Allow-Origin'] = '*'
            return error_response
        
        print(f"✅ DEBUG: Found event: {event.title}")
        
        # Get event categories
        categories = []
        try:
            category_assignments = EventCategoryAssignment.query.filter_by(event_id=event_id).all()
            print(f"🔍 DEBUG: Found {len(category_assignments)} category assignments")
            
            for assignment in category_assignments:
                category = EventCategory.query.get(assignment.category_id)
                if category:
                    categories.append({
                        'id': category.id,
                        'name': category.name,
                        'color': category.color,
                        'icon': category.icon
                    })
                    print(f"🔍 DEBUG: Added category: {category.name}")
        except Exception as e:
            print(f"❌ ERROR: Failed to fetch categories: {e}")
        
        # Get event links
        links = []
        try:
            event_links = EventLink.query.filter_by(event_id=event_id).all()
            print(f"🔍 DEBUG: Found {len(event_links)} event links")
            
            for link in event_links:
                links.append({
                    'id': link.id,
                    'title': link.title,
                    'url': link.url,
                    'open_method': 'new_tab' if link.new_tab else 'same_tab'
                })
        except Exception as e:
            print(f"❌ ERROR: Failed to fetch links: {e}")
        
        # Get event downloads
        downloads = []
        try:
            event_downloads = EventDownload.query.filter_by(event_id=event_id).all()
            print(f"🔍 DEBUG: Found {len(event_downloads)} event downloads")
            
            for download in event_downloads:
                downloads.append({
                    'id': download.id,
                    'title': download.title,
                    'file_url': f"http://127.0.0.1:8027/uploads/events/downloads/{download.filename}" if download.filename else None
                })
        except Exception as e:
            print(f"❌ ERROR: Failed to fetch downloads: {e}")
        
        # Get event gallery
        gallery = []
        try:
            event_gallery = EventGallery.query.filter_by(event_id=event_id).all()
            print(f"🔍 DEBUG: Found {len(event_gallery)} gallery images")
            
            for photo in event_gallery:
                gallery.append({
                    'id': photo.id,
                    'title': photo.title,
                    'description': photo.description,
                    'alt_text': photo.alt_text,
                    'image_url': f"http://127.0.0.1:8027/uploads/events/gallery/{photo.filename}" if photo.filename else None
                })
        except Exception as e:
            print(f"❌ ERROR: Failed to fetch gallery: {e}")
        
        # Build the complete event data
        event_data = {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'short_description': event.short_description,
            'start_date': event.start_date.isoformat() if event.start_date else None,
            'end_date': event.end_date.isoformat() if event.end_date else None,
            'all_day': event.all_day,
            'location_name': event.location_name,
            'location_address': event.location_address,
            'location_url': event.location_url,
            'contact_name': event.contact_name,
            'contact_email': event.contact_email,
            'contact_phone': event.contact_phone,
            'booking_required': event.booking_required,
            'booking_url': event.booking_url,
            'max_attendees': event.max_attendees,
            'is_free': event.is_free,
            'price': event.price,
            'featured': event.featured,
            'is_published': event.is_published,
            'featured_image': f"http://127.0.0.1:8027/uploads/events/{event.image_filename}" if event.image_filename else None,
            'categories': categories,
            'links': links,
            'downloads': downloads,
            'gallery': gallery,
            'created_at': event.created_at.isoformat() if event.created_at else None,
            'updated_at': event.updated_at.isoformat() if event.updated_at else None
        }
        
        print(f"✅ DEBUG: Event {event_id} details loaded successfully")
        print(f"🔍 DEBUG: Categories: {len(categories)}, Links: {len(links)}, Downloads: {len(downloads)}, Gallery: {len(gallery)}")
        
        response = make_response(jsonify(event_data))
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
        
    except Exception as e:
        print(f"❌ ERROR: Failed to fetch event {event_id} details: {e}")
        error_response = make_response(jsonify({
            'error': 'Failed to load event details',
            'message': str(e)
        }), 500)
        error_response.headers['Access-Control-Allow-Origin'] = '*'
        return error_response


@app.route('/api/homepage/slides', methods=['GET', 'OPTIONS'])
def get_homepage_slides():
    """Get slides from HomepageSlide table with direct CORS headers"""
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response
    
    try:
        # FIXED: Query the HomepageSlide table directly
        slides_query = HomepageSlide.query.filter_by(is_active=True).order_by(HomepageSlide.sort_order.asc()).limit(5)
        
        slides_data = []
        for slide in slides_query:
            # Construct complete image URL with subfolder path
            featured_image_url = None
            if slide.image_filename:
                featured_image_url = f"http://127.0.0.1:8027/uploads/homepage/slides/{slide.image_filename}"
            
            slide_data = {
                'id': slide.id,
                'title': slide.title,
                'description': slide.introduction,
                'featured_image': featured_image_url,
                'action_button_text': slide.button_name,
                'action_button_url': slide.button_url,
                'is_featured': slide.is_featured
            }
            slides_data.append(slide_data)
        
        response = make_response(jsonify(slides_data))
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response
        
    except Exception as e:
        print(f"Error fetching homepage slides: {e}")
        response = make_response(jsonify([]))
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response


# Enhanced Homepage Events API Endpoint - COMPLETE VERSION
@app.route('/api/homepage/events', methods=['GET', 'OPTIONS'])
def get_homepage_events():
    """Get ALL events with complete data including featured field - ENHANCED VERSION"""
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response
    
    try:
        from datetime import datetime, date
        
        print(f"🔍 DEBUG: Starting COMPLETE events API with featured field")
        print(f"🔍 DEBUG: Today's date is: {date.today()}")
        
        # Get ALL published events (past and future) for navigation
        try:
            events_query = Event.query.filter(
                Event.is_published == True
            ).order_by(Event.start_date.asc())
            
            events_list = events_query.all()
            print(f"🔍 DEBUG: Found {len(events_list)} total published events")
            
        except Exception as e:
            print(f"🔍 DEBUG: Error with events query: {e}")
            events_list = []
        
        events_data = []
        for event in events_list:
            print(f"🔍 DEBUG: Processing event: {event.title}")
            
            # Construct image URL if image exists
            featured_image_url = None
            if event.image_filename:
                featured_image_url = f"http://127.0.0.1:8027/uploads/events/{event.image_filename}"
            
            # Get categories for this event with colors
            categories = []
            try:
                # Query event categories with colors
                category_assignments = db.session.query(
                    EventCategoryAssignment, EventCategory
                ).join(
                    EventCategory, EventCategoryAssignment.category_id == EventCategory.id
                ).filter(
                    EventCategoryAssignment.event_id == event.id
                ).all()
                
                for assignment, category in category_assignments:
                    category_data = {
                        'id': category.id,
                        'name': category.name,
                        'color': category.color,
                        'icon': category.icon if hasattr(category, 'icon') else 'fas fa-calendar'
                    }
                    categories.append(category_data)
                    print(f"🔍 DEBUG: Added category: {category.name} ({category.color})")
                    
            except Exception as e:
                print(f"🔍 DEBUG: Error fetching categories for event {event.id}: {e}")
            
            # Use short_description if available, otherwise use main description (truncated)
            description = event.short_description
            if not description or description.strip() == "":
                description = event.description
                if description and len(description) > 150:
                    description = description[:150] + "..."
            
            # Build complete event data with ALL fields needed by EventsPage
            event_data = {
                'id': event.id,
                'title': event.title,
                'description': description,
                'short_description': event.short_description,
                'date': event.start_date.isoformat() if event.start_date else None,
                'time': event.start_date.strftime('%H:%M') if event.start_date else None,
                'location': event.location_name,
                'location_address': event.location_address,
                'location_url': event.location_url,
                'featured_image': featured_image_url,
                'categories': categories,
                'url': f'/ktc-events/{event.id}',
                # NEW: Additional fields for EventsPage
                'featured': event.featured,  # ✅ FEATURED FIELD ADDED
                'booking_url': event.booking_url,
                'booking_required': event.booking_required,
                'price': event.price,
                'is_free': event.is_free,
                'contact_name': event.contact_name,
                'contact_email': event.contact_email,
                'contact_phone': event.contact_phone,
                'max_attendees': event.max_attendees,
                'all_day': event.all_day,
                'start_date': event.start_date.isoformat() if event.start_date else None,
                'end_date': event.end_date.isoformat() if event.end_date else None
            }
            events_data.append(event_data)
        
        print(f"🔍 DEBUG: Final events data: {len(events_data)} events with featured field")
        for event in events_data:
            print(f"🔍 DEBUG: Event '{event['title']}' - Featured: {event['featured']}, Categories: {len(event['categories'])}")
        
        response = make_response(jsonify(events_data))
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response
        
    except Exception as e:
        print(f"Error fetching homepage events: {e}")
        response = make_response(jsonify([]))
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response


# Homepage Meetings API Endpoint
@app.route('/api/homepage/meetings', methods=['GET', 'OPTIONS'])
def get_homepage_meetings():
    """Get upcoming meetings from Meeting table with direct CORS headers"""
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response
    
    try:
        from datetime import datetime, date
        
        print(f"🔍 DEBUG: Starting meetings API debug")
        print(f"🔍 DEBUG: Today's date is: {date.today()}")
        
        # Debug: Check if MeetingType table exists and has data
        try:
            meeting_types = MeetingType.query.all()
            print(f"🔍 DEBUG: Found {len(meeting_types)} meeting types")
            for mt in meeting_types:
                print(f"🔍 DEBUG: Meeting type: ID={mt.id}, Name={mt.name}")
        except Exception as e:
            print(f"🔍 DEBUG: Error querying MeetingType: {e}")
            meeting_types = []
        
        # Debug: Check Meeting table
        try:
            total_meetings = Meeting.query.count()
            print(f"🔍 DEBUG: Total meetings in database: {total_meetings}")
            
            # Show some sample meetings
            sample_meetings = Meeting.query.limit(3).all()
            for meeting in sample_meetings:
                print(f"🔍 DEBUG: Sample meeting: ID={meeting.id}, Date={meeting.meeting_date}, Time={meeting.meeting_time}, Type_ID={meeting.meeting_type_id}")
        except Exception as e:
            print(f"🔍 DEBUG: Error querying Meeting table: {e}")
        
        meetings_data = []
        today = date.today()
        print(f"🔍 DEBUG: Looking for meetings with meeting_date >= {today}")
        
        for meeting_type in meeting_types:
            # Get the next meeting for this type
            try:
                next_meeting = Meeting.query.filter(
                    Meeting.meeting_type_id == meeting_type.id,
                    Meeting.meeting_date >= today
                ).order_by(Meeting.meeting_date.asc()).first()
                
                print(f"🔍 DEBUG: Next meeting for type {meeting_type.name}: {next_meeting.title if next_meeting else 'None'}")
                
                if next_meeting:
                    meeting_data = {
                        'id': next_meeting.id,
                        'type': meeting_type.name,
                        'date': next_meeting.meeting_date.isoformat() if next_meeting.meeting_date else None,
                        'time': next_meeting.meeting_time.strftime('%H:%M') if next_meeting.meeting_time else None,
                        'location': next_meeting.location
                    }
                    meetings_data.append(meeting_data)
            except Exception as e:
                print(f"🔍 DEBUG: Error querying meetings for type {meeting_type.name}: {e}")
        
        print(f"🔍 DEBUG: Final meetings data: {meetings_data}")
        
        response = make_response(jsonify(meetings_data))
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response
    
    except Exception as e:
        print(f"Error fetching homepage meetings: {e}")
        response = make_response(jsonify([]))
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response


# Homepage Quick Links API Endpoint
@app.route('/api/homepage/quick-links', methods=['GET', 'OPTIONS'])
def get_homepage_quick_links():
    """Get quick links from HomepageQuicklink table with direct CORS headers"""
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response
    
    try:
        # FIXED: Query the HomepageQuicklink table directly
        quick_links_query = HomepageQuicklink.query.filter_by(is_active=True).order_by(HomepageQuicklink.sort_order.asc()).limit(8)
        
        quick_links_data = []
        for quick_link in quick_links_query:
            quick_link_data = {
                'id': quick_link.id,
                'title': quick_link.title,
                'description': quick_link.description,
                'url': quick_link.button_url,
                'button_text': quick_link.button_name
            }
            quick_links_data.append(quick_link_data)
        
        response = make_response(jsonify(quick_links_data))
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response
        
    except Exception as e:
        print(f"Error fetching homepage quick links: {e}")
        response = make_response(jsonify([]))
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,OPTIONS')
        return response

@app.route('/api/event-categories', methods=['GET', 'OPTIONS'])
def get_event_categories():
    """Get all active event categories for filtering"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        print("🔍 DEBUG: Fetching event categories")
        
        # Get all active event categories
        categories = EventCategory.query.filter_by(is_active=True).order_by(EventCategory.name).all()
        
        categories_data = []
        for category in categories:
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'color': category.color,
                'icon': category.icon,
                'is_active': category.is_active
            })
        
        print(f"✅ DEBUG: Found {len(categories_data)} active categories")
        
        response = make_response(jsonify(categories_data))
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
        
    except Exception as e:
        print(f"❌ ERROR: Failed to fetch event categories: {e}")
        error_response = make_response(jsonify({
            'error': 'Failed to load event categories',
            'message': str(e)
        }), 500)
        error_response.headers['Access-Control-Allow-Origin'] = '*'
        return error_response


# Additional helper endpoint for homepage statistics (optional)
@app.route('/api/homepage/stats', methods=['GET'])
def get_homepage_stats():
    """
    Get basic statistics for homepage display
    Returns counts of events, meetings, content pages, etc.
    """
    try:
        from datetime import datetime, date
        
        today = date.today()
        
        stats = {
            'total_events': Event.query.count(),
            'upcoming_events': Event.query.filter(Event.date >= today).count(),
            'total_meetings': Meeting.query.count(),
            'upcoming_meetings': Meeting.query.filter(Meeting.date >= today).count(),
            'total_content_pages': ContentPage.query.count(),
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify(stats)
    
    except Exception as e:
        print(f"Error fetching homepage stats: {e}")
        return jsonify({
            'total_events': 0,
            'upcoming_events': 0,
            'total_meetings': 0,
            'upcoming_meetings': 0,
            'total_content_pages': 0,
            'last_updated': datetime.now().isoformat()
        })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create sample data if none exists
        if Tag.query.count() == 0:
            sample_tags = [
                {'name': 'East Ward', 'color': '#e74c3c', 'description': 'East Ward representative'},
                {'name': 'West Ward', 'color': '#3498db', 'description': 'West Ward representative'},
                {'name': 'North Ward', 'color': '#27ae60', 'description': 'North Ward representative'},
                {'name': 'South Ward', 'color': '#f39c12', 'description': 'South Ward representative'},
                {'name': 'Planning Committee', 'color': '#9b59b6', 'description': 'Planning Committee member'},
                {'name': 'Finance Committee', 'color': '#34495e', 'description': 'Finance Committee member'},
                {'name': 'Mayor', 'color': '#e67e22', 'description': 'Mayor of Kesgrave'},
                {'name': 'Deputy Mayor', 'color': '#1abc9c', 'description': 'Deputy Mayor'}
            ]
            
            for tag_data in sample_tags:
                tag = Tag(**tag_data)
                db.session.add(tag)
            
            db.session.commit()
        
        # Create sample councillors if none exist
        if Councillor.query.count() == 0:
            sample_councillors = [
                {
                    'name': 'John Smith',
                    'title': 'Mayor',
                    'intro': 'Dedicated to serving the Kesgrave community with transparency and commitment.',
                    'bio': 'John has been serving the Kesgrave community for over 15 years. He is passionate about local development and environmental sustainability.',
                    'email': 'john.smith@kesgrave-tc.gov.uk',
                    'phone': '01473 625180',
                    'address': 'Kesgrave Town Hall, Main Road, Kesgrave, IP5 2BY',
                    'qualifications': 'BA Politics, Local Government Certificate',
                    'is_published': True
                },
                {
                    'name': 'Sarah Johnson',
                    'title': 'Deputy Mayor',
                    'intro': 'Focused on community services and youth development programs.',
                    'bio': 'Sarah brings extensive experience in community development and has been instrumental in establishing youth programs in Kesgrave.',
                    'email': 'sarah.johnson@kesgrave-tc.gov.uk',
                    'phone': '01473 625181',
                    'address': 'Kesgrave Town Hall, Main Road, Kesgrave, IP5 2BY',
                    'qualifications': 'MSc Community Development, Youth Work Diploma',
                    'is_published': True
                },
                {
                    'name': 'Michael Brown',
                    'title': 'Councillor',
                    'intro': 'Specializing in planning and development with focus on sustainable growth.',
                    'bio': 'Michael has a background in urban planning and is committed to ensuring sustainable development in Kesgrave.',
                    'email': 'michael.brown@kesgrave-tc.gov.uk',
                    'phone': '01473 625182',
                    'address': 'Kesgrave Town Hall, Main Road, Kesgrave, IP5 2BY',
                    'qualifications': 'BSc Urban Planning, RTPI Member',
                    'is_published': True
                },
                {
                    'name': 'Emma Wilson',
                    'title': 'Councillor',
                    'intro': 'Advocate for environmental policies and green initiatives.',
                    'bio': 'Emma is passionate about environmental protection and has led several green initiatives in the community.',
                    'email': 'emma.wilson@kesgrave-tc.gov.uk',
                    'phone': '01473 625183',
                    'address': 'Kesgrave Town Hall, Main Road, Kesgrave, IP5 2BY',
                    'qualifications': 'MSc Environmental Science, IEMA Member',
                    'is_published': True
                },
                {
                    'name': 'David Taylor',
                    'title': 'Councillor',
                    'intro': 'Finance committee chair with expertise in budget management.',
                    'bio': 'David brings financial expertise to the council and ensures responsible budget management for the community.',
                    'email': 'david.taylor@kesgrave-tc.gov.uk',
                    'phone': '01473 625184',
                    'address': 'Kesgrave Town Hall, Main Road, Kesgrave, IP5 2BY',
                    'qualifications': 'ACCA Qualified, MBA Finance',
                    'is_published': True
                }
            ]
            
            for councillor_data in sample_councillors:
                councillor = Councillor(**councillor_data)
                db.session.add(councillor)
            
            db.session.commit()
            
            # Assign tags to councillors
            councillors = Councillor.query.all()
            tags = Tag.query.all()
            
            # Assign specific tags to each councillor
            tag_assignments = [
                (0, [6, 0, 4]),  # John Smith: Mayor, East Ward, Planning Committee
                (1, [7, 1]),     # Sarah Johnson: Deputy Mayor, West Ward
                (2, [2, 4]),     # Michael Brown: North Ward, Planning Committee
                (3, [3]),        # Emma Wilson: South Ward
                (4, [0, 5])      # David Taylor: East Ward, Finance Committee
            ]
            
            for councillor_idx, tag_indices in tag_assignments:
                councillor = councillors[councillor_idx]
                for tag_idx in tag_indices:
                    if tag_idx < len(tags):
                        councillor_tag = CouncillorTag(councillor_id=councillor.id, tag_id=tags[tag_idx].id)
                        db.session.add(councillor_tag)
            
            db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=8027)


# Event Categories Management Route

# Initialize predefined meeting types
def init_meeting_types():
    """Initialize predefined meeting types"""
    with app.app_context():
        # Create predefined meeting types if they don't exist
        predefined_types = [
            {
                'name': 'Annual Town Meeting',
                'description': 'Annual meeting open to all residents',
                'color': '#e74c3c',
                'show_schedule_applications': False
            },
            {
                'name': 'Community and Recreation',
                'description': 'Meetings for community and recreation matters',
                'color': '#2ecc71',
                'show_schedule_applications': False
            },
            {
                'name': 'Finance and Governance',
                'description': 'Meetings for finance and governance matters',
                'color': '#f39c12',
                'show_schedule_applications': False
            },
            {
                'name': 'Full Council Meetings',
                'description': 'Full council meetings with all councillors',
                'color': '#3498db',
                'show_schedule_applications': False
            },
            {
                'name': 'Planning and Development',
                'description': 'Meetings for planning and development matters',
                'color': '#9b59b6',
                'show_schedule_applications': True  # This type shows Schedule of Applications
            }
        ]
        
        for type_data in predefined_types:
            # Check if meeting type already exists
            existing_type = MeetingType.query.filter_by(name=type_data['name']).first()
            if not existing_type:
                meeting_type = MeetingType(
                    name=type_data['name'],
                    description=type_data['description'],
                    color=type_data['color'],
                    show_schedule_applications=type_data['show_schedule_applications'],
                    is_predefined=True,
                    is_active=True
                )
                db.session.add(meeting_type)
        
        db.session.commit()

# Initialize predefined content categories and subcategories
def init_content_categories():
    """Initialize predefined content categories and subcategories"""
    with app.app_context():
        # Create predefined categories if they don't exist
        predefined_categories = [
            {
                'name': 'News',
                'url_path': '/news',
                'description': 'Latest news and announcements',
                'color': '#e74c3c',
                'subcategories': []
            },
            {
                'name': 'Council Information',
                'url_path': '/council-information',
                'description': 'Information about the council and its operations',
                'color': '#3498db',
                'subcategories': []
            },
            {
                'name': 'Meetings',
                'url_path': '/meetings',
                'description': 'Meeting information and documents',
                'color': '#9b59b6',
                'subcategories': [
                    {'name': 'Annual Town Meetings', 'url_path': '/annual-town-meetings'},
                    {'name': 'Community and Recreation', 'url_path': '/community-and-recreation'},
                    {'name': 'Finance and Governance', 'url_path': '/finance-and-governance'},
                    {'name': 'Full Council Meetings', 'url_path': '/full-council-meetings'},
                    {'name': 'Planning and Development', 'url_path': '/planning-and-development'}
                ]
            },
            {
                'name': 'Financial Information',
                'url_path': '/financial-information',
                'description': 'Budget, accounts, and financial transparency',
                'color': '#f39c12',
                'subcategories': []
            },
            {
                'name': 'Reporting Problems',
                'url_path': '/reporting-problems',
                'description': 'How to report issues and problems',
                'color': '#e67e22',
                'subcategories': []
            }
        ]
        
        for cat_data in predefined_categories:
            # Check if category already exists
            existing_cat = ContentCategory.query.filter_by(url_path=cat_data['url_path']).first()
            if not existing_cat:
                category = ContentCategory(
                    name=cat_data['name'],
                    url_path=cat_data['url_path'],
                    description=cat_data['description'],
                    color=cat_data['color'],
                    is_predefined=True,
                    is_active=True
                )
                db.session.add(category)
                db.session.flush()  # Get the ID
                
                # Add subcategories
                for sub_data in cat_data['subcategories']:
                    subcategory = ContentSubcategory(
                        name=sub_data['name'],
                        url_path=sub_data['url_path'],
                        category_id=category.id,
                        is_predefined=True,
                        is_active=True
                    )
                    db.session.add(subcategory)
        
        db.session.commit()

# Add sample data initialization for events
def init_sample_events():
    """Initialize sample event categories and events"""
    with app.app_context():
        # Create sample event categories if none exist
        if EventCategory.query.count() == 0:
            categories = [
                EventCategory(name='Community Events', description='Local community gatherings and celebrations', color='#e74c3c', icon='fas fa-users'),
                EventCategory(name='Council Meetings', description='Official council meetings and public sessions', color='#3498db', icon='fas fa-gavel'),
                EventCategory(name='Sports & Recreation', description='Sports events and recreational activities', color='#2ecc71', icon='fas fa-futbol'),
                EventCategory(name='Arts & Culture', description='Cultural events, exhibitions, and performances', color='#9b59b6', icon='fas fa-palette'),
                EventCategory(name='Education & Training', description='Educational workshops and training sessions', color='#f39c12', icon='fas fa-graduation-cap'),
                EventCategory(name='Environment', description='Environmental initiatives and green events', color='#27ae60', icon='fas fa-leaf')
            ]
            
            for category in categories:
                db.session.add(category)
            
            db.session.commit()
            
            # Create sample events
            sample_events = [
                Event(
                    title='Annual Summer Fair',
                    description='Join us for our annual summer fair with stalls, games, and entertainment for all the family.',
                    category_id=1,  # Community Events
                    start_date=datetime(2025, 7, 15, 10, 0),
                    end_date=datetime(2025, 7, 15, 16, 0),
                    location_name='Kesgrave Community Centre',
                    location_address='Main Road, Kesgrave, IP5 2PB',
                    contact_name='Sarah Johnson',
                    contact_email='events@kesgrave.gov.uk',
                    contact_phone='01473 123456',
                    is_free=True,
                    featured=True,
                    status='Published',
                    is_published=True
                ),
                Event(
                    title='Town Council Meeting',
                    description='Monthly town council meeting open to the public.',
                    category_id=2,  # Council Meetings
                    start_date=datetime(2025, 7, 3, 19, 30),
                    end_date=datetime(2025, 7, 3, 21, 0),
                    location_name='Council Chambers',
                    location_address='Kesgrave Town Hall, IP5 2PB',
                    contact_name='Town Clerk',
                    contact_email='clerk@kesgrave.gov.uk',
                    is_free=True,
                    status='Published',
                    is_published=True
                ),
                Event(
                    title='Football Tournament',
                    description='Local football tournament for all age groups.',
                    category_id=3,  # Sports & Recreation
                    start_date=datetime(2025, 8, 10, 9, 0),
                    end_date=datetime(2025, 8, 10, 17, 0),
                    location_name='Kesgrave Sports Ground',
                    booking_required=True,
                    booking_url='https://kesgrave.gov.uk/book-football',
                    max_attendees=100,
                    price='£5 per team',
                    is_free=False,
                    status='Published',
                    is_published=True
                )
            ]
            
            for event in sample_events:
                db.session.add(event)
            
            db.session.commit()

def init_homepage_data():
    """Initialize default homepage data"""
    with app.app_context():
        # Create default logo settings if none exist
        if HomepageLogo.query.count() == 0:
            default_logo = HomepageLogo(
                logo_text='Kesgrave Town Council',
                is_active=True
            )
            db.session.add(default_logo)
        
        # Create default footer columns if none exist
        if HomepageFooterColumn.query.count() == 0:
            footer_columns = [
                {
                    'column_number': 1,
                    'column_title': 'Quick Links',
                    'links': [
                        {'name': 'About Us', 'url': '/about'},
                        {'name': 'Contact', 'url': '/contact'},
                        {'name': 'News', 'url': '/news'},
                        {'name': 'Events', 'url': '/events'}
                    ]
                },
                {
                    'column_number': 2,
                    'column_title': 'Services',
                    'links': [
                        {'name': 'Planning Applications', 'url': '/planning'},
                        {'name': 'Council Meetings', 'url': '/meetings'},
                        {'name': 'Community Groups', 'url': '/community'},
                        {'name': 'Local Facilities', 'url': '/facilities'}
                    ]
                },
                {
                    'column_number': 3,
                    'column_title': 'Information',
                    'links': [
                        {'name': 'Council Tax', 'url': '/council-tax'},
                        {'name': 'Local History', 'url': '/history'},
                        {'name': 'Transport', 'url': '/transport'},
                        {'name': 'Emergency Info', 'url': '/emergency'}
                    ]
                }
            ]
            
            for col_data in footer_columns:
                column = HomepageFooterColumn(
                    column_number=col_data['column_number'],
                    column_title=col_data['column_title']
                )
                db.session.add(column)
                db.session.flush()  # Get the ID
                
                for i, link_data in enumerate(col_data['links']):
                    link = HomepageFooterLink(
                        footer_column_id=column.id,
                        link_name=link_data['name'],
                        url=link_data['url'],
                        sort_order=i
                    )
                    db.session.add(link)
        
        db.session.commit()


# Councillors API Endpoint
@app.route('/api/councillors', methods=['GET'])
def get_councillors():
    """Get all published councillors with their tags for the frontend website"""
    try:
        councillors = Councillor.query.filter_by(is_published=True).order_by(Councillor.name).all()
        councillors_data = []
        
        for councillor in councillors:
            # Get tags for this councillor
            councillor_tags = []
            for tag in councillor.tags:
                if tag.is_active:
                    councillor_tags.append({
                        'id': tag.id,
                        'name': tag.name,
                        'color': tag.color,
                        'description': tag.description
                    })
            
            # Parse social links if they exist
            social_links = []
            if councillor.social_links:
                try:
                    social_links = json.loads(councillor.social_links)
                except:
                    social_links = []
            
            councillors_data.append({
                'id': councillor.id,
                'name': councillor.name,
                'title': councillor.title,
                'intro': councillor.intro,
                'bio': councillor.bio,
                'address': councillor.address,
                'email': councillor.email,
                'phone': councillor.phone,
                'qualifications': councillor.qualifications,
                'image_filename': councillor.image_filename,
                'image_url': f'/uploads/councillors/{councillor.image_filename}' if councillor.image_filename else None,
                'social_links': social_links,
                'tags': councillor_tags,
                'created_at': councillor.created_at.isoformat() if councillor.created_at else None,
                'updated_at': councillor.updated_at.isoformat() if councillor.updated_at else None
            })
        
        return jsonify(councillors_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Individual Councillor API Endpoint
@app.route('/api/councillors/<int:councillor_id>', methods=['GET'])
def get_councillor(councillor_id):
    """Get detailed information for a specific councillor"""
    try:
        councillor = Councillor.query.filter_by(id=councillor_id, is_published=True).first()
        
        if not councillor:
            return jsonify({'error': 'Councillor not found'}), 404
        
        # Get tags for this councillor
        councillor_tags = []
        for tag in councillor.tags:
            if tag.is_active:
                councillor_tags.append({
                    'id': tag.id,
                    'name': tag.name,
                    'color': tag.color,
                    'description': tag.description
                })
        
        # Parse social links if they exist
        social_links = []
        if councillor.social_links:
            try:
                social_links = json.loads(councillor.social_links)
            except:
                social_links = []
        
        councillor_data = {
            'id': councillor.id,
            'name': councillor.name,
            'title': councillor.title,
            'intro': councillor.intro,
            'bio': councillor.bio,
            'address': councillor.address,
            'email': councillor.email,
            'phone': councillor.phone,
            'qualifications': councillor.qualifications,
            'image_filename': councillor.image_filename,
            'image_url': f'/uploads/councillors/{councillor.image_filename}' if councillor.image_filename else None,
            'social_links': social_links,
            'tags': councillor_tags,
            'created_at': councillor.created_at.isoformat() if councillor.created_at else None,
            'updated_at': councillor.updated_at.isoformat() if councillor.updated_at else None
        }
        
        return jsonify(councillor_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Tags API Endpoint (for ward filtering)
@app.route('/api/tags', methods=['GET'])
def get_tags():
    """Get all active tags for filtering councillors"""
    try:
        tags = Tag.query.filter_by(is_active=True).order_by(Tag.name).all()
        tags_data = []
        
        for tag in tags:
            # Count how many councillors have this tag
            councillor_count = db.session.query(CouncillorTag).join(Councillor).filter(
                CouncillorTag.tag_id == tag.id,
                Councillor.is_published == True
            ).count()
            
            tags_data.append({
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'description': tag.description,
                'councillor_count': councillor_count,
                'created_at': tag.created_at.isoformat() if tag.created_at else None
            })
        
        return jsonify(tags_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Councillors by Tag API Endpoint
@app.route('/api/councillors/by-tag/<int:tag_id>', methods=['GET'])
def get_councillors_by_tag(tag_id):
    """Get councillors filtered by a specific tag"""
    try:
        # Verify tag exists and is active
        tag = Tag.query.filter_by(id=tag_id, is_active=True).first()
        if not tag:
            return jsonify({'error': 'Tag not found'}), 404
        
        # Get councillors with this tag
        councillors = db.session.query(Councillor).join(CouncillorTag).filter(
            CouncillorTag.tag_id == tag_id,
            Councillor.is_published == True
        ).order_by(Councillor.name).all()
        
        councillors_data = []
        for councillor in councillors:
            # Get all tags for this councillor
            councillor_tags = []
            for ctag in councillor.tags:
                if ctag.is_active:
                    councillor_tags.append({
                        'id': ctag.id,
                        'name': ctag.name,
                        'color': ctag.color,
                        'description': ctag.description
                    })
            
            # Parse social links if they exist
            social_links = []
            if councillor.social_links:
                try:
                    social_links = json.loads(councillor.social_links)
                except:
                    social_links = []
            
            councillors_data.append({
                'id': councillor.id,
                'name': councillor.name,
                'title': councillor.title,
                'intro': councillor.intro,
                'bio': councillor.bio,
                'address': councillor.address,
                'email': councillor.email,
                'phone': councillor.phone,
                'qualifications': councillor.qualifications,
                'image_filename': councillor.image_filename,
                'image_url': f'/uploads/councillors/{councillor.image_filename}' if councillor.image_filename else None,
                'social_links': social_links,
                'tags': councillor_tags,
                'created_at': councillor.created_at.isoformat() if councillor.created_at else None,
                'updated_at': councillor.updated_at.isoformat() if councillor.updated_at else None
            })
        
        return jsonify({
            'tag': {
                'id': tag.id,
                'name': tag.name,
                'color': tag.color,
                'description': tag.description
            },
            'councillors': councillors_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Main initialization function
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Initialize predefined meeting types
        init_meeting_types()
        
        # Initialize predefined content categories
        init_content_categories()
        
        # Initialize sample data
        init_sample_events()
        
        # Initialize homepage data
        init_homepage_data()
        
        # Create sample tags if none exist
        if Tag.query.count() == 0:
            tags = [
                Tag(name='East Ward', color='#3498db', description='East Ward representatives'),
                Tag(name='West Ward', color='#e74c3c', description='West Ward representatives'),
                Tag(name='North Ward', color='#2ecc71', description='North Ward representatives'),
                Tag(name='South Ward', color='#f39c12', description='South Ward representatives'),
                Tag(name='Central Ward', color='#9b59b6', description='Central Ward representatives'),
                Tag(name='Mayor', color='#e67e22', description='Mayor of Kesgrave'),
                Tag(name='Deputy Mayor', color='#34495e', description='Deputy Mayor'),
                Tag(name='Planning Committee', color='#16a085', description='Planning Committee members'),
                Tag(name='Finance Committee', color='#8e44ad', description='Finance Committee members'),
                Tag(name='Environment Committee', color='#27ae60', description='Environment Committee members')
            ]
            
            for tag in tags:
                db.session.add(tag)
            
            db.session.commit()
        
        # Create sample councillors if none exist
        if Councillor.query.count() == 0:
            councillors = [
                Councillor(
                    name='Neal Beecroft-Smith',
                    title='Mayor',
                    intro='Serving the community with dedication and transparency.',
                    bio='Neal has been serving Kesgrave for over 10 years, focusing on community development and environmental initiatives.',
                    email='neal.beecroft-smith@kesgrave.gov.uk',
                    phone='01473 123456',
                    qualifications='BSc Environmental Science, Local Government Certificate',
                    is_published=True
                ),
                Councillor(
                    name='Avtar Athwall',
                    title='Deputy Mayor',
                    intro='Committed to improving local services and community engagement.',
                    bio='Avtar brings extensive experience in local governance and community outreach programs.',
                    email='avtar.athwall@kesgrave.gov.uk',
                    phone='01473 123457',
                    qualifications='MA Public Administration',
                    is_published=True
                ),
                Councillor(
                    name='Sarah Johnson',
                    title='Councillor',
                    intro='Passionate about education and youth development.',
                    bio='Sarah has worked in education for 15 years and is dedicated to improving facilities for young people.',
                    email='sarah.johnson@kesgrave.gov.uk',
                    phone='01473 123458',
                    qualifications='MEd Educational Leadership',
                    is_published=True
                ),
                Councillor(
                    name='Michael Thompson',
                    title='Councillor',
                    intro='Focused on sustainable development and planning.',
                    bio='Michael chairs the Planning Committee and has expertise in sustainable urban development.',
                    email='michael.thompson@kesgrave.gov.uk',
                    phone='01473 123459',
                    qualifications='MSc Urban Planning',
                    is_published=True
                ),
                Councillor(
                    name='Emma Wilson',
                    title='Councillor',
                    intro='Advocate for community health and wellbeing.',
                    bio='Emma works to improve health services and promote community wellbeing initiatives.',
                    email='emma.wilson@kesgrave.gov.uk',
                    phone='01473 123460',
                    qualifications='BSc Public Health',
                    is_published=True
                )
            ]
            
            for councillor in councillors:
                db.session.add(councillor)
            
            db.session.commit()
            
            # Assign tags to councillors
            tags = Tag.query.all()
            councillors = Councillor.query.all()
            
            # Assign some sample tags to councillors
            tag_assignments = [
                (0, [0, 5]),  # Neal: East Ward, Mayor
                (1, [1, 6]),  # Avtar: West Ward, Deputy Mayor
                (2, [2, 9]),  # Sarah: North Ward, Environment Committee
                (3, [3, 7]),  # Michael: South Ward, Planning Committee
                (4, [4, 8])   # Emma: Central Ward, Finance Committee
            ]
            
            for councillor_idx, tag_indices in tag_assignments:
                councillor = councillors[councillor_idx]
                for tag_idx in tag_indices:
                    if tag_idx < len(tags):
                        councillor_tag = CouncillorTag(councillor_id=councillor.id, tag_id=tags[tag_idx].id)
                        db.session.add(councillor_tag)
            
            db.session.commit()
        
        # Create sample content categories if none exist
        if ContentCategory.query.count() == 0:
            categories = [
                ContentCategory(name='Planning', description='Planning applications and development', color='#3498db'),
                ContentCategory(name='Environment', description='Environmental policies and initiatives', color='#27ae60'),
                ContentCategory(name='Community', description='Community services and events', color='#e74c3c'),
                ContentCategory(name='Finance', description='Budget and financial information', color='#f39c12'),
                ContentCategory(name='Transport', description='Transport and highways', color='#9b59b6'),
                ContentCategory(name='Housing', description='Housing policies and development', color='#e67e22')
            ]
            
            for category in categories:
                db.session.add(category)
            
            db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=8027)


# Event Edit Route
# Event Delete Route
@login_required
def events_all():
    events = Event.query.order_by(Event.start_date.desc()).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>All Events - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .event-row:hover {
                background-color: #f8f9fa;
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link active">
                    <i class="fas fa-calendar me-2"></i>Events & Things to Do
                </a>
                <a href="/meetings" class="nav-link">
                    <i class="fas fa-handshake me-2"></i>Meetings
                </a>
                <a href="/homepage" class="nav-link">
                    <i class="fas fa-home me-2"></i>Homepage
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>📅 All Events</h1>
                <div>
                    <a href="/events" class="btn btn-secondary me-2">
                        <i class="fas fa-arrow-left me-2"></i>Back to Events
                    </a>
                    <a href="/events/add" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Add New Event
                    </a>
                </div>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Event</th>
                                    <th>Date & Time</th>
                                    <th>Category</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for event in events %}
                                <tr class="event-row">
                                    <td>
                                        <div class="d-flex align-items-center">
                                            {% if event.image_filename %}
                                            <img src="/uploads/events/{{ event.image_filename }}" 
                                                 class="rounded me-3" style="width: 50px; height: 50px; object-fit: cover;">
                                            {% else %}
                                            <div class="bg-secondary rounded me-3 d-flex align-items-center justify-content-center" 
                                                 style="width: 50px; height: 50px;">
                                                <i class="fas fa-calendar text-white"></i>
                                            </div>
                                            {% endif %}
                                            <div>
                                                <h6 class="mb-1">{{ event.title }}</h6>
                                                {% if event.location_name %}
                                                <small class="text-muted">
                                                    <i class="fas fa-map-marker-alt me-1"></i>{{ event.location_name }}
                                                </small>
                                                {% endif %}
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        <div>
                                            <strong>{{ event.start_date.strftime('%d/%m/%Y') }}</strong>
                                            {% if not event.all_day %}
                                            <br><small class="text-muted">{{ event.start_date.strftime('%H:%M') }}</small>
                                            {% endif %}
                                        </div>
                                    </td>
                                    <td>
                                        {% if event.category %}
                                        <span class="badge" style="background-color: {{ event.category.color }};">
                                            {{ event.category.name }}
                                        </span>
                                        {% else %}
                                        <span class="badge bg-secondary">Uncategorized</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if event.status == 'Published' %}
                                        <span class="badge bg-success">{{ event.status }}</span>
                                        {% elif event.status == 'Draft' %}
                                        <span class="badge bg-warning">{{ event.status }}</span>
                                        {% else %}
                                        <span class="badge bg-danger">{{ event.status }}</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <div class="btn-group btn-group-sm">
                                            <a href="/events/edit/{{ event.id }}" class="btn btn-outline-primary">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            <button class="btn btn-outline-danger" 
                                                    onclick="deleteEvent({{ event.id }}, '{{ event.title }}')">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                        
                        {% if not events %}
                        <div class="text-center py-5">
                            <i class="fas fa-calendar-times fa-3x text-muted mb-3"></i>
                            <h5 class="text-muted">No events found</h5>
                            <p class="text-muted">Start by creating your first event.</p>
                            <a href="/events/add" class="btn btn-primary">
                                <i class="fas fa-plus me-2"></i>Add New Event
                            </a>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
        function deleteEvent(eventId, eventTitle) {
            if (confirm('Are you sure you want to delete "' + eventTitle + '"? This action cannot be undone.')) {
                fetch('/events/delete/' + eventId, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                }).then(response => {
                    if (response.ok) {
                        location.reload();
                    } else {
                        alert('Error deleting event');
                    }
                });
            }
        }
        </script>
    </body>
    </html>
    ''', events=events)


# ===== MEETINGS SECTION =====

@app.route('/meetings')
@login_required
def meetings_list():
    # Get filter parameters
    meeting_type_filter = request.args.get('type', '')
    
    # Build query
    query = Meeting.query.join(MeetingType)
    
    if meeting_type_filter:
        query = query.filter(Meeting.meeting_type_id == meeting_type_filter)
    
    # Order by date descending (most recent first)
    meetings = query.order_by(Meeting.meeting_date.desc(), Meeting.meeting_time.desc()).all()
    meeting_types = MeetingType.query.filter_by(is_active=True).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Meetings - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .meeting-row:hover {
                background-color: #f8f9fa;
            }
            .meeting-type-badge {
                font-size: 0.8em;
                padding: 0.25rem 0.5rem;
            }
            .meeting-type-card {
                transition: all 0.3s ease;
                cursor: pointer;
            }
            .meeting-type-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            .meeting-type-card .card-body {
                background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/meetings" class="nav-link active">
                    <i class="fas fa-handshake me-2"></i>Meetings
                </a>
                <a href="/homepage" class="nav-link">
                    <i class="fas fa-home me-2"></i>Homepage
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>🤝 Meetings Management</h1>
                <a href="/meetings/add" class="btn btn-primary">
                    <i class="fas fa-plus me-2"></i>Add Meeting
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <!-- Filters -->
            <div class="card mb-4">
                <div class="card-body">
                    <form method="GET" class="row g-3">
                        <div class="col-md-4">
                            <label class="form-label">Filter by Meeting Type</label>
                            <select class="form-select" name="type" onchange="this.form.submit()">
                                <option value="">All Meeting Types</option>
                                {% for type in meeting_types %}
                                <option value="{{ type.id }}" {{ 'selected' if request.args.get('type') == type.id|string else '' }}>
                                    {{ type.name }}
                                </option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-8 d-flex align-items-end">
                            <button type="submit" class="btn btn-outline-primary me-2">Apply Filter</button>
                            <a href="/meetings" class="btn btn-outline-secondary">Clear Filters</a>
                        </div>
                    </form>
                </div>
            </div>
            
            <!-- Meeting Type Cards -->
            <div class="row mb-4">
                {% for type in meeting_types %}
                <div class="col-md-2 col-sm-4 col-6 mb-3">
                    <a href="/meetings?type={{ type.id }}" class="text-decoration-none">
                        <div class="card h-100 meeting-type-card" style="border-left: 4px solid {{ type.color }};">
                            <div class="card-body text-center p-3">
                                <div class="mb-2">
                                    <i class="fas fa-handshake fa-2x" style="color: {{ type.color }};"></i>
                                </div>
                                <h6 class="card-title mb-1" style="font-size: 0.9rem;">{{ type.name }}</h6>
                                <small class="text-muted">
                                    {{ type.meetings|length }} meeting{{ 's' if type.meetings|length != 1 else '' }}
                                </small>
                            </div>
                        </div>
                    </a>
                </div>
                {% endfor %}
                <div class="col-md-2 col-sm-4 col-6 mb-3">
                    <a href="/meetings" class="text-decoration-none">
                        <div class="card h-100 meeting-type-card" style="border-left: 4px solid #6c757d;">
                            <div class="card-body text-center p-3">
                                <div class="mb-2">
                                    <i class="fas fa-list fa-2x" style="color: #6c757d;"></i>
                                </div>
                                <h6 class="card-title mb-1" style="font-size: 0.9rem;">All Meetings</h6>
                                <small class="text-muted">
                                    {{ meetings|length }} total
                                </small>
                            </div>
                        </div>
                    </a>
                </div>
            </div>
            
            <!-- Meetings Table -->
            <div class="card">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>Type</th>
                                    <th>Date & Time</th>
                                    <th>Location</th>
                                    <th>Agenda</th>
                                    <th>Minutes</th>
                                    <th>Draft Minutes</th>
                                    <th id="schedule-header" style="display: none;">Schedule of Applications</th>
                                    <th>Audio</th>
                                    <th>Summary</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for meeting in meetings %}
                                <tr class="meeting-row">
                                    <td>
                                        <span class="badge meeting-type-badge" style="background-color: {{ meeting.meeting_type.color }};">
                                            {{ meeting.meeting_type.name }}
                                        </span>
                                    </td>
                                    <td>
                                        {{ meeting.meeting_date.strftime('%d %b %Y') }}<br>
                                        <small class="text-muted">{{ meeting.meeting_time.strftime('%H:%M') }}</small>
                                    </td>
                                    <td>{{ meeting.location or '-' }}</td>
                                    <td>
                                        {% if meeting.agenda_filename %}
                                        <a href="/uploads/meetings/{{ meeting.agenda_filename }}" target="_blank" class="btn btn-sm btn-outline-primary">
                                            <i class="fas fa-file-pdf me-1"></i>View
                                        </a>
                                        {% else %}
                                        <span class="text-muted">-</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if meeting.minutes_filename %}
                                        <a href="/uploads/meetings/{{ meeting.minutes_filename }}" target="_blank" class="btn btn-sm btn-outline-success">
                                            <i class="fas fa-file-pdf me-1"></i>View
                                        </a>
                                        {% else %}
                                        <span class="text-muted">-</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if meeting.draft_minutes_filename %}
                                        <a href="/uploads/meetings/{{ meeting.draft_minutes_filename }}" target="_blank" class="btn btn-sm btn-outline-warning">
                                            <i class="fas fa-file-pdf me-1"></i>Draft
                                        </a>
                                        {% else %}
                                        <span class="text-muted">-</span>
                                        {% endif %}
                                    </td>
                                    <td class="schedule-cell" style="display: none;">
                                        {% if meeting.meeting_type.show_schedule_applications %}
                                            {% if meeting.schedule_applications_filename %}
                                            <a href="/uploads/meetings/{{ meeting.schedule_applications_filename }}" target="_blank" class="btn btn-sm btn-outline-info">
                                                <i class="fas fa-file-pdf me-1"></i>View
                                            </a>
                                            {% else %}
                                            <span class="text-muted">-</span>
                                            {% endif %}
                                        {% else %}
                                        <span class="text-muted">N/A</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if meeting.audio_filename %}
                                        <a href="/uploads/meetings/{{ meeting.audio_filename }}" target="_blank" class="btn btn-sm btn-outline-secondary">
                                            <i class="fas fa-play me-1"></i>Play
                                        </a>
                                        {% else %}
                                        <span class="text-muted">-</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if meeting.summary_url %}
                                        <a href="{{ meeting.summary_url }}" target="_blank" class="btn btn-sm btn-outline-dark">
                                            <i class="fas fa-external-link-alt me-1"></i>View
                                        </a>
                                        {% else %}
                                        <span class="text-muted">-</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if meeting.status == 'Scheduled' %}
                                        <span class="badge bg-primary">{{ meeting.status }}</span>
                                        {% elif meeting.status == 'Completed' %}
                                        <span class="badge bg-success">{{ meeting.status }}</span>
                                        {% elif meeting.status == 'Cancelled' %}
                                        <span class="badge bg-danger">{{ meeting.status }}</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <div class="btn-group btn-group-sm">
                                            <a href="/meetings/edit/{{ meeting.id }}" class="btn btn-outline-primary">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            <button class="btn btn-outline-danger" onclick="deleteMeeting({{ meeting.id }}, '{{ meeting.title }}')">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                        
                        {% if not meetings %}
                        <div class="text-center py-5">
                            <i class="fas fa-handshake fa-3x text-muted mb-3"></i>
                            <h5 class="text-muted">No meetings found</h5>
                            <p class="text-muted">Start by creating your first meeting.</p>
                            <a href="/meetings/add" class="btn btn-primary">
                                <i class="fas fa-plus me-2"></i>Add New Meeting
                            </a>
                        </div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Show/hide Schedule of Applications column based on meeting types
            function updateScheduleColumn() {
                const showSchedule = {% if meetings and meetings|selectattr('meeting_type.show_schedule_applications')|list %}true{% else %}false{% endif %};
                
                const header = document.getElementById('schedule-header');
                const cells = document.querySelectorAll('.schedule-cell');
                
                if (showSchedule) {
                    header.style.display = '';
                    cells.forEach(cell => cell.style.display = '');
                } else {
                    header.style.display = 'none';
                    cells.forEach(cell => cell.style.display = 'none');
                }
            }
            
            function deleteMeeting(meetingId, meetingTitle) {
                if (confirm('Are you sure you want to delete "' + meetingTitle + '"? This action cannot be undone.')) {
                    fetch('/meetings/delete/' + meetingId, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    }).then(response => {
                        if (response.ok) {
                            location.reload();
                        } else {
                            alert('Error deleting meeting');
                        }
                    });
                }
            }
            
            // Initialize on page load
            updateScheduleColumn();
        </script>
    </body>
    </html>
    ''', meetings=meetings, meeting_types=meeting_types, request=request)

@app.route('/meetings/add', methods=['GET', 'POST'])
@login_required
def add_meeting():
    if request.method == 'POST':
        # Get meeting type for title generation
        meeting_type = MeetingType.query.get(request.form['meeting_type_id'])
        meeting_date = datetime.strptime(request.form['meeting_date'], '%Y-%m-%d').date()
        
        # Auto-generate title from meeting type and date
        auto_title = f"{meeting_type.name}: {meeting_date.strftime('%d/%m/%Y')}"
        
        # Handle form submission
        meeting = Meeting(
            title=auto_title,
            meeting_type_id=request.form['meeting_type_id'],
            meeting_date=meeting_date,
            meeting_time=datetime.strptime(request.form['meeting_time'], '%H:%M').time(),
            location=request.form.get('location'),
            status=request.form.get('status', 'Scheduled'),
            is_published=bool(request.form.get('is_published')),
            notes=request.form.get('notes')
        )
        
        # Handle file uploads and metadata
        # Agenda
        if 'agenda_file' in request.files:
            file = request.files['agenda_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'download')
                meeting.agenda_filename = filename
        meeting.agenda_title = request.form.get('agenda_title')
        meeting.agenda_description = request.form.get('agenda_description')
        
        # Minutes
        if 'minutes_file' in request.files:
            file = request.files['minutes_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'download')
                meeting.minutes_filename = filename
        meeting.minutes_title = request.form.get('minutes_title')
        meeting.minutes_description = request.form.get('minutes_description')
        
        # Draft Minutes
        if 'draft_minutes_file' in request.files:
            file = request.files['draft_minutes_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'download')
                meeting.draft_minutes_filename = filename
        meeting.draft_minutes_title = request.form.get('draft_minutes_title')
        meeting.draft_minutes_description = request.form.get('draft_minutes_description')
        
        # Schedule of Applications
        if 'schedule_applications_file' in request.files:
            file = request.files['schedule_applications_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'download')
                meeting.schedule_applications_filename = filename
        meeting.schedule_applications_title = request.form.get('schedule_applications_title')
        meeting.schedule_applications_description = request.form.get('schedule_applications_description')
        
        # Audio
        if 'audio_file' in request.files:
            file = request.files['audio_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'audio')
                meeting.audio_filename = filename
        meeting.audio_title = request.form.get('audio_title')
        meeting.audio_description = request.form.get('audio_description')
        
        # Summary URL
        meeting.summary_url = request.form.get('summary_url')
        
        db.session.add(meeting)
        
        # Handle future meetings generation
        if request.form.get('generate_future'):
            frequency = request.form.get('frequency')  # weekly, fortnightly, 4-weekly, monthly
            count = int(request.form.get('future_count', 1))
            
            base_date = meeting.meeting_date
            for i in range(1, count + 1):
                if frequency == 'weekly':
                    future_date = base_date + timedelta(weeks=i)
                elif frequency == 'fortnightly':
                    future_date = base_date + timedelta(weeks=i*2)
                elif frequency == '4-weekly':
                    future_date = base_date + timedelta(weeks=i*4)
                elif frequency == 'monthly':
                    future_date = base_date + relativedelta(months=i)
                else:
                    continue
                
                # Auto-generate title for future meeting with its specific date
                future_title = f"{meeting_type.name}: {future_date.strftime('%d/%m/%Y')}"
                
                future_meeting = Meeting(
                    title=future_title,
                    meeting_type_id=meeting.meeting_type_id,
                    meeting_date=future_date,
                    meeting_time=meeting.meeting_time,
                    location=meeting.location,
                    status='Scheduled',
                    is_published=meeting.is_published,
                    notes=meeting.notes
                )
                db.session.add(future_meeting)
        
        db.session.commit()
        flash('Meeting created successfully!', 'success')
        return redirect(url_for('meetings_list'))
    
    meeting_types = MeetingType.query.filter_by(is_active=True).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Add Meeting - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .section-card {
                border: none;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/meetings" class="nav-link active">
                <a href="/homepage" class="nav-link">
                    <i class="fas fa-home me-2"></i>Homepage
                </a>
                    <i class="fas fa-handshake me-2"></i>Meetings
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>🤝 Add New Meeting</h1>
                <a href="/meetings" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Meetings
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST" enctype="multipart/form-data">
                <!-- Basic Information -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-info-circle me-2"></i>Basic Information</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Status</label>
                                    <select class="form-select" name="status">
                                        <option value="Scheduled">Scheduled</option>
                                        <option value="Completed">Completed</option>
                                        <option value="Cancelled">Cancelled</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <div class="form-check mt-4">
                                        <input class="form-check-input" type="checkbox" name="is_published" id="is_published" checked>
                                        <label class="form-check-label" for="is_published">
                                            Publish Immediately
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Type *</label>
                                    <select class="form-select" name="meeting_type_id" required onchange="updateScheduleField()">
                                        <option value="">Select Meeting Type</option>
                                        {% for type in meeting_types %}
                                        <option value="{{ type.id }}" data-show-schedule="{{ type.show_schedule_applications|lower }}">
                                            {{ type.name }}
                                        </option>
                                        {% endfor %}
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Date *</label>
                                    <input type="date" class="form-control" name="meeting_date" required>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Time *</label>
                                    <input type="time" class="form-control" name="meeting_time" required>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Location</label>
                                    <input type="text" class="form-control" name="location" placeholder="e.g., Council Chambers, Kesgrave Town Hall">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <div class="form-check mt-4">
                                        <input class="form-check-input" type="checkbox" name="is_published" id="is_published" checked>
                                        <label class="form-check-label" for="is_published">
                                            Publish Immediately
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Notes</label>
                            <textarea class="form-control" name="notes" rows="3" placeholder="Additional notes about the meeting"></textarea>
                        </div>
                    </div>
                </div>
                
                <!-- Documents -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-file-pdf me-2"></i>Meeting Documents</h5>
                    </div>
                    <div class="card-body">
                        <!-- Agenda -->
                        <div class="row mb-4">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Agenda (PDF)</label>
                                    <input type="file" class="form-control" name="agenda_file" accept=".pdf">
                                    <small class="text-muted">Upload meeting agenda</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Agenda Title</label>
                                    <input type="text" class="form-control" name="agenda_title" placeholder="e.g., Meeting Agenda">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Agenda Description</label>
                                    <textarea class="form-control" name="agenda_description" rows="2" placeholder="Brief description of the agenda"></textarea>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Minutes -->
                        <div class="row mb-4">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Minutes (PDF)</label>
                                    <input type="file" class="form-control" name="minutes_file" accept=".pdf">
                                    <small class="text-muted">Upload meeting minutes</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Minutes Title</label>
                                    <input type="text" class="form-control" name="minutes_title" placeholder="e.g., Meeting Minutes">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Minutes Description</label>
                                    <textarea class="form-control" name="minutes_description" rows="2" placeholder="Brief description of the minutes"></textarea>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Draft Minutes -->
                        <div class="row mb-4">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Draft Minutes (PDF)</label>
                                    <input type="file" class="form-control" name="draft_minutes_file" accept=".pdf">
                                    <small class="text-muted">Upload draft meeting minutes</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Draft Minutes Title</label>
                                    <input type="text" class="form-control" name="draft_minutes_title" placeholder="e.g., Draft Meeting Minutes">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Draft Minutes Description</label>
                                    <textarea class="form-control" name="draft_minutes_description" rows="2" placeholder="Brief description of the draft minutes"></textarea>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Schedule of Applications (conditional) -->
                        <div class="row mb-4" id="schedule-field" style="display: none;">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Schedule of Applications (PDF)</label>
                                    <input type="file" class="form-control" name="schedule_applications_file" accept=".pdf">
                                    <small class="text-muted">Upload schedule of applications</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Schedule Title</label>
                                    <input type="text" class="form-control" name="schedule_applications_title" placeholder="e.g., Schedule of Applications">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Schedule Description</label>
                                    <textarea class="form-control" name="schedule_applications_description" rows="2" placeholder="Brief description of the schedule"></textarea>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Audio -->
                        <div class="row mb-4">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Audio Recording</label>
                                    <input type="file" class="form-control" name="audio_file" accept=".mp3,.wav,.m4a,.ogg">
                                    <small class="text-muted">Upload meeting audio recording</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Audio Title</label>
                                    <input type="text" class="form-control" name="audio_title" placeholder="e.g., Meeting Recording">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Audio Description</label>
                                    <textarea class="form-control" name="audio_description" rows="2" placeholder="Brief description of the audio recording"></textarea>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Summary URL -->
                        <div class="row mb-4">
                            <div class="col-md-12">
                                <div class="mb-3">
                                    <label class="form-label">Summary Page URL</label>
                                    <input type="url" class="form-control" name="summary_url" placeholder="https://example.com/meeting-summary">
                                    <small class="text-muted">Link to external meeting summary page</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Future Meetings Generator -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-calendar-plus me-2"></i>Generate Future Meetings</h5>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="generate_future" id="generate_future" onchange="toggleFutureOptions()">
                                <label class="form-check-label" for="generate_future">
                                    Generate future meetings based on this one
                                </label>
                            </div>
                        </div>
                        
                        <div id="future-options" style="display: none;">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Frequency</label>
                                        <select class="form-select" name="frequency">
                                            <option value="weekly">Weekly</option>
                                            <option value="fortnightly">Fortnightly</option>
                                            <option value="4-weekly">4-weekly</option>
                                            <option value="monthly" selected>Monthly</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="mb-3">
                                        <label class="form-label">Number of Future Meetings</label>
                                        <select class="form-select" name="future_count">
                                            <option value="1">1</option>
                                            <option value="2">2</option>
                                            <option value="3" selected>3</option>
                                            <option value="4">4</option>
                                            <option value="5">5</option>
                                            <option value="6">6</option>
                                            <option value="7">7</option>
                                            <option value="8">8</option>
                                            <option value="9">9</option>
                                            <option value="10">10</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Submit -->
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save me-2"></i>Create Meeting
                    </button>
                    <a href="/meetings" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function updateScheduleField() {
                const select = document.querySelector('select[name="meeting_type_id"]');
                const scheduleField = document.getElementById('schedule-field');
                
                if (select.value) {
                    const option = select.options[select.selectedIndex];
                    const showSchedule = option.getAttribute('data-show-schedule') === 'true';
                    scheduleField.style.display = showSchedule ? 'block' : 'none';
                } else {
                    scheduleField.style.display = 'none';
                }
            }
            
            function toggleFutureOptions() {
                const checkbox = document.getElementById('generate_future');
                const options = document.getElementById('future-options');
                options.style.display = checkbox.checked ? 'block' : 'none';
            }
        </script>
    </body>
    </html>
    ''', meeting_types=meeting_types)




@app.route('/meetings/edit/<int:meeting_id>', methods=['GET', 'POST'])
@login_required
def edit_meeting(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    
    if request.method == 'POST':
        # Update meeting details
        meeting.meeting_type_id = request.form['meeting_type_id']
        meeting.meeting_date = datetime.strptime(request.form['meeting_date'], '%Y-%m-%d').date()
        meeting.meeting_time = datetime.strptime(request.form['meeting_time'], '%H:%M').time()
        meeting.location = request.form.get('location')
        meeting.status = request.form.get('status', 'Scheduled')
        meeting.is_published = bool(request.form.get('is_published'))
        meeting.notes = request.form.get('notes')
        meeting.updated_at = datetime.utcnow()
        
        # Auto-generate title from meeting type and date
        meeting_type = MeetingType.query.get(meeting.meeting_type_id)
        meeting.title = f"{meeting_type.name}: {meeting.meeting_date.strftime('%d/%m/%Y')}"
        
        # Handle file uploads and metadata
        # Agenda
        if 'agenda_file' in request.files:
            file = request.files['agenda_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'download')
                if filename:
                    meeting.agenda_filename = filename
        meeting.agenda_title = request.form.get('agenda_title')
        meeting.agenda_description = request.form.get('agenda_description')
        
        # Minutes
        if 'minutes_file' in request.files:
            file = request.files['minutes_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'download')
                if filename:
                    meeting.minutes_filename = filename
        meeting.minutes_title = request.form.get('minutes_title')
        meeting.minutes_description = request.form.get('minutes_description')
        
        # Draft Minutes
        if 'draft_minutes_file' in request.files:
            file = request.files['draft_minutes_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'download')
                if filename:
                    meeting.draft_minutes_filename = filename
        meeting.draft_minutes_title = request.form.get('draft_minutes_title')
        meeting.draft_minutes_description = request.form.get('draft_minutes_description')
        
        # Schedule of Applications
        if 'schedule_applications_file' in request.files:
            file = request.files['schedule_applications_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'download')
                if filename:
                    meeting.schedule_applications_filename = filename
        meeting.schedule_applications_title = request.form.get('schedule_applications_title')
        meeting.schedule_applications_description = request.form.get('schedule_applications_description')
        
        # Audio
        if 'audio_file' in request.files:
            file = request.files['audio_file']
            if file and file.filename:
                filename = save_uploaded_file(file, 'meetings', 'audio')
                if filename:
                    meeting.audio_filename = filename
        meeting.audio_title = request.form.get('audio_title')
        meeting.audio_description = request.form.get('audio_description')
        
        # Summary URL
        meeting.summary_url = request.form.get('summary_url')
        
        db.session.commit()
        flash('Meeting updated successfully!', 'success')
        return redirect(url_for('meetings_list'))
    
    meeting_types = MeetingType.query.filter_by(is_active=True).all()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edit Meeting - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                width: 260px;
                background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
                color: white;
                z-index: 1000;
                overflow-y: auto;
            }
            .main-content {
                margin-left: 260px;
                padding: 2rem;
                background-color: #f8f9fa;
                min-height: 100vh;
            }
            .nav-link {
                color: rgba(255,255,255,0.8);
                padding: 0.75rem 1.5rem;
                display: block;
                text-decoration: none;
                transition: all 0.3s ease;
            }
            .nav-link:hover, .nav-link.active {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            .section-card {
                border: none;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
        </style>
    </head>
    <body>
        <nav class="sidebar">
            <div class="p-3 text-center border-bottom">
                <h4>🏛️ Kesgrave CMS</h4>
            </div>
            <div class="p-3">
                <a href="/dashboard" class="nav-link">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
                <a href="/councillors" class="nav-link">
                    <i class="fas fa-users me-2"></i>Councillors
                </a>
                <a href="/tags" class="nav-link">
                    <i class="fas fa-tags me-2"></i>Ward Tags
                </a>
                <a href="/content" class="nav-link">
                    <i class="fas fa-file-alt me-2"></i>Content
                </a>
                <a href="/events" class="nav-link">
                    <i class="fas fa-calendar me-2"></i>Events
                </a>
                <a href="/meetings" class="nav-link active">
                <a href="/homepage" class="nav-link">
                    <i class="fas fa-home me-2"></i>Homepage
                </a>
                    <i class="fas fa-handshake me-2"></i>Meetings
                </a>
                <a href="/settings" class="nav-link">
                    <i class="fas fa-cog me-2"></i>Settings
                </a>
                <hr style="border-color: rgba(255,255,255,0.2);">
                <a href="/logout" class="nav-link">
                    <i class="fas fa-sign-out-alt me-2"></i>Logout
                </a>
            </div>
        </nav>
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1>✏️ Edit Meeting: {{ meeting.title }}</h1>
                <a href="/meetings" class="btn btn-secondary">
                    <i class="fas fa-arrow-left me-2"></i>Back to Meetings
                </a>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST" enctype="multipart/form-data">
                <!-- Basic Information -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-info-circle me-2"></i>Basic Information</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Status</label>
                                    <select class="form-select" name="status">
                                        <option value="Scheduled" {{ 'selected' if meeting.status == 'Scheduled' else '' }}>Scheduled</option>
                                        <option value="Completed" {{ 'selected' if meeting.status == 'Completed' else '' }}>Completed</option>
                                        <option value="Cancelled" {{ 'selected' if meeting.status == 'Cancelled' else '' }}>Cancelled</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <div class="form-check mt-4">
                                        <input class="form-check-input" type="checkbox" name="is_published" id="is_published_edit" {{ 'checked' if meeting.is_published else '' }}>
                                        <label class="form-check-label" for="is_published_edit">
                                            Publish Immediately
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Type *</label>
                                    <select class="form-select" name="meeting_type_id" required onchange="updateScheduleField()">
                                        <option value="">Select Meeting Type</option>
                                        {% for type in meeting_types %}
                                        <option value="{{ type.id }}" data-show-schedule="{{ type.show_schedule_applications|lower }}" {{ 'selected' if meeting.meeting_type_id == type.id else '' }}>
                                            {{ type.name }}
                                        </option>
                                        {% endfor %}
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Date *</label>
                                    <input type="date" class="form-control" name="meeting_date" value="{{ meeting.meeting_date.strftime('%Y-%m-%d') }}" required>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="mb-3">
                                    <label class="form-label">Meeting Time *</label>
                                    <input type="time" class="form-control" name="meeting_time" value="{{ meeting.meeting_time.strftime('%H:%M') }}" required>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-8">
                                <div class="mb-3">
                                    <label class="form-label">Location</label>
                                    <input type="text" class="form-control" name="location" value="{{ meeting.location or '' }}" placeholder="e.g., Council Chambers, Kesgrave Town Hall">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <div class="form-check mt-4">
                                        <input class="form-check-input" type="checkbox" name="is_published" id="is_published" {{ 'checked' if meeting.is_published else '' }}>
                                        <label class="form-check-label" for="is_published">
                                            Published
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label">Notes</label>
                            <textarea class="form-control" name="notes" rows="3" placeholder="Additional notes about the meeting">{{ meeting.notes or '' }}</textarea>
                        </div>
                    </div>
                </div>
                
                <!-- Documents -->
                <div class="card section-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-file-pdf me-2"></i>Meeting Documents</h5>
                    </div>
                    <div class="card-body">
                        <!-- Agenda -->
                        <div class="row mb-4">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Agenda (PDF)</label>
                                    {% if meeting.agenda_filename %}
                                    <div class="mb-2">
                                        <small class="text-muted">Current: {{ meeting.agenda_filename }}</small>
                                        <a href="/uploads/meetings/{{ meeting.agenda_filename }}" target="_blank" class="btn btn-sm btn-outline-primary ms-2">
                                            <i class="fas fa-eye"></i> View
                                        </a>
                                    </div>
                                    {% endif %}
                                    <input type="file" class="form-control" name="agenda_file" accept=".pdf">
                                    <small class="text-muted">Upload new agenda to replace current</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Agenda Title</label>
                                    <input type="text" class="form-control" name="agenda_title" value="{{ meeting.agenda_title or '' }}" placeholder="e.g., Meeting Agenda">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Agenda Description</label>
                                    <textarea class="form-control" name="agenda_description" rows="2" placeholder="Brief description of the agenda">{{ meeting.agenda_description or '' }}</textarea>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Minutes -->
                        <div class="row mb-4">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Minutes (PDF)</label>
                                    {% if meeting.minutes_filename %}
                                    <div class="mb-2">
                                        <small class="text-muted">Current: {{ meeting.minutes_filename }}</small>
                                        <a href="/uploads/meetings/{{ meeting.minutes_filename }}" target="_blank" class="btn btn-sm btn-outline-success ms-2">
                                            <i class="fas fa-eye"></i> View
                                        </a>
                                    </div>
                                    {% endif %}
                                    <input type="file" class="form-control" name="minutes_file" accept=".pdf">
                                    <small class="text-muted">Upload new minutes to replace current</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Minutes Title</label>
                                    <input type="text" class="form-control" name="minutes_title" value="{{ meeting.minutes_title or '' }}" placeholder="e.g., Meeting Minutes">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Minutes Description</label>
                                    <textarea class="form-control" name="minutes_description" rows="2" placeholder="Brief description of the minutes">{{ meeting.minutes_description or '' }}</textarea>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Draft Minutes -->
                        <div class="row mb-4">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Draft Minutes (PDF)</label>
                                    {% if meeting.draft_minutes_filename %}
                                    <div class="mb-2">
                                        <small class="text-muted">Current: {{ meeting.draft_minutes_filename }}</small>
                                        <a href="/uploads/meetings/{{ meeting.draft_minutes_filename }}" target="_blank" class="btn btn-sm btn-outline-warning ms-2">
                                            <i class="fas fa-eye"></i> View
                                        </a>
                                    </div>
                                    {% endif %}
                                    <input type="file" class="form-control" name="draft_minutes_file" accept=".pdf">
                                    <small class="text-muted">Upload draft meeting minutes</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Draft Minutes Title</label>
                                    <input type="text" class="form-control" name="draft_minutes_title" value="{{ meeting.draft_minutes_title or '' }}" placeholder="e.g., Draft Meeting Minutes">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Draft Minutes Description</label>
                                    <textarea class="form-control" name="draft_minutes_description" rows="2" placeholder="Brief description of the draft minutes">{{ meeting.draft_minutes_description or '' }}</textarea>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Schedule of Applications (conditional) -->
                        <div class="row mb-4" id="schedule-field" style="display: {{ 'block' if meeting.meeting_type.show_schedule_applications else 'none' }};">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Schedule of Applications (PDF)</label>
                                    {% if meeting.schedule_applications_filename %}
                                    <div class="mb-2">
                                        <small class="text-muted">Current: {{ meeting.schedule_applications_filename }}</small>
                                        <a href="/uploads/meetings/{{ meeting.schedule_applications_filename }}" target="_blank" class="btn btn-sm btn-outline-info ms-2">
                                            <i class="fas fa-eye"></i> View
                                        </a>
                                    </div>
                                    {% endif %}
                                    <input type="file" class="form-control" name="schedule_applications_file" accept=".pdf">
                                    <small class="text-muted">Upload new schedule to replace current</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Schedule Title</label>
                                    <input type="text" class="form-control" name="schedule_applications_title" value="{{ meeting.schedule_applications_title or '' }}" placeholder="e.g., Schedule of Applications">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Schedule Description</label>
                                    <textarea class="form-control" name="schedule_applications_description" rows="2" placeholder="Brief description of the schedule">{{ meeting.schedule_applications_description or '' }}</textarea>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Audio -->
                        <div class="row mb-4">
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Audio Recording</label>
                                    {% if meeting.audio_filename %}
                                    <div class="mb-2">
                                        <small class="text-muted">Current: {{ meeting.audio_filename }}</small>
                                        <a href="/uploads/meetings/{{ meeting.audio_filename }}" target="_blank" class="btn btn-sm btn-outline-secondary ms-2">
                                            <i class="fas fa-play"></i> Play
                                        </a>
                                    </div>
                                    {% endif %}
                                    <input type="file" class="form-control" name="audio_file" accept=".mp3,.wav,.m4a,.ogg">
                                    <small class="text-muted">Upload meeting audio recording</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Audio Title</label>
                                    <input type="text" class="form-control" name="audio_title" value="{{ meeting.audio_title or '' }}" placeholder="e.g., Meeting Recording">
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="mb-3">
                                    <label class="form-label">Audio Description</label>
                                    <textarea class="form-control" name="audio_description" rows="2" placeholder="Brief description of the audio recording">{{ meeting.audio_description or '' }}</textarea>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Summary URL -->
                        <div class="row mb-4">
                            <div class="col-md-12">
                                <div class="mb-3">
                                    <label class="form-label">Summary Page URL</label>
                                    <input type="url" class="form-control" name="summary_url" value="{{ meeting.summary_url or '' }}" placeholder="https://example.com/meeting-summary">
                                    <small class="text-muted">Link to external meeting summary page</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Submit -->
                <div class="d-flex gap-2">
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save me-2"></i>Update Meeting
                    </button>
                    <a href="/meetings" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            function updateScheduleField() {
                const select = document.querySelector('select[name="meeting_type_id"]');
                const scheduleField = document.getElementById('schedule-field');
                
                if (select.value) {
                    const option = select.options[select.selectedIndex];
                    const showSchedule = option.getAttribute('data-show-schedule') === 'true';
                    scheduleField.style.display = showSchedule ? 'block' : 'none';
                } else {
                    scheduleField.style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    ''', meeting=meeting, meeting_types=meeting_types)

@app.route('/meetings/delete/<int:meeting_id>', methods=['POST'])
@login_required
def delete_meeting(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    
    # Delete associated files
    if meeting.agenda_filename:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'meetings', meeting.agenda_filename))
        except:
            pass
    
    if meeting.minutes_filename:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'meetings', meeting.minutes_filename))
        except:
            pass
    
    if meeting.schedule_applications_filename:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'meetings', meeting.schedule_applications_filename))
        except:
            pass
    
    db.session.delete(meeting)
    db.session.commit()
    
    flash('Meeting deleted successfully!', 'success')
    return redirect(url_for('meetings_list'))



# Content Review System Route
@app.route('/content-review')
@login_required
def content_review_system():
    # Get filter parameters
    category_filter = request.args.get('category', '')
    subcategory_filter = request.args.get('subcategory', '')
    search_query = request.args.get('search', '')
    card_filter = request.args.get('filter', '')  # New parameter for card filtering
    
    # Base query for content pages
    query = ContentPage.query.join(ContentCategory, ContentPage.category_id == ContentCategory.id, isouter=True)\
                            .join(ContentSubcategory, ContentPage.subcategory_id == ContentSubcategory.id, isouter=True)
    
    # Apply filters
    if category_filter:
        query = query.filter(ContentPage.category_id == category_filter)
    
    if subcategory_filter:
        query = query.filter(ContentPage.subcategory_id == subcategory_filter)
    
    if search_query:
        query = query.filter(ContentPage.title.contains(search_query))
    
    # Get all content pages ordered by next_review_date (oldest first, nulls last)
    all_content_pages = query.order_by(ContentPage.next_review_date.asc().nullslast()).all()
    
    # Calculate summary statistics
    today = datetime.now().date()
    
    # Pages due in next 30 days
    due_30_days = []
    # Pages due in next 14 days  
    due_14_days = []
    # Pages due in next 7 days
    due_7_days = []
    # Pages that are past due
    past_due = []
    # Pages with no review date set
    no_review_date = []
    
    for page in all_content_pages:
        if page.next_review_date:
            review_date = page.next_review_date.date() if isinstance(page.next_review_date, datetime) else page.next_review_date
            days_until_review = (review_date - today).days
            
            if days_until_review < 0:
                past_due.append(page)
            elif days_until_review <= 7:
                due_7_days.append(page)
                due_14_days.append(page)
                due_30_days.append(page)
            elif days_until_review <= 14:
                due_14_days.append(page)
                due_30_days.append(page)
            elif days_until_review <= 30:
                due_30_days.append(page)
        else:
            no_review_date.append(page)
    
    # Apply card filtering
    if card_filter == '30days':
        content_pages = due_30_days
    elif card_filter == '14days':
        content_pages = due_14_days
    elif card_filter == '7days':
        content_pages = due_7_days
    elif card_filter == 'overdue':
        content_pages = past_due
    elif card_filter == 'no_date':
        content_pages = no_review_date
    else:
        content_pages = all_content_pages
    
    # Get categories and subcategories for filters
    categories = ContentCategory.query.filter_by(is_active=True).all()
    subcategories = ContentSubcategory.query.filter_by(is_active=True).all()
    
    # Helper function to calculate days until review
    def get_days_until_review(review_date):
        if not review_date:
            return "No review date set"
        
        review_date_obj = review_date.date() if isinstance(review_date, datetime) else review_date
        days_diff = (review_date_obj - today).days
        
        if days_diff < 0:
            return f"Overdue by {abs(days_diff)} day{'s' if abs(days_diff) != 1 else ''}"
        elif days_diff == 0:
            return "Due today"
        else:
            return f"Due in {days_diff} day{'s' if days_diff != 1 else ''}"
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Content Review System - Kesgrave CMS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            {{ sidebar_css|safe }}
            .summary-card {
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                cursor: pointer;
                border: none;
                text-decoration: none;
                color: inherit;
            }
            .summary-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                text-decoration: none;
                color: inherit;
            }
            .summary-card .card-body {
                padding: 1.5rem;
            }
            .summary-card .card-title {
                font-size: 2rem;
                font-weight: bold;
                margin-bottom: 0.5rem;
            }
            .summary-card .card-text {
                color: #6c757d;
                margin-bottom: 0;
            }
            .card-due-30 { border-left: 5px solid #17a2b8; }
            .card-due-14 { border-left: 5px solid #ffc107; }
            .card-due-7 { border-left: 5px solid #fd7e14; }
            .card-past-due { border-left: 5px solid #dc3545; }
            .card-no-date { border-left: 5px solid #6c757d; }
            .table-responsive {
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .status-badge {
                font-size: 0.75rem;
                padding: 0.25rem 0.5rem;
            }
            .overdue { color: #dc3545; font-weight: bold; }
            .due-soon { color: #fd7e14; font-weight: bold; }
            .due-later { color: #28a745; }
            .no-date { color: #6c757d; font-style: italic; }
        </style>
    </head>
    <body>
        {{ sidebar_html|safe }}
        
        <div class="main-content">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1><i class="fas fa-clipboard-check me-2"></i>Content Review System</h1>
                <div class="text-muted">{{ today.strftime('%d/%m/%Y') }}</div>
            </div>
            
            <!-- Summary Cards -->
            <div class="row mb-4">
                <div class="col-md-2">
                    <a href="?filter=30days" class="summary-card card-due-30 d-block">
                        <div class="card-body text-center">
                            <div class="text-info mb-2">
                                <i class="fas fa-calendar-alt fa-2x"></i>
                            </div>
                            <h3 class="card-title text-info">{{ due_30_count }}</h3>
                            <p class="card-text">Due in next 30 days</p>
                        </div>
                    </a>
                </div>
                <div class="col-md-2">
                    <a href="?filter=14days" class="summary-card card-due-14 d-block">
                        <div class="card-body text-center">
                            <div class="text-warning mb-2">
                                <i class="fas fa-exclamation-triangle fa-2x"></i>
                            </div>
                            <h3 class="card-title text-warning">{{ due_14_count }}</h3>
                            <p class="card-text">Due in next 14 days</p>
                        </div>
                    </a>
                </div>
                <div class="col-md-2">
                    <a href="?filter=7days" class="summary-card card-due-7 d-block">
                        <div class="card-body text-center">
                            <div class="text-orange mb-2" style="color: #fd7e14;">
                                <i class="fas fa-clock fa-2x"></i>
                            </div>
                            <h3 class="card-title" style="color: #fd7e14;">{{ due_7_count }}</h3>
                            <p class="card-text">Due in next 7 days</p>
                        </div>
                    </a>
                </div>
                <div class="col-md-2">
                    <a href="?filter=overdue" class="summary-card card-past-due d-block">
                        <div class="card-body text-center">
                            <div class="text-danger mb-2">
                                <i class="fas fa-exclamation-circle fa-2x"></i>
                            </div>
                            <h3 class="card-title text-danger">{{ past_due_count }}</h3>
                            <p class="card-text">Past due</p>
                        </div>
                    </a>
                </div>
                <div class="col-md-2">
                    <a href="?filter=no_date" class="summary-card card-no-date d-block">
                        <div class="card-body text-center">
                            <div class="text-muted mb-2">
                                <i class="fas fa-question-circle fa-2x"></i>
                            </div>
                            <h3 class="card-title text-muted">{{ no_date_count }}</h3>
                            <p class="card-text">No review date</p>
                        </div>
                    </a>
                </div>
                <div class="col-md-2">
                    <a href="/content-review" class="summary-card d-block" style="border-left: 5px solid #28a745;">
                        <div class="card-body text-center">
                            <div class="text-success mb-2">
                                <i class="fas fa-list fa-2x"></i>
                            </div>
                            <h3 class="card-title text-success">{{ total_count }}</h3>
                            <p class="card-text">All pages</p>
                        </div>
                    </a>
                </div>
            </div>
            
            <!-- Active Filter Display -->
            {% if card_filter %}
            <div class="alert alert-info mb-4">
                <i class="fas fa-filter me-2"></i>
                <strong>Active Filter:</strong> 
                {% if card_filter == '30days' %}Pages due in next 30 days
                {% elif card_filter == '14days' %}Pages due in next 14 days
                {% elif card_filter == '7days' %}Pages due in next 7 days
                {% elif card_filter == 'overdue' %}Pages past due
                {% elif card_filter == 'no_date' %}Pages with no review date
                {% endif %}
                <a href="/content-review" class="btn btn-sm btn-outline-secondary ms-2">
                    <i class="fas fa-times me-1"></i>Clear Filter
                </a>
            </div>
            {% endif %}
            
            <!-- Filters -->
            <div class="card mb-4">
                <div class="card-body">
                    <form method="GET" class="row g-3">
                        {% if card_filter %}
                        <input type="hidden" name="filter" value="{{ card_filter }}">
                        {% endif %}
                        <div class="col-md-3">
                            <label class="form-label">Category</label>
                            <select class="form-select" name="category" id="categoryFilter">
                                <option value="">All Categories</option>
                                {% for category in categories %}
                                <option value="{{ category.id }}" {{ 'selected' if category_filter == category.id|string else '' }}>
                                    {{ category.name }}
                                </option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Sub Category</label>
                            <select class="form-select" name="subcategory" id="subcategoryFilter">
                                <option value="">All Sub Categories</option>
                                {% for subcategory in subcategories %}
                                <option value="{{ subcategory.id }}" 
                                        data-category="{{ subcategory.category_id }}"
                                        {{ 'selected' if subcategory_filter == subcategory.id|string else '' }}
                                        style="display: {{ 'block' if not category_filter or category_filter == subcategory.category_id|string else 'none' }};">
                                    {{ subcategory.name }}
                                </option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">Search by Page Title</label>
                            <input type="text" class="form-control" name="search" value="{{ search_query }}" placeholder="Enter page title...">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label">&nbsp;</label>
                            <div class="d-grid">
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-search me-1"></i>Filter
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
            
            <!-- Data Table -->
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Content Pages Review Status ({{ content_pages|length }} pages)</h5>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th>Category</th>
                                    <th>Sub Category</th>
                                    <th>Page Title</th>
                                    <th>Status</th>
                                    <th>Created Date</th>
                                    <th>Review Date</th>
                                    <th>Days Until Review</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for page in content_pages %}
                                <tr>
                                    <td>
                                        {% if page.category %}
                                        <span class="badge" style="background-color: {{ page.category.color }};">
                                            {{ page.category.name }}
                                        </span>
                                        {% else %}
                                        <span class="text-muted">No Category</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if page.subcategory %}
                                        {{ page.subcategory.name }}
                                        {% else %}
                                        <span class="text-muted">No Sub Category</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <strong>{{ page.title }}</strong>
                                        {% if page.short_description %}
                                        <br><small class="text-muted">{{ page.short_description[:100] }}{% if page.short_description|length > 100 %}...{% endif %}</small>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <span class="badge status-badge 
                                            {% if page.status == 'Published' %}bg-success
                                            {% elif page.status == 'Draft' %}bg-warning
                                            {% else %}bg-secondary{% endif %}">
                                            {{ page.status }}
                                        </span>
                                    </td>
                                    <td>{{ page.creation_date.strftime('%d/%m/%Y') if page.creation_date else 'N/A' }}</td>
                                    <td>{{ page.next_review_date.strftime('%d/%m/%Y') if page.next_review_date else 'Not set' }}</td>
                                    <td>
                                        {% set days_text = get_days_until_review(page.next_review_date) %}
                                        <span class="
                                            {% if 'Overdue' in days_text %}overdue
                                            {% elif 'Due in' in days_text and (days_text.split()[2]|int) <= 7 %}due-soon
                                            {% elif 'No review date' in days_text %}no-date
                                            {% else %}due-later{% endif %}">
                                            {{ days_text }}
                                        </span>
                                    </td>
                                    <td>
                                        <a href="/content/edit/{{ page.id }}" class="btn btn-sm btn-outline-primary">
                                            <i class="fas fa-edit me-1"></i>Edit
                                        </a>
                                    </td>
                                </tr>
                                {% endfor %}
                                {% if not content_pages %}
                                <tr>
                                    <td colspan="8" class="text-center text-muted py-4">
                                        <i class="fas fa-inbox fa-2x mb-2"></i><br>
                                        No content pages found matching your criteria.
                                    </td>
                                </tr>
                                {% endif %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Dynamic subcategory filtering
            document.getElementById('categoryFilter').addEventListener('change', function() {
                const selectedCategory = this.value;
                const subcategorySelect = document.getElementById('subcategoryFilter');
                const subcategoryOptions = subcategorySelect.querySelectorAll('option');
                
                // Reset subcategory selection
                subcategorySelect.value = '';
                
                // Show/hide subcategory options based on selected category
                subcategoryOptions.forEach(option => {
                    if (option.value === '') {
                        option.style.display = 'block'; // Always show "All Sub Categories"
                    } else {
                        const optionCategory = option.getAttribute('data-category');
                        option.style.display = (selectedCategory === '' || selectedCategory === optionCategory) ? 'block' : 'none';
                    }
                });
            });
        </script>
    </body>
    </html>
    ''', 
    content_pages=content_pages,
    categories=categories,
    subcategories=subcategories,
    category_filter=category_filter,
    subcategory_filter=subcategory_filter,
    search_query=search_query,
    card_filter=card_filter,
    due_30_count=len(due_30_days),
    due_14_count=len(due_14_days),
    due_7_count=len(due_7_days),
    past_due_count=len(past_due),
    no_date_count=len(no_review_date),
    total_count=len(all_content_pages),
    today=today,
    get_days_until_review=get_days_until_review,
    sidebar_html=get_sidebar_html('content-review'),
    sidebar_css=get_sidebar_css()
    )