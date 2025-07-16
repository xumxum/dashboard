# ZeeNet2 Dashboard

A modern, responsive network dashboard for monitoring and managing hosts with dark/light theme support.

![Dashboard Screenshot](https://img.shields.io/badge/status-active-brightgreen.svg)
![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)
![Bootstrap](https://img.shields.io/badge/bootstrap-5.3+-purple.svg)

## ✨ Features

### 🎯 **Core Functionality**
- **Host Management**: Add, edit, delete, and organize network hosts
- **Categories**: Group hosts by type, location, or purpose
- **Health Checking**: Monitor host availability with HTTP/HTTPS checks
- **Status Indicators**: Visual online/offline/unknown status badges
- **Custom Icons**: Upload custom icons or use FontAwesome icons

### 🎨 **User Experience**
- **Modern UI**: Clean, card-based interface with hover effects
- **Dark/Light Theme**: Toggle between themes with persistence
- **Real-time Search**: Filter hosts by name, URL, location, or notes
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Tooltips**: Hover information with notes and last check time

### 🔧 **Technical Features**
- **SQLite Database**: Reliable, fast database storage with ACID compliance
- **Icon Management**: Automatic cleanup of unused icon files
- **Input Validation**: Text sanitization and validation
- **Static Assets**: Centralized CSS/JS for maintainability

## 📋 Prerequisites

- Python 3.7 or higher
- Web browser with JavaScript enabled
- Network access to hosts you want to monitor

## 🚀 Quick Start

### 1. Clone or Download
```bash
# If using git
git clone <repository-url>
cd dashboard

# Or download and extract the files
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure the Dashboard
Copy and customize the configuration file:
```bash
cp config.yaml my_config.yaml
# Edit my_config.yaml with your preferred settings
```

### 4. Run the Dashboard
```bash
python dashboard.py my_config.yaml
```

### 5. Access the Dashboard
Open your browser and navigate to:
```
http://localhost:8003
```

## 📖 Usage

### Command Line Usage
```bash
python dashboard.py <config_file>

Required:
  config_file           YAML configuration file path

Examples:
  python dashboard.py config.yaml
  python dashboard.py /path/to/my_dashboard_config.yaml
```

## 🏗️ Project Structure

```
dashboard/
├── dashboard.py              # Main Flask application
├── database.py              # Database operations module
├── config.yaml              # Sample configuration file
├── dashboard.service         # Systemd service file
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── todo.md                  # Feature roadmap
├── scripts/                 # Database migration scripts
│   ├── migrate_json_to_sqlite.py  # JSON to SQLite migration
│   └── export_sqlite_to_json.py   # SQLite to JSON export
├── static/                  # Static assets
│   ├── css/
│   │   └── dashboard-theme.css  # Centralized theme styles
│   └── js/
│       └── dashboard-theme.js   # Theme functionality
└── templates/               # HTML templates
    ├── index.html          # Main dashboard
    ├── categories.html     # Category management
    ├── update_host.html    # Add/edit host form
    └── update_category.html # Add/edit category form
```

## 🎨 Themes

The dashboard supports both light and dark themes:

### Light Theme (Default)
- Clean white background
- Dark text for readability
- Subtle shadows and borders

### Dark Theme
- Dark background (#1a1a1a)
- Light text (#e9ecef)
- Enhanced contrast for night viewing

**Theme persistence**: Your choice is saved in browser localStorage and persists across sessions.

## 🔧 Configuration

### YAML Configuration File
The dashboard uses a YAML configuration file for all settings. Copy the sample `config.yaml` and customize it:

```yaml
# Application configuration
app:
  name: "Dashboard"                # Dashboard name (browser title/headers)
  max_upload_size: 5              # Max icon upload size (MB)
  allowed_extensions:             # Allowed icon file types
    - png
    - jpg
    - jpeg
    - gif 
    - svg
  health_check_timeout: 5         # Health check timeout (seconds)

# Database and storage configuration
database:
  file: "./dashboard_data/dashboard.db"  # Full path to SQLite database
  icons_dir: "icons"                     # Icons folder (relative to DB location)

# Web server configuration  
server:
  host: "0.0.0.0"                 # Bind to all interfaces
  port: 8003                      # Web server port
  debug: true                     # Enable debug mode
```

### Data Storage
The dashboard creates the following structure based on your configuration:
```
your_data_directory/
├── dashboard.db         # SQLite database (hosts and categories)
└── icons/              # Uploaded host icons
    ├── 1.png
    ├── 2.jpg
    └── ...
```

### Database Migration
If migrating from the old JSON format, use the migration script:
```bash
cd scripts
python migrate_json_to_sqlite.py ../config.yaml hosts.json categories.json
```

To export back to JSON format:
```bash
cd scripts
python export_sqlite_to_json.py ../config.yaml ./exported_json/
```

### Database Backup
To backup your dashboard data, simply copy the SQLite database file:
```bash
cp /path/to/data/directory/dashboard.db /path/to/backup/dashboard_backup_$(date +%Y%m%d_%H%M%S).db
```
Don't forget to also backup the icons directory if you have custom icons.

### Categories
Create categories to organize your hosts:
- **Network**: Routers, switches, access points
- **Media**: NAS, streaming devices, smart TVs
- **IoT**: Smart home devices, sensors
- **Servers**: Web servers, databases, services

### Host Icons
Two ways to add icons:
1. **Upload**: Custom PNG, JPG, GIF, or SVG files
2. **FontAwesome**: Use FA classes like `fa-server`, `fa-router`, `fa-desktop`

## 🔍 Health Checking

The dashboard can check host availability:

### Supported Protocols
- **HTTP**: Automatic protocol detection
- **HTTPS**: SSL/TLS support
- **Auto-detection**: Tries both HTTP and HTTPS

### Check Behavior
- **Timeout**: 5 seconds per request
- **Success**: HTTP status < 400
- **Individual**: Check single host
- **Bulk**: Check all hosts at once

### Status Indicators
- 🟢 **Online**: Host responded successfully
- 🔴 **Offline**: Host unreachable or error
- ⚪ **Unknown**: Not yet checked

## 🛠️ Development

### Adding Features
1. **Backend**: Modify `dashboard.py` for new routes/functionality
2. **Database**: Update `database.py` for new database operations
3. **Frontend**: Update templates in `templates/`
4. **Styling**: Modify `static/css/dashboard-theme.css`
5. **JavaScript**: Update `static/js/dashboard-theme.js`

### Database Schema
The SQLite database has a normalized structure with foreign key relationships:

**hosts table**:
```sql
CREATE TABLE hosts (
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
);
```

**categories table**:
```sql
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT
);
```


## 🐳 Deployment

### Systemd Service
A sample service file is included (`dashboard.service`):

```bash
# Copy and modify the service file
sudo cp dashboard.service /etc/systemd/system/
sudo systemctl edit dashboard.service  # Modify paths
sudo systemctl enable dashboard.service
sudo systemctl start dashboard.service
```

### Docker (Future)
Docker support is planned for easier deployment.

### Reverse Proxy
For production, use nginx or Apache as a reverse proxy:

```nginx
location /dashboard/ {
    proxy_pass http://localhost:8003/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## 🔐 Security

### Considerations
- **No authentication**: Consider adding auth for production
- **File uploads**: Icons are validated by extension
- **Input sanitization**: Text inputs are cleaned and escaped
- **Database security**: SQLite file permissions should be restricted
- **Local network**: Designed for trusted network environments

### Recommendations
- Run on internal networks only
- Use firewall rules to restrict access
- Consider VPN access for remote monitoring
- Regular backups of data directory

## 🤝 Contributing

### Bug Reports
1. Check existing issues
2. Provide detailed description
3. Include browser/Python version
4. Steps to reproduce

### Feature Requests
See `todo.md` for planned features or suggest new ones!

### Development
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is open source. Please check the license file for details.

## 🙏 Acknowledgments

- **Bootstrap**: Responsive UI framework
- **FontAwesome**: Beautiful icons
- **Flask**: Python web framework
- **SQLite**: Reliable embedded database
- **jQuery**: JavaScript library

## 📞 Support

For issues and questions:
1. Check this README
2. Review `todo.md` for known limitations
3. Check the browser console for errors
4. Create an issue with details

---

**Happy monitoring!** 🎉
