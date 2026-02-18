# core/normalization.py
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import re

def clean_url(url: str) -> str:
    """
    (Ponto 2) Remove parâmetros de rastreamento (utm_, etc) para evitar duplicidade.
    """
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Mantém apenas parâmetros essenciais (ex: id, sku)
        allowed_params = ['id', 'sku', 'cod', 'productId']
        clean_params = {k: v for k, v in query_params.items() if k in allowed_params}
        
        clean_query = urlencode(clean_params, doseq=True)
        
        # Reconstrói a URL limpa e sem fragmentos (#)
        clean_url = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            clean_query,
            None 
        ))
        return clean_url
    except:
        return url

def identify_pharmacy(url: str):
    """Extrai o domínio para criar/vincular a Farmácia"""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    name = domain.split('.')[0].capitalize()
    return name, domain

def classify_product(name: str):
    """(Ponto 3) Taxonomia Farmacológica Simples"""
    name_lower = name.lower()
    
    taxonomy = {
        'Estrogen': ['estradiol', 'estrogênio', 'climene', 'primogyna', 'sandrena', 'oestrogel'],
        'Antiandrogen': ['espironolactona', 'bicalutamida', 'ciproterona', 'acetato'],
        'Testosterone': ['testosterona', 'durateston', 'deposteron', 'androgel'],
        'Blocker': ['perlutan', 'algestona', 'leuprorrelina']
    }
    
    for category, keywords in taxonomy.items():
        if any(k in name_lower for k in keywords):
            return category
            
    return "Outros" # Categoria Default