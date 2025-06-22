#!/bin/bash

# Stop the Kindly Sourced Paper Flask App

echo "Stopping Kindly Sourced Paper Flask App..."

# Kill any running Flask processes
pkill -f "python.*run_flask.py"

# Remove PID file if it exists
if [ -f "flask.pid" ]; then
    rm flask.pid
    echo "Removed PID file"
fi

echo "Flask app stopped" 