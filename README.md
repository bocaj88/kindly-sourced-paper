<meta name="robots" content="noindex">

# 📚 Kindly Sourced Paper

*A whimsically named educational tool for... acquiring reading materials through legitimate academic channels.*

## 🎭 What is This?

This is a Flask-based web application that helps you manage your Amazon wishlist and educational resources. It provides a clean web interface for organizing your academic reading list and integrating with your e-reader workflow.

**Disclaimer**: This tool is for educational purposes only. Users are responsible for complying with all applicable laws and terms of service.

## ✨ Features

- 📖 **Wishlist Management**: Monitor your Amazon wishlist for new academic materials
- 🔍 **Manual Search**: Find specific educational resources when needed  
- 📱 **E-reader Integration**: Seamless workflow with your reading device
- 📊 **Web Dashboard**: Beautiful, responsive interface for managing everything
- 🗂️ **File Management**: Organize your digital library efficiently
- ⚙️ **Settings**: Configurable preferences and automation options
- 📈 **Logging**: Detailed activity tracking and debugging
- 🎯 **Smart Deduplication**: Prevents downloading the same material twice

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Conda or virtualenv
- Modern web browser

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/bocaj88/kindly-sourced-paper.git
   cd kindly-sourced-paper
   ```

2. **Create conda environment**:
   ```bash
   conda create -n kindle_fetcher python=3.10
   conda activate kindle_fetcher
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup Playwright** (for browser automation):
   ```bash
   python setup_playwright.py
   ```

5. **Install the system service** (recommended):
   ```bash
   # Make sure you're in the conda environment
   conda activate kindle_fetcher
   
   # Install the service
   ./manage_daemon.sh install
   ```

6. **Start the service**:
   ```bash
   ./manage_daemon.sh start
   ```

7. **Open your browser** and navigate to: `http://localhost:5001`

### Alternative: Manual Run (without service)
If you prefer not to install as a service, you can run manually:
```bash
python run_flask.py
```

## Getting started notes!
1. You MUST set your wishlist and it's gotta be public (Don't forget to hit save)
2. You MUST "Setup your kindle" so we can get your authentication on a real computer with a display
3. We need a $DISPLAY argument... so headless get's tricky for now... I haven't looked into this yet
4. The app can run as a system service (daemon) and start automatically at boot (after installation)
   ```bash
   # Check if the service is running
   ./manage_daemon.sh status
   
   # If not running, start it
   ./manage_daemon.sh start
   ```

## 🎯 How to Use

### First Time Setup

1. **Configure Settings**: Visit the Settings page to configure your preferences
2. **Set Wishlist URL**: Add your Amazon wishlist URL 
3. **Setup E-reader**: Configure your device integration (one-time setup)
4. **Test Connection**: Use the "Test Wishlist" button to verify everything works

### Daily Workflow

1. **Dashboard**: Monitor recent activity and system status
2. **Manual Search**: Find specific materials when needed
3. **Automatic Processing**: Let the system monitor your wishlist
4. **Review Logs**: Check the activity log for any issues

## 🛠️ Configuration

Key configuration files:
- `user_settings.json` - Your personal preferences (auto-generated)
- `config.py` - Application settings
- `.env` - Environment variables (create if needed)

## 🔄 Running as a System Service (Daemon)

The application can be configured to run as a systemd service, which provides better reliability and automatic startup management.

### Service Installation

**First-time setup**: You need to install the service before using it. Make sure you're in your conda environment and run:

```bash
conda activate kindle_fetcher
./manage_daemon.sh install
```

This will:
- Create a systemd service file customized for your environment
- Install it to the system
- Enable automatic startup at boot

### Service Management

Once installed, here are the key management commands:

```bash
# Check service status
./manage_daemon.sh status

# Start the service
./manage_daemon.sh start

# Stop the service
./manage_daemon.sh stop

# Restart the service
./manage_daemon.sh restart

# Enable automatic startup at boot
./manage_daemon.sh enable

# Disable automatic startup
./manage_daemon.sh disable

# View service logs
./manage_daemon.sh logs

# View daemon.log file
./manage_daemon.sh daemon-logs

# Uninstall the service (if needed)
./manage_daemon.sh uninstall
```

### Service Configuration

The service configuration file is located at `/etc/systemd/system/kindly-sourced-paper.service` and includes:

- **Automatic startup** at boot
- **Automatic restart** if the service crashes
- **Proper environment** setup for conda
- **Logging** to `logs/daemon.log`
- **User permissions** (runs as your user account)

### Daemon Management Script

For convenience, use the provided management script:

```bash
# Quick commands
./manage_daemon.sh status      # Check service status
./manage_daemon.sh start       # Start the daemon
./manage_daemon.sh stop        # Stop the daemon
./manage_daemon.sh restart     # Restart the daemon
./manage_daemon.sh logs        # View live systemd logs
./manage_daemon.sh daemon-logs # View live daemon.log file

# See all available commands
./manage_daemon.sh
```

### Manual Control Scripts

You can also use the original scripts for manual control:

```bash
# Start manually (if service is stopped)
./start_flask.sh

# Stop manually
./stop_flask.sh
```

**Note**: If you use the manual scripts while the service is running, you may have conflicts. Use `./manage_daemon.sh stop` first.

## ⏰ Automated Wishlist Crawling

Set up automatic wishlist crawling to run every 12 hours using cron:

### Add the Cron Job

```bash
crontab -e
```

Add this line for every 12 hours:

```bash
# KindleSource Automatic Wishlist Crawler - Every 12 hours
0 */12 * * * curl -s -X POST http://localhost:5001/api/crawl-wishlist
```

**Alternative Schedules:**
```bash
# Daily at 8 AM and 8 PM
0 8,20 * * * curl -s -X POST http://localhost:5001/api/crawl-wishlist

# Daily at midnight and noon
0 0,12 * * * curl -s -X POST http://localhost:5001/api/crawl-wishlist

# Daily at 6 AM and 6 PM  
0 6,18 * * * curl -s -X POST http://localhost:5001/api/crawl-wishlist
```

### Optional: Add Basic Logging

```bash
# With simple logging
0 */12 * * * curl -s -X POST http://localhost:5001/api/crawl-wishlist >> /home/jakem/Documents/Projects/kindly-sourced-paper/logs/cron.log 2>&1
```

**Note**: The Flask app daemon must be running for the cron job to work. Check service status with `sudo systemctl status kindly-sourced-paper.service`.

## 🔧 Troubleshooting

### Common Issues

**Connection Problems**:
- Check your internet connection
- Verify wishlist URL is public
- Review the logs for detailed error messages

**Browser Automation Issues**:
- Ensure Playwright is properly installed
- Try refreshing your browser session in Settings
- Check for browser updates

**File Management**:
- Verify download directory permissions
- Check available disk space
- Review file naming conventions

**Service/Daemon Issues**:
- First, ensure the service is installed: `./manage_daemon.sh install`
- Check service status: `./manage_daemon.sh status`
- View service logs: `./manage_daemon.sh logs`
- Restart service: `./manage_daemon.sh restart`
- Check daemon logs: `./manage_daemon.sh daemon-logs`

**Cron Job Issues**:
- Ensure the service is installed and running: `./manage_daemon.sh status`
- Check `logs/cron.log` for cron-specific errors
- Verify service is enabled: `./manage_daemon.sh status`

### Debug Mode

Enable debug mode in Settings to:
- Save detailed debug files
- Get verbose logging
- Generate troubleshooting data

## 📁 Project Structure

```
kindly-sourced-paper/
├── app.py                 # Main Flask application
├── run_flask.py          # Application runner
├── book_downloader.py    # Resource acquisition logic
├── send_to_kindle.py     # E-reader integration
├── wishlist_scraper.py   # Wishlist monitoring
├── settings.py           # Configuration management
├── logger.py             # Centralized logging
├── templates/            # Web interface templates
├── static/              # CSS, JS, and assets
└── requirements.txt     # Python dependencies
```

## 🔒 Privacy & Security

- **Local Operation**: All processing happens on your machine
- **No Data Sharing**: Your preferences and data stay private
- **Secure Storage**: Sensitive data is encrypted and protected
- **Open Source**: Full transparency - inspect the code yourself

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome! Feel free to:
- Report bugs via GitHub Issues
- Suggest features or improvements
- Submit pull requests for fixes

## 📄 License

This project is for educational purposes only. Users are responsible for ensuring their usage complies with all applicable laws and terms of service.

## 🎉 Acknowledgments

- Built with Flask, Playwright, and lots of coffee ☕
- Inspired by the need for better digital library management
- Thanks to the open-source community for amazing tools

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the application logs
3. Create a GitHub issue with details


## TODO 
There's alwasy more to be done...
- [ ] Allow us to update the polling (Like every 12 hours via the app) (instead of using CRON) (And update the readme)
- [ ] Setup misses are not obvious when I need to authenticate/upload to kindle... it just fails... and I have to look ... Both auth and Wishlist being empty are not obvious failures...

---

*Remember: This tool is for educational purposes only. Always respect copyright laws and terms of service.*


