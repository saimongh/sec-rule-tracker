# src/downloader.py
import requests
from bs4 import BeautifulSoup

def download_rule(url):
    """
    Downloads and extracts text from a FINRA/SEC rule page.
    Includes 'Stealth Mode' and multiple fallback selectors.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # LIST OF TARGETS: We try these one by one until we find text.
        # These are common HTML containers used on government sites.
        possible_targets = [
            {'class_': 'rule-book-content'},          # Standard FINRA box
            {'class_': 'field-item even'},            # Older pages
            {'id': 'block-system-main'},              # Main content block
            {'class_': 'field--name-body'},           # Drupal default
            {'role': 'main'},                         # Semantic HTML
            {'tag': 'article'}                        # Generic Article
        ]

        content_div = None
        
        # 1. Try specific selectors first
        for target in possible_targets:
            if 'tag' in target:
                content_div = soup.find(target['tag'])
            else:
                content_div = soup.find('div', **target) or soup.find('section', **target)
            
            # If we found it AND it has enough text, stop looking
            if content_div and len(content_div.get_text(strip=True)) > 50:
                break
        
        # 2. Last Resort: If nothing worked, try to grab all paragraphs
        if not content_div:
            text_content = "\n".join([p.get_text() for p in soup.find_all('p')])
            if len(text_content) > 100:
                return text_content.strip()

        # 3. Return the prize (or the error)
        if content_div:
            return content_div.get_text(separator='\n').strip()
        else:
            return "Error: Could not find rule content. The page structure might have changed."

    except Exception as e:
        return f"Connection Error: {e}"
