# KindleSource Flask Web Interface

A modern web interface for the KindleSource book downloader and Kindle automation tool.

## Features

- **Dashboard**: Overview of system status, recent books, and quick controls
- **Manual Search**: Search for and download individual books from LibGen
- **Recent Books**: View and manage all downloaded books
- **Logs**: Real-time application logs with filtering and search
- **Cache Management**: Manage book page cache for faster wishlist crawling
- **Settings**: Configure wishlist URL, download preferences, and other options through the web interface
- **Real-time Status**: Live updates of download progress and system status

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Flask App**:
   ```bash
   python run_flask.py
   ```

3. **Open in Browser**:
   Open `http://localhost:5000` in your web browser

## Features Overview

### Dashboard (`/`)
- Current system status and progress
- Recent downloaded books preview with **download and delete actions**
- **Book Management**: Download any book or delete unwanted books directly from the dashboard
- Quick action buttons for wishlist crawling and Kindle setup
- Real-time activity logs
- Manual action links for Send to Kindle and LibGen search

### Manual Search (`/manual-search`)
- Search LibGen for individual books
- Download and automatically send to Kindle
- Search history with local storage
- Helpful search tips and examples

### Recent Books (`/recent-books`)
- View all downloaded books with metadata
- **Download Books**: Direct download links for all your books
- **Delete Books**: Remove books with confirmation dialogs
- Filter by format (EPUB, PDF, MOBI)
- Sort by date, name, or size
- Statistics on book collection
- Book management with organized table layout

### Logs (`/logs`)
- Real-time application logs
- Filter by log level (Info, Warning, Error)
- Search log messages
- Auto-refresh capability
- Log statistics

### Cache Management (`/cache`)
- View cached book page data
- Cache statistics and performance info
- Clear cache functionality
- Understand cache benefits

### Debug Files (`/debug`)
- View debugging HTML files generated during scraping
- Includes wishlist pages, LibGen search results, and download pages
- Click to view files in browser or download them
- Clear debug files when no longer needed

### Settings (`/settings`)
- **Wishlist Configuration**: Set your Amazon wishlist URL with validation and testing
- **Download Preferences**: Configure preferred formats (EPUB, PDF, MOBI) and download settings
- **Kindle Settings**: Enable/disable automatic sending to Kindle
- **Notifications**: Configure SMS notifications with phone number
- **Cache Settings**: Adjust cache expiry time (1-168 hours)
- **Browser Compatibility**: Automatic user agent caching for better Amazon compatibility and reduced blocking
- **Advanced Options**: Enable debug mode and other developer settings
- **Export/Import**: Backup and restore your settings as JSON files
- **Real-time Validation**: URL validation and wishlist testing

## API Endpoints

The Flask app provides several API endpoints for automation:

- `POST /api/crawl-wishlist` - Start wishlist crawling
- `POST /api/manual-search` - Search for a book
- `POST /api/setup-kindle` - Setup Kindle authentication
- `POST /api/clear-cache` - Clear book page cache
- `POST /debug/clear` - Clear debug HTML files
- `GET /status` - Get current system status
- `GET /api/settings` - Get current settings
- `POST /api/settings` - Save settings
- `POST /api/settings/reset` - Reset settings to defaults
- `GET /api/settings/export` - Export settings as JSON
- `POST /api/settings/import` - Import settings from JSON
- `POST /api/test-wishlist` - Test a wishlist URL
- `GET /download/<filename>` - Download a book file
- `DELETE /api/delete-book/<filename>` - Delete a book file
- `POST /api/update-user-agent` - Cache browser user agent for Amazon compatibility
- `GET /api/get-user-agent-status` - Check cached user agent status

## Configuration

### Flask App Configuration

You can configure the Flask app using environment variables:

- `FLASK_HOST` - Host to bind to (default: 0.0.0.0)
- `FLASK_PORT` - Port to listen on (default: 5001)
- `FLASK_DEBUG` - Enable debug mode (default: True)

Example:
```bash
export FLASK_HOST=127.0.0.1
export FLASK_PORT=8080
export FLASK_DEBUG=False
python run_flask.py
```

### Application Settings

The app now uses a web-based settings system instead of editing config files:

1. **First Time Setup**: Visit `/settings` to configure your wishlist URL
2. **Settings Storage**: Configuration saved in `user_settings.json`
3. **Validation**: Real-time validation of wishlist URLs and settings
4. **Backup**: Export/import settings for backup or sharing between machines
5. **Defaults**: Sensible defaults provided for all settings

**Important**: The wishlist URL is now set through the web interface rather than `config.py`. Your existing `config.py` settings will be migrated automatically.

## Architecture

The Flask app integrates with your existing KindleSource modules:

- `wishlist_scraper.py` - Amazon wishlist scraping
- `book_downloader.py` - LibGen book downloading
- `send_to_kindle.py` - Kindle upload functionality
- `config.py` - Configuration management

## Cache System

The app includes an intelligent caching system that:

- Stores book page data for 24 hours
- Speeds up repeated wishlist crawls
- Reduces Amazon server load
- Persists across app restarts
- Can be managed through the web interface

## Logging

The app includes a comprehensive centralized logging system:

### Features:
- **Unified Logging**: All `print()` statements from your scripts now appear in the web interface
- **Real-time Display**: Logs appear instantly in the browser logs page
- **File Storage**: Stored in `logs/app.log` with rotation  
- **Multiple Levels**: Info, Warning, Error with color coding
- **Filterable**: Filter by level and search log messages
- **Memory Efficient**: Limited to last 100 entries in memory

### Integration:
- **Automatic**: All existing `print()` statements are captured
- **Enhanced**: Scripts now use `logger.info()`, `logger.warning()`, `logger.error()`
- **Status Tracking**: Built-in progress tracking for long operations
- **Cross-Module**: Works across all Python files in the project

## Browser Compatibility

The web interface is built with modern web standards and works with:

- Chrome/Edge (recommended)
- Firefox
- Safari
- Mobile browsers (responsive design)

## Error Handling

The application now includes robust error handling that ensures continuous operation:

### **Fail-Safe Processing**
- **Individual Book Failures**: If one book fails to download or send to Kindle, the process continues with remaining books
- **Detailed Logging**: All failures are logged with specific error messages for troubleshooting
- **Progress Tracking**: Real-time status updates show which books succeed or fail
- **Summary Reports**: Completion messages show total success/failure counts

### **Error Recovery**
- **Download Failures**: Logged and skipped, process continues
- **Kindle Upload Failures**: Logged and skipped, process continues  
- **Network Issues**: Logged with specific error details
- **File System Errors**: Graceful handling with informative messages

## User Agent Caching

The application automatically captures and caches your browser's user agent to improve Amazon compatibility:

### **How It Works**
- **Automatic Capture**: Your browser's user agent is automatically captured when you visit any page
- **Smart Caching**: User agent is cached for 24 hours to avoid Amazon blocking
- **Real User Agent**: Uses your actual browser's user agent instead of generic scraping user agents
- **Background Updates**: Automatically refreshes when the cache expires

### **Benefits**
- **Reduced Blocking**: Real browser user agents are less likely to be blocked by Amazon
- **Better Compatibility**: Improved success rate for wishlist crawling and book downloads
- **Transparent Operation**: Works automatically without user intervention
- **Fresh Data**: Automatically updates to keep user agent current

### **Settings Integration**
- **Status Display**: View current user agent status in Settings page
- **Manual Refresh**: Force refresh user agent if needed
- **Cache Monitoring**: See when user agent was last updated
- **Automatic Validation**: Ensures only valid browser user agents are cached

## Troubleshooting

### Common Issues

1. **Port already in use**: Change the port with `FLASK_PORT=8080`
2. **Import errors**: Make sure all dependencies are installed
3. **Kindle setup fails**: Use the web interface Setup Kindle button
4. **Cache issues**: Clear cache through the web interface
5. **Book processing fails**: Check logs page for specific error details - other books will continue processing

### Debug Mode

Run with debug mode for development:
```bash
export FLASK_DEBUG=True
python run_flask.py
```

This enables:
- Auto-reload on code changes
- Detailed error messages
- Debug toolbar (if installed)

## Security Notes

- The app runs on all interfaces (0.0.0.0) by default
- For production use, consider:
  - Setting `FLASK_HOST=127.0.0.1` for local-only access
  - Using a reverse proxy (nginx/Apache)
  - Enabling HTTPS
  - Setting a strong `app.secret_key`

## Contributing

The Flask app is designed to be:
- Easy to extend with new features
- RESTful API compatible
- Mobile-friendly responsive design
- Accessible and user-friendly

Feel free to contribute improvements! 