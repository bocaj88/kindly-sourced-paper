import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
from bs4 import BeautifulSoup
import re
import logger
import settings

def get_page_content(url, headers):
    """Fetch and parse a webpage."""
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return None

def is_private_wishlist(soup):
    """Check if the wishlist is private."""
    return "This list is private" in str(soup) or "This list is not public" in str(soup)

def get_book_details(detail_url, headers):
    """Extract book details (author, ISBN) from the detail page."""
    try:
        detail_soup = get_page_content(detail_url, headers)
        if not detail_soup:
            return None, None

        # Extract author
        author = "Author not found"
        by_text = detail_soup.find(string=lambda s: s and 'by' in s.lower())
        if by_text:
            author_link = by_text.find_next('a')
            if author_link:
                author = author_link.get_text(strip=True)

        # Extract ISBN
        isbn = "ISBN not found"
        isbn_section = detail_soup.find(string=lambda s: s and 'isbn' in s.lower())
        if isbn_section:
            isbn = isbn_section.find_next(string=True).strip()

        return author, isbn
    except Exception as e:
        logger.error(f"Error getting book details: {str(e)}")
        return None, None

def find_parent_with_author(element):
    """Find the parent element that contains both title and author info."""
    parent = element
    while parent and not (parent.find('a', string=lambda s: s and 'by' in s.lower()) or 
                         parent.find(string=lambda s: s and 'by' in s.lower())):
        parent = parent.parent
    return parent

def is_book_item(text):
    """Check if an item is likely a book based on its text content."""
    keywords = ['kindle', 'book', 'ebook', 'author', 'isbn', 'hardcover', 'paperback']
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)

def get_wishlist_books(wishlist_url):
    """
    Scrape the Amazon wishlist for Kindle books.
    Returns a list of dicts with title, author, and ISBN.
    """
    try:
        # Use cached browser user agent for better Amazon compatibility
        user_agent = settings.get_cached_user_agent()
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        logger.info(f"Using cached user agent: {user_agent[:50]}...")
        
        logger.info(f"Fetching wishlist from: {wishlist_url}")
        resp = requests.get(wishlist_url, headers=headers)
        resp.raise_for_status()
        
        # Print the first 1000 characters of the HTML for debugging
        # logger.debug("\n--- HTML Preview ---")
        # logger.debug(resp.text[:1000])
        # logger.debug("--- END HTML Preview ---\n")
        
        # Debug: Print response status and headers
        logger.info(f"Response Status: {resp.status_code}")
        logger.info(f"Content Type: {resp.headers.get('content-type', 'unknown')}")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Save the HTML to a file for inspection
        debug_dir = 'static/debug'
        os.makedirs(debug_dir, exist_ok=True)
        with open(os.path.join(debug_dir, 'wishlist_debug.html'), 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        logger.info("HTML saved to static/debug/wishlist_debug.html for inspection")
        
        # Debug: Print page title
        logger.info(f"Page Title: {soup.title.string if soup.title else 'No title'}")
        
        
        # Debug: Print all links that might be book links
        logger.info("Looking for book links...")
        book_links = soup.find_all('a', href=lambda x: x and 'dp/' in x)
        logger.info(f"Found {len(book_links)} potential book links")
        books = []
        seen_urls = set()  # Cache to avoid duplicates
        for link in book_links:
            href = link.get('href', '')
            if href.startswith('/'):
                href = f"https://www.amazon.com{href}"
            # Strip everything after '?' to remove parameters
            href = href.split('?')[0]
            # Skip if URL already seen
            if href in seen_urls:
                continue
            seen_urls.add(href)
            logger.debug(f"Link: {href}")
            logger.debug(f"Text: {link.get_text(strip=True)}")           
            # Get detailed book information using the wishlist page.
            title, author, isbn = get_book_details_from_wishlist(href, soup)
            if not title:
                # If it fails try the URL directly... this often times fails headless. 
                title, author, isbn = get_book_details_from_url(href)                
            logger.debug(f"  Title: {title}")
            logger.debug(f"  Author: {author}")
            logger.debug(f"  ISBN: {isbn}")
            if not title:
                logger.error(f"  No title found for {href}")
                continue
            # Save to the list if title and author are found
            if title and author:
                books.append({
                    'title': title,
                    'author': author,
                    'url': href,
                    'isbn': isbn
                })
                logger.info(f"Added book: {title}")
            logger.debug("---")
        
        # Use the correct selector for wishlist items
        wishlist_items = soup.find_all('div', class_='awl-ul-item-container-desktop')
        logger.info(f"Found {len(wishlist_items)} wishlist items using 'awl-ul-item-container-desktop' selector")
        
        return books
        
    except Exception as e:
        logger.error(f"Error scraping wishlist: {str(e)}")
        return []

def get_book_details_from_url(url):
    """Get book details from a specific Amazon book URL."""
    # Use cached browser user agent for better Amazon compatibility
    user_agent = settings.get_cached_user_agent()
    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Get title
        title = None
        title_elem = soup.find('span', {'id': 'productTitle'})
        if title_elem:
            title = title_elem.get_text(strip=True)

        # Get author (try multiple locations)
        author = None
        # Try all possible author locations
        author_selectors = [
            'a.contributorNameID',
            'a.author',
            'a.a-link-normal.contributorNameID',
            'span.author',
            'span.contributorNameID'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author = author_elem.get_text(strip=True)
                # Clean up author name (remove "(Author)" and extra spaces)
                author = re.sub(r'\(Author\)', '', author).strip()
                break

        # Get ISBN from detail bullets
        isbn = None
        detail_bullets = soup.find('div', {'id': 'detailBullets_feature_div'})
        if detail_bullets:
            for li in detail_bullets.find_all('li'):
                text = li.get_text(strip=True)
                if 'ISBN-13' in text:
                    # Extract ISBN using regex
                    match = re.search(r'ISBN-13\s*:\s*([0-9\-]+)', text)
                    if match:
                        isbn = match.group(1)
                    else:
                        # Fallback: split by colon and take the last part
                        isbn = text.split(':')[-1].strip()
                    break

        return title, author, isbn

    except Exception as e:
        logger.error(f"Error getting book details: {str(e)}")
        return None, None, None

def get_book_details_from_wishlist(url, soup):
    """Get book details from the wishlist page."""
    try:
        # Extract ASIN from URL (e.g., /dp/B00280LYIC -> B00280LYIC)
        asin_match = re.search(r'/dp/([A-Z0-9]+)', url)
        if not asin_match:
            logger.debug(f"Could not extract ASIN from URL: {url}")
            return None, None, None
        
        asin = asin_match.group(1)
        logger.debug(f"Looking for ASIN: {asin}")
        
        # Find the specific wishlist item container for this ASIN
        item_container = None
        
        # Find all links to this specific ASIN
        asin_links = soup.find_all('a', href=lambda x: x and f'/dp/{asin}' in x)
        logger.debug(f"Found {len(asin_links)} links to ASIN {asin}")
        
        if not asin_links:
            logger.debug(f"No links found for ASIN: {asin}")
            return None, None, None
        
        # For each link, find the closest container that has both title and author info
        for link in asin_links:
            # Method 1: Look for parent li with awl-item-wrapper (mobile)
            parent_li = link.find_parent('li', class_=lambda x: x and 'awl-item-wrapper' in x)
            if parent_li:
                # Verify this container is specifically for this ASIN by checking if it has title/author
                title_elem = parent_li.find(['h2', 'h3'], class_=lambda x: x and 'item-title' in x) if parent_li else None
                byline_elem = parent_li.find('span', id=lambda x: x and 'item-byline' in x) if parent_li else None
                if title_elem or byline_elem:
                    item_container = parent_li
                    logger.debug(f"Found specific container (li): {parent_li.get('id', 'no-id')}")
                    break
            
            # Method 2: Look for parent div structure (desktop)
            if not item_container:
                # Walk up to find a div that contains both itemName and item-byline elements
                current = link.parent
                while current and current.name != 'body':
                    if current.name == 'div':
                        title_elem = current.find(id=lambda x: x and 'itemName' in x)
                        byline_elem = current.find('span', id=lambda x: x and 'item-byline' in x)
                        if title_elem and byline_elem:
                            item_container = current
                            logger.debug(f"Found specific container (div): {current.get('id', 'no-id')}")
                            break
                    current = current.parent
                    
                if item_container:
                    break
        
        if not item_container:
            logger.debug(f"Could not find specific item container for ASIN: {asin}")
            return None, None, None
        
        # Extract title - try multiple approaches for different layouts
        title = None
        
        # Method 1: Look for h3 with item-title class (mobile version)
        title_elem = item_container.find('h3', class_=lambda x: x and 'item-title' in x)
        if title_elem:
            title = title_elem.get_text(strip=True)
            logger.debug(f"Found title (h3): {title}")
        
        # Method 2: Look for element with id containing "itemName" (desktop version)
        if not title:
            title_elem = item_container.find(id=lambda x: x and 'itemName' in x)
            if title_elem:
                title = title_elem.get_text(strip=True)
                logger.debug(f"Found title (itemName): {title}")
        
        # Method 3: Look for a link with title attribute that matches the ASIN pattern
        if not title:
            title_link = item_container.find('a', {'href': lambda x: x and f'/dp/{asin}' in x, 'title': True})
            if title_link and title_link.get('title'):
                title = title_link.get('title').strip()
                logger.debug(f"Found title (link title): {title}")
        
        # Extract author from byline span with id containing "item-byline"
        author = None
        byline_elem = item_container.find('span', id=lambda x: x and 'item-byline' in x)
        if byline_elem:
            byline_text = byline_elem.get_text(strip=True)
            logger.debug(f"Found byline: {byline_text}")
            
            # Extract author from "by [Author Name] (Kindle Edition)" format
            author_match = re.search(r'by\s+([^(]+)', byline_text)
            if author_match:
                author = author_match.group(1).strip()
                logger.debug(f"Extracted author: {author}")
        
        # For now, return None for ISBN since it's not typically shown on wishlist pages
        isbn = None
        
        return title, author, isbn
        
    except Exception as e:
        logger.error(f"Error extracting book details from wishlist: {str(e)}")
        return None, None, None
    

def test_specific_url():
    test_url = "https://www.amazon.com/dp/B0CW1J2FDT"
    title, author, isbn = get_book_details_from_url(test_url)
    
    logger.info("\nFinal Book Details:")
    logger.info(f"Title: {title}")
    logger.info(f"Author: {author}")
    logger.info(f"ISBN: {isbn}")


def test_wishlist():
    # Test with a specific wishlist URL that has 2 books
    wishlist_url = "https://www.amazon.com/hz/wishlist/ls/3W5CPCQO3G9NH"
    
    logger.info("\nFetching wishlist items...")
    books = get_wishlist_books(wishlist_url)

    
    logger.info(f"\nFound {len(books)} books in wishlist")
    for book in books:
        logger.info(f"Title: {book['title']}")
        logger.info(f"Author: {book['author']}")
        logger.info(f"ISBN: {book['isbn']}")
        logger.info(f"URL: {book['url']}")
        logger.info("-" * 50)

    # great, now we have a list of books with title, author, and isbn go download them...


if __name__ == "__main__":
    test_wishlist()
