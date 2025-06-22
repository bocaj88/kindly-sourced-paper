import os
import json
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, abort
from werkzeug.utils import secure_filename
import logging
from logging.handlers import RotatingFileHandler

# Import existing modules
from wishlist_scraper import get_wishlist_books, get_book_details_from_url
from book_downloader import search_and_download_book
from send_to_kindle import send_epub_to_kindle, setup_kindle_auth
from config import DOWNLOAD_DIR, STATUS_MESSAGE_PHONE_NUMBER
from main import get_already_downloaded, save_already_downloaded, FakeCom
import logger
import settings

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24).hex())

# Setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure app logger
logging.basicConfig(level=logging.INFO)
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240000, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('KindleSource Flask app startup')

# Global variables for status tracking
app_status = {
    'is_running': False,
    'current_task': None,
    'progress': 0,
    'last_update': datetime.now(),
    'logs': []
}

# Cache for book pages to speed up wishlist scraping
book_cache = {}
CACHE_FILE = 'book_cache.json'
CACHE_EXPIRY_HOURS = 24

def load_cache():
    """Load book cache from file"""
    global book_cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                # Filter out expired entries
                current_time = time.time()
                book_cache = {
                    url: info for url, info in data.items()
                    if current_time - info.get('timestamp', 0) < CACHE_EXPIRY_HOURS * 3600
                }
        except Exception as e:
            app.logger.error(f"Error loading cache: {e}")
            book_cache = {}

def save_cache():
    """Save book cache to file"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(book_cache, f, indent=2)
    except Exception as e:
        app.logger.error(f"Error saving cache: {e}")

def add_log(message, level='info'):
    """Add a log message to the app status"""
    timestamp = datetime.now()
    log_entry = {
        'timestamp': timestamp.isoformat(),
        'level': level,
        'message': message
    }
    app_status['logs'].append(log_entry)
    app_status['last_update'] = timestamp
    
    # Keep only last 100 log entries (important for performance)
    if len(app_status['logs']) > 100:
        app_status['logs'] = app_status['logs'][-100:]
    
    # Also log to file for persistence
    if level == 'error':
        app.logger.error(message)
    elif level == 'warning':
        app.logger.warning(message)
    else:
        app.logger.info(message)

def load_recent_logs_from_file():
    """Load recent logs from the file to populate in-memory logs on startup"""
    log_file_path = 'logs/app.log'
    if not os.path.exists(log_file_path):
        return
    
    try:
        # Read the last 200 lines from the log file (to get ~100 unique messages after filtering)
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Take the last 200 lines to ensure we get enough after filtering
        recent_lines = lines[-200:] if len(lines) > 200 else lines
        
        parsed_logs = []
        
        for line in recent_lines:
            line = line.strip()
            if not line:
                continue
                
            try:
                # Parse log format: "2025-06-22 17:32:28,111 INFO: message [in ...]"
                # Find the timestamp, level, and message
                parts = line.split(' ', 3)
                if len(parts) < 4:
                    continue
                    
                date_part = parts[0]
                time_part = parts[1]
                level_part = parts[2].rstrip(':')
                message_part = parts[3]
                
                # Remove the "[in ...]" suffix from the message
                if ' [in ' in message_part:
                    message_part = message_part.split(' [in ')[0]
                
                # Convert timestamp to ISO format
                timestamp_str = f"{date_part} {time_part}"
                try:
                    # Parse the timestamp and convert to ISO format
                    dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                    iso_timestamp = dt.isoformat()
                except ValueError:
                    # Skip lines that don't match the expected timestamp format
                    continue
                
                # Map log levels
                level_mapping = {
                    'INFO': 'info',
                    'WARNING': 'warning', 
                    'ERROR': 'error',
                    'DEBUG': 'debug'
                }
                level = level_mapping.get(level_part, 'info')
                
                # Skip duplicate messages (Flask logs many things twice)
                message = message_part.strip()
                if message.startswith('[INFO] ') or message.startswith('[WARNING] ') or message.startswith('[ERROR] '):
                    # Skip the [LEVEL] prefixed duplicate messages
                    continue
                
                # Create log entry in the same format as add_log()
                log_entry = {
                    'timestamp': iso_timestamp,
                    'level': level,
                    'message': message
                }
                
                parsed_logs.append(log_entry)
                
            except (IndexError, ValueError) as e:
                # Skip malformed lines
                continue
        
        # Remove duplicates while preserving order (keep the last occurrence)
        seen_messages = {}
        unique_logs = []
        
        for log_entry in parsed_logs:
            key = (log_entry['message'], log_entry['level'])
            if key not in seen_messages:
                seen_messages[key] = log_entry
                unique_logs.append(log_entry)
            else:
                # Update timestamp to the more recent one
                seen_messages[key]['timestamp'] = log_entry['timestamp']
        
        # Sort by timestamp and take the last 100
        unique_logs.sort(key=lambda x: x['timestamp'])
        app_status['logs'] = unique_logs[-100:]
        
        if app_status['logs']:
            print(f"Loaded {len(app_status['logs'])} recent log entries from file")
        
    except Exception as e:
        print(f"Error loading logs from file: {e}")

def get_cached_book_details(url):
    """Get book details from cache or fetch if not cached"""
    if url in book_cache:
        cached_info = book_cache[url]
        # Check if cache is still valid
        if time.time() - cached_info.get('timestamp', 0) < CACHE_EXPIRY_HOURS * 3600:
            return cached_info['title'], cached_info['author'], cached_info['isbn']
    
    # Fetch fresh data
    title, author, isbn = get_book_details_from_url(url)
    
    # Cache the result
    if title and author:
        book_cache[url] = {
            'title': title,
            'author': author,
            'isbn': isbn,
            'timestamp': time.time()
        }
        save_cache()
    
    return title, author, isbn

def get_recent_books():
    """Get list of recently downloaded books"""
    recent_books = []
    if os.path.exists(DOWNLOAD_DIR):
        try:
            # Get all files in download directory
            files = []
            for f in os.listdir(DOWNLOAD_DIR):
                if f.endswith(('.epub', '.pdf', '.mobi')) and f != 'already_downloaded.txt':
                    file_path = os.path.join(DOWNLOAD_DIR, f)
                    if os.path.isfile(file_path):
                        files.append({
                            'name': f,
                            'path': file_path,
                            'size': os.path.getsize(file_path),
                            'modified': os.path.getmtime(file_path)
                        })
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
            # Format for display
            for file_info in files[:20]:  # Show last 20 files
                recent_books.append({
                    'name': file_info['name'],
                    'size': f"{file_info['size'] / (1024*1024):.1f} MB",
                    'date': datetime.fromtimestamp(file_info['modified']).strftime('%Y-%m-%d %H:%M'),
                    'format': file_info['name'].split('.')[-1].upper()
                })
        except Exception as e:
            add_log(f"Error getting recent books: {e}", 'error')
    
    return recent_books

def run_wishlist_crawl():
    """Run wishlist crawling in background thread"""
    try:
        app_status['is_running'] = True
        app_status['current_task'] = 'Fetching wishlist books'
        app_status['progress'] = 10
        add_log("Starting wishlist crawl...")
        
        # Get wishlist books
        wishlist_url = settings.get_wishlist_url()
        books = get_wishlist_books(wishlist_url)
        add_log(f"Found {len(books)} books in wishlist")
        
        if not books:
            add_log("No books found in wishlist", 'warning')
            return
        
        # Get already downloaded books
        already_downloaded = get_already_downloaded()
        new_books = [book for book in books if book['title'] not in already_downloaded]
        
        add_log(f"Found {len(new_books)} new books to download")
        
        if not new_books:
            add_log("All books have already been downloaded")
            return
        
        # Process each new book
        total_books = len(new_books)
        successful_books = 0
        failed_books = 0
        
        for i, book in enumerate(new_books):
            try:
                app_status['current_task'] = f"Processing: {book['title']}"
                app_status['progress'] = 20 + (i * 60 // total_books)
                
                add_log(f"Processing: {book['title']} by {book['author']}")
                
                # Download book
                download_result = search_and_download_book(
                    book['title'], 
                    book['author'], 
                    book['isbn'], 
                    preferred_formats=['epub']
                )
                
                if not download_result:
                    add_log(f"Failed to download: {book['title']}", 'warning')
                    failed_books += 1
                    continue
                
                # Mark as downloaded since we got the book successfully
                save_already_downloaded(book['title'])
                
                # Send to Kindle
                app_status['current_task'] = f"Sending to Kindle: {book['title']}"
                add_log(f"Download successful, sending to Kindle: {book['title']}")
                epub_path = download_result['download_result']
                
                result = send_epub_to_kindle(epub_path)
                if result:
                    add_log(f"Successfully sent to Kindle: {book['title']}")
                    successful_books += 1
                else:
                    add_log(f"Failed to send to Kindle: {book['title']}", 'error')
                    failed_books += 1
                    
            except Exception as e:
                # Log the error and continue with the next book
                error_msg = f"Error processing {book['title']}: {str(e)}"
                add_log(error_msg, 'error')
                failed_books += 1
                continue
        
        app_status['progress'] = 100
        
        # Send summary message
        summary_msg = f"Wishlist crawl completed: {successful_books} successful, {failed_books} failed out of {total_books} books"
        add_log(summary_msg)
        
    except Exception as e:
        add_log(f"Error during wishlist crawl: {e}", 'error')
    finally:
        app_status['is_running'] = False
        app_status['current_task'] = None
        app_status['progress'] = 0

@app.route('/')
def index():
    """Main dashboard page"""
    recent_books = get_recent_books()
    return render_template('index.html', 
                         status=app_status, 
                         recent_books=recent_books,
                         wishlist_url=settings.get_wishlist_url())

@app.route('/status')
def status():
    """Get current status as JSON"""
    # Convert datetime to ISO format for consistent JavaScript parsing
    status_copy = app_status.copy()
    if status_copy['last_update']:
        status_copy['last_update'] = status_copy['last_update'].isoformat()
    return jsonify(status_copy)

@app.route('/logs')
def logs():
    """Get logs page"""
    return render_template('logs.html', logs=app_status['logs'])

@app.route('/manual-search')
def manual_search_page():
    """Manual search page"""
    return render_template('manual_search.html')

@app.route('/api/manual-search', methods=['POST'])
def api_manual_search():
    """API endpoint for manual book search"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query is required'})
        
        add_log(f"Manual search for: {query}")
        
        # Search and download book
        download_result = search_and_download_book(query, preferred_formats=['epub'])
        
        if not download_result:
            add_log(f"No results found for: {query}", 'warning')
            return jsonify({'success': False, 'error': 'No books found'})
        
        # Send to Kindle
        epub_path = download_result['download_result']
        kindle_result = send_epub_to_kindle(epub_path)
        
        if kindle_result:
            add_log(f"Successfully downloaded and sent to Kindle: {download_result['title']}")
            save_already_downloaded(download_result['title'])
            return jsonify({
                'success': True, 
                'title': download_result['title'],
                'author': download_result['author'],
                'format': download_result['format']
            })
        else:
            add_log(f"Downloaded but failed to send to Kindle: {download_result['title']}", 'warning')
            # Still mark as downloaded since we got the book, even if Kindle sending failed
            save_already_downloaded(download_result['title'])
            return jsonify({
                'success': True,
                'title': download_result['title'],
                'author': download_result['author'],
                'format': download_result['format'],
                'warning': 'Downloaded but failed to send to Kindle'
            })
    
    except Exception as e:
        add_log(f"Error in manual search: {e}", 'error')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/crawl-wishlist', methods=['POST'])
def api_crawl_wishlist():
    """API endpoint to start wishlist crawling"""
    if app_status['is_running']:
        return jsonify({'success': False, 'error': 'A task is already running'})
    
    # Start crawling in background thread
    thread = threading.Thread(target=run_wishlist_crawl)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': 'Wishlist crawling started'})

@app.route('/api/setup-kindle', methods=['POST'])
def api_setup_kindle():
    """API endpoint to setup Kindle authentication"""
    try:
        add_log("Starting Kindle authentication setup...")
        result = setup_kindle_auth()
        
        if result:
            add_log("Kindle authentication setup completed successfully")
            return jsonify({'success': True, 'message': 'Kindle authentication setup completed'})
        else:
            add_log("Kindle authentication setup failed", 'error')
            return jsonify({'success': False, 'error': 'Setup failed'})
    
    except Exception as e:
        add_log(f"Error setting up Kindle authentication: {e}", 'error')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/cache')
def cache_page():
    """Cache management page"""
    cache_stats = {
        'total_entries': len(book_cache),
        'cache_size': f"{len(json.dumps(book_cache)) / 1024:.1f} KB",
        'oldest_entry': None,
        'newest_entry': None
    }
    
    if book_cache:
        timestamps = [info.get('timestamp', 0) for info in book_cache.values()]
        if timestamps:
            cache_stats['oldest_entry'] = datetime.fromtimestamp(min(timestamps)).strftime('%Y-%m-%d %H:%M')
            cache_stats['newest_entry'] = datetime.fromtimestamp(max(timestamps)).strftime('%Y-%m-%d %H:%M')
    
    return render_template('cache.html', cache_stats=cache_stats, cache_entries=book_cache)

@app.route('/api/clear-cache', methods=['POST'])
def api_clear_cache():
    """API endpoint to clear the book cache"""
    global book_cache
    book_cache = {}
    save_cache()
    add_log("Book cache cleared")
    return jsonify({'success': True, 'message': 'Cache cleared successfully'})

@app.route('/recent-books')
def recent_books_page():
    """Recent books page"""
    recent_books = get_recent_books()
    return render_template('recent_books.html', recent_books=recent_books)

@app.route('/download/<path:filename>')
def download_book(filename):
    """Download a book file"""
    try:
        # First, try the filename as-is
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        
        # Check if file exists as-is
        if not os.path.exists(file_path):
            # If not found, try to find a file that matches (case-insensitive and handle URL encoding issues)
            if os.path.exists(DOWNLOAD_DIR):
                for existing_file in os.listdir(DOWNLOAD_DIR):
                    if existing_file.lower() == filename.lower():
                        filename = existing_file
                        file_path = os.path.join(DOWNLOAD_DIR, filename)
                        break
                else:
                    add_log(f"Download requested for non-existent file: {filename}", 'warning')
                    abort(404)
            else:
                abort(404)
        
        # Check if it's a book file
        if not filename.lower().endswith(('.epub', '.pdf', '.mobi')):
            add_log(f"Download blocked for non-book file: {filename}", 'warning')
            abort(403)
        
        add_log(f"Book download: {filename}")
        
        # Determine the mimetype
        mimetype = 'application/octet-stream'
        if filename.lower().endswith('.epub'):
            mimetype = 'application/epub+zip'
        elif filename.lower().endswith('.pdf'):
            mimetype = 'application/pdf'
        elif filename.lower().endswith('.mobi'):
            mimetype = 'application/x-mobipocket-ebook'
        
        return send_from_directory(
            DOWNLOAD_DIR, 
            filename, 
            as_attachment=True,
            mimetype=mimetype
        )
        
    except Exception as e:
        add_log(f"Error downloading file {filename}: {e}", 'error')
        abort(500)

@app.route('/api/delete-book/<path:filename>', methods=['DELETE'])
def delete_book(filename):
    """Delete a book file"""
    try:
        # First, try the filename as-is
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        
        # Check if file exists as-is
        if not os.path.exists(file_path):
            # If not found, try to find a file that matches (case-insensitive)
            if os.path.exists(DOWNLOAD_DIR):
                for existing_file in os.listdir(DOWNLOAD_DIR):
                    if existing_file.lower() == filename.lower():
                        filename = existing_file
                        file_path = os.path.join(DOWNLOAD_DIR, filename)
                        break
                else:
                    return jsonify({'success': False, 'error': 'File not found'})
            else:
                return jsonify({'success': False, 'error': 'File not found'})
        
        # Check if it's a book file
        if not filename.lower().endswith(('.epub', '.pdf', '.mobi')):
            return jsonify({'success': False, 'error': 'Invalid file type'})
        
        # Delete the file
        os.remove(file_path)
        add_log(f"Book deleted: {filename}")
        
        # Also remove from already downloaded list if present
        already_downloaded_file = os.path.join(DOWNLOAD_DIR, "already_downloaded.txt")
        if os.path.exists(already_downloaded_file):
            try:
                with open(already_downloaded_file, 'r') as f:
                    lines = f.readlines()
                
                # Remove any lines that match this book (try different variations)
                book_title_variations = [
                    filename,
                    filename.rsplit('.', 1)[0],  # filename without extension
                    filename.replace('_', ' '),
                    filename.rsplit('.', 1)[0].replace('_', ' ')
                ]
                
                updated_lines = []
                for line in lines:
                    line_stripped = line.strip()
                    if not any(variation in line_stripped for variation in book_title_variations):
                        updated_lines.append(line)
                
                with open(already_downloaded_file, 'w') as f:
                    f.writelines(updated_lines)
                    
            except Exception as e:
                add_log(f"Error updating already downloaded list: {e}", 'warning')
        
        return jsonify({'success': True, 'message': 'Book deleted successfully'})
        
    except Exception as e:
        add_log(f"Error deleting file {filename}: {e}", 'error')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/debug')
def debug_files():
    """Debug files viewer page"""
    debug_dir = os.path.join('static', 'debug')
    debug_files = []
    
    if os.path.exists(debug_dir):
        for filename in os.listdir(debug_dir):
            if filename.endswith('.html'):
                filepath = os.path.join(debug_dir, filename)
                debug_files.append({
                    'name': filename,
                    'size': f"{os.path.getsize(filepath) / 1024:.1f} KB",
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S'),
                    'url': f"/static/debug/{filename}"
                })
    
    # Sort by modification time (newest first)
    debug_files.sort(key=lambda x: x['modified'], reverse=True)
    
    return render_template('debug.html', debug_files=debug_files)

@app.route('/debug/clear', methods=['POST'])
def clear_debug_files():
    """Clear all debug files"""
    debug_dir = os.path.join('static', 'debug')
    cleared_count = 0
    
    if os.path.exists(debug_dir):
        for filename in os.listdir(debug_dir):
            if filename.endswith('.html'):
                try:
                    os.remove(os.path.join(debug_dir, filename))
                    cleared_count += 1
                except Exception as e:
                    add_log(f"Error deleting debug file {filename}: {e}", 'error')
    
    add_log(f"Cleared {cleared_count} debug files")
    return jsonify({'success': True, 'cleared_count': cleared_count})

@app.route('/settings')
def settings_page():
    """Settings configuration page"""
    return render_template('settings.html')

@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    """API endpoint to get current settings"""
    try:
        current_settings = settings.load_settings()
        return jsonify(current_settings)
    except Exception as e:
        add_log(f"Error loading settings: {e}", 'error')
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings', methods=['POST'])
def api_save_settings():
    """API endpoint to save settings"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        # Validate wishlist URL if provided
        if 'wishlist_url' in data:
            if not settings.is_valid_wishlist_url(data['wishlist_url']):
                return jsonify({'success': False, 'error': 'Invalid wishlist URL format'})
        
        # Save settings
        success = settings.save_settings(data)
        if success:
            add_log("Settings updated successfully")
            return jsonify({'success': True, 'message': 'Settings saved successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save settings'})
    
    except Exception as e:
        add_log(f"Error saving settings: {e}", 'error')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/settings/reset', methods=['POST'])
def api_reset_settings():
    """API endpoint to reset settings to defaults"""
    try:
        success = settings.reset_settings()
        if success:
            add_log("Settings reset to defaults")
            return jsonify({'success': True, 'message': 'Settings reset to defaults'})
        else:
            return jsonify({'success': False, 'error': 'Failed to reset settings'})
    except Exception as e:
        add_log(f"Error resetting settings: {e}", 'error')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/settings/export', methods=['GET'])
def api_export_settings():
    """API endpoint to export settings as JSON"""
    try:
        settings_json = settings.export_settings()
        return settings_json, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        add_log(f"Error exporting settings: {e}", 'error')
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/import', methods=['POST'])
def api_import_settings():
    """API endpoint to import settings from JSON"""
    try:
        data = request.get_json()
        if not data or 'settings' not in data:
            return jsonify({'success': False, 'error': 'No settings data provided'})
        
        success = settings.import_settings(data['settings'])
        if success:
            add_log("Settings imported successfully")
            return jsonify({'success': True, 'message': 'Settings imported successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to import settings'})
    
    except Exception as e:
        add_log(f"Error importing settings: {e}", 'error')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/test-wishlist', methods=['POST'])
def api_test_wishlist():
    """API endpoint to test a wishlist URL"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})
        
        if not settings.is_valid_wishlist_url(url):
            return jsonify({'success': False, 'error': 'Invalid wishlist URL format'})
        
        add_log(f"Testing wishlist URL: {url}")
        
        # Try to fetch books from the wishlist
        books = get_wishlist_books(url)
        
        if books:
            add_log(f"Wishlist test successful: found {len(books)} books")
            return jsonify({'success': True, 'book_count': len(books), 'books': books[:5]})  # Return first 5 books as preview
        else:
            add_log("Wishlist test failed: no books found", 'warning')
            return jsonify({'success': False, 'error': 'No books found in wishlist'})
    
    except Exception as e:
        add_log(f"Error testing wishlist: {e}", 'error')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update-user-agent', methods=['POST'])
def api_update_user_agent():
    """API endpoint to cache the browser's user agent"""
    try:
        data = request.get_json()
        user_agent = data.get('user_agent', '').strip()
        
        if not user_agent:
            return jsonify({'success': False, 'error': 'User agent is required'})
        
        # Basic validation - should contain common browser indicators
        if not any(browser in user_agent for browser in ['Chrome', 'Firefox', 'Safari', 'Edge']):
            return jsonify({'success': False, 'error': 'Invalid user agent format'})
        
        success = settings.set_cached_user_agent(user_agent)
        if success:
            add_log(f"Browser user agent cached: {user_agent[:50]}...")
            return jsonify({'success': True, 'message': 'User agent cached successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to cache user agent'})
    
    except Exception as e:
        add_log(f"Error caching user agent: {e}", 'error')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get-user-agent-status', methods=['GET'])
def api_get_user_agent_status():
    """API endpoint to get current user agent cache status"""
    try:
        cached_ua = settings.get_setting('cached_user_agent')
        last_updated = settings.get_setting('user_agent_last_updated')
        is_fresh = settings.is_user_agent_fresh()
        
        status = {
            'has_cached_user_agent': bool(cached_ua),
            'is_fresh': is_fresh,
            'last_updated': last_updated,
            'user_agent_preview': cached_ua[:50] + '...' if cached_ua else None
        }
        
        return jsonify(status)
    
    except Exception as e:
        add_log(f"Error getting user agent status: {e}", 'error')
        return jsonify({'error': str(e)}), 500

@app.route('/api/populate-downloaded', methods=['POST'])
def api_populate_downloaded():
    """API endpoint to populate already_downloaded.txt with existing books"""
    try:
        count = populate_already_downloaded()
        return jsonify({'success': True, 'count': count, 'message': f'Populated with {count} books'})
    except Exception as e:
        add_log(f"Error populating downloaded list: {e}", 'error')
        return jsonify({'success': False, 'error': str(e)})

# Initialize cache on startup
load_cache()

# Load recent logs from file to persist across app restarts
load_recent_logs_from_file()

# Initialize logger to capture all print statements
logger.set_flask_logger(add_log)
logger.enable_print_logging()

def populate_already_downloaded():
    """Populate already_downloaded.txt with titles from existing book files"""
    try:
        if not os.path.exists(DOWNLOAD_DIR):
            return 0
            
        existing_books = set()
        book_files = []
        
        # Get all book files
        for filename in os.listdir(DOWNLOAD_DIR):
            if filename.endswith(('.epub', '.pdf', '.mobi')) and filename != 'already_downloaded.txt':
                book_files.append(filename)
        
        # Extract titles from filenames
        for filename in book_files:
            # Try to extract a clean title from the filename
            # Remove file extension
            title = filename.rsplit('.', 1)[0]
            
            # Try to extract title from common LibGen naming patterns
            # Pattern: "Author - Title _Year_ Publisher_ - libgen.li"
            if ' - ' in title and '_' in title:
                parts = title.split(' - ')
                if len(parts) >= 2:
                    title = parts[1].split('_')[0].strip()
            
            # Clean up title
            title = title.replace('_', ' ').strip()
            
            # Remove common LibGen suffixes if present
            title = title.replace(' - libgen.li', '').strip()
            
            if title:
                existing_books.add(title)
                add_log(f"Found existing book: {title}")
        
        # Read current already_downloaded list
        current_downloaded = get_already_downloaded()
        
        # Merge with existing books
        all_downloaded = current_downloaded.union(existing_books)
        
        # Save to file
        already_downloaded_file = os.path.join(DOWNLOAD_DIR, "already_downloaded.txt")
        with open(already_downloaded_file, 'w') as f:
            for title in sorted(all_downloaded):
                f.write(title + '\n')
        
        new_count = len(existing_books) - len(current_downloaded.intersection(existing_books))
        add_log(f"Populated already_downloaded.txt with {len(all_downloaded)} books ({new_count} new)")
        return len(all_downloaded)
        
    except Exception as e:
        add_log(f"Error populating already_downloaded.txt: {e}", 'error')
        return 0

if __name__ == '__main__':
    add_log("KindleSource Flask app starting...")
    app.run(debug=True, host='0.0.0.0', port=5001) 