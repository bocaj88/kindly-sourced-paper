"""
Author: Jake Michalski
Date: 6/16/2025
Project Name: Kindle Fetcher
Description:
    This script is used to download books from the wishlist and send them to the Kindle.

CondaEnv: kindle_fetcher
"""

import os, time, argparse
from wishlist_scraper import get_wishlist_books
from book_downloader import search_and_download_book
from send_to_kindle import send_epub_to_kindle
# from email_to_kindle import email_file_to_kindle
from config import DOWNLOAD_DIR, STATUS_MESSAGE_PHONE_NUMBER
import settings
import logger

if STATUS_MESSAGE_PHONE_NUMBER:
    from gmail import CommObj


ALREADY_DOWNLOADED_FILE = os.path.join(DOWNLOAD_DIR, "already_downloaded.txt")


class FakeCom:
    def send(self, message):
        logger.info(f"SMS: {message}")

def main():
    if STATUS_MESSAGE_PHONE_NUMBER:
        com = CommObj(STATUS_MESSAGE_PHONE_NUMBER)
    else:
        com = FakeCom()

    try:
        ## Get the books from the wishlist and those we have already downloaded
        already_downloaded = get_already_downloaded()
        wishlist_url = settings.get_wishlist_url()
        books = get_wishlist_books(wishlist_url)
        if len(books) == 0:
            # Try again in ~10 seconds
            time.sleep(10)
            books = get_wishlist_books(wishlist_url)
        
        # books = [{'title': 'Buy Back Your Time: Get Unstuck, Reclaim Your Freedom, and Build Your Empire', 'author': 'Dan   Martell', 'url': 'https://www.amazon.com/dp/B09Y55GLXJ/', 'isbn': '\u200e978-0593422984'}, {'title': 'Atomic Habits: An Easy & Proven Way to Build Good Habits & Break Bad Ones', 'author': 'James Clear', 'url': 'https://www.amazon.com/dp/B07D23CFGR/', 'isbn': '\u200e978-0735211308'}, {'title': 'The Guest List: A Novel', 'author': 'Lucy Foley', 'url': 'https://www.amazon.com/dp/B07WG8L7WC/', 'isbn': '\u200e978-0062868954'}, {'title': 'Topgrading, 3rd Edition: The Proven Hiring and Promoting Method That Turbocharges Company Performance', 'author': 'Bradford D. Smart Ph.D.', 'url': 'https://www.amazon.com/dp/1591845262/', 'isbn': '\u200e978-1591845263'}, {'title': 'Art of the Start 2.0: The Time-Tested, Battle-Hardened Guide for Anyone Starting Anything', 'author': 'Guy Kawasaki', 'url': 'https://www.amazon.com/dp/0241187265/', 'isbn': '\u200e978-0241187265'}, {'title': "Broken Country (Reese's Book Club)", 'author': 'Clare Leslie Hall', 'url': 'https://www.amazon.com/dp/B0CW1J2FDT/', 'isbn': '\u200e978-1668078204'}]

        successful_books = 0
        failed_books = 0
        
        for book in books:
            if book['title'] not in already_downloaded:
                try:
                    ## Download the book
                    logger.info(f"Processing: {book['title']} by {book['author']}")
                    com.send(f"Downloading {book['title']} by {book['author']}")
                    download_result = search_and_download_book(book['title'], book['author'], book['isbn'], preferred_formats=['epub'])
                    
                    if not download_result:
                        logger.warning(f"Failed to download {book['title']} by {book['author']}")
                        com.send(f"Failed to download {book['title']} by {book['author']}")
                        failed_books += 1
                        continue
                    
                    ## Send the book to the Kindle
                    logger.info(f"Download successful, sending to Kindle: {book['title']}")
                    com.send(f"Got it! Sending to Kindle...")
                    epub_path = download_result['download_result']
                    res = send_epub_to_kindle(epub_path)
                    # res = email_file_to_kindle(epub_path)
                    if res:
                        logger.info(f"Successfully sent to Kindle: {book['title']}")
                        com.send(f"Sent to Kindle!")
                        successful_books += 1
                        # Save the book to the already downloaded file
                        save_already_downloaded(book['title'])
                    else:
                        logger.error(f"Failed to send to Kindle: {book['title']}")
                        com.send(f"Failed to send to Kindle!")
                        failed_books += 1
                        continue
                        
                except Exception as e:
                    # Log the error and continue with the next book
                    error_msg = f"Error processing {book['title']}: {str(e)}"
                    logger.error(error_msg)
                    com.send(error_msg)
                    failed_books += 1
                    continue
        
        # Send summary message
        total_processed = successful_books + failed_books
        if total_processed > 0:
            summary_msg = f"Processing complete: {successful_books} successful, {failed_books} failed out of {total_processed} books"
            logger.info(summary_msg)
            com.send(summary_msg)
        else:
            logger.info("No new books to process")
            com.send("No new books found in wishlist")
    
    except Exception as e:
        # If we failed anywhere along the way, send a message to the user
        com.send(f"Error: {e}")
        raise e


def manual_search(search_query):
    try:
        logger.info(f"Starting manual search for: {search_query}")
        download_result = search_and_download_book(search_query, preferred_formats=['epub'])
        if not download_result:
            logger.error("Failed to download book!")
            return False
        
        logger.info("Downloaded book! Uploading to Kindle...")
        epub_path = download_result['download_result']
        res = send_epub_to_kindle(epub_path)
        if not res:
            logger.error("Failed to send to Kindle!")
            return False
        
        logger.info("Sent to Kindle!")
        return True
    except Exception as e:
        logger.error(f"Error during manual search: {str(e)}")
        return False

def get_already_downloaded():
    if not os.path.exists(ALREADY_DOWNLOADED_FILE):
        # create the file
        with open(ALREADY_DOWNLOADED_FILE, "w") as f:
            f.write("")
            return set()
        
    with open(ALREADY_DOWNLOADED_FILE, "r") as f:
        return set(f.read().splitlines())

def save_already_downloaded(book):
    with open(ALREADY_DOWNLOADED_FILE, "a") as f:
        if isinstance(book, dict):
            f.write(book['title'] + "\n")
        else:
            f.write(book + "\n")



if __name__ == "__main__":    
    parser = argparse.ArgumentParser(description='Book downloader and Kindle sender')
    parser.add_argument('--search', type=str, help='Manual search for a book', required=False)
    args = parser.parse_args()
    
    if args.search:
        manual_search(args.search)
    else:
        main()