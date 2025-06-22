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

5. **Run the application**:
   ```bash
   python run_flask.py
   ```

6. **Open your browser** and navigate to: `http://localhost:5001`

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

---

*Remember: This tool is for educational purposes only. Always respect copyright laws and terms of service.*