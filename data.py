"""
Data Module for Commercial Pricing Guidance & Realization.
Handles data loading and mock data generation following the Digital Twin schema.
"""

import pandas as pd
from typing import Tuple, Dict, List


def load_reference_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load reference data for the pricing guidance system.
    Returns 2 DataFrames: catalog_df, pricing_df (merged costs + targets)
    """
    catalog_df = generate_catalog_data()
    pricing_df = generate_pricing_data()
    
    return catalog_df, pricing_df


def generate_catalog_data() -> pd.DataFrame:
    """
    Generate Product Catalog with material codes and pricing models.
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
    Generate merged Pricing data with costs AND target pricing per product/region.
    Schema: material_code, tx_variant, region_classification, cost_variable, cost_fixed, target_variable, target_fixed
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
            
            cost_variable = round(cost_base['var_base'] * cost_mult['var'] * var_mult, 6)
            cost_fixed = round(cost_base['fixed_base'] * cost_mult['fixed'] * var_mult, 4)
            target_variable = round(target_base['var_base'] * target_mult['var'] * var_mult, 6)
            target_fixed = round(target_base['fixed_base'] * target_mult['fixed'] * var_mult, 4)
            
            data.append({
                'material_code': material_code,
                'tx_variant': tx_variant,
                'region_classification': region,
                'cost_variable': cost_variable,
                'cost_fixed': cost_fixed,
                'target_variable': target_variable,
                'target_fixed': target_fixed,
            })
    
    return pd.DataFrame(data)


def get_material_codes() -> List[str]:
    """Return list of available material codes."""
    return ['AcquiringService', 'ProcessingService', 'RevenueProtectService']


def get_tx_variants_for_material(material_code: str) -> List[str]:
    """Return list of transaction variants for a specific material code."""
    if material_code == 'RevenueProtectService':
        return ['N/A']
    return ['visa', 'mc', 'amex', 'maestro']


def get_all_tx_variants() -> List[str]:
    """Return list of all transaction variants."""
    return ['visa', 'mc', 'amex', 'maestro', 'N/A']


def get_classifications() -> List[str]:
    """Return list of available price guidance classifications."""
    return ['Europe Domestic', 'NorthAmerica Domestic', 'Global']


def get_default_atv(material_code: str, tx_variant: str) -> float:
    """Get default ATV for a product/variant combination."""
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
    
    default_atv = get_default_atv(material_code, tx_variant)
    
    return {
        'tx_variant': tx_variant,
        'region_classification': classification,
        'volume_eur': 100000.0,
        'atv': default_atv,
        'tx_count': int(100000.0 / default_atv),
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
    """
    material_code = str(material_code).strip() if pd.notna(material_code) else ''
    tx_variant = str(tx_variant).strip() if pd.notna(tx_variant) else ''
    classification = str(classification).strip() if pd.notna(classification) else ''
    
    if not material_code or not tx_variant or not classification:
        return {
            'cost_variable': 0.0,
            'cost_fixed': 0.0,
            'target_variable': 0.0,
            'target_fixed': 0.0,
            'found': False
        }
    
    mask = (
        (pricing_df['material_code'] == material_code) &
        (pricing_df['tx_variant'] == tx_variant) &
        (pricing_df['region_classification'] == classification)
    )
    
    matched = pricing_df[mask]
    
    if matched.empty:
        return {
            'cost_variable': 0.0,
            'cost_fixed': 0.0,
            'target_variable': 0.0,
            'target_fixed': 0.0,
            'found': False
        }
    
    row = matched.iloc[0]
    return {
        'cost_variable': float(row['cost_variable']),
        'cost_fixed': float(row['cost_fixed']),
        'target_variable': float(row['target_variable']),
        'target_fixed': float(row['target_fixed']),
        'found': True
    }


def hydrate_new_rows(
    deal_data: pd.DataFrame,
    material_code: str,
    pricing_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Ensure all rows in deal data have valid values.
    For new/empty rows, fill in defaults based on the first valid tx_variant and classification.
    This function handles the case when st.data_editor creates new rows with blank values.
    """
    if deal_data.empty:
        return deal_data
    
    updated_data = deal_data.copy()
    tx_variants = get_tx_variants_for_material(material_code)
    classifications = get_classifications()
    default_classification = classifications[0]
    default_variant = tx_variants[0]
    
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
        
        default_atv = get_default_atv(material_code, tx_variant)
        pricing = lookup_pricing(pricing_df, material_code, tx_variant, classification)
        
        if needs_full_init:
            updated_data.at[idx, 'volume_eur'] = 100000.0
            updated_data.at[idx, 'atv'] = default_atv
            updated_data.at[idx, 'tx_count'] = max(1, int(100000.0 / default_atv))
            updated_data.at[idx, 'target_variable_pct'] = round(pricing['target_variable'] * 100, 4)
            updated_data.at[idx, 'target_fixed_eur'] = round(pricing['target_fixed'], 4)
            updated_data.at[idx, 'proposed_variable_pct'] = round(pricing['target_variable'] * 100, 4)
            updated_data.at[idx, 'proposed_fixed_eur'] = round(pricing['target_fixed'], 4)
        else:
            volume = row.get('volume_eur', None)
            if pd.isna(volume) or volume == 0:
                updated_data.at[idx, 'volume_eur'] = 100000.0
                volume = 100000.0
            else:
                volume = float(volume)
            
            atv = row.get('atv', None)
            if pd.isna(atv) or atv == 0:
                updated_data.at[idx, 'atv'] = default_atv
                atv = default_atv
            else:
                atv = float(atv)
            
            tx_count = row.get('tx_count', None)
            if pd.isna(tx_count) or tx_count == 0:
                updated_data.at[idx, 'tx_count'] = max(1, int(volume / atv))
            
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
