"""
Repository Module for Commercial Pricing Guidance & Realization.
Handles database access for materials, variants, and pricing data.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from sqlalchemy import and_
from sqlalchemy.orm import Session
import streamlit as st

from models import (
    Material, TxVariant, PricingRef,
    get_session, init_db, get_engine
)


def init_database():
    """Initialize database tables."""
    init_db()


@st.cache_data(ttl=300)
def get_catalog_df() -> pd.DataFrame:
    """
    Fetch product catalog from database.
    Returns DataFrame with material_code, tx_variant, pricing_model, default_atv.
    """
    session = get_session()
    try:
        results = session.query(
            Material.material_code,
            TxVariant.variant_code.label('tx_variant'),
            Material.pricing_model,
            TxVariant.default_atv
        ).join(TxVariant, Material.id == TxVariant.material_id).filter(
            Material.is_active == True,
            TxVariant.is_active == True
        ).all()
        
        if not results:
            return pd.DataFrame(columns=['material_code', 'tx_variant', 'pricing_model', 'default_atv'])
        
        data = [
            {
                'material_code': r.material_code,
                'tx_variant': r.tx_variant,
                'pricing_model': r.pricing_model,
                'default_atv': r.default_atv
            }
            for r in results
        ]
        return pd.DataFrame(data)
    finally:
        session.close()


@st.cache_data(ttl=300)
def get_pricing_df() -> pd.DataFrame:
    """
    Fetch pricing data from database.
    Returns DataFrame with material_code, tx_variant, region_classification,
    cost_variable, cost_fixed, target_variable, target_fixed.
    """
    session = get_session()
    try:
        results = session.query(
            Material.material_code,
            TxVariant.variant_code.label('tx_variant'),
            PricingRef.region_classification,
            PricingRef.cost_variable,
            PricingRef.cost_fixed,
            PricingRef.target_variable,
            PricingRef.target_fixed
        ).join(
            Material, PricingRef.material_id == Material.id
        ).join(
            TxVariant, PricingRef.variant_id == TxVariant.id
        ).filter(
            Material.is_active == True,
            TxVariant.is_active == True,
            PricingRef.is_active == True
        ).all()
        
        if not results:
            return pd.DataFrame(columns=[
                'material_code', 'tx_variant', 'region_classification',
                'cost_variable', 'cost_fixed', 'target_variable', 'target_fixed'
            ])
        
        data = [
            {
                'material_code': r.material_code,
                'tx_variant': r.tx_variant,
                'region_classification': r.region_classification,
                'cost_variable': r.cost_variable,
                'cost_fixed': r.cost_fixed,
                'target_variable': r.target_variable,
                'target_fixed': r.target_fixed
            }
            for r in results
        ]
        return pd.DataFrame(data)
    finally:
        session.close()


def get_material_codes_from_db() -> List[str]:
    """Fetch list of active material codes from database."""
    session = get_session()
    try:
        results = session.query(Material.material_code).filter(
            Material.is_active == True
        ).order_by(Material.material_code).all()
        return [r.material_code for r in results]
    finally:
        session.close()


def get_tx_variants_for_material_from_db(material_code: str) -> List[str]:
    """Fetch list of transaction variants for a specific material code."""
    session = get_session()
    try:
        results = session.query(TxVariant.variant_code).join(
            Material, TxVariant.material_id == Material.id
        ).filter(
            Material.material_code == material_code,
            TxVariant.is_active == True
        ).order_by(TxVariant.variant_code).all()
        return [r.variant_code for r in results]
    finally:
        session.close()


def get_classifications_from_db() -> List[str]:
    """Fetch list of unique region classifications from database."""
    session = get_session()
    try:
        results = session.query(PricingRef.region_classification).filter(
            PricingRef.is_active == True
        ).distinct().order_by(PricingRef.region_classification).all()
        return [r.region_classification for r in results]
    finally:
        session.close()


def get_default_atv_from_db(material_code: str, tx_variant: str) -> float:
    """Get default ATV for a product/variant combination from database."""
    session = get_session()
    try:
        result = session.query(TxVariant.default_atv).join(
            Material, TxVariant.material_id == Material.id
        ).filter(
            Material.material_code == material_code,
            TxVariant.variant_code == tx_variant
        ).first()
        
        if result:
            return result.default_atv
        return 100.0
    finally:
        session.close()


def lookup_pricing_from_db(
    material_code: str,
    tx_variant: str,
    classification: str
) -> Dict:
    """
    Look up pricing data from database for a specific product/variant/region.
    """
    if not material_code or not tx_variant or not classification:
        return {
            'cost_variable': 0.0,
            'cost_fixed': 0.0,
            'target_variable': 0.0,
            'target_fixed': 0.0,
            'found': False
        }
    
    session = get_session()
    try:
        result = session.query(
            PricingRef.cost_variable,
            PricingRef.cost_fixed,
            PricingRef.target_variable,
            PricingRef.target_fixed
        ).join(
            Material, PricingRef.material_id == Material.id
        ).join(
            TxVariant, PricingRef.variant_id == TxVariant.id
        ).filter(
            Material.material_code == material_code,
            TxVariant.variant_code == tx_variant,
            PricingRef.region_classification == classification,
            PricingRef.is_active == True
        ).first()
        
        if result:
            return {
                'cost_variable': result.cost_variable,
                'cost_fixed': result.cost_fixed,
                'target_variable': result.target_variable,
                'target_fixed': result.target_fixed,
                'found': True
            }
        
        return {
            'cost_variable': 0.0,
            'cost_fixed': 0.0,
            'target_variable': 0.0,
            'target_fixed': 0.0,
            'found': False
        }
    finally:
        session.close()


def check_database_has_data() -> bool:
    """Check if database has been seeded with data."""
    session = get_session()
    try:
        count = session.query(Material).count()
        return count > 0
    except Exception:
        return False
    finally:
        session.close()


def clear_cache():
    """Clear Streamlit's cached data to force refresh from database."""
    st.cache_data.clear()
