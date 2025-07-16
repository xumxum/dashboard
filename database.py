"""
Database operations module for the dashboard application.
Handles all SQLite database interactions for hosts and categories.
"""

import sqlite3
import os
from datetime import datetime


class DashboardDatabase:
    """Database class to handle all SQLite operations for the dashboard"""
    
    def __init__(self, db_file):
        self.db_file = db_file
    
    def get_connection(self):
        """Get database connection with Row factory"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        conn = self.get_connection()
        
        # Create categories table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT
            )
        ''')
        
        # Create hosts table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                location TEXT,
                notes TEXT,
                status TEXT DEFAULT 'unknown',
                last_checked DATETIME,
                icon TEXT,
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Database initialized successfully")
    
    # Host operations
    def get_all_hosts(self):
        """Get all hosts from database"""
        conn = self.get_connection()
        hosts = conn.execute('''
            SELECT h.*, c.name as category_name 
            FROM hosts h 
            LEFT JOIN categories c ON h.category_id = c.id
            ORDER BY h.name
        ''').fetchall()
        conn.close()
        return [dict(host) for host in hosts]
    
    def get_host_by_id(self, host_id):
        """Get a single host by ID"""
        conn = self.get_connection()
        host = conn.execute('SELECT * FROM hosts WHERE id = ?', (host_id,)).fetchone()
        conn.close()
        return dict(host) if host else None
    
    def save_host(self, host_data, host_id=None):
        """Save or update a host"""
        conn = self.get_connection()
        
        if host_id and host_id != 0:
            # Update existing host
            conn.execute('''
                UPDATE hosts 
                SET name=?, url=?, location=?, notes=?, category_id=?, icon=?
                WHERE id=?
            ''', (
                host_data['name'], host_data['url'], host_data['location'], 
                host_data['notes'], host_data.get('category_id'), 
                host_data.get('icon'), host_id
            ))
        else:
            # Insert new host
            cursor = conn.execute('''
                INSERT INTO hosts (name, url, location, notes, status, last_checked, icon, category_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                host_data['name'], host_data['url'], host_data['location'], 
                host_data['notes'], host_data.get('status', 'unknown'), 
                host_data.get('last_checked'), host_data.get('icon'),
                host_data.get('category_id')
            ))
            host_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return host_id
    
    def delete_host(self, host_id):
        """Delete a host"""
        conn = self.get_connection()
        conn.execute('DELETE FROM hosts WHERE id = ?', (host_id,))
        conn.commit()
        conn.close()
    
    def update_host_status(self, host_id, status, last_checked):
        """Update host status and last checked time"""
        conn = self.get_connection()
        conn.execute('''
            UPDATE hosts 
            SET status=?, last_checked=?
            WHERE id=?
        ''', (status, last_checked, host_id))
        conn.commit()
        conn.close()
    
    def get_unique_locations(self):
        """Get all unique locations from hosts"""
        conn = self.get_connection()
        locations = conn.execute('''
            SELECT DISTINCT location 
            FROM hosts 
            WHERE location IS NOT NULL AND location != ''
            ORDER BY location
        ''').fetchall()
        conn.close()
        return [row['location'] for row in locations]
    
    # Category operations
    def get_all_categories(self):
        """Get all categories from database"""
        conn = self.get_connection()
        categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
        conn.close()
        return [dict(cat) for cat in categories]
    
    def get_category_by_id(self, category_id):
        """Get a single category by ID"""
        conn = self.get_connection()
        category = conn.execute('SELECT * FROM categories WHERE id = ?', (category_id,)).fetchone()
        conn.close()
        return dict(category) if category else None
    
    def save_category(self, category_data, category_id=None):
        """Save or update a category"""
        conn = self.get_connection()
        
        if category_id and category_id != 0:
            # Update existing category
            conn.execute('''
                UPDATE categories 
                SET name=?, description=?
                WHERE id=?
            ''', (category_data['name'], category_data['description'], category_id))
        else:
            # Insert new category
            cursor = conn.execute('''
                INSERT INTO categories (name, description)
                VALUES (?, ?)
            ''', (category_data['name'], category_data['description']))
            category_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return category_id
    
    def delete_category(self, category_id):
        """Delete a category"""
        conn = self.get_connection()
        conn.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()
        conn.close()


# Factory function to create database instance
def create_database_instance(db_file):
    """Factory function to create a DashboardDatabase instance"""
    return DashboardDatabase(db_file)
