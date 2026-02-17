import logging
import sys
import os

# Cria pastas necessárias
os.makedirs("logs", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Formato detalhado: Data - Nível - Mensagem
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Salva em arquivo
    file_handler = logging.FileHandler(f"logs/mizuki.log", encoding='utf-8')
    file_handler.setFormatter(formatter)

    # Mostra no terminal
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    
    return logger

logger = setup_logger("Mizuki")