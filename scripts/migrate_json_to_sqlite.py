#!/usr/bin/env python3
"""
Migration script to import existing JSON data into SQLite database
Usage: python3 migrate_json_to_sqlite.py <database_dir> <json_hosts_file> <json_categories_file>
"""

import argparse
import json
import sqlite3
import os
from datetime import datetime
import sys

def convert_datetime_format(datetime_str):
    """Convert datetime from various formats to SQLite DATETIME format (YYYY-MM-DD HH:MM:SS)"""
    if not datetime_str:
        return None
    
    try:
        # Try parsing ISO format (with or without microseconds)
        if 'T' in datetime_str:
            if '.' in datetime_str:
                # Format: 2024-01-15T14:30:00.123456
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            else:
                # Format: 2024-01-15T14:30:00
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Already in the correct format or other format
            try:
                # Try parsing as existing SQLite format
                dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                return datetime_str  # Already in correct format
            except ValueError:
                # Try other common formats
                for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S']:
                    try:
                        dt = datetime.strptime(datetime_str, fmt)
                        return dt.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        continue
                
                # If all parsing fails, return None
                print(f"Warning: Could not parse datetime '{datetime_str}', setting to None")
                return None
    except Exception as e:
        print(f"Warning: Error converting datetime '{datetime_str}': {e}, setting to None")
        return None

def load_json(filename):
    """Load JSON data from file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filename} not found, skipping...")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing {filename}: {e}")
        return {}

def init_database(db_file):
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect(db_file)
    
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

def migrate_categories(db_file, categories_data):
    """Migrate categories from JSON to SQLite"""
    if not categories_data:
        print("No categories to migrate")
        return {}
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Mapping from old ID to new ID
    id_mapping = {}
    
    # Sort by original ID to maintain order
    sorted_categories = sorted(categories_data.items(), key=lambda x: int(x[0]))
    
    for old_id, category in sorted_categories:
        cursor.execute('''
            INSERT INTO categories (name, description)
            VALUES (?, ?)
        ''', (
            category.get('name', ''),
            category.get('description', '')
        ))
        
        new_id = cursor.lastrowid
        id_mapping[int(old_id)] = new_id
        print(f"Migrated category: {category.get('name')} (old ID: {old_id}, new ID: {new_id})")
    
    conn.commit()
    conn.close()
    
    print(f"Successfully migrated {len(categories_data)} categories")
    return id_mapping

def migrate_hosts(db_file, hosts_data, category_id_mapping):
    """Migrate hosts from JSON to SQLite"""
    if not hosts_data:
        print("No hosts to migrate")
        return
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Sort by original ID to maintain order
    sorted_hosts = sorted(hosts_data.items(), key=lambda x: int(x[0]))
    
    migrated_count = 0
    for old_id, host in sorted_hosts:
        # Map old category ID to new category ID
        category_id = None
        if host.get('category_id') and int(host['category_id']) in category_id_mapping:
            category_id = category_id_mapping[int(host['category_id'])]
        
        cursor.execute('''
            INSERT INTO hosts (name, url, location, notes, status, last_checked, icon, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            host.get('name', ''),
            host.get('url', ''),
            host.get('location', ''),
            host.get('notes', ''),
            host.get('status', 'unknown'),
            convert_datetime_format(host.get('last_checked')),
            host.get('icon'),
            category_id
        ))
        
        new_id = cursor.lastrowid
        print(f"Migrated host: {host.get('name')} (old ID: {old_id}, new ID: {new_id})")
        migrated_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"Successfully migrated {migrated_count} hosts")

def main():
    parser = argparse.ArgumentParser(description='Migrate JSON data to SQLite database')
    parser.add_argument('database_dir', help='Directory where SQLite database will be created')
    parser.add_argument('json_hosts_file', help='Path to JSON hosts file')
    parser.add_argument('json_categories_file', help='Path to JSON categories file')
    parser.add_argument('--force', action='store_true', help='Overwrite existing database')
    
    args = parser.parse_args()
    
    # Validate input files
    if not os.path.exists(args.json_hosts_file):
        print(f"Error: Hosts file {args.json_hosts_file} does not exist")
        sys.exit(1)
    
    if not os.path.exists(args.json_categories_file):
        print(f"Warning: Categories file {args.json_categories_file} does not exist, will create empty categories")
    
    # Create database directory if it doesn't exist
    if not os.path.exists(args.database_dir):
        os.makedirs(args.database_dir)
        print(f"Created database directory: {args.database_dir}")
    
    # Database file path
    db_file = os.path.join(args.database_dir, 'dashboard.db')
    
    # Check if database already exists
    if os.path.exists(db_file) and not args.force:
        response = input(f"Database {db_file} already exists. Overwrite? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Migration cancelled")
            sys.exit(0)
        os.remove(db_file)
    
    print("Starting migration...")
    print(f"Database: {db_file}")
    print(f"Hosts JSON: {args.json_hosts_file}")
    print(f"Categories JSON: {args.json_categories_file}")
    print("-" * 50)
    
    # Initialize database
    init_database(db_file)
    
    # Load JSON data
    print("Loading JSON data...")
    categories_data = load_json(args.json_categories_file)
    hosts_data = load_json(args.json_hosts_file)
    
    print(f"Found {len(categories_data)} categories and {len(hosts_data)} hosts in JSON files")
    
    # Migrate categories first (to get ID mapping)
    print("\nMigrating categories...")
    category_id_mapping = migrate_categories(db_file, categories_data)
    
    # Migrate hosts
    print("\nMigrating hosts...")
    migrate_hosts(db_file, hosts_data, category_id_mapping)
    
    print("\n" + "=" * 50)
    print("Migration completed successfully!")
    print(f"SQLite database created at: {db_file}")
    print("\nYou can now run the dashboard with:")
    print(f"python3 dashboard.py {args.database_dir}")

if __name__ == '__main__':
    main()
