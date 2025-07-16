#!/usr/bin/env python3
"""
Export SQLite database to JSON format
Usage: python3 export_sqlite_to_json.py <database_file> <output_directory>

This script exports the SQLite database back to JSON format, creating:
- hosts.json: Contains all host data
- categories.json: Contains all category data
"""

import argparse
import json
import sqlite3
import os
import sys
from datetime import datetime

def convert_sqlite_row_to_dict(row):
    """Convert SQLite Row object to dictionary with proper data types"""
    result = {}
    for key in row.keys():
        value = row[key]
        # Convert datetime strings back to ISO format for compatibility
        if key == 'last_checked' and value:
            try:
                # Parse SQLite datetime format and convert to ISO
                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                result[key] = dt.isoformat()
            except ValueError:
                # If parsing fails, keep original value
                result[key] = value
        else:
            result[key] = value
    return result

def export_categories(db_file):
    """Export categories from SQLite to dictionary format"""
    if not os.path.exists(db_file):
        print(f"Database file {db_file} does not exist.")
        return None
    
    print(f"Exporting categories from: {db_file}")
    
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if categories table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='categories'
        """)
        if not cursor.fetchone():
            print("No categories table found.")
            conn.close()
            return {}
        
        # Export categories
        cursor.execute("SELECT * FROM categories ORDER BY id")
        categories_rows = cursor.fetchall()
        
        categories_dict = {}
        for row in categories_rows:
            category_data = convert_sqlite_row_to_dict(row)
            # Use string ID as key for JSON compatibility
            categories_dict[str(category_data['id'])] = {
                'name': category_data['name'],
                'description': category_data.get('description', '')
            }
        
        conn.close()
        print(f"Exported {len(categories_dict)} categories")
        return categories_dict
        
    except Exception as e:
        print(f"Error exporting categories: {e}")
        return None

def export_hosts(db_file):
    """Export hosts from SQLite to dictionary format"""
    if not os.path.exists(db_file):
        print(f"Database file {db_file} does not exist.")
        return None
    
    print(f"Exporting hosts from: {db_file}")
    
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if hosts table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='hosts'
        """)
        if not cursor.fetchone():
            print("No hosts table found.")
            conn.close()
            return {}
        
        # Export hosts with category information
        cursor.execute("""
            SELECT h.*, c.name as category_name 
            FROM hosts h 
            LEFT JOIN categories c ON h.category_id = c.id
            ORDER BY h.id
        """)
        hosts_rows = cursor.fetchall()
        
        hosts_dict = {}
        for row in hosts_rows:
            host_data = convert_sqlite_row_to_dict(row)
            
            # Use string ID as key for JSON compatibility
            host_id = str(host_data['id'])
            
            # Build host entry in original JSON format
            hosts_dict[host_id] = {
                'name': host_data['name'],
                'url': host_data['url'],
                'location': host_data.get('location', ''),
                'notes': host_data.get('notes', ''),
                'status': host_data.get('status', 'unknown'),
                'last_checked': host_data.get('last_checked'),
                'icon': host_data.get('icon', ''),
                'category_id': host_data.get('category_id')
            }
            
            # Remove None values to keep JSON clean
            hosts_dict[host_id] = {k: v for k, v in hosts_dict[host_id].items() if v is not None}
        
        conn.close()
        print(f"Exported {len(hosts_dict)} hosts")
        return hosts_dict
        
    except Exception as e:
        print(f"Error exporting hosts: {e}")
        return None

def export_database_to_json(db_file, output_dir):
    """Export entire database to JSON files"""
    print(f"Starting export from database: {db_file}")
    print(f"Output directory: {output_dir}")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Export categories
    categories_data = export_categories(db_file)
    if categories_data is not None:
        categories_file = os.path.join(output_dir, 'categories.json')
        try:
            with open(categories_file, 'w', encoding='utf-8') as f:
                json.dump(categories_data, f, indent=2, ensure_ascii=False)
            print(f"Categories exported to: {categories_file}")
        except Exception as e:
            print(f"Error writing categories file: {e}")
            return False
    else:
        print("Failed to export categories")
        return False
    
    # Export hosts
    hosts_data = export_hosts(db_file)
    if hosts_data is not None:
        hosts_file = os.path.join(output_dir, 'hosts.json')
        try:
            with open(hosts_file, 'w', encoding='utf-8') as f:
                json.dump(hosts_data, f, indent=2, ensure_ascii=False)
            print(f"Hosts exported to: {hosts_file}")
        except Exception as e:
            print(f"Error writing hosts file: {e}")
            return False
    else:
        print("Failed to export hosts")
        return False
    
    return True

def export_database_summary(db_file):
    """Print a summary of the database contents"""
    print(f"\n=== Database Summary ===")
    print(f"Database: {db_file}")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Count categories
        try:
            cursor.execute("SELECT COUNT(*) FROM categories")
            categories_count = cursor.fetchone()[0]
            print(f"Categories: {categories_count}")
        except:
            print("Categories: 0 (table doesn't exist)")
        
        # Count hosts
        try:
            cursor.execute("SELECT COUNT(*) FROM hosts")
            hosts_count = cursor.fetchone()[0]
            print(f"Hosts: {hosts_count}")
            
            # Count by status
            cursor.execute("SELECT status, COUNT(*) FROM hosts GROUP BY status")
            status_counts = cursor.fetchall()
            for status, count in status_counts:
                print(f"  - {status}: {count}")
                
        except:
            print("Hosts: 0 (table doesn't exist)")
        
        conn.close()
        
    except Exception as e:
        print(f"Error reading database: {e}")
    
    print("========================\n")

def main():
    parser = argparse.ArgumentParser(description='Export SQLite database to JSON format')
    parser.add_argument('database_file', help='Path to the SQLite database file')
    parser.add_argument('output_directory', help='Directory to save the exported JSON files')
    parser.add_argument('--summary', action='store_true', help='Show database summary before export')
    
    args = parser.parse_args()
    
    # Validate database file exists
    if not os.path.exists(args.database_file):
        print(f"Error: Database file '{args.database_file}' does not exist.")
        sys.exit(1)
    
    # Show summary if requested
    if args.summary:
        export_database_summary(args.database_file)
    
    # Perform export
    if export_database_to_json(args.database_file, args.output_directory):
        print("\n✅ Export completed successfully!")
        print(f"Files created in: {os.path.abspath(args.output_directory)}")
        print("- categories.json")
        print("- hosts.json")
        
        # Show final summary
        export_database_summary(args.database_file)
        
        sys.exit(0)
    else:
        print("\n❌ Export failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
