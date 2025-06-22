#!/usr/bin/env python3
"""
Run script for KindleSource Flask app
"""

import os
from app import app, add_log
import logger

if __name__ == '__main__':
    add_log("Starting KindleSource Flask application...")
    
    # Get configuration from environment variables or use defaults
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Starting KindleSource Flask app on http://{host}:{port}")
    logger.info("Available endpoints:")
    logger.info("  / - Main dashboard")
    logger.info("  /manual-search - Manual book search")
    logger.info("  /recent-books - View downloaded books")
    logger.info("  /logs - Application logs")
    logger.info("  /cache - Cache management")
    logger.info("  /debug - Debug files viewer")
    logger.info("")
    logger.info("Press Ctrl+C to stop the server")
    
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        logger.info("\nShutting down KindleSource Flask app...")
        add_log("KindleSource Flask application stopped") 