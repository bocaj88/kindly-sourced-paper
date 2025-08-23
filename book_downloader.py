import os, time, re
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from urllib.parse import urlparse
import difflib
import logger


# Add parent directory to Python path to find utils module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Constants
LIBGEN_BASE_URL = "https://libgen.li"
# Helpful for checking status https://www.libgen.help/
# Another one for status https://open-slum.org/

# Libgen Mirrors:
# .li, .gs, .vg, .la, .bz, .gl, .le

# Other book sites: 
# https://annas-archive.org/
# https://z-lib.gd/
# https://welib.org/


HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    

def search_and_download_book(title, author="", isbn="", download_dir="downloads", preferred_formats=['epub', 'pdf', 'mobi']):
    """
    Search for a book on LibGen and download it if found.
    Tries ISBN first, then title + author, then title only.
    Returns the path to the downloaded file or None if not found.
    """
    # Ensure download directory exists
    os.makedirs(download_dir, exist_ok=True)

    # Create a list of search queries to try
    search_queries = []
    if isbn:
        search_queries.append(isbn)
    if title and author:
        search_queries.append(f"{title} {author}".strip())
    search_queries.append(title)

    # Also include creative search queries, where we regex the name...with and without the author
    search_queries.append(clean_title(title) + " " + author)
    search_queries.append(clean_title(title))

    for search_query in search_queries:
        if result := hunt_for_book(search_query, preferred_formats, download_dir, title): return result
        logger.warning(f"Search query {search_query} failed, trying next...")
        time.sleep(1)

    logger.error(f"No books found for {title} by {author} with ISBN {isbn}")
    return None


def clean_title(title):
    # 1. Remove everything after a colon (common subtitle delimiter)
    title = title.split(':')[0]

    # 2. Remove edition information
    title = re.sub(r'\b\d+(st|nd|rd|th)\s+edition\b', '', title, flags=re.IGNORECASE)

    # 3. Remove content inside parentheses or brackets
    title = re.sub(r'\s*[\(\[].*?[\)\]]', '', title)

    # 4. Remove leading/trailing whitespace and excessive internal spaces
    title = re.sub(r'\s+', ' ', title).strip()

    return title


def hunt_for_book(search_query, preferred_formats=['epub', 'pdf', 'mobi'], download_dir="downloads", original_title=None):
    """
    Search for the link to download a book on LibGen.
    Returns the download URL for the best matching book or None if not found.
    """
    search_url = get_search_url(search_query)
    logger.info(f"Searching LibGen with URL: {search_url}")
    
    response = requests.get(search_url, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    # Save the HTML response for debugging
    debug_dir = 'static/debug'
    os.makedirs(debug_dir, exist_ok=True)
    with open(os.path.join(debug_dir, 'libgen_response.html'), 'w', encoding='utf-8') as f: 
        f.write(soup.prettify())
    logger.info("LibGen Search Results saved to static/debug/libgen_response.html")

    table = soup.select_one("#tablelibgen")
    
    if not table:
        logger.warning("No results table found")
        return None
        
    # Get all rows except the header
    rows = table.find_all("tr")
    
    if not rows:
        logger.warning("No book results found")
        return None
        
    logger.info(f"Found {len(rows)} potential book matches")
    
    # Parse each row to find the best match in the table
    all_results = []
    for i, row in enumerate(rows):
        cells = row.find_all('td')
        
        if len(cells) < 9:  # Need at least 9 columns based on the table structure
            continue
            
        # Extract book information from the row
        # Column 0: Title/ID info
        # Column 1: Author(s) 
        # Column 2: Publisher
        # Column 3: Year
        # Column 4: Language
        # Column 5: Pages
        # Column 6: Size
        # Column 7: File extension
        # Column 8: Mirrors (download links)
        
        title_cell = cells[0]
        author = cells[1].get_text(strip=True)
        publisher = cells[2].get_text(strip=True)
        year = cells[3].get_text(strip=True)
        language = cells[4].get_text(strip=True)
        pages = cells[5].get_text(strip=True)
        size = cells[6].get_text(strip=True)
        file_format = cells[7].get_text(strip=True).lower()
        mirrors_cell = cells[8]
        
        # Extract title from the first cell (it contains links and other info)
        title_obj = title_cell.find('b')
        if title_obj:
            title = title_obj.get_text(strip=True)
        else:
            title_link = title_cell.find('a')
            title = title_link.get_text(strip=True) if title_link else "Unknown Title"
        
        
        
        all_results.append({
            'title': title,
            'author': author,
            'publisher': publisher,
            'year': year,
            'language': language,
            'pages': pages,
            'size': size,
            'file_format': file_format,
            'mirrors': mirrors_cell
        })

    # rank them based on closest match to the real title
    real_title = original_title or search_query
    sorted_results = order_results_by_closest_match(real_title, all_results)

    titles = [res['title'] for res in sorted_results]

    # First check if any have the desired format
    have_desired_format = False
    for result in sorted_results:
        if result['file_format'] in preferred_formats:
            have_desired_format = True
            continue
        
        

    for i, result in enumerate(sorted_results):
        title = result['title']
        author = result['author']
        file_format = result['file_format']
        size = result['size']
        mirrors_cell = result['mirrors']
        
        logger.info(f"Book {i+1}: {title} by {author} ({file_format}, {size})")
        
        # Check if this book matches our preferred formats
        found_format = False
        for preferred_format in preferred_formats:
            if preferred_format.lower() in file_format:
                logger.info(f"Found preferred format {preferred_format} for: {title}")
                found_format = True
                break
                
        # If we have the desired format and this one just isnt it, we continue, but if we don't have the desired format return with anything we have...
        if have_desired_format and not found_format:
            logger.warning(f"Found a book, but format {file_format} not in {preferred_formats}")
            continue
                
        # Get the download link from all mirrors
        while True:
            download_link = extract_download_link(mirrors_cell, cursor=0)
            if not download_link:
                logger.warning(f"No valid download link or ran out of mirrors for {title}")
                break
        
            logger.info(f"Successfully found download link for {title}")
            try:
                download_result = download_book(download_link, download_dir)
            except Exception as e:
                logger.error(f"Failed to download book: {title} on first mirror")
                continue
            
            return {
                'title': title,
                'author': author,
                'format': file_format,
                'size': size,
                'download_url': download_link,
                'download_result': download_result
            }
            
    logger.warning("No books found that work for us...")
    return None

def closest_match(real_title, candidate_title):
    """
    Return a similarity score between 0 and 1 where 1 is an exact match.
    """
    return difflib.SequenceMatcher(None, real_title.lower(), candidate_title.lower()).ratio()

def order_results_by_closest_match(real_title, results):
    """
    Sort a list of results (dicts) by similarity of their 'title' to real_title.
    """
    return sorted(results, key=lambda x: -closest_match(real_title, x['title']))

def make_absolute_url(url):
    """
    Convert a relative URL to an absolute URL using the LIBGEN_BASE_URL.
    """
    if url.startswith('http'):
        return url
    elif url.startswith('/'):
        return LIBGEN_BASE_URL + url
    else:
        return LIBGEN_BASE_URL + '/' + url

def extract_download_link(mirrors_cell, cursor=0):
    """
    Extract the actual download link from the mirrors cell.
    The mirrors cell contains multiple badge links, we want the first one (libgen).
    """
    # Look for links in the mirrors cell
    # The first badge usually points to the libgen mirror: /ads.php?md5=...
    links = mirrors_cell.find_all('a', href=True)
    
    if not links:
        return None
        
    # Get the first mirror link (usually the libgen one)
    if cursor >= len(links):
        return None
    first_link = links[cursor]
    mirror_url = first_link.get('href')
    
    if not mirror_url:
        return extract_download_link(mirrors_cell, cursor=cursor+1)
        
    # Make the mirror URL absolute
    mirror_url = make_absolute_url(mirror_url)
        
    logger.info(f"Found mirror URL: {mirror_url}")

    # Now get this page with soup and find the GET link
    response = requests.get(mirror_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    # Save the HTML response for debugging
    debug_dir = 'static/debug'
    os.makedirs(debug_dir, exist_ok=True)
    with open(os.path.join(debug_dir, 'mirror_response.html'), 'w', encoding='utf-8') as f: 
        f.write(soup.prettify())
    logger.info("Mirror response saved to static/debug/mirror_response.html")

    # The button will be a big GET button
    download_element = soup.find('a', string='GET')
    if not download_element:
        return extract_download_link(mirrors_cell, cursor=cursor+1)
    
    download_link = download_element.get('href')
    
    # Make the download link absolute
    download_link = make_absolute_url(download_link)
    
    return download_link


def get_search_url(search_query):
    """
    Get the search URL for a given search query.
    """
    # https://libgen.li/index.php?req=Art+of+the+Start+guy+kawasaki&columns%5B%5D=t&columns%5B%5D=a&columns%5B%5D=s&columns%5B%5D=y&columns%5B%5D=p&columns%5B%5D=i&objects%5B%5D=f&objects%5B%5D=e&objects%5B%5D=s&objects%5B%5D=a&objects%5B%5D=p&objects%5B%5D=w&topics%5B%5D=l&topics%5B%5D=c&topics%5B%5D=f&topics%5B%5D=a&topics%5B%5D=m&topics%5B%5D=r&topics%5B%5D=s&res=100&filesuns=all
    # This is an example of a search URL where the key was Art of the Start guy kawasaki
    encoded_search_query = quote(search_query)
    return f"{LIBGEN_BASE_URL}/index.php?req={encoded_search_query}&columns%5B%5D=t&columns%5B%5D=a&columns%5B%5D=s&columns%5B%5D=y&columns%5B%5D=p&columns%5B%5D=i&objects%5B%5D=f&objects%5B%5D=e&objects%5B%5D=s&objects%5B%5D=a&objects%5B%5D=p&objects%5B%5D=w&topics%5B%5D=l&topics%5B%5D=c&topics%5B%5D=f&topics%5B%5D=a&topics%5B%5D=m&topics%5B%5D=r&topics%5B%5D=s&res=100&filesuns=all"


def download_book(book_url, download_dir="downloads"):
    """
    Download a book from a given URL.
    Returns the path to the downloaded file or None if not found.
    """
    # Get the download URL from the book page
    # Create download directory if it doesn't exist
    os.makedirs(download_dir, exist_ok=True)
    
    # Download the file
        
    response = requests.get(book_url, stream=True, headers=HEADERS)
    response.raise_for_status()
    
    # Try to get filename from Content-Disposition header
    filename = None
    if 'Content-Disposition' in response.headers:
        content_disposition = response.headers['Content-Disposition']
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
    
    # If no filename from header, try to extract from URL
    if not filename:
        parsed_url = urlparse(book_url)
        filename = os.path.basename(parsed_url.path)
    
    # If still no filename, generate a generic one
    if not filename or filename == '':
        filename = f"book_{int(time.time())}.pdf"
    
    # Ensure the filename has an extension
    if not os.path.splitext(filename)[1]:
        filename += '.pdf'
    
    # Remove any special characters from the filename and strip it
    filename = re.sub(r'[^a-zA-Z0-9.\-_ ]', '_', filename)
    filename = filename.strip()
    filepath = os.path.join(download_dir, filename)
    
    # Download the file in chunks
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    
    logger.info(f"Downloaded book to: {filepath}")
    return filepath
        

def main():
    """
    Main function to download books from Amazon wishlist.
    """
    # Books from Amazon wishlist
    books = [
        {
            "title": "The Giver (Giver Quartet, Book 1)",
            "author": "Lois Lowry"
        },
        {
            "title": "The Guest List: A Novel",
            "author": "Lucy Foley",
            "isbn": "978-0062868954"
        },
        {
            "title": "Atomic Habits: An Easy & Proven Way to Build Good Habits & Break Bad Ones",
            "author": "James Clear",
            "isbn": "978-0735211308"
        },
        {
            "title": "Buy Back Your Time: Get Unstuck, Reclaim Your Freedom, and Build Your Empire",
            "author": "Dan   Martell",
            "isbn": "978-0593422984"
        },
        {
            "title": "Topgrading, 3rd Edition: The Proven Hiring and Promoting Method That Turbocharges Company Performance",
            "author": "Bradford D. Smart Ph.D.",
            "isbn": "978-1591845263"
        },
        {
            "title": "Art of the Start",
            "author": "Guy Kawasaki",
            "isbn": "978-0241187265"
        },
        {
            "title": "Broken Country (Reese's Book Club)",
            "author": "Clare Leslie Hall",
            "isbn": "978-1668078204"
        }
    ]
    
    download_dir = "downloads"
    successful_downloads = []
    failed_downloads = []
    
    logger.info(f"Starting download of {len(books)} books...")
    
    for book in books:
        logger.info(f"\n--- Processing: {book['title']} ---")
        result = search_and_download_book(
            title=book['title'],
            author=book['author'],
            isbn=book.get('isbn'),
            download_dir=download_dir,
            preferred_formats=['epub']
        )
        
        if result:
            successful_downloads.append(book['title'])
            logger.info(f"✓ Successfully downloaded: {book['title']}")
        else:
            failed_downloads.append(book['title'])
            logger.error(f"✗ Failed to download: {book['title']}")
    
    # Summary
    logger.info(f"\n--- Download Summary ---")
    logger.info(f"Total books: {len(books)}")
    logger.info(f"Successful downloads: {len(successful_downloads)}")
    logger.info(f"Failed downloads: {len(failed_downloads)}")
    
    if successful_downloads:
        logger.info("Successfully downloaded:")
        for title in successful_downloads:
            logger.info(f"  - {title}")
    
    if failed_downloads:
        logger.warning("Failed to download:")
        for title in failed_downloads:
            logger.warning(f"  - {title}")

if __name__ == "__main__":
    main() 