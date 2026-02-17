from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from .connection import engine

Base = declarative_base()

class TargetURL(Base):
    """
    Tabela que armazena as URLs que foram adicionadas via terminal.
    fila de trabalho.
    """
    __tablename__ = "target_urls"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)
    active = Column(Boolean, default=True) # se False, o bot ignora
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # relacionamento com os resultados
    results = relationship("ScrapingResult", back_populates="target")

class ScrapingResult(Base):
    """
    Tabela que armazena o QUE a Mizuki extraiu dessas URLs.
    """
    __tablename__ = "scraping_results"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("target_urls.id"))
    
    status = Column(String)  # 'success' ou 'error'
    price_found = Column(String, nullable=True)
    html_snapshot = Column(Text, nullable=True) # HTML bruto para possível análise 
    scraped_at = Column(DateTime, default=datetime.utcnow)

    target = relationship("TargetURL", back_populates="results")

# cria/atualiza as tabelas no banco
Base.metadata.create_all(bind=engine)