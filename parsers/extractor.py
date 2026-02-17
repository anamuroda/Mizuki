import json
import re
from bs4 import BeautifulSoup

def _clean_price(price_str):
    """Converte 'R$ 1.200,50' para float 1200.50"""
    if not price_str: return None
    try:
        # Remove R$, espaços e caracteres invisíveis
        clean = re.sub(r'[^\d,]', '', str(price_str))
        # Troca virgula por ponto para o Python entender
        return float(clean.replace(',', '.'))
    except:
        return None

def extract_price_heuristic(html_content):
    """
    Estratégia Híbrida para Farmácias:
    1. Tenta ler metadados ocultos (JSON-LD) -> 99% de precisão.
    2. Se falhar, varre todos os preços visíveis e pega o MENOR (lógica de promoção).
    """
    if not html_content:
        return "N/A"

    soup = BeautifulSoup(html_content, 'html.parser')
    
    # --- ESTRATÉGIA 1: JSON-LD (O "Cheat Code" do SEO) ---
    # Sites como Drogal, Raia, Panvel usam isso para o Google Shopping.
    # O preço está limpo dentro de uma tag <script>.
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            data = json.loads(script.string)
            # Às vezes o JSON é uma lista, às vezes um objeto
            if isinstance(data, list):
                data = data[0] if data else {}
            
            # Procura pela estrutura de 'offers' (Padrão Schema.org)
            if 'offers' in data:
                offer = data['offers']
                # Se for uma lista de ofertas, pega a primeira ou a com menor preço
                if isinstance(offer, list):
                    offer = offer[0]
                
                if 'price' in offer:
                    price = float(offer['price'])
                    return f"R$ {price:.2f}".replace('.', ',')
        except:
            continue

    # --- ESTRATÉGIA 2: Varredura Visual (Menor Preço) ---
    # Se não achou JSON, procura visualmente.
    
    # Remove tags que atrapalham (scripts, estilos)
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
        
    text_content = soup.get_text(separator=' ', strip=True)
    
    # Regex para capturar qualquer valor monetário (R$ XX,XX)
    pattern = re.compile(r'R\$\s?(\d{1,3}(?:\.\d{3})*,\d{2})')
    matches = pattern.findall(text_content)
    
    valid_prices = []
    for price_str in matches:
        # Converte para float para podermos comparar matematicamente
        val = _clean_price(price_str)
        if val and val > 0: # Ignora zeros ou erros
            valid_prices.append(val)
    
    if valid_prices:
        # A MÁGICA: Pegamos o MENOR preço da página.
        # Isso resolve o problema de pegar o preço "De" (maior) em vez do "Por" (menor).
        best_price = min(valid_prices)
        return f"R$ {best_price:.2f}".replace('.', ',')

    return "Não encontrado"