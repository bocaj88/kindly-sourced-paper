import os
import json
import time
import base64
import asyncio
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import logger
import settings



SEND_TO_KINDLE_URL = "https://www.amazon.com/sendtokindle"
COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kindle_cookies.json")

def get_amazon_credentials():
    """Get Amazon credentials from settings"""
    return settings.get_amazon_credentials()

def send_epub_to_kindle(epub_path, force_reauth=False):
    """
    Send an EPUB file to Kindle using saved session data.
    
    Args:
        epub_path: Path to the EPUB file
        force_reauth: If True, forces re-authentication even if session exists
        
    Returns True if successful, False otherwise.
    """
    if not os.path.exists(epub_path):
        logger.error(f"File not found: {epub_path}")
        return False

    # Check if we have saved session data
    if not force_reauth and not os.path.exists(COOKIES_FILE):
        logger.error("No saved authentication found.")
        logger.info("Please run setup_kindle_auth() first or use the setup script.")
        return False

    with sync_playwright() as p:
        try:
            # Launch browser
            logger.info("Launching browser...")
            browser = p.chromium.launch(
                headless=False,  # Set to True for headless mode
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor"
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            logger.info("Browser launched successfully")
            
            # Load saved session data unless forcing reauth
            session_loaded = False
            if not force_reauth:
                session_loaded = load_session_data(context, page)
            
            if session_loaded:
                # Navigate to Send to Kindle page
                page.goto(SEND_TO_KINDLE_URL)
                page.wait_for_load_state('domcontentloaded')
                
                # Verify session is still valid
                if not is_session_valid(page):
                    logger.error("Saved session is no longer valid - attempting automatic re-authentication")
                    
                    # Try automatic re-authentication with stored credentials
                    amazon_email, amazon_password = get_amazon_credentials()
                    if amazon_email and amazon_password:
                        logger.info("Found stored credentials, attempting automatic login...")
                        # Navigate to Send to Kindle page to start fresh
                        page.goto(SEND_TO_KINDLE_URL)
                        page.wait_for_load_state('domcontentloaded')
                        
                        # Look for sign in button and attempt login
                        try:
                            signin_btn = page.locator("[id*='sign-in-button']")
                            if signin_btn.count() > 0:
                                success = perform_login(page, amazon_email, amazon_password)
                                if success:
                                    # Save the new session data
                                    cookies = context.cookies()
                                    session_data = {
                                        'cookies': cookies,
                                        'current_url': page.url,
                                        'local_storage': {},
                                        'session_storage': {},
                                        'timestamp': time.time()
                                    }
                                    try:
                                        with open(COOKIES_FILE, 'w') as f:
                                            json.dump(session_data, f, indent=2)
                                        logger.info("New session data saved successfully")
                                    except Exception as e:
                                        logger.warning(f"Could not save new session data: {e}")
                                else:
                                    logger.error("Automatic re-authentication failed")
                                    return False
                            else:
                                logger.error("Sign in button not found")
                                return False
                        except Exception as e:
                            logger.error(f"Error during automatic re-authentication: {e}")
                            return False
                    else:
                        logger.error("No stored credentials available for automatic re-authentication")
                        logger.info("Please run setup_kindle_auth() again or configure credentials in Settings")
                        return False
            else:
                logger.error("No valid session data available")
                
                # Try automatic authentication with stored credentials
                amazon_email, amazon_password = get_amazon_credentials()
                if amazon_email and amazon_password:
                    logger.info("No saved session found, but found stored credentials. Attempting automatic login...")
                    # Navigate to Send to Kindle page
                    page.goto(SEND_TO_KINDLE_URL)
                    page.wait_for_load_state('domcontentloaded')
                    
                    # Look for sign in button and attempt login
                    try:
                        signin_btn = page.locator("[id*='sign-in-button']")
                        if signin_btn.count() > 0:
                            success = perform_login(page, amazon_email, amazon_password)
                            if success:
                                # Save the new session data
                                cookies = context.cookies()
                                session_data = {
                                    'cookies': cookies,
                                    'current_url': page.url,
                                    'local_storage': {},
                                    'session_storage': {},
                                    'timestamp': time.time()
                                }
                                try:
                                    with open(COOKIES_FILE, 'w') as f:
                                        json.dump(session_data, f, indent=2)
                                    logger.info("New session data saved successfully")
                                except Exception as e:
                                    logger.warning(f"Could not save new session data: {e}")
                            else:
                                logger.error("Automatic authentication failed")
                                logger.info("Please run setup_kindle_auth() first to authenticate manually")
                                return False
                        else:
                            logger.error("Sign in button not found")
                            return False
                    except Exception as e:
                        logger.error(f"Error during automatic authentication: {e}")
                        return False
                else:
                    logger.info("Please run setup_kindle_auth() first to authenticate or configure credentials in Settings")
                    return False
            
            # At this point we should be authenticated and on the Send to Kindle page
            logger.info(f"Uploading {epub_path}")
            
            # Wait for the drag-and-drop container
            logger.info("Looking for upload container...")
            upload_container = page.locator("#s2k-dnd-container")
            upload_container.wait_for(state="visible", timeout=30000)
            logger.info("Upload container found")
            
            # Scroll to the upload area
            upload_container.scroll_into_view_if_needed()
            time.sleep(1)
            
            # Imitate a drag and drop using a fancy data buffer
            logger.info(f"Uploading file: {os.path.abspath(epub_path)}")

            file_path = os.path.abspath(epub_path)
            file_name = Path(file_path).name
            
            # Read file content as base64
            with open(file_path, "rb") as f:
                content = f.read()
            
            logger.debug(f"Creating DataTransfer object with file: {file_name}")
            
            # Create DataTransfer in page context with actual file content
            data_transfer = page.evaluate_handle(
                """async ({ name, buffer }) => {
                    const dt = new DataTransfer();
                    const uint8Array = Uint8Array.from(atob(buffer), c => c.charCodeAt(0));
                    const file = new File([uint8Array], name, { type: 'application/epub+zip' });
                    dt.items.add(file);
                    return dt;
                }""",
                {
                    "name": file_name,
                    "buffer": base64.b64encode(content).decode("utf-8"),
                },
            )
            
            logger.debug("Dispatching drag and drop events with file data...")
            # Dispatch drag events with actual file data
            upload_container.dispatch_event("dragenter", {"dataTransfer": data_transfer})
            upload_container.dispatch_event("dragover", {"dataTransfer": data_transfer})
            upload_container.dispatch_event("drop", {"dataTransfer": data_transfer})
            
            # File dragged in, win!
            # Now it's time to hit the send button 
            # Wait for and click the send button
            logger.info("Looking for send button...")
            send_button = page.locator("#s2k-r2s-send-button")
            send_button.wait_for(state="visible", timeout=30000)
            logger.info("Send button found, clicking...")
            send_button.click()
            
            logger.info("File upload initiated")
            
            # Wait for upload confirmation
            logger.info("Waiting for upload confirmation...")
            # Wait for the success header to appear
            success_header = page.locator("#s2k-dnd-files-on-the-way-header")
            success_header.wait_for(state="visible", timeout=30000)
            logger.info("Success header found, upload successful!")
            return True

                
        except Exception as e:
            logger.error(f"Error during Kindle upload: {str(e)}")
            return False
            
        finally:
            try:
                context.close()
                browser.close()
            except:
                pass


def is_session_valid(page):
    """
    Check if the current session is valid by looking for the upload form.
    Returns True if valid, False otherwise.
    """
    try:
        page.goto(SEND_TO_KINDLE_URL)
        page.wait_for_load_state('domcontentloaded')
        
        # Look for upload form
        upload_button = page.locator("#s2k-dnd-add-your-files-button")
        if upload_button.count() > 0:
            logger.info("Session is valid - upload form found")
            return True
        else:
            logger.warning("Session invalid - upload form not found")
            return False
        
    except Exception as e:
        logger.error(f"Error checking session validity: {e}")
        return False


def load_session_data(context, page):
    """
    Load saved session data into the browser context.
    Returns True if successful, False otherwise.
    """
    if not os.path.exists(COOKIES_FILE):
        logger.warning("No saved session data found")
        return False
    
    try:
        with open(COOKIES_FILE, 'r') as f:
            session_data = json.load(f)
        
        # Check if session data is too old (older than 24 hours)
        if 'timestamp' in session_data:
            age_hours = (time.time() - session_data['timestamp']) / 3600
            if age_hours > 24:
                print(f"Session data is {age_hours:.1f} hours old - may need refresh")
        
        print("Loading saved session data...")
        
        # Load cookies
        if 'cookies' in session_data:
            # Convert Selenium cookie format to Playwright format
            playwright_cookies = []
            for cookie in session_data['cookies']:
                playwright_cookie = {
                    'name': cookie['name'],
                    'value': cookie['value'],
                    'domain': cookie['domain'],
                    'path': cookie.get('path', '/'),
                }
                # Add optional fields if they exist
                if 'expires' in cookie:
                    playwright_cookie['expires'] = cookie['expires']
                if 'httpOnly' in cookie:
                    playwright_cookie['httpOnly'] = cookie['httpOnly']
                if 'secure' in cookie:
                    playwright_cookie['secure'] = cookie['secure']
                if 'sameSite' in cookie:
                    playwright_cookie['sameSite'] = cookie['sameSite']
                    
                playwright_cookies.append(playwright_cookie)
            
            context.add_cookies(playwright_cookies)
            print(f"Loaded {len(playwright_cookies)} cookies")
        
        # Navigate to Amazon first to establish session
        page.goto("https://www.amazon.com")
        page.wait_for_load_state('domcontentloaded')
        
        # Load local storage and session storage
        if 'local_storage' in session_data:
            for key, value in session_data['local_storage'].items():
                try:
                    page.evaluate(f"localStorage.setItem('{key}', '{value}');")
                except Exception as e:
                    print(f"Could not set localStorage {key}: {e}")
        
        if 'session_storage' in session_data:
            for key, value in session_data['session_storage'].items():
                try:
                    page.evaluate(f"sessionStorage.setItem('{key}', '{value}');")
                except Exception as e:
                    print(f"Could not set sessionStorage {key}: {e}")
        
        print("Session data loaded successfully")
        return True
        
    except Exception as e:
        print(f"Error loading session data: {e}")
        return False


def setup_kindle_auth():
    """
    One-time setup to authenticate with Amazon and save session data.
    Should be run once initially to establish authentication.
    Returns True if successful, False otherwise.
    """
    print("Setting up Kindle authentication...")
    print("This is a one-time setup that will save your session for future use.")
    
    with sync_playwright() as p:
        try:
            # Launch browser
            browser = p.chromium.launch(
                headless=False,  # Keep visible for authentication
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor"
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = context.new_page()
            print("Browser launched successfully")
            
            # Navigate to Send to Kindle page
            page.goto(SEND_TO_KINDLE_URL)
            page.wait_for_load_state('domcontentloaded')
            
            # Look for sign in button
            signin_btn = page.locator("[id*='sign-in-button']")
            
            # Attempt automatic login if credentials are provided
            amazon_email, amazon_password = get_amazon_credentials()
            if amazon_email and amazon_password:
                success = perform_login(page, amazon_email, amazon_password)
                if not success:
                    print("Automatic login failed - please sign in manually")
            else:
                print("No credentials configured - please sign in manually")
                print("Configure Amazon username and password in the Settings page for automatic login")
            
            # Wait for login to complete
            try:
                upload_button = page.locator("#s2k-dnd-add-your-files-button")
                upload_button.wait_for(state="visible", timeout=120*1000)
                print("Login successful!")
            except PlaywrightTimeoutError:
                print("Login verification failed - please ensure you're signed in")
                input("Press Enter if you have successfully signed in...")
            
            # Save complete session data
            cookies = context.cookies()
            
            session_data = {
                'cookies': cookies,
                'current_url': page.url,
                'local_storage': {},
                'session_storage': {},
                'timestamp': time.time()
            }
            
            # Get local storage and session storage
            try:
                local_storage = page.evaluate("""
                    () => {
                        const ls = {};
                        for (let i = 0; i < localStorage.length; i++) {
                            const key = localStorage.key(i);
                            ls[key] = localStorage.getItem(key);
                        }
                        return ls;
                    }
                """)
                session_data['local_storage'] = local_storage
                
                session_storage = page.evaluate("""
                    () => {
                        const ss = {};
                        for (let i = 0; i < sessionStorage.length; i++) {
                            const key = sessionStorage.key(i);
                            ss[key] = sessionStorage.getItem(key);
                        }
                        return ss;
                    }
                """)
                session_data['session_storage'] = session_storage
                
            except Exception as e:
                print(f"Could not save storage data: {e}")
            
            # Save session data to file
            try:
                os.makedirs(os.path.dirname(COOKIES_FILE), exist_ok=True)
                with open(COOKIES_FILE, 'w') as f:
                    json.dump(session_data, f, indent=2)
                print(f"Session data saved successfully to {COOKIES_FILE}")
                return True
                
            except Exception as e:
                print(f"Failed to save session data: {e}")
                return False
                
        except Exception as e:
            print(f"Error during setup: {str(e)}")
            return False
            
        finally:
            try:
                context.close()
                browser.close()
            except:
                pass


def perform_login(page, email, password):
    """Automatically perform Amazon login"""
    print("Attempting automatic login...")
    
    try:
        # Find and click sign in button
        signin_btn = page.locator("[id='s2k-dnd-sign-in-button']")
        signin_btn.click()
        page.wait_for_load_state('domcontentloaded')
        
        # Check if we just need password or email too 
        password_field = page.locator("input[type='password']")
        try:
            password_field.wait_for(state="visible", timeout=10000)
        except PlaywrightTimeoutError:
            # No password field found, so we need to fill email first
            email_field = page.locator("input[type='email']")
            email_field.wait_for(state="visible", timeout=10000)
            email_field.fill(email)
            print("Email entered")
                
            # Click continue button
            continue_btn = page.locator("#continue")
            continue_btn.click()
            page.wait_for_load_state('domcontentloaded')
        
            # Wait for and fill password field
            password_field = page.locator("input[type='password']")
            password_field.wait_for(state="visible", timeout=10000)
        
        password_field.fill(password)
        print("Password entered")
        
        # Click sign in button
        signin_btn = page.locator("#signInSubmit")
        signin_btn.click()
        print("Sign in button clicked")
        
        page.wait_for_load_state('domcontentloaded')
        
        # Check for 2FA
        try:
            two_factor_input = page.locator("input[name='otpCode'], input[name='code']")
            if two_factor_input.count() > 0:
                print("2FA detected - please enter the code manually")
                input("Please complete 2FA and press Enter...")
                return True
        except:
            pass
        
        print("Login successful!")
        return True
        
    except PlaywrightTimeoutError as e:
        print(f"Login failed: {str(e)}")
        return False
    except Exception as e:
        print(f"Login error: {str(e)}")
        return False


if __name__ == "__main__":
    import sys
    
    def print_usage():
        """Print usage information"""
        print("Usage:")
        print("  python send_to_kindle.py <epub_file>     # Send an EPUB file to Kindle")
        print("  python send_to_kindle.py setup           # Run authentication setup")
        print("  python send_to_kindle.py --help          # Show this help message")
        print()
        print("Examples:")
        print("  python send_to_kindle.py book.epub")
        print("  python send_to_kindle.py setup")
    
    def main():
        """Main function to handle command line arguments"""
        # Check for help or setup commands
        if len(sys.argv) > 1:
            if sys.argv[1] in ['--help', '-h', 'help']:
                print_usage()
                return True
            elif sys.argv[1] == 'setup':
                print("Running authentication setup...")
                success = setup_kindle_auth()
                if success:
                    print("✅ Setup completed successfully!")
                else:
                    print("❌ Setup failed. Please try again.")
                return success
            else:
                epub_path = sys.argv[1]
        else:
            # Prompt user for file path
            epub_path = input("Enter the path to your EPUB file (or 'setup' to configure authentication): ").strip()
            
            if epub_path.lower() == 'setup':
                print("Running authentication setup...")
                success = setup_kindle_auth()
                if success:
                    print("✅ Setup completed successfully!")
                else:
                    print("❌ Setup failed. Please try again.")
                return success
            
        # Remove quotes if user wrapped the path in quotes
        if epub_path.startswith('"') and epub_path.endswith('"'):
            epub_path = epub_path[1:-1]
        elif epub_path.startswith("'") and epub_path.endswith("'"):
            epub_path = epub_path[1:-1]
            
        # Check if file exists
        if not os.path.exists(epub_path):
            print(f"Error: File not found at '{epub_path}'")
            print("Please check the file path and try again.")
            print()
            print("If you haven't set up authentication yet, run:")
            print("  python send_to_kindle.py setup")
            return False
            
        # Check if it's an EPUB file
        if not epub_path.lower().endswith('.epub'):
            print(f"Warning: '{epub_path}' doesn't appear to be an EPUB file")
            proceed = input("Do you want to proceed anyway? (y/n): ").strip().lower()
            if proceed not in ['y', 'yes']:
                return False
        
        # Check if authentication is set up
        if not os.path.exists(COOKIES_FILE):
            print("❌ No authentication found.")
            print("Please run the setup first:")
            print("  python send_to_kindle.py setup")
            return False
        
        print(f"Attempting to send '{epub_path}' to Kindle...")
        print("This will open a browser window. Please be patient during the upload process.")
        print("-" * 60)
        
        # Call the main function
        success = send_epub_to_kindle(epub_path)
        
        print("-" * 60)
        if success:
            print("✅ Successfully sent EPUB to Kindle!")
        else:
            print("❌ Failed to send EPUB to Kindle.")
            print("If authentication expired, try running setup again:")
            print("  python send_to_kindle.py setup")
            
        return success
    
    # Run the main function
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}") 