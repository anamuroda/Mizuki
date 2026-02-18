from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Enum, Text, BigInteger
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum
from .connection import engine

Base = declarative_base()

# Enums para padronização (Ponto 1 da Análise)
class AvailabilityStatus(enum.Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"
    PRE_ORDER = "pre_order"

# --- Entidades Estruturais ---

class Region(Base):
    """(Ponto 5) Sistema Regional Inteligente"""
    __tablename__ = "regions"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False) # ex: São Paulo
    region_code = Column(String, unique=True) # ex: BR-SP
    
    pharmacies = relationship("Pharmacy", back_populates="region")

class Category(Base):
    """(Ponto 3) Classificação Semântica"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False) # ex: Estrogen, Antiandrogen
    classification_logic = Column(String) # Keywords para auto-classificação
    
    products = relationship("Product", back_populates="category")

class Pharmacy(Base):
    """(Ponto 1) Normalização de Farmácias"""
    __tablename__ = "pharmacies"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True) # ex: drogaraia.com.br
    
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    region = relationship("Region", back_populates="pharmacies")
    
    products = relationship("Product", back_populates="pharmacy")

# --- Entidade Principal ---

class Product(Base):
    """(Ponto 1) Modelo de Domínio Completo"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    
    # Identificação e Normalização (Ponto 2)
    url = Column(String, unique=True, index=True)
    canonical_url = Column(String) 
    product_name = Column(String, index=True)
    
    # Relacionamentos
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    
    # Estado Atual
    price_current = Column(Float)
    availability_status = Column(Enum(AvailabilityStatus), default=AvailabilityStatus.IN_STOCK)
    
    # Configuração de Monitoramento (Mantendo funcionalidade do Bot)
    target_price = Column(Float, nullable=True)
    discord_channel_id = Column(BigInteger, nullable=True)
    active = Column(Boolean, default=True)
    
    # Metadados
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos Inversos
    pharmacy = relationship("Pharmacy", back_populates="products")
    category = relationship("Category", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

# --- Dados Históricos ---

class PriceHistory(Base):
    """(Ponto 6) Persistência de Séries Temporais"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    
    price = Column(Float, nullable=False)
    availability = Column(Boolean)
    captured_at = Column(DateTime, default=datetime.now, index=True)
    
    product = relationship("Product", back_populates="price_history")

# Criação das tabelas
Base.metadata.create_all(bind=engine)