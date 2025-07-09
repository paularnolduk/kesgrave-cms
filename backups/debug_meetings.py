#!/usr/bin/env python3

"""
Debug script to isolate the meetings route issue
"""

def debug_meetings_issue():
    print("🔍 Debugging Meetings Route Issue")
    print("=" * 50)
    
    try:
        # Test 1: Import the app
        print("1️⃣ Testing app import...")
        from cms_final_complete import app
        print("✅ App imported successfully")
        
        # Test 2: Check route registration
        print("\n2️⃣ Checking route registration...")
        with app.app_context():
            meeting_routes = []
            all_routes = []
            for rule in app.url_map.iter_rules():
                all_routes.append(rule.rule)
                if 'meeting' in rule.rule:
                    meeting_routes.append(f"{rule.rule} -> {rule.endpoint}")
            
            print(f"📊 Total routes registered: {len(all_routes)}")
            if meeting_routes:
                print("✅ Meeting routes found:")
                for route in meeting_routes:
                    print(f"   📍 {route}")
            else:
                print("❌ No meeting routes found!")
                print("🔍 All routes:")
                for route in sorted(all_routes)[:20]:  # Show first 20 routes
                    print(f"   📍 {route}")
        
        # Test 3: Test the route with test client
        print("\n3️⃣ Testing route with test client...")
        with app.test_client() as client:
            response = client.get('/meetings')
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 404:
                print("❌ 404 Error - Route not found!")
                # Try to access a known working route
                dashboard_response = client.get('/dashboard')
                print(f"📊 Dashboard route status: {dashboard_response.status_code}")
            elif response.status_code == 302:
                print("✅ 302 Redirect - Route working (login required)")
                print(f"📍 Redirect to: {response.headers.get('Location', 'Unknown')}")
            else:
                print(f"📊 Unexpected status: {response.status_code}")
        
        # Test 4: Check if function exists
        print("\n4️⃣ Checking if meetings_list function exists...")
        try:
            from cms_final_complete import meetings_list
            print("✅ meetings_list function found")
            print(f"📍 Function: {meetings_list}")
        except ImportError as e:
            print(f"❌ meetings_list function not found: {e}")
        
        # Test 5: Check file size and modification time
        print("\n5️⃣ Checking file information...")
        import os
        import time
        
        file_path = 'cms_final_complete.py'
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            mod_time = os.path.getmtime(file_path)
            mod_time_str = time.ctime(mod_time)
            print(f"📄 File size: {file_size:,} bytes")
            print(f"🕒 Last modified: {mod_time_str}")
        else:
            print("❌ CMS file not found!")
            
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

def create_minimal_test_server():
    """Create a minimal test server with just the meetings route"""
    print("\n🧪 Creating minimal test server...")
    
    try:
        from flask import Flask, render_template_string
        
        test_app = Flask(__name__)
        test_app.secret_key = 'test_key'
        
        @test_app.route('/test-meetings')
        def test_meetings():
            return render_template_string('''
            <html>
            <head><title>Test Meetings</title></head>
            <body>
                <h1>🎉 Test Meetings Route Working!</h1>
                <p>If you can see this, the meetings route functionality is working.</p>
            </body>
            </html>
            ''')
        
        # Test the minimal route
        with test_app.test_client() as client:
            response = client.get('/test-meetings')
            if response.status_code == 200:
                print("✅ Minimal test route working")
                return True
            else:
                print(f"❌ Minimal test route failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Minimal test failed: {e}")
        return False

if __name__ == "__main__":
    debug_meetings_issue()
    create_minimal_test_server()
    
    print("\n" + "=" * 50)
    print("🎯 DIAGNOSIS COMPLETE")
    print("\n💡 If the routes are registered but you still get 404:")
    print("1. Make sure you've completely stopped and restarted your Flask app")
    print("2. Check if you have multiple Python processes running")
    print("3. Try running: pkill -f cms_final_complete.py")
    print("4. Then start fresh: python3 cms_final_complete.py")
    print("5. Make sure you're accessing the correct port")

