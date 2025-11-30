"""
Data Module for Commercial Pricing Guidance & Realization.
Handles data loading from database or mock data generation as fallback.
"""

import pandas as pd
from typing import Tuple, Dict, List
import os
import threading

USE_DATABASE = os.environ.get('DATABASE_URL') is not None


_database_initialized = False
_database_lock = threading.Lock()


def ensure_database_seeded():
    """Ensure database is seeded (run once at startup, thread-safe with locking)."""
    global _database_initialized
    
    if _database_initialized:
        return
    
    with _database_lock:
        if _database_initialized:
            return
        
        try:
            from repository import check_database_has_data, clear_cache
            if not check_database_has_data():
                from seed_database import seed_database
                seed_database()
                clear_cache()
            _database_initialized = True
        except Exception as e:
            print(f"Database initialization warning: {e}")
            _database_initialized = True


def load_reference_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load reference data for the pricing guidance system.
    Uses database if available, otherwise falls back to mock data.
    Returns 2 DataFrames: catalog_df, pricing_df (merged costs + targets)
    """
    if USE_DATABASE:
        try:
            ensure_database_seeded()
            
            from repository import get_catalog_df, get_pricing_df
            
            catalog_df = get_catalog_df()
            pricing_df = get_pricing_df()
            
            if catalog_df.empty or pricing_df.empty:
                print("Database empty, using mock data")
                return generate_catalog_data(), generate_pricing_data()
            
            return catalog_df, pricing_df
        except Exception as e:
            print(f"Database error, falling back to mock data: {e}")
            return generate_catalog_data(), generate_pricing_data()
    else:
        return generate_catalog_data(), generate_pricing_data()


def generate_catalog_data() -> pd.DataFrame:
    """
    Generate Product Catalog with material codes and pricing models (fallback mock data).
    """
    data = [
        {'material_code': 'AcquiringService', 'tx_variant': 'visa', 'pricing_model': 'Blended', 'default_atv': 100.0},
        {'material_code': 'AcquiringService', 'tx_variant': 'mc', 'pricing_model': 'Blended', 'default_atv': 95.0},
        {'material_code': 'AcquiringService', 'tx_variant': 'amex', 'pricing_model': 'Blended', 'default_atv': 150.0},
        {'material_code': 'AcquiringService', 'tx_variant': 'maestro', 'pricing_model': 'Blended', 'default_atv': 45.0},
        {'material_code': 'ProcessingService', 'tx_variant': 'visa', 'pricing_model': 'FixedPerTx', 'default_atv': 100.0},
        {'material_code': 'ProcessingService', 'tx_variant': 'mc', 'pricing_model': 'FixedPerTx', 'default_atv': 95.0},
        {'material_code': 'ProcessingService', 'tx_variant': 'amex', 'pricing_model': 'FixedPerTx', 'default_atv': 150.0},
        {'material_code': 'ProcessingService', 'tx_variant': 'maestro', 'pricing_model': 'FixedPerTx', 'default_atv': 45.0},
        {'material_code': 'RevenueProtectService', 'tx_variant': 'N/A', 'pricing_model': 'VariableOnly', 'default_atv': 100.0},
    ]
    return pd.DataFrame(data)


def generate_pricing_data() -> pd.DataFrame:
    """
    Generate merged Pricing data with costs AND target pricing per product/region (fallback mock data).
    Now includes ECOM and POS specific pricing for Acquiring and Processing services.
    
    ECOM typically has lower costs (online transactions) while POS has slightly higher costs.
    """
    regions = ['Europe Domestic', 'NorthAmerica Domestic', 'Global']
    products = [
        ('AcquiringService', 'visa'),
        ('AcquiringService', 'mc'),
        ('AcquiringService', 'amex'),
        ('AcquiringService', 'maestro'),
        ('ProcessingService', 'visa'),
        ('ProcessingService', 'mc'),
        ('ProcessingService', 'amex'),
        ('ProcessingService', 'maestro'),
        ('RevenueProtectService', 'N/A'),
    ]
    
    cost_matrix = {
        'Europe Domestic': {'var_base': 0.0015, 'fixed_base': 0.015},
        'NorthAmerica Domestic': {'var_base': 0.0018, 'fixed_base': 0.018},
        'Global': {'var_base': 0.0025, 'fixed_base': 0.025},
    }
    
    target_matrix = {
        'Europe Domestic': {'var_base': 0.006, 'fixed_base': 0.05},
        'NorthAmerica Domestic': {'var_base': 0.0065, 'fixed_base': 0.055},
        'Global': {'var_base': 0.008, 'fixed_base': 0.07},
    }
    
    ecom_cost_multiplier = 0.9
    pos_cost_multiplier = 1.15
    ecom_target_multiplier = 0.95
    pos_target_multiplier = 1.1
    
    product_cost_multipliers = {
        'AcquiringService': {'var': 1.0, 'fixed': 1.0},
        'ProcessingService': {'var': 0.0, 'fixed': 0.8},
        'RevenueProtectService': {'var': 0.5, 'fixed': 0.0},
    }
    
    product_target_multipliers = {
        'AcquiringService': {'var': 1.0, 'fixed': 1.0},
        'ProcessingService': {'var': 0.0, 'fixed': 1.2},
        'RevenueProtectService': {'var': 0.3, 'fixed': 0.0},
    }
    
    variant_multipliers = {
        'visa': 1.0,
        'mc': 1.05,
        'amex': 1.5,
        'maestro': 0.85,
        'N/A': 1.0,
    }
    
    data = []
    for material_code, tx_variant in products:
        for region in regions:
            cost_base = cost_matrix[region]
            target_base = target_matrix[region]
            cost_mult = product_cost_multipliers[material_code]
            target_mult = product_target_multipliers[material_code]
            var_mult = variant_multipliers[tx_variant]
            
            base_cost_variable = cost_base['var_base'] * cost_mult['var'] * var_mult
            base_cost_fixed = cost_base['fixed_base'] * cost_mult['fixed'] * var_mult
            base_target_variable = target_base['var_base'] * target_mult['var'] * var_mult
            base_target_fixed = target_base['fixed_base'] * target_mult['fixed'] * var_mult
            
            if material_code in ['AcquiringService', 'ProcessingService']:
                ecom_cost_variable = round(base_cost_variable * ecom_cost_multiplier, 6)
                ecom_cost_fixed = round(base_cost_fixed * ecom_cost_multiplier, 4)
                ecom_target_variable = round(base_target_variable * ecom_target_multiplier, 6)
                ecom_target_fixed = round(base_target_fixed * ecom_target_multiplier, 4)
                
                pos_cost_variable = round(base_cost_variable * pos_cost_multiplier, 6)
                pos_cost_fixed = round(base_cost_fixed * pos_cost_multiplier, 4)
                pos_target_variable = round(base_target_variable * pos_target_multiplier, 6)
                pos_target_fixed = round(base_target_fixed * pos_target_multiplier, 4)
            else:
                ecom_cost_variable = round(base_cost_variable, 6)
                ecom_cost_fixed = round(base_cost_fixed, 4)
                ecom_target_variable = round(base_target_variable, 6)
                ecom_target_fixed = round(base_target_fixed, 4)
                pos_cost_variable = ecom_cost_variable
                pos_cost_fixed = ecom_cost_fixed
                pos_target_variable = ecom_target_variable
                pos_target_fixed = ecom_target_fixed
            
            data.append({
                'material_code': material_code,
                'tx_variant': tx_variant,
                'region_classification': region,
                'cost_variable': round(base_cost_variable, 6),
                'cost_fixed': round(base_cost_fixed, 4),
                'target_variable': round(base_target_variable, 6),
                'target_fixed': round(base_target_fixed, 4),
                'ecom_cost_variable': ecom_cost_variable,
                'ecom_cost_fixed': ecom_cost_fixed,
                'ecom_target_variable': ecom_target_variable,
                'ecom_target_fixed': ecom_target_fixed,
                'pos_cost_variable': pos_cost_variable,
                'pos_cost_fixed': pos_cost_fixed,
                'pos_target_variable': pos_target_variable,
                'pos_target_fixed': pos_target_fixed,
            })
    
    return pd.DataFrame(data)


def get_material_codes() -> List[str]:
    """Return list of available material codes."""
    if USE_DATABASE:
        try:
            from repository import get_material_codes_from_db
            codes = get_material_codes_from_db()
            if codes:
                return codes
        except Exception:
            pass
    return ['AcquiringService', 'ProcessingService', 'RevenueProtectService']


def get_tx_variants_for_material(material_code: str) -> List[str]:
    """Return list of transaction variants for a specific material code."""
    if USE_DATABASE:
        try:
            from repository import get_tx_variants_for_material_from_db
            variants = get_tx_variants_for_material_from_db(material_code)
            if variants:
                return variants
        except Exception:
            pass
    
    if material_code == 'RevenueProtectService':
        return ['N/A']
    return ['visa', 'mc', 'amex', 'maestro']


def get_all_tx_variants() -> List[str]:
    """Return list of all transaction variants."""
    return ['visa', 'mc', 'amex', 'maestro', 'N/A']


def get_classifications() -> List[str]:
    """Return list of available price guidance classifications."""
    if USE_DATABASE:
        try:
            from repository import get_classifications_from_db
            classifications = get_classifications_from_db()
            if classifications:
                return classifications
        except Exception:
            pass
    return ['Europe Domestic', 'NorthAmerica Domestic', 'Global']


def get_default_atv(material_code: str, tx_variant: str) -> float:
    """Get default ATV for a product/variant combination."""
    if USE_DATABASE:
        try:
            from repository import get_default_atv_from_db
            atv = get_default_atv_from_db(material_code, tx_variant)
            if atv:
                return atv
        except Exception:
            pass
    
    atv_defaults = {
        ('AcquiringService', 'visa'): 100.0,
        ('AcquiringService', 'mc'): 95.0,
        ('AcquiringService', 'amex'): 150.0,
        ('AcquiringService', 'maestro'): 45.0,
        ('ProcessingService', 'visa'): 100.0,
        ('ProcessingService', 'mc'): 95.0,
        ('ProcessingService', 'amex'): 150.0,
        ('ProcessingService', 'maestro'): 45.0,
        ('RevenueProtectService', 'N/A'): 100.0,
    }
    return atv_defaults.get((material_code, tx_variant), 100.0)


def create_empty_deal_row_for_product(
    material_code: str,
    tx_variant: str,
    classification: str,
    pricing_df: pd.DataFrame
) -> Dict:
    """
    Create an empty deal input row with default values pre-populated from target pricing.
    ATV is now a global deal setting, tx_count will be calculated from Volume / Global ATV.
    """
    mask = (
        (pricing_df['material_code'] == material_code) &
        (pricing_df['tx_variant'] == tx_variant) &
        (pricing_df['region_classification'] == classification)
    )
    
    matched = pricing_df[mask]
    
    if not matched.empty:
        row = matched.iloc[0]
        target_var = float(row['target_variable']) * 100
        target_fixed = float(row['target_fixed'])
    else:
        target_var = 0.60
        target_fixed = 0.05
    
    return {
        'tx_variant': tx_variant,
        'region_classification': classification,
        'volume_eur': 100000.0,
        'tx_count': 0,
        'target_variable_pct': round(target_var, 4),
        'target_fixed_eur': round(target_fixed, 4),
        'proposed_variable_pct': round(target_var, 4),
        'proposed_fixed_eur': round(target_fixed, 4),
    }


def create_default_deal_data_for_product(
    material_code: str,
    pricing_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Create default deal data for a product with one row per transaction variant.
    """
    tx_variants = get_tx_variants_for_material(material_code)
    default_classification = 'Europe Domestic'
    
    rows = []
    for tx_variant in tx_variants:
        row = create_empty_deal_row_for_product(
            material_code, tx_variant, default_classification, pricing_df
        )
        rows.append(row)
    
    return pd.DataFrame(rows)


def parse_uploaded_csv(uploaded_file, expected_columns: List[str]) -> pd.DataFrame:
    """
    Parse an uploaded CSV file and validate its columns.
    Returns DataFrame if valid, raises ValueError if invalid.
    """
    try:
        df = pd.read_csv(uploaded_file)
        missing_cols = set(expected_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        return df
    except Exception as e:
        raise ValueError(f"Error parsing CSV: {str(e)}")


def get_pricing_expected_columns() -> List[str]:
    """Return expected columns for pricing CSV upload (merged costs + targets)."""
    return [
        'material_code', 'tx_variant', 'region_classification',
        'cost_variable', 'cost_fixed', 'target_variable', 'target_fixed'
    ]


def lookup_pricing(
    pricing_df: pd.DataFrame,
    material_code: str,
    tx_variant: str,
    classification: str
) -> Dict:
    """
    Look up pricing data (costs and targets) for a specific product/variant/region.
    Now includes ECOM and POS specific pricing for channel-based calculations.
    Uses database if available, otherwise uses the provided DataFrame.
    """
    material_code = str(material_code).strip() if pd.notna(material_code) else ''
    tx_variant = str(tx_variant).strip() if pd.notna(tx_variant) else ''
    classification = str(classification).strip() if pd.notna(classification) else ''
    
    default_result = {
        'cost_variable': 0.0,
        'cost_fixed': 0.0,
        'target_variable': 0.0,
        'target_fixed': 0.0,
        'ecom_cost_variable': 0.0,
        'ecom_cost_fixed': 0.0,
        'ecom_target_variable': 0.0,
        'ecom_target_fixed': 0.0,
        'pos_cost_variable': 0.0,
        'pos_cost_fixed': 0.0,
        'pos_target_variable': 0.0,
        'pos_target_fixed': 0.0,
        'found': False
    }
    
    if not material_code or not tx_variant or not classification:
        return default_result
    
    if USE_DATABASE:
        try:
            from repository import lookup_pricing_from_db
            result = lookup_pricing_from_db(material_code, tx_variant, classification)
            if result['found']:
                if 'ecom_cost_variable' not in result:
                    result['ecom_cost_variable'] = result['cost_variable']
                    result['ecom_cost_fixed'] = result['cost_fixed']
                    result['ecom_target_variable'] = result['target_variable']
                    result['ecom_target_fixed'] = result['target_fixed']
                    result['pos_cost_variable'] = result['cost_variable']
                    result['pos_cost_fixed'] = result['cost_fixed']
                    result['pos_target_variable'] = result['target_variable']
                    result['pos_target_fixed'] = result['target_fixed']
                return result
        except Exception:
            pass
    
    mask = (
        (pricing_df['material_code'] == material_code) &
        (pricing_df['tx_variant'] == tx_variant) &
        (pricing_df['region_classification'] == classification)
    )
    
    matched = pricing_df[mask]
    
    if matched.empty:
        return default_result
    
    row = matched.iloc[0]
    
    result = {
        'cost_variable': float(row['cost_variable']),
        'cost_fixed': float(row['cost_fixed']),
        'target_variable': float(row['target_variable']),
        'target_fixed': float(row['target_fixed']),
        'found': True
    }
    
    if 'ecom_cost_variable' in row:
        result['ecom_cost_variable'] = float(row['ecom_cost_variable'])
        result['ecom_cost_fixed'] = float(row['ecom_cost_fixed'])
        result['ecom_target_variable'] = float(row['ecom_target_variable'])
        result['ecom_target_fixed'] = float(row['ecom_target_fixed'])
        result['pos_cost_variable'] = float(row['pos_cost_variable'])
        result['pos_cost_fixed'] = float(row['pos_cost_fixed'])
        result['pos_target_variable'] = float(row['pos_target_variable'])
        result['pos_target_fixed'] = float(row['pos_target_fixed'])
    else:
        result['ecom_cost_variable'] = result['cost_variable']
        result['ecom_cost_fixed'] = result['cost_fixed']
        result['ecom_target_variable'] = result['target_variable']
        result['ecom_target_fixed'] = result['target_fixed']
        result['pos_cost_variable'] = result['cost_variable']
        result['pos_cost_fixed'] = result['cost_fixed']
        result['pos_target_variable'] = result['target_variable']
        result['pos_target_fixed'] = result['target_fixed']
    
    return result


def hydrate_new_rows(
    deal_data: pd.DataFrame,
    material_code: str,
    pricing_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Ensure all rows in deal data have valid values.
    For new/empty rows, fill in defaults based on the first valid tx_variant and classification.
    This function handles the case when st.data_editor creates new rows with blank values.
    Note: ATV is now global (from Deal Settings), tx_count is calculated separately.
    """
    if deal_data.empty:
        return deal_data
    
    updated_data = deal_data.copy()
    tx_variants = get_tx_variants_for_material(material_code)
    classifications = get_classifications()
    default_classification = classifications[0] if classifications else 'Europe Domestic'
    default_variant = tx_variants[0] if tx_variants else 'visa'
    
    for idx, row in updated_data.iterrows():
        tx_variant = row.get('tx_variant', None)
        needs_full_init = False
        
        if pd.isna(tx_variant) or str(tx_variant).strip() == '' or str(tx_variant) == 'nan':
            updated_data.at[idx, 'tx_variant'] = default_variant
            tx_variant = default_variant
            needs_full_init = True
        else:
            tx_variant = str(tx_variant).strip()
        
        classification = row.get('region_classification', None)
        if pd.isna(classification) or str(classification).strip() == '' or str(classification) == 'nan':
            updated_data.at[idx, 'region_classification'] = default_classification
            classification = default_classification
            needs_full_init = True
        else:
            classification = str(classification).strip()
        
        pricing = lookup_pricing(pricing_df, material_code, tx_variant, classification)
        
        if needs_full_init:
            updated_data.at[idx, 'volume_eur'] = 100000.0
            updated_data.at[idx, 'tx_count'] = 0
            updated_data.at[idx, 'target_variable_pct'] = round(pricing['target_variable'] * 100, 4)
            updated_data.at[idx, 'target_fixed_eur'] = round(pricing['target_fixed'], 4)
            updated_data.at[idx, 'proposed_variable_pct'] = round(pricing['target_variable'] * 100, 4)
            updated_data.at[idx, 'proposed_fixed_eur'] = round(pricing['target_fixed'], 4)
        else:
            volume = row.get('volume_eur', None)
            if pd.isna(volume) or volume == 0:
                updated_data.at[idx, 'volume_eur'] = 100000.0
            
            target_var = row.get('target_variable_pct', None)
            if pd.isna(target_var) or target_var == 0:
                updated_data.at[idx, 'target_variable_pct'] = round(pricing['target_variable'] * 100, 4)
            
            target_fixed = row.get('target_fixed_eur', None)
            if pd.isna(target_fixed):
                updated_data.at[idx, 'target_fixed_eur'] = round(pricing['target_fixed'], 4)
            
            proposed_var = row.get('proposed_variable_pct', None)
            if pd.isna(proposed_var) or proposed_var == 0:
                updated_data.at[idx, 'proposed_variable_pct'] = round(pricing['target_variable'] * 100, 4)
            
            proposed_fixed = row.get('proposed_fixed_eur', None)
            if pd.isna(proposed_fixed):
                updated_data.at[idx, 'proposed_fixed_eur'] = round(pricing['target_fixed'], 4)
    
    return updated_data
