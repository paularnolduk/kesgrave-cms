#!/usr/bin/env python3

"""
Database Update Script for Meetings Enhancement
This script adds the new fields to the Meeting table that were added for the enhanced functionality.
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def update_database():
    try:
        from cms_final_complete import app, db
        from sqlalchemy import text
        
        with app.app_context():
            print("🔄 Updating Meeting table with new fields...")
            
            # List of new fields to add
            new_fields = [
                "agenda_title TEXT",
                "agenda_description TEXT", 
                "minutes_title TEXT",
                "minutes_description TEXT",
                "draft_minutes_filename TEXT",
                "draft_minutes_title TEXT",
                "draft_minutes_description TEXT",
                "schedule_applications_title TEXT", 
                "schedule_applications_description TEXT",
                "audio_filename TEXT",
                "audio_title TEXT",
                "audio_description TEXT",
                "summary_url TEXT"
            ]
            
            # Check which fields already exist
            existing_fields = []
            try:
                result = db.session.execute(text("PRAGMA table_info(meeting)"))
                existing_columns = [row[1] for row in result.fetchall()]
                print(f"📋 Existing columns: {existing_columns}")
            except Exception as e:
                print(f"⚠️  Could not check existing columns: {e}")
                existing_columns = []
            
            # Add each new field if it doesn't exist
            added_fields = []
            for field in new_fields:
                field_name = field.split()[0]
                if field_name not in existing_columns:
                    try:
                        db.session.execute(text(f"ALTER TABLE meeting ADD COLUMN {field}"))
                        added_fields.append(field_name)
                        print(f"✅ Added field: {field_name}")
                    except Exception as e:
                        print(f"⚠️  Could not add field {field_name}: {e}")
                else:
                    print(f"⏭️  Field {field_name} already exists, skipping")
            
            # Commit all changes
            if added_fields:
                db.session.commit()
                print(f"🎉 Successfully added {len(added_fields)} new fields to Meeting table!")
                print(f"📝 Added fields: {', '.join(added_fields)}")
            else:
                print("✅ All fields already exist, no updates needed!")
                
            # Verify the update
            print("\n🔍 Verifying updated table structure...")
            result = db.session.execute(text("PRAGMA table_info(meeting)"))
            all_columns = [row[1] for row in result.fetchall()]
            print(f"📊 Total columns in meeting table: {len(all_columns)}")
            
            # Check for the new fields
            new_field_names = [field.split()[0] for field in new_fields]
            missing_fields = [field for field in new_field_names if field not in all_columns]
            
            if missing_fields:
                print(f"❌ Missing fields: {missing_fields}")
                return False
            else:
                print("✅ All required fields are present!")
                return True
                
    except ImportError as e:
        print(f"❌ Could not import CMS modules: {e}")
        print("Make sure you're running this script from the CMS directory.")
        return False
    except Exception as e:
        print(f"❌ Database update failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_meetings_functionality():
    """Test if the meetings functionality works after database update"""
    try:
        from cms_final_complete import app, Meeting, MeetingType
        
        with app.app_context():
            print("\n🧪 Testing meetings functionality...")
            
            # Test querying meetings
            meetings = Meeting.query.all()
            print(f"📊 Found {len(meetings)} meetings in database")
            
            # Test querying meeting types
            meeting_types = MeetingType.query.filter_by(is_active=True).all()
            print(f"📋 Found {len(meeting_types)} active meeting types")
            
            if len(meeting_types) == 0:
                print("⚠️  No meeting types found. You may need to run the meeting types initialization.")
                print("💡 Try running: python3 -c \"from cms_final_complete import *; init_meeting_types()\"")
            
            print("✅ Meetings functionality test passed!")
            return True
            
    except Exception as e:
        print(f"❌ Meetings functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/debug-routes')
def debug_routes():
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    meeting_routes = [r for r in routes if 'meeting' in r]
    return f"All routes: {len(routes)}<br>Meeting routes: {meeting_routes}"


if __name__ == "__main__":
    print("🚀 Starting Meetings Database Update...")
    print("=" * 50)
    
    # Update database
    if update_database():
        print("\n" + "=" * 50)
        # Test functionality
        if test_meetings_functionality():
            print("\n🎉 SUCCESS! Meetings enhancement is ready to use!")
            print("\n📝 Next steps:")
            print("1. Restart your CMS application")
            print("2. Navigate to /meetings in your browser")
            print("3. Enjoy the enhanced meetings functionality!")
        else:
            print("\n⚠️  Database updated but functionality test failed.")
            print("Please check the error messages above.")
    else:
        print("\n❌ Database update failed. Please check the error messages above.")

