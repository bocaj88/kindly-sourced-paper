#!/usr/bin/env python3
"""
Test script to demonstrate the new centralized logging system
"""

import logger

def test_logging():
    """Test various logging levels"""
    logger.info("Starting logging test...")
    
    # Test different log levels
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.debug("This is a debug message")
    
    # Test status tracking
    tracker = logger.StatusTracker("Test Operation")
    tracker.update("Processing step 1", 25)
    tracker.update("Processing step 2", 50)
    tracker.update("Processing step 3", 75)
    tracker.complete("All steps completed")
    
    logger.info("Logging test completed!")

if __name__ == "__main__":
    # Test without Flask app (should buffer logs)
    print("Testing logging without Flask app (logs will be buffered):")
    test_logging()
    
    print("\nNow testing with Flask app integration:")
    # Import Flask app to initialize logger
    from app import add_log
    logger.set_flask_logger(add_log)
    
    # Test with Flask app (should send to web interface)
    test_logging() 