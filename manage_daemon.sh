#!/bin/bash

# Kindly Sourced Paper Daemon Management Script

SERVICE_NAME="kindly-sourced-paper.service"

case "$1" in
    start)
        echo "Starting Kindly Sourced Paper daemon..."
        sudo systemctl start $SERVICE_NAME
        ;;
    stop)
        echo "Stopping Kindly Sourced Paper daemon..."
        sudo systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "Restarting Kindly Sourced Paper daemon..."
        sudo systemctl restart $SERVICE_NAME
        ;;
    status)
        sudo systemctl status $SERVICE_NAME
        ;;
    enable)
        echo "Enabling daemon to start at boot..."
        sudo systemctl enable $SERVICE_NAME
        ;;
    disable)
        echo "Disabling daemon from starting at boot..."
        sudo systemctl disable $SERVICE_NAME
        ;;
    logs)
        echo "Showing daemon logs (Ctrl+C to exit)..."
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    daemon-logs)
        echo "Showing daemon.log file (Ctrl+C to exit)..."
        tail -f logs/daemon.log
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|enable|disable|logs|daemon-logs}"
        echo ""
        echo "Commands:"
        echo "  start        - Start the daemon"
        echo "  stop         - Stop the daemon"
        echo "  restart      - Restart the daemon"
        echo "  status       - Show daemon status"
        echo "  enable       - Enable automatic startup at boot"
        echo "  disable      - Disable automatic startup at boot"
        echo "  logs         - Show systemd logs (live)"
        echo "  daemon-logs  - Show daemon.log file (live)"
        exit 1
        ;;
esac 