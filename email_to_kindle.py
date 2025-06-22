import os
import json
import time
from gmail import CommObj
from config import KINDLE_EMAIL

def email_file_to_kindle(f_path):
    """
    Email a file to Kindle using Gmail.
    Returns True if successful, False otherwise.
    """
    com = CommObj(KINDLE_EMAIL)
    res = com.send("Book Attached", attachments=[f_path])
    return res

def main():
    f_path = "/Users/jakem/Documents/Projects/Coding/KindleSource/downloads/Art of the Start 20 The Time-Tested Battle-Hardened Guide for Anyone Starting Anything.epub"
    email_file_to_kindle(f_path)


if __name__ == "__main__":
    main()