#!/bin/bash

# Kindly Sourced Paper Daemon Management Script

SERVICE_NAME="kindly-sourced-paper.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
TEMPLATE_FILE="kindly-sourced-paper.service.template"

install_service() {
    echo "Installing Kindly Sourced Paper as a system service..."
    
    # Check if template exists
    if [ ! -f "$TEMPLATE_FILE" ]; then
        echo "Error: Service template file not found: $TEMPLATE_FILE"
        exit 1
    fi
    
    # Get current user and working directory
    CURRENT_USER=$(whoami)
    WORKING_DIR=$(pwd)
    
    # Try to detect conda environment
    if [ -n "$CONDA_DEFAULT_ENV" ] && [ "$CONDA_DEFAULT_ENV" != "base" ]; then
        CONDA_ENV_NAME="$CONDA_DEFAULT_ENV"
        CONDA_ENV_PATH="$CONDA_PREFIX"
    else
        echo "Warning: No active conda environment detected."
        echo "Please activate your conda environment (e.g., 'conda activate kindle_fetcher') and try again."
        echo "Or enter the conda environment details manually:"
        read -p "Conda environment name: " CONDA_ENV_NAME
        read -p "Conda environment path: " CONDA_ENV_PATH
    fi
    
    # Validate conda environment
    if [ ! -f "$CONDA_ENV_PATH/bin/python" ]; then
        echo "Error: Python not found in conda environment: $CONDA_ENV_PATH/bin/python"
        exit 1
    fi
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    # Create service file from template
    sed -e "s|__USER__|$CURRENT_USER|g" \
        -e "s|__WORKING_DIR__|$WORKING_DIR|g" \
        -e "s|__CONDA_ENV_PATH__|$CONDA_ENV_PATH|g" \
        -e "s|__CONDA_ENV_NAME__|$CONDA_ENV_NAME|g" \
        -e "s|__PATH__|$PATH|g" \
        "$TEMPLATE_FILE" > /tmp/"$SERVICE_NAME"
    
    # Install service file
    sudo cp /tmp/"$SERVICE_NAME" "$SERVICE_FILE"
    sudo chmod 644 "$SERVICE_FILE"
    
    # Clean up temp file
    rm /tmp/"$SERVICE_NAME"
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    
    echo "Service installed successfully!"
    echo "To start the service: ./manage_daemon.sh start"
    echo "To check status: ./manage_daemon.sh status"
}

uninstall_service() {
    echo "Uninstalling Kindly Sourced Paper service..."
    
    # Stop and disable service
    sudo systemctl stop "$SERVICE_NAME" 2>/dev/null
    sudo systemctl disable "$SERVICE_NAME" 2>/dev/null
    
    # Remove service file
    if [ -f "$SERVICE_FILE" ]; then
        sudo rm "$SERVICE_FILE"
        echo "Service file removed: $SERVICE_FILE"
    fi
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    echo "Service uninstalled successfully!"
}

case "$1" in
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
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
        echo "Usage: $0 {install|uninstall|start|stop|restart|status|enable|disable|logs|daemon-logs}"
        echo ""
        echo "Commands:"
        echo "  install      - Install the service (run this first!)"
        echo "  uninstall    - Remove the service"
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