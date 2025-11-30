"""
Database Models for Commercial Pricing Guidance & Realization.
Defines SQLAlchemy models for materials, variants, and pricing.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class Material(Base):
    """Product catalog table - stores material codes and their properties."""
    __tablename__ = 'materials'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_code = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255))
    pricing_model = Column(String(50), nullable=False)
    default_atv = Column(Float, default=100.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    variants = relationship("TxVariant", back_populates="material", cascade="all, delete-orphan")
    pricing_refs = relationship("PricingRef", back_populates="material", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Material(code={self.material_code}, model={self.pricing_model})>"


class TxVariant(Base):
    """Transaction variants table - stores variant codes linked to materials."""
    __tablename__ = 'tx_variants'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False)
    variant_code = Column(String(50), nullable=False)
    display_name = Column(String(100))
    default_atv = Column(Float, default=100.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    material = relationship("Material", back_populates="variants")
    pricing_refs = relationship("PricingRef", back_populates="variant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TxVariant(code={self.variant_code}, material={self.material_id})>"


class PricingRef(Base):
    """Pricing reference table - stores cost and target pricing by material/variant/region."""
    __tablename__ = 'pricing_refs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False)
    variant_id = Column(Integer, ForeignKey('tx_variants.id'), nullable=False)
    region_classification = Column(String(100), nullable=False)
    cost_variable = Column(Float, default=0.0)
    cost_fixed = Column(Float, default=0.0)
    target_variable = Column(Float, default=0.0)
    target_fixed = Column(Float, default=0.0)
    effective_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    material = relationship("Material", back_populates="pricing_refs")
    variant = relationship("TxVariant", back_populates="pricing_refs")
    
    def __repr__(self):
        return f"<PricingRef(material={self.material_id}, variant={self.variant_id}, region={self.region_classification})>"


_engine = None
_SessionFactory = None


def get_database_url():
    """Get database URL from environment."""
    return os.environ.get('DATABASE_URL')


def get_engine():
    """Get or create the database engine singleton."""
    global _engine
    if _engine is None:
        database_url = get_database_url()
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        _engine = create_engine(
            database_url, 
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
    return _engine


def get_session():
    """Create and return a new database session using the singleton engine."""
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_engine()
        _SessionFactory = sessionmaker(bind=engine)
    return _SessionFactory()


def init_db():
    """Initialize database by creating all tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine
