#!/usr/bin/env python3
"""
Setup script for Playwright browsers
Run this after installing the requirements.txt to install the browser binaries
"""

import subprocess
import sys
import os

def install_playwright_browsers():
    """Install Playwright browser binaries"""
    print("🎭 Installing Playwright browsers...")
    print("This will download Chromium, Firefox, and WebKit browsers.")
    print("This may take a few minutes depending on your internet connection.")
    print()
    
    try:
        # Install all browsers
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Playwright browsers installed successfully!")
        print()
        print("You can now use the send_to_kindle.py script.")
        print("To get started, run:")
        print("  python send_to_kindle.py setup")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("❌ Failed to install Playwright browsers")
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error output: {e.stderr}")
        print()
        print("You can try installing manually with:")
        print("  python -m playwright install")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_playwright_installation():
    """Check if Playwright is properly installed"""
    try:
        import playwright
        # Try to get version, but don't fail if it's not available
        try:
            from playwright import __version__
            print(f"✅ Playwright Python package found (version: {__version__})")
        except (ImportError, AttributeError):
            print("✅ Playwright Python package found")
        return True
    except ImportError:
        print("❌ Playwright Python package not found")
        print("Please install it first with:")
        print("  pip install -r requirements.txt")
        return False

def main():
    print("🔧 Playwright Setup for Kindle Source")
    print("=" * 50)
    
    # Check if Playwright package is installed
    if not check_playwright_installation():
        return False
    
    # Install browsers
    success = install_playwright_browsers()
    
    if success:
        print()
        print("🎉 Setup complete!")
        print()
        print("Next steps:")
        print("See the Git Repo README.md for next steps!")
    
    return success

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error during setup: {e}") 