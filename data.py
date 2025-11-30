"""
Data Module for Commercial Pricing Guidance & Realization.
Handles data loading and mock data generation following the Digital Twin schema.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple


def load_reference_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load reference data for the pricing guidance system.
    Returns 3 DataFrames: catalog_df, costs_df, guidance_df
    """
    catalog_df = generate_catalog_data()
    costs_df = generate_costs_data()
    guidance_df = generate_guidance_data()
    
    return catalog_df, costs_df, guidance_df


def generate_catalog_data() -> pd.DataFrame:
    """
    Generate Product Catalog (Table A) with material codes and pricing models.
    """
    data = [
        {'material_code': 'AcquiringService', 'tx_variant': 'visa', 'pricing_model': 'Blended'},
        {'material_code': 'AcquiringService', 'tx_variant': 'mc', 'pricing_model': 'Blended'},
        {'material_code': 'AcquiringService', 'tx_variant': 'amex', 'pricing_model': 'Blended'},
        {'material_code': 'AcquiringService', 'tx_variant': 'maestro', 'pricing_model': 'Blended'},
        {'material_code': 'ProcessingService', 'tx_variant': 'visa', 'pricing_model': 'FixedPerTx'},
        {'material_code': 'ProcessingService', 'tx_variant': 'mc', 'pricing_model': 'FixedPerTx'},
        {'material_code': 'ProcessingService', 'tx_variant': 'amex', 'pricing_model': 'FixedPerTx'},
        {'material_code': 'ProcessingService', 'tx_variant': 'maestro', 'pricing_model': 'FixedPerTx'},
        {'material_code': 'RevenueProtectService', 'tx_variant': 'N/A', 'pricing_model': 'VariableOnly'},
    ]
    return pd.DataFrame(data)


def generate_costs_data() -> pd.DataFrame:
    """
    Generate Cost Base (Table B) with cost structures per product and region.
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
    
    product_multipliers = {
        'AcquiringService': {'var': 1.0, 'fixed': 1.0},
        'ProcessingService': {'var': 0.0, 'fixed': 0.8},
        'RevenueProtectService': {'var': 0.5, 'fixed': 0.0},
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
            base = cost_matrix[region]
            prod_mult = product_multipliers[material_code]
            var_mult = variant_multipliers[tx_variant]
            
            cost_variable = round(base['var_base'] * prod_mult['var'] * var_mult, 6)
            cost_fixed_eur = round(base['fixed_base'] * prod_mult['fixed'] * var_mult, 4)
            
            data.append({
                'material_code': material_code,
                'tx_variant': tx_variant,
                'region_classification': region,
                'cost_variable': cost_variable,
                'cost_fixed_eur': cost_fixed_eur,
            })
    
    return pd.DataFrame(data)


def generate_guidance_data() -> pd.DataFrame:
    """
    Generate Commercial Guidance (Table C) with pricing tiers and validity dates.
    """
    today = datetime.now().date()
    valid_from = today - timedelta(days=365)
    valid_to = today + timedelta(days=365)
    
    classifications = ['Europe Domestic', 'NorthAmerica Domestic', 'Global']
    
    volume_tiers = [
        (0, 100000),
        (100000, 500000),
        (500000, 1000000),
        (1000000, 5000000),
        (5000000, 50000000),
        (50000000, float('inf')),
    ]
    
    tier_discounts = [1.0, 0.95, 0.90, 0.85, 0.80, 0.75]
    
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
    
    base_fees = {
        'Europe Domestic': {'var': 0.006, 'fixed': 0.05},
        'NorthAmerica Domestic': {'var': 0.0065, 'fixed': 0.055},
        'Global': {'var': 0.008, 'fixed': 0.07},
    }
    
    product_fee_multipliers = {
        'AcquiringService': {'var': 1.0, 'fixed': 1.0},
        'ProcessingService': {'var': 0.0, 'fixed': 1.2},
        'RevenueProtectService': {'var': 0.3, 'fixed': 0.0},
    }
    
    variant_fee_multipliers = {
        'visa': 1.0,
        'mc': 1.02,
        'amex': 1.4,
        'maestro': 0.9,
        'N/A': 1.0,
    }
    
    data = []
    for material_code, tx_variant in products:
        for classification in classifications:
            for (min_vol, max_vol), discount in zip(volume_tiers, tier_discounts):
                base = base_fees[classification]
                prod_mult = product_fee_multipliers[material_code]
                var_mult = variant_fee_multipliers[tx_variant]
                
                advised_fee_variable = round(base['var'] * prod_mult['var'] * var_mult * discount, 6)
                advised_fee_fixed_eur = round(base['fixed'] * prod_mult['fixed'] * var_mult * discount, 4)
                
                max_vol_display = max_vol if max_vol != float('inf') else 999999999999
                
                data.append({
                    'material_code': material_code,
                    'tx_variant': tx_variant,
                    'price_guidance_classification': classification,
                    'min_vol_eur': min_vol,
                    'max_vol_eur': max_vol_display,
                    'valid_from': pd.Timestamp(valid_from),
                    'valid_to': pd.Timestamp(valid_to),
                    'advised_fee_variable': advised_fee_variable,
                    'advised_fee_fixed_eur': advised_fee_fixed_eur,
                })
    
    return pd.DataFrame(data)


def get_material_codes() -> list:
    """Return list of available material codes."""
    return ['AcquiringService', 'ProcessingService', 'RevenueProtectService']


def get_tx_variants() -> list:
    """Return list of available transaction variants."""
    return ['visa', 'mc', 'amex', 'maestro', 'N/A']


def get_classifications() -> list:
    """Return list of available price guidance classifications."""
    return ['Europe Domestic', 'NorthAmerica Domestic', 'Global']


def create_empty_deal_row() -> dict:
    """Create an empty deal input row with default values."""
    return {
        'material_code': 'AcquiringService',
        'tx_variant': 'visa',
        'volume_eur': 100000.0,
        'tx_count': 1000,
        'proposed_variable_pct': 0.60,
        'proposed_fixed_eur': 0.05,
    }


def parse_uploaded_csv(uploaded_file, expected_columns: list) -> pd.DataFrame:
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


def get_costs_expected_columns() -> list:
    """Return expected columns for costs CSV upload."""
    return [
        'material_code', 'tx_variant', 'region_classification',
        'cost_variable', 'cost_fixed_eur'
    ]


def get_guidance_expected_columns() -> list:
    """Return expected columns for guidance CSV upload."""
    return [
        'material_code', 'tx_variant', 'price_guidance_classification',
        'min_vol_eur', 'max_vol_eur', 'valid_from', 'valid_to',
        'advised_fee_variable', 'advised_fee_fixed_eur'
    ]
