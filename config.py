import os
## Normal Configuration
# Amazon Wishlist Configuration (be sure it's public!)
WISHLIST_URL = "https://www.amazon.com/hz/wishlist/ls/3W5CPCQO3G9NH"  # Your wishlist ID


## Advanced Configuration
# File System Configuration (You can leave this alone...)
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# This is finicky for me, AKA not working... feel free to fix it...
STATUS_MESSAGE_PHONE_NUMBER = None
