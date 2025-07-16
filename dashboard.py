from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask import send_from_directory

import requests
import json
import os
import sys
import argparse
import yaml
from pprint import pprint
from datetime import datetime

# Import our database module
from database import create_database_instance


app = Flask(__name__)

# Global variables for configuration and database
CONFIG = None
DATABASE_DIR = None
UPLOAD_FOLDER = None
DATABASE_FILE = None
db = None  # Database instance

# Default configuration values
DEFAULT_CONFIG = {
    'app': {
        'name': 'Dashboard',
        'max_upload_size': 5,
        'allowed_extensions': ['png', 'jpg', 'jpeg', 'gif', 'svg'],
        'health_check_timeout': 5
    },
    'database': {
        'file': './dashboard_data/dashboard.db',
        'icons_dir': 'icons'
    },
    'server': {
        'host': '0.0.0.0',
        'port': 8003,
        'debug': True
    }
}

KEY_ICON='icon' 

def clean_text_input(text):
    """Clean and escape text input for safe storage"""
    if not text:
        return ""
    
    # Strip whitespace
    text = text.strip()
    
    # Replace problematic characters that might cause issues
    replacements = {
        '\r\n': '\n',  # Normalize line endings
        '\r': '\n',    # Normalize line endings
        '\x00': '',    # Remove null bytes
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def allowed_file(filename):
    allowed_extensions = set(CONFIG['app']['allowed_extensions'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def file_extension(filename):
    fname, fextension = os.path.splitext(filename)
    return fextension


@app.route('/')
def index():
    hosts = db.get_all_hosts()
    
    for host in hosts:
        tooltip = "<b>Notes:</b><br> " + (host['notes'] if host['notes'] else 'No notes') + "<br>"
        # Add placeholder for last checked time - will be updated by JavaScript
        if host['last_checked']:
            tooltip += "<b>Last checked:</b><br><span class='relative-time'>Loading...</span>"
        host['tooltip'] = tooltip

    return render_template('index.html', hosts=hosts, dashboard_name=CONFIG['app']['name'])



@app.route('/update_host/<host_id>', methods=['GET', 'POST'])
def update_host(host_id):
    host_id = int(host_id)

    if request.method == 'POST':
        name = clean_text_input(request.form['name'])
        url = clean_text_input(request.form['url'])
        notes = clean_text_input(request.form['notes'])
        location = clean_text_input(request.form['location'])
        category_id = request.form.get('category_id')

        host_data = {
            'name': name,
            'url': url,
            'notes': notes,
            'location': location,
            'status': 'unknown',
            'last_checked': None
        }
        
        # Only add category if one is selected
        if category_id and category_id != '':
            host_data['category_id'] = int(category_id)

        # Handle icon upload
        if KEY_ICON in request.files:
            iconFile = request.files[KEY_ICON]
            if iconFile and iconFile.filename != '' and allowed_file(iconFile.filename):
                # Generate filename
                if host_id == 0:
                    # For new hosts, we need to save first to get the ID
                    saved_host_id = db.save_host(host_data)
                    saved_filename = str(saved_host_id) + file_extension(iconFile.filename)
                else:
                    # For updates, delete the old icon file first
                    existing_host = db.get_host_by_id(host_id)
                    if existing_host and existing_host.get('icon'):
                        old_icon_path = os.path.join(UPLOAD_FOLDER, existing_host['icon'])
                        try:
                            os.remove(old_icon_path)
                            print(f'Deleted old icon: {existing_host["icon"]}')
                        except FileNotFoundError:
                            pass
                    
                    saved_filename = str(host_id) + file_extension(iconFile.filename)
                    saved_host_id = host_id

                # Save the file
                path = os.path.join(UPLOAD_FOLDER, saved_filename)
                iconFile.save(path)
                host_data['icon'] = saved_filename
                
                # Update the host with icon info
                db.save_host(host_data, saved_host_id)
            else:
                # No new icon, just save the host
                if host_id == 0:
                    db.save_host(host_data)
                else:
                    # Keep existing icon for updates
                    existing_host = db.get_host_by_id(host_id)
                    if existing_host and existing_host.get('icon'):
                        host_data['icon'] = existing_host['icon']
                    db.save_host(host_data, host_id)
        else:
            # No icon file in form
            if host_id == 0:
                db.save_host(host_data)
            else:
                # Keep existing icon for updates
                existing_host = db.get_host_by_id(host_id)
                if existing_host and existing_host.get('icon'):
                    host_data['icon'] = existing_host['icon']
                db.save_host(host_data, host_id)

        return redirect(url_for('index'))
    
    # GET request - show form
    if host_id != 0:
        existing_host = db.get_host_by_id(host_id)
        print('Editing existing host')
    else:
        existing_host = {'id': 0}
    
    print(existing_host)

    categories = db.get_all_categories()
    return render_template('update_host.html', host=existing_host, categories=categories, dashboard_name=CONFIG['app']['name'])


@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files (CSS, JS, etc.)"""
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    return send_from_directory(static_dir, filename)


@app.route('/img/<path:fname>')
def send_image(fname):
    #print(f'Wants an image: {fname}')
    return send_from_directory(UPLOAD_FOLDER, fname, as_attachment=False)


@app.route('/delete_host/<host_id>', endpoint='delete_host')
def delete_host_route(host_id):
    host = db.get_host_by_id(int(host_id))
    
    if host and host.get('icon'):
        path = os.path.join(UPLOAD_FOLDER, host['icon'])
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

    db.delete_host(int(host_id))
    return redirect(url_for('index'))


@app.route('/categories')
def categories():
    categories = db.get_all_categories()
    return render_template('categories.html', categories=categories, dashboard_name=CONFIG['app']['name'])

@app.route('/update_category/<category_id>', methods=['GET', 'POST'])
def update_category(category_id):
    category_id = int(category_id)

    if request.method == 'POST':
        name = clean_text_input(request.form['name'])
        description = clean_text_input(request.form['description'])

        category_data = {
            'name': name,
            'description': description
        }

        db.save_category(category_data, category_id if category_id != 0 else None)
        return redirect(url_for('categories'))
    
    if category_id != 0:
        existing_category = db.get_category_by_id(category_id)
        print('Editing existing category')
    else:
        existing_category = {'id': 0}
    
    print(existing_category)
    return render_template('update_category.html', category=existing_category, dashboard_name=CONFIG['app']['name'])

@app.route('/delete_category/<category_id>', endpoint='delete_category')
def delete_category_route(category_id):
    db.delete_category(int(category_id))
    return redirect(url_for('categories'))


def load_config(config_file):
    """Load configuration from YAML file"""
    global CONFIG
    
    try:
        with open(config_file, 'r') as f:
            CONFIG = yaml.safe_load(f)
        
        # Merge with defaults for any missing keys
        def merge_config(default, loaded):
            for key, value in default.items():
                if key not in loaded:
                    loaded[key] = value
                elif isinstance(value, dict) and isinstance(loaded[key], dict):
                    merge_config(value, loaded[key])
        
        merge_config(DEFAULT_CONFIG, CONFIG)
        
        print(f'Configuration loaded from: {config_file}')
        return True
        
    except FileNotFoundError:
        print(f'Error: Configuration file not found: {config_file}')
        return False
    except yaml.YAMLError as e:
        print(f'Error: Invalid YAML in configuration file: {e}')
        return False
    except Exception as e:
        print(f'Error loading configuration: {e}')
        return False


def init_paths():
    """Initialize the global path variables based on the configuration"""
    global DATABASE_DIR, UPLOAD_FOLDER, DATABASE_FILE, db
    
    DATABASE_FILE = os.path.abspath(CONFIG['database']['file'])
    DATABASE_DIR = os.path.dirname(DATABASE_FILE)
    UPLOAD_FOLDER = os.path.join(DATABASE_DIR, CONFIG['database']['icons_dir'])
    
    # Create directories if they don't exist
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR)
        print(f'Created database directory: {DATABASE_DIR}')
    
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        print(f'Created icons directory: {UPLOAD_FOLDER}')
    
    # Set Flask config
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = CONFIG['app']['max_upload_size'] * 1024 * 1024  # Convert MB to bytes
    
    # Initialize database
    db = create_database_instance(DATABASE_FILE)
    
    print(f'Database directory: {DATABASE_DIR}')
    print(f'Icons folder: {UPLOAD_FOLDER}')
    print(f'Database file: {DATABASE_FILE}')


# Health check functionality
def check_host_status(url):
    """Check if a host is reachable"""
    timeout = CONFIG['app']['health_check_timeout']
    try:
        # Remove any trailing slashes and handle different URL formats
        clean_url = url.rstrip('/')
        if not clean_url.startswith(('http://', 'https://')):
            # Try both http and https
            for protocol in ['http://', 'https://']:
                try:
                    test_url = protocol + clean_url
                    response = requests.get(test_url, timeout=timeout)
                    return 'online' if response.status_code < 400 else 'offline'
                except:
                    continue
            return 'offline'
        else:
            response = requests.get(clean_url, timeout=timeout)
            return 'online' if response.status_code < 400 else 'offline'
    except:
        return 'offline'

@app.route('/check_host/<host_id>')
def check_single_host(host_id):
    """Check status of a single host"""
    host = db.get_host_by_id(int(host_id))
    if host and host['url']:
        status = check_host_status(host['url'])
        last_checked = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.update_host_status(int(host_id), status, last_checked)
    return redirect(url_for('index'))

@app.route('/check_all_hosts')
def check_all_hosts():
    """Check status of all hosts"""
    hosts = db.get_all_hosts()
    checked_count = 0
    online_count = 0
    offline_count = 0
    
    for host in hosts:
        if host['url']:
            status = check_host_status(host['url'])
            last_checked = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.update_host_status(host['id'], status, last_checked)
            checked_count += 1
            
            if status == 'online':
                online_count += 1
            else:
                offline_count += 1
    
    # Check if this is an AJAX request by looking for XMLHttpRequest header or JSON accept header
    is_ajax = (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('Accept', '') or
        request.args.get('ajax') == '1'
    )
    
    if is_ajax:
        return jsonify({
            'success': True,
            'checked': checked_count,
            'online': online_count,
            'offline': offline_count,
            'message': f'Checked {checked_count} hosts: {online_count} online, {offline_count} offline'
        })
    else:
        # Regular browser request - redirect as before
        return redirect(url_for('index'))

@app.route('/open_host/<host_id>')
def open_host(host_id):
    """Redirect to host URL"""
    host = db.get_host_by_id(int(host_id))
    if host and host.get('url'):
        url = host['url']
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        return redirect(url)
    return redirect(url_for('index'))

@app.route('/locations')
def get_locations():
    """Get all unique locations from existing hosts"""
    locations = db.get_unique_locations()
    
    # Return as a list of objects with value and text properties for tom-select
    location_list = [{'value': loc, 'text': loc} for loc in locations]
    return jsonify({'locations': location_list})


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Network Dashboard Management System')
    parser.add_argument('config_file', help='YAML configuration file path')
    
    args = parser.parse_args()
    
    # Load configuration from YAML file
    if not load_config(args.config_file):
        sys.exit(1)
    
    # Initialize paths and database
    init_paths()
    
    # Initialize database tables
    db.init_database()
    
    # Log database contents on startup
    try:
        hosts = db.get_all_hosts()
        categories = db.get_all_categories()
        print(f"Database loaded: {len(hosts)} hosts, {len(categories)} categories")       

    except Exception as e:
        print(f"Warning: Could not load database statistics: {e}")

    # Start the Flask app
    app.run(
        debug=CONFIG['server']['debug'],
        host=CONFIG['server']['host'],
        port=CONFIG['server']['port']
    )