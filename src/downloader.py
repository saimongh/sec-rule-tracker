# src/downloader.py
import requests
from bs4 import BeautifulSoup
import time

def download_rule(url):
    """
    Downloads rule text. Includes heavy error handling and fallbacks.
    """
    # Use a very standard 'Real Person' User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }
    
    try:
        # 1. Try to connect
        response = requests.get(url, headers=headers, timeout=15)
        
        # If FINRA blocks us (403 Forbidden), return a clear error
        if response.status_code == 403:
            return "Error 403: FINRA blocked the automated request. Use 'Load Test Data' to demo."
        
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 2. Aggressive Text Extraction
        # We try specific containers first, but if they fail, we grab the whole body
        content = ""
        
        # Try finding the main rule container (specific to FINRA)
        target = soup.find('div', class_='rule-book-content') or \
                 soup.find('div', class_='field-item even') or \
                 soup.find('div', id='block-system-main')
                 
        if target:
            content = target.get_text(separator='\n').strip()
        
        # FALLBACK: If specific targets failed, grab all paragraph text
        if len(content) < 100:
            paragraphs = soup.find_all('p')
            content = "\n\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20])
            
        # 3. Final Check
        if len(content) < 50:
            return "Error: Connected to page but found no readable text."
            
        return content

    except Exception as e:
        return f"Connection Error: {str(e)}"
