# src/downloader.py
import requests
from bs4 import BeautifulSoup

def download_rule(url):
    """
    Downloads and extracts text from a FINRA/SEC rule page.
    Includes 'Stealth Mode' headers to bypass basic bot detection.
    """
    # 1. The Disguise: Pretend to be a Chrome Browser on a Mac
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Check for 403 Forbidden or 404 Errors
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 2. The Target: Try to find the specific box where the law lives
        # FINRA uses these classes often:
        content_div = soup.find('div', class_='rule-book-content') or \
                      soup.find('div', class_='field-item even') or \
                      soup.find('div', id='block-system-main')
        
        if content_div:
            # Clean up the text (remove extra spaces)
            return content_div.get_text(separator='\n').strip()
        else:
            return "Error: Could not find rule content on page."

    except Exception as e:
        return f"Connection Error: {e}"
