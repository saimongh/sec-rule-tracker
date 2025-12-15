# src/downloader.py
import requests
from bs4 import BeautifulSoup

def download_rule(url):
    """
    Downloads text. Logic Updated: Rejects empty containers and forces fallbacks.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Targets to try
        possible_targets = [
            {'class_': 'rule-book-content'},
            {'class_': 'field-item even'},
            {'id': 'block-system-main'},
            {'class_': 'field--name-body'},
            {'role': 'main'},
            {'tag': 'article'}
        ]

        best_text = ""
        
        # 1. Search for specific containers
        for target in possible_targets:
            element = None
            if 'tag' in target:
                element = soup.find(target['tag'])
            else:
                element = soup.find('div', **target) or soup.find('section', **target)
            
            if element:
                text = element.get_text(separator='\n').strip()
                # CRITICAL FIX: Only accept if it has substantial content
                if len(text) > 100:
                    return text
        
        # 2. Fallback: If no container worked, grab all paragraphs
        if len(best_text) < 100:
            paragraphs = soup.find_all('p')
            combined_text = "\n\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 0])
            if len(combined_text) > 100:
                return combined_text

        return "Error: Could not find any rule text on this page."

    except Exception as e:
        return f"Connection Error: {e}"
