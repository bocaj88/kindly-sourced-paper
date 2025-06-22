"""
Centralized logging utility for KindleSource
Provides consistent logging across all modules that appears in the web interface
"""

import os
import sys
import json
from datetime import datetime
from typing import Optional

# Global log storage for when Flask app isn't available
_log_buffer = []
_flask_add_log = None

def set_flask_logger(flask_add_log_func):
    """Set the Flask app's add_log function"""
    global _flask_add_log
    _flask_add_log = flask_add_log_func
    
    # Flush any buffered logs
    for log_entry in _log_buffer:
        _flask_add_log(log_entry['message'], log_entry['level'])
    _log_buffer.clear()

def log(message: str, level: str = 'info'):
    """
    Send log message to Flask app or buffer it if Flask isn't available
    
    Args:
        message: The log message
        level: Log level ('info', 'warning', 'error')
    """
    # Also print to console for immediate feedback
    print(f"[{level.upper()}] {message}")
    
    if _flask_add_log:
        # Flask app is available, send directly
        _flask_add_log(message, level)
    else:
        # Buffer the log for later when Flask app is available
        _log_buffer.append({
            'message': message,
            'level': level,
            'timestamp': datetime.now().isoformat()
        })

def info(message: str):
    """Log an info message"""
    log(message, 'info')

def warning(message: str):
    """Log a warning message"""
    log(message, 'warning')

def error(message: str):
    """Log an error message"""
    log(message, 'error')

def debug(message: str):
    """Log a debug message (shown as info in web interface)"""
    log(message, 'info')

# Create aliases for common logging patterns
def print_and_log(message: str, level: str = 'info'):
    """Legacy compatibility - same as log()"""
    log(message, level)

# Monkey patch print to also log (optional - can be enabled)
_original_print = print

def enable_print_logging():
    """Enable automatic logging of all print statements"""
    def logged_print(*args, **kwargs):
        # Convert print arguments to string
        message = ' '.join(str(arg) for arg in args)
        
        # Call original print
        _original_print(*args, **kwargs)
        
        # Also log to web interface (but don't double-print)
        if _flask_add_log:
            _flask_add_log(message, 'info')
        else:
            _log_buffer.append({
                'message': message,
                'level': 'info',
                'timestamp': datetime.now().isoformat()
            })
    
    # Replace global print function
    import builtins
    builtins.print = logged_print

def disable_print_logging():
    """Restore original print function"""
    import builtins
    builtins.print = _original_print

# Status tracking for long-running operations
class StatusTracker:
    """Helper class for tracking operation status"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = datetime.now()
        info(f"Starting {operation_name}...")
    
    def update(self, message: str, progress: Optional[int] = None):
        """Update operation status"""
        if progress is not None:
            info(f"{self.operation_name} - {message} ({progress}%)")
        else:
            info(f"{self.operation_name} - {message}")
    
    def complete(self, message: str = "completed"):
        """Mark operation as complete"""
        elapsed = datetime.now() - self.start_time
        info(f"{self.operation_name} {message} in {elapsed.total_seconds():.1f}s")
    
    def error(self, message: str):
        """Mark operation as failed"""
        elapsed = datetime.now() - self.start_time
        error(f"{self.operation_name} failed after {elapsed.total_seconds():.1f}s: {message}")

# Export commonly used functions
__all__ = [
    'log', 'info', 'warning', 'error', 'debug',
    'set_flask_logger', 'enable_print_logging', 'disable_print_logging',
    'StatusTracker'
] 