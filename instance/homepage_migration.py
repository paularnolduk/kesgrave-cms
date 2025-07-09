#!/usr/bin/env python3
"""
Homepage CMS Database Migration Script
=====================================

This script adds the new homepage tables to your existing Kesgrave CMS database.
Run this script to update your database schema for the Homepage CMS functionality.

Usage:
    python homepage_migration.py

Requirements:
    - Your existing CMS database file (cms.db)
    - Python with SQLAlchemy installed
"""

import sqlite3
import os
from datetime import datetime

def create_homepage_tables():
    """Create the homepage tables in the existing database"""
    
    # Database file path (adjust if your database is in a different location)
    db_path = 'kesgrave_working.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file '{db_path}' not found!")
        print("Please make sure you're running this script from the same directory as your CMS database.")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Starting homepage tables migration...")
        
        # Create HomepageLogo table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS homepage_logo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                logo_image_filename VARCHAR(255),
                logo_text VARCHAR(200),
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created homepage_logo table")
        
        # Create HomepageHeaderLink table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS homepage_header_link (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link_name VARCHAR(100) NOT NULL,
                url VARCHAR(500) NOT NULL,
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created homepage_header_link table")
        
        # Create HomepageFooterColumn table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS homepage_footer_column (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                column_number INTEGER NOT NULL,
                column_title VARCHAR(100) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created homepage_footer_column table")
        
        # Create HomepageFooterLink table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS homepage_footer_link (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                footer_column_id INTEGER NOT NULL,
                link_name VARCHAR(100) NOT NULL,
                url VARCHAR(500) NOT NULL,
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (footer_column_id) REFERENCES homepage_footer_column (id)
            )
        ''')
        print("✅ Created homepage_footer_link table")
        
        # Create HomepageSlide table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS homepage_slide (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                introduction TEXT,
                image_filename VARCHAR(255),
                button_name VARCHAR(100),
                button_url VARCHAR(500),
                open_method VARCHAR(20) DEFAULT 'same_tab',
                is_featured BOOLEAN DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created homepage_slide table")
        
        # Create HomepageQuicklink table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS homepage_quicklink (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                button_name VARCHAR(100),
                button_url VARCHAR(500),
                open_method VARCHAR(20) DEFAULT 'same_tab',
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created homepage_quicklink table")
        
        # Insert default data
        print("🔄 Adding default homepage data...")
        
        # Insert default logo
        cursor.execute('''
            INSERT OR IGNORE INTO homepage_logo (logo_text, is_active)
            VALUES ('Kesgrave Town Council', 1)
        ''')
        
        # Insert default footer columns
        footer_columns = [
            (1, 'Quick Links'),
            (2, 'Services'), 
            (3, 'Information')
        ]
        
        for col_num, col_title in footer_columns:
            cursor.execute('''
                INSERT OR IGNORE INTO homepage_footer_column (column_number, column_title)
                VALUES (?, ?)
            ''', (col_num, col_title))
        
        # Insert default footer links
        footer_links = [
            # Column 1 - Quick Links
            (1, 'About Us', '/about', 0),
            (1, 'Contact', '/contact', 1),
            (1, 'News', '/news', 2),
            (1, 'Events', '/events', 3),
            # Column 2 - Services
            (2, 'Planning Applications', '/planning', 0),
            (2, 'Council Meetings', '/meetings', 1),
            (2, 'Community Groups', '/community', 2),
            (2, 'Local Facilities', '/facilities', 3),
            # Column 3 - Information
            (3, 'Council Tax', '/council-tax', 0),
            (3, 'Local History', '/history', 1),
            (3, 'Transport', '/transport', 2),
            (3, 'Emergency Info', '/emergency', 3)
        ]
        
        for col_num, link_name, url, sort_order in footer_links:
            cursor.execute('''
                INSERT OR IGNORE INTO homepage_footer_link 
                (footer_column_id, link_name, url, sort_order)
                SELECT id, ?, ?, ?
                FROM homepage_footer_column 
                WHERE column_number = ?
            ''', (link_name, url, sort_order, col_num))
        
        # Commit all changes
        conn.commit()
        print("✅ Default homepage data added")
        
        # Close connection
        conn.close()
        
        print("\n🎉 Homepage database migration completed successfully!")
        print("✅ All homepage tables have been created")
        print("✅ Default data has been inserted")
        print("\nYou can now use the Homepage CMS section in your admin panel.")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_upload_folders():
    """Create the required upload folders for homepage images"""
    
    folders = [
        'uploads/homepage',
        'uploads/homepage/logo',
        'uploads/homepage/slides'
    ]
    
    print("\n🔄 Creating upload folders...")
    
    for folder in folders:
        try:
            os.makedirs(folder, exist_ok=True)
            print(f"✅ Created folder: {folder}")
        except Exception as e:
            print(f"❌ Failed to create folder {folder}: {e}")
            return False
    
    print("✅ All upload folders created successfully!")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🏠 HOMEPAGE CMS DATABASE MIGRATION")
    print("=" * 60)
    print()
    
    # Step 1: Create database tables
    if create_homepage_tables():
        # Step 2: Create upload folders
        if create_upload_folders():
            print("\n" + "=" * 60)
            print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print()
            print("Next steps:")
            print("1. Replace your CMS file with the new version")
            print("2. Restart your CMS application")
            print("3. Access the Homepage section in the admin panel")
            print()
        else:
            print("\n❌ Migration failed during folder creation")
    else:
        print("\n❌ Migration failed during database update")

