import json
import re
from bs4 import BeautifulSoup
from core.logger import logger

def normalize_price(price_raw):
    """(Pilar 2) Limpa a bagunça: 'R$ 1.200,00' -> 1200.00"""
    if not price_raw: return 0.0
    if isinstance(price_raw, (float, int)): return float(price_raw)
    
    try:
        clean = re.sub(r'[^\d,.]', '', str(price_raw))
        if ',' in clean:
            clean = clean.replace('.', '').replace(',', '.')
        return float(clean)
    except:
        return 0.0

def check_availability(soup):
    """(Pilar 2) Detecta se está em estoque"""
    text = soup.get_text().lower()
    keywords = ['esgotado', 'indisponível', 'sem estoque', 'sold out', 'avise-me']
    for k in keywords:
        if k in text:
            return False # Esgotado
    return True # Disponível

def extract_hybrid(html_content):
    """(Pilar 2) Parser Híbrido: JSON-LD > CSS > Regex"""
    if not html_content: return 0.0, False, "N/A"

    soup = BeautifulSoup(html_content, 'html.parser')
    is_available = check_availability(soup)
    
    # 1. JSON-LD (Padrão Ouro)
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, list): data = data[0]
            offers = data.get('offers', {})
            if isinstance(offers, list): offers = offers[0]
            
            if 'price' in offers:
                p = normalize_price(offers['price'])
                if p > 0: return p, is_available, "JSON-LD"
        except: continue

    # 2. CSS Selectors (Específicos)
    css_targets = ['.price', '.product-price', '.sales-price', '.valor-por', '[itemprop="price"]']
    for selector in css_targets:
        el = soup.select_one(selector)
        if el:
            val = normalize_price(el.get_text())
            if val > 0: return val, is_available, "CSS"

    # 3. Regex (Visual - Menor Preço)
    text = soup.get_text(separator=' ')
    matches = re.findall(r'R\$\s?(\d{1,3}(?:\.?\d{3})*,\d{2})', text)
    valid_prices = [normalize_price(m) for m in matches if normalize_price(m) > 0]
    
    if valid_prices:
        return min(valid_prices), is_available, "Regex"

    return 0.0, False, "Falha"