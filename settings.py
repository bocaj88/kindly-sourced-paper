"""
Settings management for KindleSource
Handles user configuration through the web interface
"""

import os
import json
from typing import Dict, Any, Optional

SETTINGS_FILE = 'user_settings.json'

# Default settings
DEFAULT_SETTINGS = {
    'wishlist_url': 'https://www.amazon.com/hz/wishlist/ls/YOUR_WISHLIST_ID',
    'preferred_formats': ['epub', 'pdf', 'mobi'],
    'auto_send_to_kindle': True,
    'notification_phone': None,
    'download_timeout': 30,
    'max_concurrent_downloads': 3,
    'cache_expiry_hours': 24,
    'debug_mode': False,
    'cached_user_agent': None,
    'user_agent_last_updated': None,
    'amazon_username': None,
    'amazon_password': None
}

def load_settings() -> Dict[str, Any]:
    """Load settings from file or return defaults"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged_settings = DEFAULT_SETTINGS.copy()
                merged_settings.update(settings)
                return merged_settings
        except Exception as e:
            print(f"Error loading settings: {e}")
            return DEFAULT_SETTINGS.copy()
    else:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: Dict[str, Any]) -> bool:
    """Save settings to file"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

def get_setting(key: str, default: Any = None) -> Any:
    """Get a specific setting value"""
    settings = load_settings()
    return settings.get(key, default)

def update_setting(key: str, value: Any) -> bool:
    """Update a specific setting"""
    settings = load_settings()
    settings[key] = value
    return save_settings(settings)

def get_wishlist_url() -> str:
    """Get the current wishlist URL"""
    return get_setting('wishlist_url', DEFAULT_SETTINGS['wishlist_url'])

def set_wishlist_url(url: str) -> bool:
    """Set the wishlist URL"""
    return update_setting('wishlist_url', url)

def get_preferred_formats() -> list:
    """Get preferred book formats"""
    return get_setting('preferred_formats', DEFAULT_SETTINGS['preferred_formats'])

def is_valid_wishlist_url(url: str) -> bool:
    """Validate if a URL looks like an Amazon wishlist URL"""
    if not url or not isinstance(url, str):
        return False
    
    # Check if it's an Amazon wishlist URL
    valid_patterns = [
        'amazon.com/hz/wishlist/ls/',
        'amazon.co.uk/hz/wishlist/ls/',
        'amazon.ca/hz/wishlist/ls/',
        'amazon.de/hz/wishlist/ls/',
        'amazon.fr/hz/wishlist/ls/',
        'amazon.it/hz/wishlist/ls/',
        'amazon.es/hz/wishlist/ls/',
        'amazon.com.au/hz/wishlist/ls/',
        'amazon.co.jp/hz/wishlist/ls/'
    ]
    
    return any(pattern in url.lower() for pattern in valid_patterns)

def reset_settings() -> bool:
    """Reset all settings to defaults"""
    return save_settings(DEFAULT_SETTINGS.copy())

def export_settings() -> str:
    """Export settings as JSON string"""
    settings = load_settings()
    return json.dumps(settings, indent=2)

def import_settings(json_str: str) -> bool:
    """Import settings from JSON string"""
    try:
        settings = json.loads(json_str)
        # Validate required keys exist
        for key in DEFAULT_SETTINGS:
            if key not in settings:
                settings[key] = DEFAULT_SETTINGS[key]
        return save_settings(settings)
    except Exception as e:
        print(f"Error importing settings: {e}")
        return False

def get_cached_user_agent() -> str:
    """Get the cached user agent from browser"""
    cached_ua = get_setting('cached_user_agent')
    if cached_ua:
        return cached_ua
    
    # Fallback to a modern user agent if none cached
    return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.60 Safari/537.36'

def set_cached_user_agent(user_agent: str) -> bool:
    """Set the cached user agent from browser"""
    import time
    success = update_setting('cached_user_agent', user_agent)
    if success:
        update_setting('user_agent_last_updated', time.time())
    return success

def is_user_agent_fresh() -> bool:
    """Check if the cached user agent is fresh (less than 24 hours old)"""
    import time
    last_updated = get_setting('user_agent_last_updated')
    if not last_updated:
        return False
    
    # Consider fresh if updated within last 24 hours
    return (time.time() - last_updated) < 86400  # 24 hours in seconds

def get_amazon_username() -> Optional[str]:
    """Get the Amazon username"""
    return get_setting('amazon_username')

def set_amazon_username(username: str) -> bool:
    """Set the Amazon username"""
    return update_setting('amazon_username', username if username else None)

def get_amazon_password() -> Optional[str]:
    """Get the Amazon password"""
    return get_setting('amazon_password')

def set_amazon_password(password: str) -> bool:
    """Set the Amazon password"""
    return update_setting('amazon_password', password if password else None)

def get_amazon_credentials() -> tuple[Optional[str], Optional[str]]:
    """Get both Amazon username and password"""
    return get_amazon_username(), get_amazon_password()

def has_amazon_credentials() -> bool:
    """Check if both Amazon username and password are configured"""
    username, password = get_amazon_credentials()
    return username is not None and password is not None and username.strip() != '' and password.strip() != ''

# Initialize settings file if it doesn't exist
if not os.path.exists(SETTINGS_FILE):
    save_settings(DEFAULT_SETTINGS.copy()) 