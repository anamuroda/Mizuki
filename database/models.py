from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from .connection import engine

Base = declarative_base()

class TargetURL(Base):
    __tablename__ = "target_urls"
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True)
    product_name = Column(String)
    active = Column(Boolean, default=True)
    target_price = Column(Float, nullable=True) # Gatilho de alerta
    results = relationship("ScrapingResult", back_populates="target")

class ScrapingResult(Base):
    __tablename__ = "scraping_results"
    id = Column(Integer, primary_key=True)
    target_id = Column(Integer, ForeignKey("target_urls.id"))
    price = Column(Float)
    available = Column(Boolean)
    method = Column(String) # JSON-LD, CSS, etc
    scraped_at = Column(DateTime, default=datetime.now)
    target = relationship("TargetURL", back_populates="results")

Base.metadata.create_all(bind=engine)